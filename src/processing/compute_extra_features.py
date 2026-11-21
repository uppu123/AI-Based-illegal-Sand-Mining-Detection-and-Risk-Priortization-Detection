# -*- coding: utf-8 -*-
"""Phase B/C: water fraction, Coal Mine Index (CMI) and river distance.

Computes three additional features for EVERY rebuilt Sentinel-2 composite
(5 annual + 6 quarterly) and for the 252 rebuilt chips:

1. Water fraction - per-scene Otsu threshold on decoded NDSI (band 14).
   NDSI = (B3 - B11)/(B3 + B11) is water-positive in this build, so water =
   pixels with NDSI greater than the Otsu threshold of the valid pixels.
2. CMI - Coal Mine Index from Mukherjee et al.: (B11 - B12)/(B11 + B12),
   computed from stored bands 9 and 10. The x10000 reflectance scaling
   cancels in the ratio, so no rescaling is needed.
3. Distance to river - metres from the existing river centreline GeoJSON,
   via rasterio rasterization + scipy euclidean distance transform.

All outputs go to a NEW folder (C:\\New folder\\extra_features by default).
Nothing under yamuna_data/ or yamuna_work/chips/ is modified.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import os
import sys
import time
from pathlib import Path

import numpy as np
import rasterio
from rasterio.features import rasterize
from rasterio.windows import from_bounds
from scipy.ndimage import distance_transform_edt
from skimage.filters import threshold_otsu

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
from config import project_config as cfg  # noqa: E402

ANNUAL = (2018, 2019, 2020, 2021, 2022)
QUARTERS = ("2023_Q1", "2023_Q2", "2023_Q3", "2023_Q4", "2024_Q1", "2024_Q2")
FIXED_S2 = cfg.WORKSPACE_ROOT / "yamuna_data_fixed" / "sentinel2"
FIXED_CHIPS = cfg.WORKSPACE_ROOT / "chips_fixed"
DEFAULT_OUT = cfg.WORKSPACE_ROOT / "extra_features"
CENTRELINE = cfg.CENTERLINE_PATH

NDSI_BAND = 14
B11_BAND, B12_BAND = 9, 10
INDEX_SCALE = 5000.0
EARTH_M = 111320.0


def composite_paths() -> list[tuple[str, Path]]:
    out = []
    for y in ANNUAL:
        out.append((str(y), FIXED_S2 / str(y) / f"S2_{y}_composite.tif"))
    for q in QUARTERS:
        out.append((q, FIXED_S2 / "2023_2024" / f"S2_{q}_composite.tif"))
    return [(lab, p) for lab, p in out if p.exists()]


def valid_mask(src) -> np.ndarray:
    """True where at least one of the 10 spectral bands is non-zero (nodata=0)."""
    spec = src.read(list(range(1, 11)))
    return np.any(spec != 0, axis=0)


def write_raster(path: Path, array: np.ndarray, profile: dict, dtype: str,
                 nodata, description: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    p = profile.copy()
    p.update(dtype=dtype, count=1, nodata=nodata, compress="lzw")
    with rasterio.open(path, "w", **p) as dst:
        dst.write(array.astype(dtype), 1)
        dst.set_band_description(1, description)


def process_scene(label: str, src_path: Path, out: Path) -> dict:
    t0 = time.time()
    with rasterio.open(src_path) as src:
        profile = src.profile.copy()
        valid = valid_mask(src)

        # ---- NDSI -> per-scene Otsu water mask ----
        raw = src.read(NDSI_BAND).astype(np.float32)
        ndsi = np.where(raw > 0, raw / INDEX_SCALE - 1.0, np.nan).astype(np.float32)
        ok = valid & np.isfinite(ndsi)
        thr_otsu = float(threshold_otsu(ndsi[ok]))
        # (B3-B11)/(B3+B11) is MNDWI (Xu 2006): water is POSITIVE. If Otsu
        # falls below zero it is splitting the dominant sand class, not finding
        # water (observed on dry-season Q2: Otsu -0.183 -> 49% "water", while
        # only 1.82% of pixels are water-positive). Clamp to the physical
        # water-positive boundary and keep the raw value for transparency.
        thr = max(thr_otsu, 0.0)
        water = ok & (ndsi > thr)
        water_u8 = np.where(valid, water.astype(np.uint8), 0).astype(np.uint8)
        water_frac = float(water[valid].mean()) if valid.any() else 0.0
        fixed_frac = float((ndsi[valid] > 0).mean()) if valid.any() else 0.0

        # ---- CMI (Mukherjee): (B11 - B12)/(B11 + B12) ----
        b11 = src.read(B11_BAND).astype(np.float32)
        b12 = src.read(B12_BAND).astype(np.float32)
        den = b11 + b12
        cmi = np.full(den.shape, np.nan, dtype=np.float32)
        good = den > 0
        cmi[good] = (b11[good] - b12[good]) / den[good]
        cmi = np.where(valid, cmi, np.nan).astype(np.float32)
        cmi_mean = float(np.nanmean(cmi)) if np.isfinite(cmi).any() else float("nan")

        # ---- distance to centreline (metres) ----
        import geopandas as gpd
        gdf = gpd.read_file(CENTRELINE)
        geoms = [g for g in gdf.geometry if g is not None and not g.is_empty]
        line_mask = rasterize(
            [(g, 1) for g in geoms],
            out_shape=(src.height, src.width),
            transform=src.transform,
            fill=0, all_touched=True, dtype="uint8",
        )
        lat_mid = math.radians((cfg.AOI_SOUTH + cfg.AOI_NORTH) / 2.0)
        px_m = abs(src.transform.a) * EARTH_M * math.cos(lat_mid)
        py_m = abs(src.transform.e) * EARTH_M
        dist = distance_transform_edt(line_mask == 0, sampling=(py_m, px_m))
        dist = np.where(valid, dist.astype(np.float32), np.nan).astype(np.float32)
        dist_mean = float(np.nanmean(dist)) if np.isfinite(dist).any() else float("nan")
        dist_max = float(np.nanmax(dist)) if np.isfinite(dist).any() else float("nan")

    # ---- write rasters ----
    folder = out / "rasters" / label
    write_raster(folder / f"water_mask_{label}.tif", water_u8, profile,
                 "uint8", 0, "water=1 (NDSI > scene Otsu threshold)")
    write_raster(folder / f"cmi_{label}.tif", cmi, profile,
                 "float32", np.nan, "CMI=(B11-B12)/(B11+B12)")
    write_raster(folder / f"distance_m_{label}.tif", dist, profile,
                 "float32", np.nan, "distance_m_to_river_centreline")

    print(f"  {label:<8} water={water_frac:6.2%} (otsu {thr_otsu:+.3f}->applied {thr:+.3f}) "
          f"CMI={cmi_mean:+.4f} dist={dist_mean:6.0f}m (max {dist_max:.0f}m)  [{time.time()-t0:.1f}s]")
    return {
        "label": label,
        "source": str(src_path),
        "bands": 14,
        "valid_fraction": round(float(valid.mean()), 4),
        "water_threshold_otsu_raw": round(thr_otsu, 4),
        "water_threshold_applied": round(thr, 4),
        "water_fraction_otsu": round(water_frac, 5),
        "water_fraction_fixed_gt0": round(fixed_frac, 5),
        "cmi_mean": round(cmi_mean, 5),
        "distance_mean_m": round(dist_mean, 1),
        "distance_max_m": round(dist_max, 1),
        "seconds": round(time.time() - t0, 1),
    }


def chip_features(out: Path) -> list[dict]:
    """Per-chip stats from the three feature rasters (6 quarters x 42 chips)."""
    rows = []
    for q in QUARTERS:
        folder = out / "rasters" / q
        paths = {
            "water": folder / f"water_mask_{q}.tif",
            "cmi": folder / f"cmi_{q}.tif",
            "dist": folder / f"distance_m_{q}.tif",
        }
        if not all(p.exists() for p in paths.values()):
            continue
        handles = {k: rasterio.open(p) for k, p in paths.items()}
        chip_dir = FIXED_CHIPS / q
        for chip in sorted(chip_dir.glob(f"T*_{q}.tif")):
            with rasterio.open(chip) as c:
                b = c.bounds
            vals = {}
            for k, ds in handles.items():
                win = from_bounds(*b, transform=ds.transform)
                arr = ds.read(1, window=win, boundless=True,
                              fill_value=np.nan).astype(np.float64)
                if k == "water":
                    vals["water_frac"] = round(float(np.nanmean(arr)), 4)
                elif k == "cmi":
                    vals["cmi_mean"] = round(float(np.nanmean(arr)), 4)
                else:
                    vals["distance_mean_m"] = round(float(np.nanmean(arr)), 1)
                    vals["distance_min_m"] = round(float(np.nanmin(arr)), 1)
            rows.append({"chip_id": chip.stem, "quarter": q,
                         "transect_id": chip.stem.split("_")[0], **vals})
        for ds in handles.values():
            ds.close()
    return rows


def write_csv(path: Path, rows: list[dict]) -> None:
    if not rows:
        return
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)


def main() -> int:
    ap = argparse.ArgumentParser(description="Compute water fraction, CMI and river distance")
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    ap.add_argument("--only", nargs="*", default=None, help="process only these labels")
    args = ap.parse_args()

    out = args.out
    out.mkdir(parents=True, exist_ok=True)
    print("Output:", out)
    print("Centreline:", CENTRELINE)

    scenes = composite_paths()
    if args.only:
        scenes = [(l, p) for l, p in scenes if l in args.only]
    print("Composites:", len(scenes))

    t0 = time.time()
    summary = []
    for label, path in scenes:
        summary.append(process_scene(label, path, out))

    write_csv(out / "scene_features.csv", summary)
    chips = chip_features(out)
    write_csv(out / "chip_features.csv", chips)
    (out / "scene_features.json").write_text(
        json.dumps({"created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                    "formulas": {
                        "NDSI": "(B3 - B11)/(B3 + B11), decoded raw/5000 - 1",
                        "water_mask": "NDSI > max(per-scene Otsu, 0.0); MNDWI is water-positive so negative Otsu is rejected",
                        "CMI": "(B11 - B12)/(B11 + B12)  [Mukherjee et al.]",
                        "distance": "euclidean metres from rasterized centreline (EPSG:4326 -> metres)",
                    },
                    "scenes": summary}, indent=2), encoding="utf-8")

    print(f"\nscene rows: {len(summary)}   chip rows: {len(chips)}")
    print("elapsed:", round(time.time() - t0, 1), "s")
    print("written:", out / "scene_features.csv")
    print("written:", out / "chip_features.csv")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
