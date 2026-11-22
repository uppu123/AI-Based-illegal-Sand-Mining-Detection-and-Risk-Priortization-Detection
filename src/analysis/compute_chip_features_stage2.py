# -*- coding: utf-8 -*-
"""Stage 2: compute 252-chip feature table + water-threshold candidates.

Protocol constraints:
- Read-only inputs: yamuna_data, yamuna_data_fixed, chips_fixed, verified_labels.
- Do NOT choose water threshold. Write candidates + histogram; leave
  water_frac/dependent fields blank in features_v2 until student decision.
- Do NOT use 2024 composites/chips for threshold selection.
- Writes new files only.
"""
from __future__ import annotations

import argparse
import csv
import json
import logging
import math
from pathlib import Path

import numpy as np
import rasterio

BANDS = ["B2","B3","B4","B5","B6","B7","B8","B8A","B11","B12","NDVI","NDWI","NDBI","NDSI"]
IDX = {b:i for i,b in enumerate(BANDS)}


def setup_logger(log_path: Path) -> logging.Logger:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger("stage2_features")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()
    fmt = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
    fh = logging.FileHandler(log_path, encoding="utf-8")
    fh.setFormatter(fmt)
    sh = logging.StreamHandler()
    sh.setFormatter(fmt)
    logger.addHandler(fh)
    logger.addHandler(sh)
    return logger


def decode_index(raw: np.ndarray) -> np.ndarray:
    arr = raw.astype(np.float32)
    valid = raw != 0
    out = np.full(arr.shape, np.nan, dtype=np.float32)
    out[valid] = arr[valid] / 5000.0 - 1.0
    return out


def safe_mean(a: np.ndarray) -> float:
    v = a[np.isfinite(a)]
    return float(v.mean()) if v.size else float("nan")


def safe_std(a: np.ndarray) -> float:
    v = a[np.isfinite(a)]
    return float(v.std()) if v.size else float("nan")


def main() -> int:
    ap = argparse.ArgumentParser(description="Stage 2 chip features and water-threshold candidates")
    ap.add_argument("--chips-dir", type=Path, default=Path(r"C:\New folder\chips_fixed"))
    ap.add_argument("--extra-features", type=Path, default=Path(r"C:\New folder\extra_features\chip_features.csv"))
    ap.add_argument("--out-dir", type=Path, default=Path(r"C:\Users\upend\AI-Based-illegal-Sand-Mining-Detection-and-Risk-Priortization\metadata"))
    ap.add_argument("--docs-dir", type=Path, default=Path(r"C:\Users\upend\AI-Based-illegal-Sand-Mining-Detection-and-Risk-Priortization\docs"))
    ap.add_argument("--log", type=Path, default=Path(r"C:\Users\upend\AI-Based-illegal-Sand-Mining-Detection-and-Risk-Priortization\reports\logs\stage2_features.log"))
    args = ap.parse_args()

    logger = setup_logger(args.log)
    args.out_dir.mkdir(parents=True, exist_ok=True)
    args.docs_dir.mkdir(parents=True, exist_ok=True)

    chips = sorted(args.chips_dir.glob("**/T*_????_Q?.tif"))
    logger.info("chips found: %d", len(chips))
    if len(chips) != 252:
        logger.warning("Expected 252 chips, found %d", len(chips))

    extra = {}
    if args.extra_features.exists():
        with args.extra_features.open("r", encoding="utf-8-sig", newline="") as f:
            for row in csv.DictReader(f):
                extra[row["chip_id"]] = row
        logger.info("extra features rows: %d", len(extra))
    else:
        logger.warning("extra features not found: %s", args.extra_features)

    rows = []
    ndsi_2023 = []
    for p in chips:
        quarter = p.parent.name
        chip_id = p.stem
        transect_id = chip_id.split("_")[0]
        with rasterio.open(p) as ds:
            desc = list(ds.descriptions)
            data = ds.read()
        if desc != BANDS:
            logger.warning("Unexpected band descriptions for %s: %s", chip_id, desc)
        # valid where spectral bands non-zero
        valid = np.all(data[:10] != 0, axis=0)
        n_valid = int(valid.sum())
        n_total = int(valid.size)
        ndvi = decode_index(data[IDX["NDVI"]])[valid]
        ndwi = decode_index(data[IDX["NDWI"]])[valid]
        ndbi = decode_index(data[IDX["NDBI"]])[valid]
        ndsi = decode_index(data[IDX["NDSI"]])[valid]
        if quarter.startswith("2023"):
            ndsi_2023.append(ndsi[np.isfinite(ndsi)])
        ex = extra.get(chip_id, {})
        row = {
            "chip_id": chip_id,
            "quarter": quarter,
            "transect_id": transect_id,
            "valid_pixels": n_valid,
            "total_pixels": n_total,
            "valid_fraction": round(n_valid / n_total, 6) if n_total else "",
            "ndvi_mean": round(safe_mean(ndvi), 6),
            "ndvi_std": round(safe_std(ndvi), 6),
            "ndwi_mean": round(safe_mean(ndwi), 6),
            "ndwi_std": round(safe_std(ndwi), 6),
            "ndbi_mean": round(safe_mean(ndbi), 6),
            "ndbi_std": round(safe_std(ndbi), 6),
            "ndsi_mean": round(safe_mean(ndsi), 6),
            "ndsi_std": round(safe_std(ndsi), 6),
            "cmi_mean": ex.get("cmi_mean", ""),
            "distance_mean_m": ex.get("distance_mean_m", ""),
            "distance_min_m": ex.get("distance_min_m", ""),
            # water_frac intentionally blank until student threshold decision
            "water_frac": "",
            "water_threshold": "",
            "water_threshold_status": "PENDING_STUDENT_DECISION",
        }
        rows.append(row)

    # write raw/provisional features
    raw_path = args.out_dir / "features_stage2_raw.csv"
    with raw_path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    logger.info("wrote %s", raw_path)

    # features_v2: same but explicit gate - water_frac blank
    v2_path = args.out_dir / "features_v2.csv"
    with v2_path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    logger.info("wrote %s (water_frac blank pending decision)", v2_path)

    # Water threshold candidates - 2023 only
    ndsi2023 = np.concatenate(ndsi_2023) if ndsi_2023 else np.array([], dtype=np.float32)
    ndsi2023 = ndsi2023[np.isfinite(ndsi2023)]
    candidates = []
    for t in [-0.10, -0.05, 0.0, 0.05, 0.10]:
        frac = float((ndsi2023 > t).mean()) if ndsi2023.size else float("nan")
        candidates.append({"threshold_ndsi_gt": t, "water_pixel_fraction_2023": round(frac, 6)})
    # percentiles for context
    pcts = {p: float(np.percentile(ndsi2023, p)) for p in [50,75,90,95,99]} if ndsi2023.size else {}

    # Histogram
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(8,4.5))
    ax.hist(ndsi2023, bins=120, color="#4C78A8", alpha=0.85)
    for c in candidates:
        t=c["threshold_ndsi_gt"]
        ax.axvline(t, color="red", linestyle="--", linewidth=1, alpha=0.7)
        ax.text(t, ax.get_ylim()[1]*0.95, f" {t}", rotation=90, va="top", fontsize=8, color="red")
    ax.set_title("NDSI distribution (2023 chips only) - threshold selection excludes 2024")
    ax.set_xlabel("NDSI (decoded)")
    ax.set_ylabel("Pixel count")
    ax.grid(alpha=0.25)
    hist_path = args.out_dir / "water_hist.png"
    fig.tight_layout()
    fig.savefig(hist_path, dpi=160)
    plt.close(fig)
    logger.info("wrote %s", hist_path)

    cand_path = args.docs_dir / "water_threshold_candidates.md"
    lines = [
        "# Stage 2 - Water Threshold Candidates",
        "",
        "Generated from 2023 chips only (2024 excluded from threshold selection).",
        "Student must choose threshold and record decision in `docs/water_threshold_decision.md`.",
        "Until decision: `water_frac` remains blank and water-dependent features are PROVISIONAL.",
        "",
        f"- 2023 NDSI pixels (valid, finite): {ndsi2023.size}",
        f"- NDSI percentiles (2023): " + ", ".join([f"p{p}={v:.4f}" for p,v in pcts.items()]),
        "",
        "## Candidates",
        "",
        "| Candidate (NDSI > t) | 2023 water pixel fraction | Notes |",
        "|---:|---:|---|",
    ]
    notes = {
        -0.10: "Very permissive; likely includes wet sand/mixed pixels",
        -0.05: "Permissive",
        0.0: "Physical water-positive boundary (MNDWI>0 style); conservative",
        0.05: "Conservative",
        0.10: "Very conservative; may miss shallow/turbid water",
    }
    for c in candidates:
        t=c["threshold_ndsi_gt"]
        lines.append(f"| {t:.2f} | {c['water_pixel_fraction_2023']:.6f} | {notes.get(t,'')} |")
    lines += [
        "",
        "## Histogram",
        f"- `metadata/water_hist.png`",
        "",
        "## Decision required",
        "Create `docs/water_threshold_decision.md` with:",
        "- chosen threshold (value)",
        "- rationale",
        "- date and approver (student)",
        "- statement: 2024 was not used for threshold selection",
    ]
    cand_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    logger.info("wrote %s", cand_path)

    summary = {
        "chips": len(rows),
        "ndsi_2023_pixels": int(ndsi2023.size),
        "percentiles_2023": pcts,
        "candidates": candidates,
        "water_frac_status": "PENDING_STUDENT_DECISION",
    }
    (args.out_dir / "features_stage2_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    logger.info("stage2 compute complete")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
