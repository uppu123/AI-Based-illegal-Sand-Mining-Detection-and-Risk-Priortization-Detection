#!/usr/bin/env python3
"""


extract_chips_all_quarters.py

Extract 256x256 chips from ALL Sentinel-2 quarterly composites (2023 Q1-Q4, 2024 Q1-Q2)
at each transect point. Saves to chips/<quarter>/ with same structure as 04_extract_chips.py.
"""
# --- central configuration (no hard-coded paths in pipeline scripts) ---
from pathlib import Path as _Path
import sys as _sys
_sys.path.insert(0, str(_Path(__file__).resolve().parents[2]))
from config import project_config as _cfg


import argparse
import sys
from pathlib import Path
import rasterio
from rasterio.windows import Window
import numpy as np
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
import warnings
warnings.filterwarnings("ignore")


# ============================================================
# CONFIGURATION
# ============================================================
S2_BASE = _cfg.S2_QUARTERLY_DIR
TRANSECT_TABLE = _cfg.TRANSECT_TABLE
BASE_OUTPUT = _cfg.CHIPS_S2_DIR

QUARTERS = ["2023_Q1", "2023_Q2", "2023_Q3", "2023_Q4", "2024_Q1", "2024_Q2"]

CHIP_SIZE = 256
HALF_CHIP = CHIP_SIZE // 2
MAX_NODATA_FRAC = 0.20
PCT_LOW, PCT_HIGH = 2, 98

# Band indices (1-indexed)
RGB_BANDS = (3, 2, 1)  # B4, B3, B2
NDSI_BAND = 14
SPECTRAL_BANDS_IDX = list(range(1, 11))  # 1-10

NODATA_VALUE = 0


def percentile_stretch(arr, low=PCT_LOW, high=PCT_HIGH):
    arr = arr.astype(np.float32)
    valid = arr[arr > 0]
    if len(valid) == 0:
        return np.zeros_like(arr, dtype=np.uint8)
    lo, hi = np.percentile(valid, [low, high])
    if hi <= lo:
        return np.zeros_like(arr, dtype=np.uint8)
    stretched = np.clip((arr - lo) / (hi - lo), 0, 1)
    return (stretched * 255).astype(np.uint8)


def decode_index(raw):
    return raw.astype(np.float32) / 5000.0 - 1.0


def process_quarter(quarter, df_transects, base_output):
    """Process one quarter composite."""
    s2_path = S2_BASE / f"S2_{quarter}_composite.tif"
    if not s2_path.exists():
        print(f"  [SKIP] Missing: {s2_path}")
        return 0, 0

    out_dir = base_output / quarter
    preview_dir = out_dir / "previews"
    out_dir.mkdir(parents=True, exist_ok=True)
    preview_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n=== {quarter} ===")
    print(f"  Source: {s2_path}")

    with rasterio.open(s2_path) as src:
        print(f"  Shape: {src.height}x{src.width}, Bands: {src.count}, Nodata: {src.nodata}")
        profile = src.profile.copy()
        profile.update({
            'width': CHIP_SIZE, 'height': CHIP_SIZE, 'count': 14,
            'transform': None, 'nodata': src.nodata
        })

        kept = 0
        skipped = 0
        kept_previews = []
        metadata_rows = []

        for _, row in df_transects.iterrows():
            tid = row['transect_id']
            lon, lat = row['lon'], row['lat']

            try:
                r, c = src.index(lon, lat)
            except Exception:
                skipped += 1
                metadata_rows.append({
                    'chip_id': f"{tid}_{quarter}", 'transect_id': tid,
                    'source_file': str(s2_path), 'center_lon': lon, 'center_lat': lat,
                    'status': 'skipped', 'skip_reason': 'index_error'
                })
                continue

            r0, c0 = r - HALF_CHIP, c - HALF_CHIP
            if r0 < 0 or c0 < 0 or r0 + CHIP_SIZE > src.height or c0 + CHIP_SIZE > src.width:
                skipped += 1
                metadata_rows.append({
                    'chip_id': f"{tid}_{quarter}", 'transect_id': tid,
                    'source_file': str(s2_path), 'center_lon': lon, 'center_lat': lat,
                    'status': 'skipped', 'skip_reason': 'outside_raster'
                })
                continue

            window = Window(c0, r0, CHIP_SIZE, CHIP_SIZE)
            try:
                chip = src.read(window=window)  # (14, 256, 256)
            except Exception:
                skipped += 1
                continue

            # Nodata check
            spectral = chip[:10]
            nodata_mask = np.all((spectral == 0) | (spectral == src.nodata), axis=0)
            nodata_frac = np.mean(nodata_mask)
            if nodata_frac > MAX_NODATA_FRAC:
                skipped += 1
                metadata_rows.append({
                    'chip_id': f"{tid}_{quarter}", 'transect_id': tid,
                    'source_file': str(s2_path), 'center_lon': lon, 'center_lat': lat,
                    'status': 'skipped', 'skip_reason': f'too_much_nodata ({nodata_frac:.2%})',
                    'nodata_fraction': round(nodata_frac, 4)
                })
                continue

            # Save chip
            chip_id = f"{tid}_{quarter}"
            chip_path = out_dir / f"{chip_id}.tif"
            win_transform = src.window_transform(window)
            chip_profile = profile.copy()
            chip_profile['transform'] = win_transform

            with rasterio.open(chip_path, 'w', **chip_profile) as dst:
                dst.write(chip)
                for i, desc in enumerate(["B2","B3","B4","B5","B6","B7","B8","B8A","B11","B12",
                                           "NDVI","NDWI","NDBI","NDSI"], 1):
                    dst.set_band_description(i, desc)

            # Previews
            rgb = np.stack([percentile_stretch(chip[RGB_BANDS[0]-1]),
                           percentile_stretch(chip[RGB_BANDS[1]-1]),
                           percentile_stretch(chip[RGB_BANDS[2]-1])], axis=-1)
            plt.imsave(preview_dir / f"{chip_id}_truecolour.png", rgb)

            ndsi_dec = decode_index(chip[NDSI_BAND-1])
            cmap = LinearSegmentedColormap.from_list('ndsi', ['blue', 'white', 'red'])
            ndsi_norm = np.clip((ndsi_dec + 1) / 2, 0, 1)
            ndsi_colored = cmap(ndsi_norm)[:, :, :3]
            plt.imsave(preview_dir / f"{chip_id}_NDSI.png", ndsi_colored)

            # Index means
            valid = ~nodata_mask
            ndvi = decode_index(chip[10])
            ndwi = decode_index(chip[11])
            ndbi = decode_index(chip[12])
            ndsi = decode_index(chip[13])

            metadata_rows.append({
                'chip_id': chip_id, 'transect_id': tid,
                'source_file': str(s2_path), 'center_lon': lon, 'center_lat': lat,
                'row': r, 'col': c, 'nodata_fraction': round(nodata_frac, 4),
                'mean_NDVI': round(float(np.mean(ndvi[valid])), 4) if np.any(valid) else '',
                'mean_NDWI': round(float(np.mean(ndwi[valid])), 4) if np.any(valid) else '',
                'mean_NDBI': round(float(np.mean(ndbi[valid])), 4) if np.any(valid) else '',
                'mean_NDSI': round(float(np.mean(ndsi[valid])), 4) if np.any(valid) else '',
                'mask_status': 'no_mask_band', 'status': 'kept', 'skip_reason': '',
                'overlap_with_prev_km': round(CHIP_SIZE * abs(src.transform.a) * 111320 * np.cos(np.radians(lat)) / 1000, 2)
            })

            kept_previews.append((chip_id, rgb))
            kept += 1

        # Contact sheet
        if kept_previews:
            n = len(kept_previews)
            cols = min(8, n)
            rows = (n + cols - 1) // cols
            fig, axes = plt.subplots(rows, cols, figsize=(cols*2, rows*2))
            if rows == 1: axes = axes.reshape(1, -1)
            elif cols == 1: axes = axes.reshape(-1, 1)
            for i, (cid, img) in enumerate(kept_previews):
                rr, cc = divmod(i, cols)
                axes[rr, cc].imshow(img)
                axes[rr, cc].set_title(cid, fontsize=6)
                axes[rr, cc].axis('off')
            for i in range(n, rows*cols):
                rr, cc = divmod(i, cols)
                axes[rr, cc].axis('off')
            plt.tight_layout()
            plt.savefig(preview_dir / "contact_sheet.png", dpi=150)
            plt.close()

        # Save metadata CSV
        meta_dir = _cfg.METADATA_DIR
        meta_dir.mkdir(exist_ok=True)
        df_meta = pd.DataFrame(metadata_rows)
        csv_path = meta_dir / f"chips_{quarter}.csv"
        df_meta.to_csv(csv_path, index=False)
        print(f"  Kept: {kept}, Skipped: {skipped} -> {csv_path}")

        return kept, skipped


def main():
    parser = argparse.ArgumentParser(description="Extract chips for all S2 quarters")
    parser.add_argument("--quarters", nargs="+", default=QUARTERS, help="Quarters to process")
    args = parser.parse_args()

    df_transects = pd.read_csv(TRANSECT_TABLE)
    print(f"Loaded {len(df_transects)} transects")

    total_kept = total_skipped = 0
    for q in args.quarters:
        k, s = process_quarter(q, df_transects, BASE_OUTPUT)
        total_kept += k
        total_skipped += s

    print(f"\n=== TOTAL ===")
    print(f"Kept: {total_kept}, Skipped: {total_skipped}")
    print(f"Output dirs: {BASE_OUTPUT}/<quarter>/")

if __name__ == "__main__":
    main()