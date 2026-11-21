#!/usr/bin/env python3
"""


04_extract_training_chips.py

Extract 256x256 chips from S2_2023_Q2_composite.tif at each transect point.
Saves chips as GeoTIFF and creates previews (true colour, NDSI, contact sheet).
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
from rasterio.transform import Affine
import numpy as np
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
import warnings
warnings.filterwarnings("ignore")


# ============================================================
# CONFIGURATION
# ============================================================
S2_PATH = _cfg.S2_Q2_COMPOSITE
TRANSECT_TABLE = _cfg.TRANSECT_TABLE
TRANSECT_POINTS = _cfg.TRANSECT_POINTS
OUTPUT_DIR = _cfg.CHIPS_S2_Q2_DIR
PREVIEW_DIR = OUTPUT_DIR / "previews"
METADATA_DIR = _cfg.METADATA_DIR

CHIP_SIZE = 256
HALF_CHIP = CHIP_SIZE // 2  # 128

# Band indices (1-indexed in rasterio)
# S2 composite: B2,B3,B4,B5,B6,B7,B8,B8A,B11,B12,NDVI,NDWI,NDBI,NDSI
RGB_BANDS = (3, 2, 1)  # B4, B3, B2 (Red, Green, Blue) - 1-indexed
NDSI_BAND = 14  # NDSI is band 14
SPECTRAL_BANDS = list(range(1, 11))  # Bands 1-10 (B2-B12)

# Nodata threshold for spectral bands
NODATA_VALUE = 0

# Percentile stretch for true colour
PCT_LOW = 2
PCT_HIGH = 98

# Nodata fraction threshold
MAX_NODATA_FRAC = 0.20


def percentile_stretch(arr, low=PCT_LOW, high=PCT_HIGH):
    """Apply percentile stretch to array."""
    arr = arr.astype(np.float32)
    valid = arr[arr > 0]  # Ignore zeros
    if len(valid) == 0:
        return np.zeros_like(arr, dtype=np.uint8)
    lo, hi = np.percentile(valid, [low, high])
    if hi <= lo:
        return np.zeros_like(arr, dtype=np.uint8)
    stretched = np.clip((arr - lo) / (hi - lo), 0, 1)
    return (stretched * 255).astype(np.uint8)


def decode_index(raw):
    """Decode index from uint16: value = (index + 1) * 5000."""
    return raw.astype(np.float32) / 5000.0 - 1.0


def main():
    parser = argparse.ArgumentParser(description="Extract 2023_Q2 chips at transect points")
    parser.add_argument("--chip-size", type=int, default=CHIP_SIZE, help="Chip size in pixels")
    parser.add_argument("--max-nodata", type=float, default=MAX_NODATA_FRAC, help="Max nodata fraction")
    args = parser.parse_args()

    chip_size = args.chip_size
    half_chip = chip_size // 2
    max_nodata_frac = args.max_nodata

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    PREVIEW_DIR.mkdir(parents=True, exist_ok=True)
    METADATA_DIR.mkdir(parents=True, exist_ok=True)

    # Load transect table
    print("Loading transect table...")
    df_transects = pd.read_csv(TRANSECT_TABLE)
    print(f"  {len(df_transects)} transects")

    # Open S2 composite
    print(f"Opening S2 composite: {S2_PATH}")
    with rasterio.open(S2_PATH) as src:
        print(f"  CRS: {src.crs}")
        print(f"  Shape: {src.height} x {src.width}")
        print(f"  Bands: {src.count}")
        print(f"  Nodata: {src.nodata}")
        print(f"  Transform: {src.transform}")
        
        # Read band descriptions
        descs = src.descriptions if src.descriptions else []
        print(f"  Band descriptions: {descs}")
        
        # Verify 14 bands
        if src.count != 14:
            print(f"WARNING: Expected 14 bands, got {src.count}")
        
        profile = src.profile.copy()
        profile.update({
            'width': chip_size,
            'height': chip_size,
            'count': 14,
            'transform': None,  # will set per chip
            'nodata': src.nodata
        })

        # Process each transect
        chips_kept = []
        chips_skipped = []
        kept_previews = []

        for idx, row in df_transects.iterrows():
            transect_id = row['transect_id']
            lon = row['lon']
            lat = row['lat']

            # Convert lon/lat to row/col
            try:
                row_idx, col_idx = src.index(lon, lat)
            except Exception as e:
                chips_skipped.append({
                    'transect_id': transect_id,
                    'reason': f'index_error: {e}',
                    'lon': lon, 'lat': lat
                })
                continue

            # Check if window is within raster bounds
            win_row_start = row_idx - half_chip
            win_col_start = col_idx - half_chip
            win_row_end = win_row_start + chip_size
            win_col_end = win_col_start + chip_size

            outside_raster = False
            if win_row_start < 0 or win_col_start < 0 or \
               win_row_end > src.height or win_col_end > src.width:
                outside_raster = True

            if outside_raster:
                chips_skipped.append({
                    'transect_id': transect_id,
                    'reason': 'outside_raster',
                    'lon': lon, 'lat': lat,
                    'row': row_idx, 'col': col_idx
                })
                continue

            # Define window
            window = Window(win_col_start, win_row_start, chip_size, chip_size)

            # Read all 14 bands
            try:
                chip_data = src.read(window=window)  # shape: (14, 256, 256)
            except Exception as e:
                chips_skipped.append({
                    'transect_id': transect_id,
                    'reason': f'read_error: {e}',
                    'lon': lon, 'lat': lat
                })
                continue

            # Check nodata fraction
            # A pixel is nodata if ALL 10 spectral bands are 0 or nodata
            spectral = chip_data[:10]  # First 10 bands (B2-B12)
            if src.nodata is not None:
                nodata_mask = np.all((spectral == 0) | (spectral == src.nodata), axis=0)
            else:
                nodata_mask = np.all(spectral == 0, axis=0)
            
            nodata_frac = np.sum(nodata_mask) / (chip_size * chip_size)

            if nodata_frac > max_nodata_frac:
                chips_skipped.append({
                    'transect_id': transect_id,
                    'reason': f'too_much_nodata ({nodata_frac:.2%})',
                    'lon': lon, 'lat': lat,
                    'row': row_idx, 'col': col_idx,
                    'nodata_frac': round(nodata_frac, 4)
                })
                continue

            # Compute window transform
            win_transform = src.window_transform(window)

            # Compute index means
            ndvi_raw = chip_data[10]  # Band 11
            ndwi_raw = chip_data[11]  # Band 12
            ndbi_raw = chip_data[12]  # Band 13
            ndsi_raw = chip_data[13]  # Band 14

            ndvi_dec = decode_index(ndvi_raw)
            ndwi_dec = decode_index(ndwi_raw)
            ndbi_dec = decode_index(ndbi_raw)
            ndsi_dec = decode_index(ndsi_raw)

            # Mask out nodata pixels for mean calculation
            valid_mask = ~nodata_mask
            if np.any(valid_mask):
                mean_ndvi = float(np.mean(ndvi_dec[valid_mask]))
                mean_ndwi = float(np.mean(ndwi_dec[valid_mask]))
                mean_ndbi = float(np.mean(ndbi_dec[valid_mask]))
                mean_ndsi = float(np.mean(ndsi_dec[valid_mask]))
            else:
                mean_ndvi = mean_ndwi = mean_ndbi = mean_ndsi = np.nan

            # Save chip GeoTIFF
            chip_filename = f"{transect_id}_2023Q2.tif"
            chip_path = OUTPUT_DIR / chip_filename
            
            chip_profile = profile.copy()
            chip_profile['transform'] = win_transform
            
            with rasterio.open(chip_path, 'w', **chip_profile) as dst:
                dst.write(chip_data)
                # Write band descriptions
                band_descs = ["B2", "B3", "B4", "B5", "B6", "B7", "B8", "B8A", "B11", "B12",
                             "NDVI", "NDWI", "NDBI", "NDSI"]
                for i, desc in enumerate(band_descs, 1):
                    dst.set_band_description(i, desc)

            # Create previews
            # True colour: bands 3,2,1 (B4,B3,B2) -> RGB
            r = chip_data[RGB_BANDS[0] - 1]
            g = chip_data[RGB_BANDS[1] - 1]
            b = chip_data[RGB_BANDS[2] - 1]
            rgb = np.stack([percentile_stretch(r), percentile_stretch(g), percentile_stretch(b)], axis=-1)
            
            truecolour_path = PREVIEW_DIR / f"{transect_id}_truecolour.png"
            plt.imsave(truecolour_path, rgb)

            # NDSI preview: band 14 decoded, diverging colormap -1 to 1
            ndsi_img = ndsi_dec
            # Create diverging colormap (blue-white-red)
            cmap = LinearSegmentedColormap.from_list('ndsi', ['blue', 'white', 'red'])
            ndsi_norm = np.clip((ndsi_img + 1) / 2, 0, 1)  # -1..1 -> 0..1
            ndsi_colored = cmap(ndsi_norm)[:, :, :3]  # Drop alpha
            
            ndsi_path = PREVIEW_DIR / f"{transect_id}_NDSI.png"
            plt.imsave(ndsi_path, ndsi_colored)

            # Record kept chip
            chips_kept.append({
                'chip_id': f"{transect_id}_2023Q2",
                'transect_id': transect_id,
                'source_file': str(S2_PATH),
                'center_lon': lon,
                'center_lat': lat,
                'row': row_idx,
                'col': col_idx,
                'nodata_fraction': round(nodata_frac, 4),
                'mean_NDVI': round(mean_ndvi, 4) if not np.isnan(mean_ndvi) else '',
                'mean_NDWI': round(mean_ndwi, 4) if not np.isnan(mean_ndwi) else '',
                'mean_NDBI': round(mean_ndbi, 4) if not np.isnan(mean_ndbi) else '',
                'mean_NDSI': round(mean_ndsi, 4) if not np.isnan(mean_ndsi) else '',
                'mask_status': 'no_mask_band',
                'status': 'kept',
                'skip_reason': '',
                'overlap_with_prev_km': round(chip_size * abs(src.transform.a) * 111320 * np.cos(np.radians(lat)) / 1000, 2)
            })
            
            kept_previews.append((transect_id, rgb))

            if (idx + 1) % 10 == 0:
                print(f"  Processed {idx+1}/{len(df_transects)} transects...")

        print(f"\nKept: {len(chips_kept)}, Skipped: {len(chips_skipped)}")

        # Create contact sheet
        if kept_previews:
            print("Creating contact sheet...")
            n = len(kept_previews)
            cols = min(8, n)
            rows = (n + cols - 1) // cols
            
            fig, axes = plt.subplots(rows, cols, figsize=(cols * 2, rows * 2))
            if rows == 1:
                axes = axes.reshape(1, -1)
            elif cols == 1:
                axes = axes.reshape(-1, 1)
            
            for i, (tid, img) in enumerate(kept_previews):
                r, c = divmod(i, cols)
                ax = axes[r, c]
                ax.imshow(img)
                ax.set_title(tid, fontsize=6)
                ax.axis('off')
            
            # Hide empty subplots
            for i in range(n, rows * cols):
                r, c = divmod(i, cols)
                axes[r, c].axis('off')
            
            plt.tight_layout()
            contact_path = PREVIEW_DIR / "contact_sheet.png"
            plt.savefig(contact_path, dpi=150, bbox_inches='tight')
            plt.close()
            print(f"  Contact sheet: {contact_path}")

    # Save metadata CSVs
    df_kept = pd.DataFrame(chips_kept)
    df_skipped = pd.DataFrame(chips_skipped)
    
    chips_csv = METADATA_DIR / "chips_2023Q2.csv"
    skipped_csv = METADATA_DIR / "skipped_transects.csv"
    
    df_kept.to_csv(chips_csv, index=False)
    df_skipped.to_csv(skipped_csv, index=False)
    
    print(f"\nSaved:")
    print(f"  {chips_csv} ({len(df_kept)} chips)")
    print(f"  {skipped_csv} ({len(df_skipped)} skipped)")

    # Summary
    print(f"\n=== SUMMARY ===")
    print(f"Total transects: {len(df_transects)}")
    print(f"Kept: {len(chips_kept)}")
    print(f"Skipped: {len(chips_skipped)}")
    if len(chips_skipped) > 0:
        skip_reasons = df_skipped['reason'].value_counts()
        print(f"Skip reasons:")
        for reason, count in skip_reasons.items():
            print(f"  {reason}: {count}")

    sys.exit(0)


if __name__ == "__main__":
    main()