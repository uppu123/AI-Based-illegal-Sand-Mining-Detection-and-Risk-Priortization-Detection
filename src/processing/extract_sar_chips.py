#!/usr/bin/env python3
"""


extract_sar_chips.py

Extract 256x256 Sentinel-1 VV/VH chips at each transect point for all quarters.
Saves to chips_s1/<quarter>/ with VV and VH as separate bands (2-band GeoTIFF).
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
import matplotlib.pyplot as plt
import warnings
warnings.filterwarnings("ignore")


# ============================================================
# CONFIGURATION
# ============================================================
S1_BASE = _cfg.S1_QUARTERLY_DIR
TRANSECT_TABLE = _cfg.TRANSECT_TABLE
BASE_OUTPUT = _cfg.CHIPS_S1_DIR

QUARTERS = ["2023_Q1", "2023_Q2", "2023_Q3", "2023_Q4", "2024_Q1", "2024_Q2"]

CHIP_SIZE = 256
HALF_CHIP = CHIP_SIZE // 2
MAX_NODATA_FRAC = 0.20
PCT_LOW, PCT_HIGH = 2, 98

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


def process_quarter(quarter, df_transects, base_output):
    """Process one quarter: VV and VH."""
    vv_path = S1_BASE / f"S1_{quarter}_VV.tif"
    vh_path = S1_BASE / f"S1_{quarter}_VH.tif"

    if not vv_path.exists() or not vh_path.exists():
        print(f"  [SKIP] Missing VV or VH for {quarter}")
        return 0, 0

    out_dir = base_output / quarter
    preview_dir = out_dir / "previews"
    out_dir.mkdir(parents=True, exist_ok=True)
    preview_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n=== {quarter} (S1 VV+VH) ===")

    with rasterio.open(vv_path) as src_vv, rasterio.open(vh_path) as src_vh:
        print(f"  VV: {src_vv.width}x{src_vv.height}, VH: {src_vh.width}x{src_vh.height}")
        assert src_vv.crs == src_vh.crs == "EPSG:4326"
        assert src_vv.transform.almost_equals(src_vh.transform)
        assert src_vv.width == src_vh.width and src_vv.height == src_vh.height

        profile = src_vv.profile.copy()
        profile.update({
            'width': CHIP_SIZE, 'height': CHIP_SIZE, 'count': 2,
            'transform': None, 'nodata': src_vv.nodata
        })

        df_transects = pd.read_csv(_cfg.TRANSECT_TABLE)
        kept = skipped = 0
        metadata_rows = []

        for _, row in df_transects.iterrows():
            tid = row['transect_id']
            lon, lat = row['lon'], row['lat']

            try:
                r, c = src_vv.index(lon, lat)
            except Exception:
                skipped += 1
                metadata_rows.append({
                    'chip_id': f"{tid}_{quarter}", 'transect_id': tid,
                    'source_vv': str(vv_path), 'source_vh': str(vh_path),
                    'center_lon': lon, 'center_lat': lat,
                    'status': 'skipped', 'skip_reason': 'index_error'
                })
                continue

            r0, c0 = r - HALF_CHIP, c - HALF_CHIP
            if r0 < 0 or c0 < 0 or r0 + CHIP_SIZE > src_vv.height or c0 + CHIP_SIZE > src_vv.width:
                skipped += 1
                metadata_rows.append({
                    'chip_id': f"{tid}_{quarter}", 'transect_id': tid,
                    'source_vv': str(vv_path), 'source_vh': str(vh_path),
                    'center_lon': lon, 'center_lat': lat,
                    'status': 'skipped', 'skip_reason': 'outside_raster'
                })
                continue

            window = Window(c0, r0, CHIP_SIZE, CHIP_SIZE)

            vv_chip = src_vv.read(1, window=window)
            vh_chip = src_vh.read(1, window=window)

            # Nodata check (0 is nodata for S1)
            nodata_mask = (vv_chip == 0) | (vh_chip == 0)
            nodata_frac = np.mean(nodata_mask)
            if nodata_frac > MAX_NODATA_FRAC:
                skipped += 1
                metadata_rows.append({
                    'chip_id': f"{tid}_{quarter}", 'transect_id': tid,
                    'source_vv': str(vv_path), 'source_vh': str(vh_path),
                    'center_lon': lon, 'center_lat': lat,
                    'status': 'skipped', 'skip_reason': f'too_much_nodata ({nodata_frac:.2%})',
                    'nodata_fraction': round(nodata_frac, 4)
                })
                continue

            # Save 2-band GeoTIFF (VV, VH)
            chip_id = f"{tid}_{quarter}"
            chip_path = out_dir / f"{chip_id}.tif"
            win_transform = src_vv.window_transform(window)
            chip_profile = profile.copy()
            chip_profile.update({'transform': win_transform, 'count': 2})

            with rasterio.open(chip_path, 'w', **chip_profile) as dst:
                dst.write(vv_chip, 1)
                dst.write(vh_chip, 2)
                dst.set_band_description(1, 'VV')
                dst.set_band_description(2, 'VH')

            # Previews
            vv_stretch = percentile_stretch(vv_chip)
            vh_stretch = percentile_stretch(vh_chip)
            # False colour: VV=Red, VH=Green, (VV+VH)/2=Blue
            false_colour = np.stack([vv_stretch, vh_stretch, (vv_stretch + vh_stretch) // 2], axis=-1)
            plt.imsave(preview_dir / f"{chip_id}_falsecolour.png", false_colour)

            # Individual pol previews
            plt.imsave(preview_dir / f"{chip_id}_VV.png", vv_stretch, cmap='gray')
            plt.imsave(preview_dir / f"{chip_id}_VH.png", vh_stretch, cmap='gray')

            metadata_rows.append({
                'chip_id': chip_id, 'transect_id': tid,
                'source_vv': str(vv_path), 'source_vh': str(vh_path),
                'center_lon': lon, 'center_lat': lat,
                'row': r, 'col': c, 'nodata_fraction': round(nodata_frac, 4),
                'mean_VV': round(float(np.mean(vv_chip[~nodata_mask])), 2) if np.any(~nodata_mask) else '',
                'mean_VH': round(float(np.mean(vh_chip[~nodata_mask])), 2) if np.any(~nodata_mask) else '',
                'status': 'kept', 'skip_reason': '',
                'overlap_with_prev_km': round(CHIP_SIZE * abs(src_vv.transform.a) * 111320 * np.cos(np.radians(lat)) / 1000, 2)
            })

            kept += 1

        # Contact sheet (false colour)
        kept_chips = [r for r in metadata_rows if r['status'] == 'kept']
        if kept_chips:
            # Reload images for contact sheet
            n = len(kept_chips)
            cols = min(8, n)
            rows = (n + cols - 1) // cols
            fig, axes = plt.subplots(rows, cols, figsize=(cols*2, rows*2))
            if rows == 1: axes = axes.reshape(1, -1)
            elif cols == 1: axes = axes.reshape(-1, 1)
            for i, meta in enumerate(kept_chips):
                rr, cc = divmod(i, cols)
                img_path = preview_dir / f"{meta['chip_id']}_falsecolour.png"
                if img_path.exists():
                    axes[rr, cc].imshow(plt.imread(img_path))
                axes[rr, cc].set_title(meta['chip_id'], fontsize=6)
                axes[rr, cc].axis('off')
            for i in range(n, rows*cols):
                rr, cc = divmod(i, cols)
                axes[rr, cc].axis('off')
            plt.tight_layout()
            plt.savefig(preview_dir / "contact_sheet.png", dpi=150)
            plt.close()

        # Save metadata
        meta_dir = _cfg.METADATA_DIR
        meta_dir.mkdir(exist_ok=True)
        csv_path = meta_dir / f"chips_s1_{quarter}.csv"
        pd.DataFrame(metadata_rows).to_csv(csv_path, index=False)
        print(f"  Kept: {kept}, Skipped: {skipped} -> {csv_path}")

        return kept, skipped


def main():
    parser = argparse.ArgumentParser(description="Extract S1 VV/VH chips for all quarters")
    parser.add_argument("--quarters", nargs="+", default=QUARTERS, help="Quarters to process")
    args = parser.parse_args()

    total_k = total_s = 0
    for q in args.quarters:
        k, s = process_quarter(q, None, BASE_OUTPUT)
        total_k += k
        total_s += s

    print(f"\n=== TOTAL S1 ===")
    print(f"Kept: {total_k}, Skipped: {total_s}")
    print(f"Output: {BASE_OUTPUT}/<quarter>/")

if __name__ == "__main__":
    main()