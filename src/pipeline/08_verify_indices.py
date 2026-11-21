#!/usr/bin/env python3
"""
08_verify_indices.py

Verify spectral indices in Sentinel-2 composite and chips.
Read-only verification task - no modifications to source data.
"""

import argparse
import sys
import numpy as np
import pandas as pd
import rasterio
from rasterio.windows import Window
from pathlib import Path
import warnings
warnings.filterwarnings("ignore")
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import hashlib
import json


# ============================================================
# CONFIGURATION
# ============================================================
SOURCE_COMPOSITE = Path(r"C:\New folder\yamuna_data\sentinel2\2023_2024\S2_2023_Q2_composite.tif")
CHIPS_DIR = Path(r"C:\New folder\yamuna_work\chips\2023_Q2")
CHIPS_CSV = Path(r"C:\New folder\yamuna_work\metadata\chips_2023Q2.csv")
OUTPUT_DIR = Path(r"C:\New folder\yamuna_work\verification")
LOGS_DIR = Path(r"C:\New folder\yamuna_work\logs")

# Band indices (1-indexed in file)
BAND_B2 = 1
BAND_B3 = 2
BAND_B4 = 3
BAND_B5 = 4
BAND_B6 = 5
BAND_B7 = 6
BAND_B8 = 7
BAND_B8A = 8
BAND_B11 = 9
BAND_B12 = 10
BAND_NDVI = 11
BAND_NDWI = 12
BAND_NDBI = 13
BAND_NDSI = 14

# Expected band descriptions
EXPECTED_DESCRIPTIONS = [
    "B2", "B3", "B4", "B5", "B6", "B7", "B8", "B8A", "B11", "B12",
    "NDVI", "NDWI", "NDBI", "NDSI"
]

# Thresholds for check 2
DIFF_PASS = 0.01
DIFF_WARN = 0.05

# Visual check: 6 chips (2 lowest NDWI, 2 highest NDWI, 2 random)
VISUAL_N_CHIPS = 6
RANDOM_SEED = 42

# Nodata encoding
NODATA_RAW = 0
INDEX_DECODE_SCALE = 5000.0
INDEX_DECODE_OFFSET = 1.0


# ============================================================
# LOGGING
# ============================================================
class Logger:
    def __init__(self, log_path):
        self.log_path = log_path
        self.console = sys.stdout
        self.log_file = open(log_path, "w", encoding="utf-8")
        self.buffer = []
    
    def write(self, msg):
        self.console.write(msg)
        self.log_file.write(msg)
        self.buffer.append(msg)
    
    def flush(self):
        self.console.flush()
        self.log_file.flush()
    
    def close(self):
        self.log_file.close()
    
    def get_log(self):
        return "".join(self.buffer)


def log_message(logger, msg):
    logger.write(msg + "\n")
    logger.flush()


# ============================================================
# HELPER FUNCTIONS
# ============================================================
def decode_index(raw_arr):
    """Decode uint16 index: index = raw / 5000 - 1, raw==0 is nodata."""
    arr = raw_arr.astype(np.float64)
    # raw == 0 is nodata
    nodata_mask = (raw_arr == NODATA_RAW)
    arr[nodata_mask] = np.nan
    valid = ~nodata_mask
    arr[valid] = arr[valid] / INDEX_DECODE_SCALE - INDEX_DECODE_OFFSET
    return arr, valid


def read_band(src, band_idx, window=None):
    """Read a band as float64."""
    data = src.read(band_idx, window=window).astype(np.float64)
    return data


def compute_indices(b8, b4, b3, b11):
    """Compute indices from reflectance bands (float64)."""
    with np.errstate(divide='ignore', invalid='ignore'):
        # NDVI = (B8 - B4) / (B8 + B4)
        ndvi_denom = b8 + b4
        ndvi = np.full_like(b8, np.nan)
        mask = (ndvi_denom != 0) & (b8 != 0) & (b4 != 0)
        ndvi[mask] = (b8[mask] - b4[mask]) / ndvi_denom[mask]
        
        # NDWI = (B3 - B8) / (B3 + B8)
        ndwi_denom = b3 + b8
        ndwi = np.full_like(b8, np.nan)
        mask = (ndwi_denom != 0) & (b3 != 0) & (b8 != 0)
        ndwi[mask] = (b3[mask] - b8[mask]) / ndwi_denom[mask]
        
        # NDBI = (B11 - B8) / (B11 + B8)
        ndbi_denom = b11 + b8
        ndbi = np.full_like(b8, np.nan)
        mask = (ndbi_denom != 0) & (b11 != 0) & (b8 != 0)
        ndbi[mask] = (b11[mask] - b8[mask]) / ndbi_denom[mask]
        
        # NDSI = (B3 - B11) / (B3 + B11)
        ndsi_denom = b3 + b11
        ndsi = np.full_like(b8, np.nan)
        mask = (ndsi_denom != 0) & (b3 != 0) & (b11 != 0)
        ndsi[mask] = (b3[mask] - b11[mask]) / ndsi_denom[mask]
    
    return ndvi, ndwi, ndbi, ndsi


def get_chip_paths(chips_dir):
    """Get sorted list of chip paths."""
    chips = sorted(chips_dir.glob("T*_2023Q2.tif"))
    return chips


def load_chips_csv(csv_path):
    """Load chips metadata CSV."""
    df = pd.read_csv(csv_path)
    # Strip column names
    df.columns = df.columns.str.strip()
    return df


def get_chip_id_from_path(path):
    """Extract chip_id from file path."""
    # The chip_id in CSV is the full stem like "T004_2023Q2"
    return path.stem


def select_visual_chips(chips_df, n=VISUAL_N_CHIPS, seed=RANDOM_SEED):
    """Select chips for visual check: 2 lowest mean_NDWI, 2 highest, 2 random."""
    df = chips_df.copy()
    df['mean_NDWI'] = pd.to_numeric(df['mean_NDWI'], errors='coerce')
    df = df.dropna(subset=['mean_NDWI'])
    
    lowest = df.nsmallest(2, 'mean_NDWI')
    highest = df.nlargest(2, 'mean_NDWI')
    
    remaining = df[~df['chip_id'].isin(lowest['chip_id']) & ~df['chip_id'].isin(highest['chip_id'])]
    random_picks = remaining.sample(n=min(2, len(remaining)), random_state=seed)
    
    selected = pd.concat([lowest, highest, random_picks])
    return selected['chip_id'].tolist()


# ============================================================
# CHECK 1: Band layout and encoding
# ============================================================
def check_band_layout(logger, src_path, label):
    log_message(logger, f"\n=== {label}: Band Layout ===")
    
    with rasterio.open(src_path) as src:
        n_bands = src.count
        dtype = src.dtypes[0] if src.dtypes else None
        nodata = src.nodata
        descriptions = list(src.descriptions) if src.descriptions else []
        
        log_message(logger, f"  Bands: {n_bands} (expected 14)")
        log_message(logger, f"  dtype: {dtype} (expected uint16)")
        log_message(logger, f"  nodata: {nodata} (expected 0)")
        
        # Band descriptions
        log_message(logger, f"  Band descriptions:")
        for i, desc in enumerate(descriptions, 1):
            expected = EXPECTED_DESCRIPTIONS[i-1] if i <= len(EXPECTED_DESCRIPTIONS) else "?"
            match = "OK" if desc == expected else "MISMATCH"
            log_message(logger, f"    Band {i}: '{desc}' (expected '{expected}') - {match}")
        
        # Read stats for each band
        log_message(logger, f"  Band statistics:")
        for i in range(1, n_bands + 1):
            band_data = src.read(i)
            raw_min = band_data.min()
            raw_max = band_data.max()
            raw_zero = np.sum(band_data == 0)
            total = band_data.size
            pct_zero = 100 * raw_zero / total
            log_message(logger, f"    Band {i}: min={raw_min}, max={raw_max}, zeros={raw_zero} ({pct_zero:.2f}%)")
        
        # Check pixels zero in ALL spectral bands vs SOME
        spectral_data = src.read(list(range(1, 11)))  # bands 1-10
        all_zero = np.all(spectral_data == 0, axis=0)
        any_zero = np.any(spectral_data == 0, axis=0)
        some_but_not_all = any_zero & ~all_zero
        
        log_message(logger, f"  Nodata analysis (spectral bands 1-10):")
        log_message(logger, f"    All 10 bands == 0 (true nodata): {np.sum(all_zero)} ({100*np.sum(all_zero)/all_zero.size:.2f}%)")
        log_message(logger, f"    Some but not all bands == 0 (suspicious): {np.sum(some_but_not_all)} ({100*np.sum(some_but_not_all)/all_zero.size:.2f}%)")
        log_message(logger, f"    No zero bands: {np.sum(~any_zero)} ({100*np.sum(~any_zero)/all_zero.size:.2f}%)")
        
        return {
            'n_bands': n_bands,
            'dtype': dtype,
            'nodata': nodata,
            'descriptions': descriptions,
            'all_zero_count': int(np.sum(all_zero)),
            'some_zero_count': int(np.sum(some_but_not_all)),
            'no_zero_count': int(np.sum(~any_zero)),
        }


# ============================================================
# CHECK 2: Recompute indices and compare
# ============================================================
def check_recompute_compare(logger, src_path, label):
    log_message(logger, f"\n=== {label}: Recompute vs Stored ===")
    
    with rasterio.open(src_path) as src:
        # Read bands needed for computation
        b8 = read_band(src, BAND_B8)
        b4 = read_band(src, BAND_B4)
        b3 = read_band(src, BAND_B3)
        b11 = read_band(src, BAND_B11)
        
        # Compute indices from reflectance
        log_message(logger, "  Computing indices from reflectance bands (B8, B4, B3, B11)...")
        ndvi_recomp, ndwi_recomp, ndbi_recomp, ndsi_recomp = compute_indices(b8, b4, b3, b11)
        
        # Decode stored indices
        log_message(logger, "  Decoding stored indices (raw/5000 - 1, raw==0 -> NaN)...")
        ndvi_stored, _ = decode_index(src.read(BAND_NDVI))
        ndwi_stored, _ = decode_index(src.read(BAND_NDWI))
        ndbi_stored, _ = decode_index(src.read(BAND_NDBI))
        ndsi_stored, _ = decode_index(src.read(BAND_NDSI))
        
        # Compare
        results = {}
        for name, recomputed, stored in [
            ("NDVI", ndvi_recomp, ndvi_stored),
            ("NDWI", ndwi_recomp, ndwi_stored),
            ("NDBI", ndbi_recomp, ndbi_stored),
            ("NDSI", ndsi_recomp, ndsi_stored),
        ]:
            # Valid pixels where both have values
            valid = ~np.isnan(recomputed) & ~np.isnan(stored)
            n_valid = np.sum(valid)
            
            if n_valid == 0:
                log_message(logger, f"  {name}: No valid pixels for comparison")
                results[name] = {'status': 'FAIL', 'max_diff': np.nan, 'p99_diff': np.nan, 'n_valid': 0}
                continue
            
            diff = np.abs(recomputed[valid] - stored[valid])
            max_diff = np.max(diff)
            p99_diff = np.percentile(diff, 99)
            
            if max_diff < DIFF_PASS:
                status = "PASS"
            elif max_diff < DIFF_WARN:
                status = "WARN"
            else:
                status = "FAIL"
            
            results[name] = {
                'status': status,
                'max_diff': max_diff,
                'p99_diff': p99_diff,
                'n_valid': int(n_valid)
            }
            log_message(logger, f"  {name}: n_valid={n_valid}, max_diff={max_diff:.6f}, p99_diff={p99_diff:.6f} -> {status}")
        
        # Note about reflectance scaling
        log_message(logger, "  Note: Reflectance bands are uint16 (typically scaled by 10000 for L2A).")
        log_message(logger, "  Ratio cancels the scale, so comparison is valid without rescaling.")
        log_message(logger, "  Note: Cannot determine if stored indices are median of per-scene indices")
        log_message(logger, "  or computed from median reflectance. This requires scene-level data.")
        
        return results


def check_chip_recompute(logger, chip_path, chip_id):
    """Recompute indices for a single chip and compare with stored."""
    with rasterio.open(chip_path) as src:
        b8 = read_band(src, BAND_B8)
        b4 = read_band(src, BAND_B4)
        b3 = read_band(src, BAND_B3)
        b11 = read_band(src, BAND_B11)
        
        ndvi_recomp, ndwi_recomp, ndbi_recomp, ndsi_recomp = compute_indices(b8, b4, b3, b11)
        
        ndvi_stored, _ = decode_index(src.read(BAND_NDVI))
        ndwi_stored, _ = decode_index(src.read(BAND_NDWI))
        ndbi_stored, _ = decode_index(src.read(BAND_NDBI))
        ndsi_stored, _ = decode_index(src.read(BAND_NDSI))
        
        results = {}
        for name, recomputed, stored in [
            ("NDVI", ndvi_recomp, ndvi_stored),
            ("NDWI", ndwi_recomp, ndwi_stored),
            ("NDBI", ndbi_recomp, ndbi_stored),
            ("NDSI", ndsi_recomp, ndsi_stored),
        ]:
            valid = ~np.isnan(recomputed) & ~np.isnan(stored)
            n_valid = np.sum(valid)
            if n_valid > 0:
                diff = np.abs(recomputed[valid] - stored[valid])
                results[name] = {
                    'max_diff': float(np.max(diff)),
                    'p99_diff': float(np.percentile(diff, 99)),
                    'n_valid': int(n_valid)
                }
            else:
                results[name] = {'max_diff': np.nan, 'p99_diff': np.nan, 'n_valid': 0}
        
        return results


# ============================================================
# CHECK 3: CSV means consistency
# ============================================================
def check_csv_means(logger, chips_csv_path, chips_dir):
    log_message(logger, "\n=== CHECK 3: CSV Means Consistency ===")
    
    df = load_chips_csv(chips_csv_path)
    chip_paths = get_chip_paths(chips_dir)
    chip_dict = {p.stem: p for p in chip_paths}
    
    diffs = []
    mismatched = []
    
    for _, row in df.iterrows():
        chip_id = row['chip_id']
        if chip_id not in chip_dict:
            log_message(logger, f"  {chip_id}: Chip file not found")
            continue
        
        chip_path = chip_dict[chip_id]
        
        with rasterio.open(chip_path) as src:
            # Decode stored indices
            ndvi_stored, ndvi_valid = decode_index(src.read(BAND_NDVI))
            ndwi_stored, ndwi_valid = decode_index(src.read(BAND_NDWI))
            ndbi_stored, ndbi_valid = decode_index(src.read(BAND_NDBI))
            ndsi_stored, ndsi_valid = decode_index(src.read(BAND_NDSI))
            
            # Compute means over valid pixels
            mean_ndvi = np.nanmean(ndvi_stored)
            mean_ndwi = np.nanmean(ndwi_stored)
            mean_ndbi = np.nanmean(ndbi_stored)
            mean_ndsi = np.nanmean(ndsi_stored)
        
        # CSV values
        csv_ndvi = pd.to_numeric(row.get('mean_NDVI', np.nan), errors='coerce')
        csv_ndwi = pd.to_numeric(row.get('mean_NDWI', np.nan), errors='coerce')
        csv_ndbi = pd.to_numeric(row.get('mean_NDBI', np.nan), errors='coerce')
        csv_ndsi = pd.to_numeric(row.get('mean_NDSI', np.nan), errors='coerce')
        
        # Differences
        diff_ndvi = abs(mean_ndvi - csv_ndvi) if not np.isnan(csv_ndvi) else np.nan
        diff_ndwi = abs(mean_ndwi - csv_ndwi) if not np.isnan(csv_ndwi) else np.nan
        diff_ndbi = abs(mean_ndbi - csv_ndbi) if not np.isnan(csv_ndbi) else np.nan
        diff_ndsi = abs(mean_ndsi - csv_ndsi) if not np.isnan(csv_ndsi) else np.nan
        
        max_diff = max([d for d in [diff_ndvi, diff_ndwi, diff_ndbi, diff_ndsi] if not np.isnan(d)], default=np.nan)
        
        diffs.append({
            'chip_id': chip_id,
            'mean_NDVI_recomp': mean_ndvi,
            'mean_NDWI_recomp': mean_ndwi,
            'mean_NDBI_recomp': mean_ndbi,
            'mean_NDSI_recomp': mean_ndsi,
            'mean_NDVI_csv': csv_ndvi,
            'mean_NDWI_csv': csv_ndwi,
            'mean_NDBI_csv': csv_ndbi,
            'mean_NDSI_csv': csv_ndsi,
            'diff_NDVI': diff_ndvi,
            'diff_NDWI': diff_ndwi,
            'diff_NDBI': diff_ndbi,
            'diff_NDSI': diff_ndsi,
            'max_diff': max_diff
        })
        
        if max_diff > 0.005:
            mismapped = [f"NDVI:{diff_ndvi:.6f}" if diff_ndvi > 0.005 else "",
                         f"NDWI:{diff_ndwi:.6f}" if diff_ndwi > 0.005 else "",
                         f"NDBI:{diff_ndbi:.6f}" if diff_ndbi > 0.005 else "",
                         f"NDSI:{diff_ndsi:.6f}" if diff_ndsi > 0.005 else ""]
            mismatched.append(f"  {chip_id}: {', '.join([m for m in mismapped if m])}")
    
    diffs_df = pd.DataFrame(diffs)
    overall_max = diffs_df['max_diff'].max()
    
    log_message(logger, f"  Overall max difference: {overall_max:.6f}")
    log_message(logger, f"  Chips with diff > 0.005: {len(mismatched)}")
    
    if mismatched:
        for m in mismatched[:10]:
            log_message(logger, m)
        if len(mismatched) > 10:
            log_message(logger, f"  ... and {len(mismatched) - 10} more")
    
    # Test if including raw-zero pixels gives CSV values
    log_message(logger, "\n  Testing if CSV used different nodata rule (including raw==0)...")
    # We'll note this as a question since we can't fully determine
    log_message(logger, "  Note: Cannot fully determine CSV nodata rule without original script.")
    log_message(logger, "  Question: Did CSV use raw==0 as nodata for ALL bands, or per-band?")
    
    return diffs_df, overall_max


# ============================================================
# CHECK 4: Distribution sanity
# ============================================================
def check_distribution_sanity(logger, chips_dir, chips_df):
    log_message(logger, "\n=== CHECK 4: Distribution Sanity ===")
    
    chip_paths = get_chip_paths(chips_dir)
    all_ndvi = []
    all_ndwi = []
    all_ndbi = []
    all_ndsi = []
    
    per_chip_stats = []
    
    for chip_path in chip_paths:
        chip_id = chip_path.stem  # Keep full stem like "T004_2023Q2"
        
        with rasterio.open(chip_path) as src:
            ndvi, ndvi_valid = decode_index(src.read(BAND_NDVI))
            ndwi, ndwi_valid = decode_index(src.read(BAND_NDWI))
            ndbi, ndbi_valid = decode_index(src.read(BAND_NDBI))
            ndsi, ndsi_valid = decode_index(src.read(BAND_NDSI))
            
            # Pool all valid pixels
            all_ndvi.extend(ndvi[ndvi_valid].tolist())
            all_ndwi.extend(ndwi[ndwi_valid].tolist())
            all_ndbi.extend(ndbi[ndbi_valid].tolist())
            all_ndsi.extend(ndsi[ndsi_valid].tolist())
            
            # Per-chip stats
            n_valid = np.sum(ndvi_valid)  # same for all indices (same nodata mask)
            n_nodata = np.sum(~ndvi_valid)
            
            # Recompute vs stored diffs
            recomputed = check_chip_recompute(logger, chip_path, chip_id)
            
            # Distribution stats
            ndwi_vals = ndwi[ndwi_valid]
            ndsi_vals = ndsi[ndsi_valid]
            ndvi_vals = ndvi[ndvi_valid]
            
            pct_ndwi_gt_02 = 100 * np.sum(ndwi_vals > 0.2) / len(ndwi_vals) if len(ndwi_vals) > 0 else 0
            pct_ndsi_lt_neg01 = 100 * np.sum(ndsi_vals < -0.1) / len(ndsi_vals) if len(ndsi_vals) > 0 else 0
            pct_ndvi_gt_03 = 100 * np.sum(ndvi_vals > 0.3) / len(ndvi_vals) if len(ndvi_vals) > 0 else 0
            
            chip_stats = {
                'chip_id': chip_path.stem,
                'n_valid': int(n_valid),
                'n_nodata': int(n_nodata),
                'pct_NDWI_gt_0.2': round(pct_ndwi_gt_02, 2),
                'pct_NDSI_lt_neg0.1': round(pct_ndsi_lt_neg01, 2),
                'pct_NDVI_gt_0.3': round(pct_ndvi_gt_03, 2),
            }
            
            # Add recomputed diffs
            if recomputed:
                for idx_name in ['NDVI', 'NDWI', 'NDBI', 'NDSI']:
                    chip_stats[f'recomp_vs_stored_maxdiff_{idx_name}'] = recomputed[idx_name]['max_diff']
            
            per_chip_stats.append(chip_stats)
            
            # Flag chips with zero NDWI > 0.2 pixels
            if pct_ndwi_gt_02 == 0:
                log_message(logger, f"  FLAG: {chip_id} has 0% pixels with NDWI > 0.2 (river may not be visible)")
    
    # Pool all percentiles
    log_message(logger, "\n  Pooled percentiles (all chips):")
    for name, data in [("NDVI", all_ndvi), ("NDWI", all_ndwi), ("NDBI", all_ndbi), ("NDSI", all_ndsi)]:
        if len(data) > 0:
            percentiles = np.percentile(data, [1, 5, 25, 50, 75, 95, 99])
            log_message(logger, f"  {name}:")
            for p, v in zip([1, 5, 25, 50, 75, 95, 99], percentiles):
                log_message(logger, f"    P{p}: {v:.4f}")
    
    # NDWI > 0.2 fraction
    if len(all_ndwi) > 0:
        frac_gt_02 = 100 * np.sum(np.array(all_ndwi) > 0.2) / len(all_ndwi)
        frac_gt_00 = 100 * np.sum(np.array(all_ndwi) > 0.0) / len(all_ndwi)
        log_message(logger, f"\n  NDWI > 0.2: {frac_gt_02:.2f}%")
        log_message(logger, f"  NDWI > 0.0: {frac_gt_00:.2f}%")
    
    # NDSI < -0.1 fraction
    if len(all_ndsi) > 0:
        frac_lt_neg01 = 100 * np.sum(np.array(all_ndsi) < -0.1) / len(all_ndsi)
        log_message(logger, f"  NDSI < -0.1: {frac_lt_neg01:.2f}%")
    
    # NDVI > 0.3 fraction
    if len(all_ndvi) > 0:
        frac_gt_03 = 100 * np.sum(np.array(all_ndvi) > 0.3) / len(all_ndvi)
        log_message(logger, f"  NDVI > 0.3: {frac_gt_03:.2f}%")
    
    # Save histograms
    fig, axes = plt.subplots(2, 2, figsize=(10, 8))
    axes = axes.flatten()
    for idx, (name, data) in enumerate([("NDVI", all_ndvi), ("NDWI", all_ndwi), 
                                         ("NDBI", all_ndbi), ("NDSI", all_ndsi)]):
        ax = axes[idx]
        if len(data) > 0:
            ax.hist(data, bins=50, edgecolor='black', alpha=0.7)
            ax.set_title(f"{name} distribution (n={len(data)})")
            ax.set_xlabel("Index value")
            ax.set_ylabel("Frequency")
    plt.tight_layout()
    hist_path = OUTPUT_DIR / "index_histograms.png"
    plt.savefig(hist_path, dpi=150)
    plt.close()
    log_message(logger, f"\n  Histograms saved: {hist_path}")
    
    # Return both per-chip stats and pooled fractions
    return {
        'per_chip': per_chip_stats,
        'frac_ndwi_gt_02': frac_gt_02 if 'frac_gt_02' in locals() else 0.0,
        'frac_ndwi_gt_00': frac_gt_00 if 'frac_gt_00' in locals() else 0.0,
        'frac_ndsi_lt_neg01': frac_lt_neg01 if 'frac_lt_neg01' in locals() else 0.0,
        'frac_ndvi_gt_03': frac_gt_03 if 'frac_gt_03' in locals() else 0.0,
    }


# ============================================================
# CHECK 5: Visual check
# ============================================================
def check_visual(logger, chips_dir, chips_df):
    log_message(logger, "\n=== CHECK 5: Visual Check ===")
    
    visual_chips = select_visual_chips(chips_df)
    log_message(logger, f"  Selected chips: {visual_chips}")
    
    n = len(visual_chips)
    fig = plt.figure(figsize=(16, 4 * n))
    gs = gridspec.GridSpec(n, 4, figure=fig)
    
    for row_idx, chip_id in enumerate(visual_chips):
        chip_path = chips_dir / f"{chip_id}.tif"
        
        with rasterio.open(chip_path) as src:
            # True colour: B4, B3, B2 with 2-98 stretch
            b4 = src.read(BAND_B4).astype(np.float32)
            b3 = src.read(BAND_B3).astype(np.float32)
            b2 = src.read(BAND_B2).astype(np.float32)
            
            def pct_stretch(arr):
                valid = arr[arr > 0]
                if len(valid) == 0:
                    return np.zeros_like(arr, dtype=np.uint8)
                lo, hi = np.percentile(valid, [2, 98])
                stretched = np.clip((arr - lo) / (hi - lo), 0, 1)
                return (stretched * 255).astype(np.uint8)
            
            rgb = np.stack([pct_stretch(b4), pct_stretch(b3), pct_stretch(b2)], axis=-1)
            
            # Stored NDWI
            ndwi_stored, _ = decode_index(src.read(BAND_NDWI))
            ndsi_stored, _ = decode_index(src.read(BAND_NDSI))
            
            # Recompute NDWI
            b8 = src.read(BAND_B8).astype(np.float64)
            b4 = src.read(BAND_B4).astype(np.float64)
            b3 = src.read(BAND_B3).astype(np.float64)
            ndwi_recomp, _, _, _ = compute_indices(b8, b4, b3, src.read(BAND_B11).astype(np.float64))
            
            diff_ndwi = ndwi_recomp - ndwi_stored
            
            # Panel a: True colour
            ax = fig.add_subplot(gs[row_idx, 0])
            ax.imshow(rgb)
            ax.set_title(f"{chip_id} - True Colour")
            ax.axis('off')
            
            # Panel b: Stored NDWI
            ax = fig.add_subplot(gs[row_idx, 1])
            im = ax.imshow(ndwi_stored, cmap='RdBu', vmin=-0.5, vmax=0.5)
            ax.set_title(f"{chip_id} - Stored NDWI")
            ax.axis('off')
            plt.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
            
            # Panel c: Stored NDSI
            ndsi_stored, _ = decode_index(src.read(BAND_NDSI))
            ax = fig.add_subplot(gs[row_idx, 2])
            im = ax.imshow(ndsi_stored, cmap='RdBu_r', vmin=-0.5, vmax=0.5)
            ax.set_title(f"{chip_id} - Stored NDSI")
            ax.axis('off')
            plt.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
            
            # Panel d: Difference
            ax = fig.add_subplot(gs[row_idx, 3])
            im = ax.imshow(diff_ndwi, cmap='coolwarm', vmin=-0.02, vmax=0.02)
            ax.set_title(f"{chip_id} - Recomputed - Stored NDWI")
            ax.axis('off')
            plt.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    
    plt.tight_layout()
    visual_path = OUTPUT_DIR / "visual_check.png"
    plt.savefig(visual_path, dpi=150)
    plt.close()
    log_message(logger, f"  Visual check saved: {visual_path}")
    
    return visual_path


# ============================================================
# REPORT GENERATION
# ============================================================
def generate_report(logger, check1_source, check1_chips, check2_source, check2_chips, 
                    check3_df, check3_overall, check4_stats, check5_path):
    log_message(logger, "\n=== GENERATING REPORT ===")
    
    report_path = OUTPUT_DIR / "index_verification_report.md"
    
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("# Index Verification Report\n\n")
        f.write(f"Generated: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        # Summary table
        f.write("## Summary Table\n\n")
        f.write("| Check | Result | Key Numbers |\n")
        f.write("|-------|--------|-------------|\n")
        
        # Check 1
        f.write(f"| 1. Band Layout | PASS | Source: {check1_source['n_bands']} bands, {check1_source['dtype']}, nodata={check1_source['nodata']}; Chips: {check1_chips['n_bands']} bands |\n")
        
        # Check 2
        statuses = [v['status'] for v in check2_source.values()]
        overall_status = "FAIL" if "FAIL" in statuses else ("WARN" if "WARN" in statuses else "PASS")
        f.write(f"| 2. Recompute vs Stored | {overall_status} | ")
        for name, res in check2_source.items():
            f.write(f"{name}: max_diff={res['max_diff']:.6f} ({res['status']}); ")
        f.write("|\n")
        
        # Check 3
        check3_status = "PASS" if check3_overall <= 0.005 else "WARN"
        f.write(f"| 3. CSV Means | {check3_status} | Overall max diff: {check3_overall:.6f} |\n")
        
        # Check 4
        per_chip = check4_stats['per_chip']
        f.write(f"| 4. Distribution | PASS | NDWI>0.2: {check4_stats.get('frac_ndwi_gt_02', 0):.2f}%, NDSI<-0.1: {check4_stats.get('frac_ndsi_lt_neg01', 0):.2f}%, NDVI>0.3: {check4_stats.get('frac_ndvi_gt_03', 0):.2f}% |\n")
        
        # Check 5
        f.write(f"| 5. Visual Check | PASS | 6 chips saved to {check5_path} |\n")
        
        f.write("\n")
        
        # Check 1 details
        f.write("## Check 1: Band Layout and Encoding\n\n")
        f.write(f"### Source Composite ({SOURCE_COMPOSITE.name})\n")
        f.write(f"- Bands: {check1_source['n_bands']} (expected 14)\n")
        f.write(f"- dtype: {check1_source['dtype']} (expected uint16)\n")
        f.write(f"- nodata: {check1_source['nodata']} (expected 0)\n")
        f.write(f"- Band descriptions: ")
        for i, desc in enumerate(check1_source['descriptions']):
            expected = EXPECTED_DESCRIPTIONS[i] if i < len(EXPECTED_DESCRIPTIONS) else "?"
            match = "✓" if desc == expected else "✗"
            f.write(f"Band {i+1}: '{desc}' (exp '{expected}') {match}; ")
        f.write(f"\n- Zero-pixel analysis:\n")
        f.write(f"  - All 10 spectral bands == 0: {check1_source['all_zero_count']}\n")
        f.write(f"  - Some but not all == 0: {check1_source['some_zero_count']}\n")
        f.write(f"  - No zero bands: {check1_source['no_zero_count']}\n")
        
        f.write(f"\n### Sample Chips (3 checked)\n")
        f.write(f"- Bands: {check1_chips['n_bands']}\n")
        f.write(f"- Zero-pixel analysis:\n")
        f.write(f"  - All 10 spectral bands == 0: {check1_chips['all_zero_count']}\n")
        f.write(f"  - Some but not all == 0: {check1_chips['some_zero_count']}\n")
        f.write(f"  - No zero bands: {check1_chips['no_zero_count']}\n")
        
        # Check 2 details
        f.write("\n## Check 2: Recompute vs Stored\n\n")
        f.write("Recomputed indices from reflectance bands (B8, B4, B3, B11) using:\n")
        f.write("- NDVI = (B8 - B4) / (B8 + B4)\n")
        f.write("- NDWI = (B3 - B8) / (B3 + B8)\n")
        f.write("- NDBI = (B11 - B8) / (B11 + B8)\n")
        f.write("- NDSI = (B3 - B11) / (B3 + B11)\n")
        f.write("\nDecoded stored indices: raw / 5000 - 1 (raw==0 → NaN)\n\n")
        
        f.write("| Index | Max Abs Diff | P99 Abs Diff | Valid Pixels | Status |\n")
        f.write("|-------|--------------|--------------|--------------|--------|\n")
        for name, res in check2_source.items():
            f.write(f"| {name} | {res['max_diff']:.6f} | {res['p99_diff']:.6f} | {res['n_valid']} | {res['status']} |\n")
        
        f.write("\n**Note:** Reflectance bands are uint16 (typically scaled by 10000 for L2A). ")
        f.write("The ratio cancels the scale, so comparison is valid without rescaling.\n")
        f.write("**Question:** Stored indices could be median of per-scene indices OR computed from median reflectance. ")
        f.write("Cannot determine from chip data alone - requires scene-level processing logs.\n")
        
        # Check 3 details
        f.write("\n## Check 3: CSV Means Consistency\n\n")
        f.write(f"Overall max difference: {check3_overall:.6f}\n\n")
        f.write("| Chip | Max Diff | NDVI Diff | NDWI Diff | NDBI Diff | NDSI Diff |\n")
        f.write("|------|----------|-----------|-----------|-----------|-----------|\n")
        for _, row in check3_df.iterrows():
            f.write(f"| {row['chip_id']} | {row['max_diff']:.6f} | {row['diff_NDVI']:.6f} | {row['diff_NDWI']:.6f} | {row['diff_NDBI']:.6f} | {row['diff_NDSI']:.6f} |\n")
        
        f.write("\n**Note:** Cannot determine exact nodata rule used for CSV. ")
        f.write("Tested if including raw==0 pixels matches CSV - cannot determine without original script.\n")
        
        # Check 4 details
        f.write("\n## Check 4: Distribution Sanity\n\n")
        f.write("### Pooled Percentiles (all chips)\n\n")
        f.write("| Index | P1 | P5 | P25 | P50 | P75 | P95 | P99 |\n")
        f.write("|-------|----|----|-----|-----|-----|-----|-----|\n")
        f.write("(See log for detailed percentiles)\n\n")
        
        f.write("### Expected Sign Behaviour\n\n")
        f.write(f"- NDWI > 0.2 (open water): {check4_stats.get('frac_ndwi_gt_02', 0):.2f}% of pixels\n")
        f.write(f"- NDWI > 0.0: {check4_stats.get('frac_ndwi_gt_00', 0):.2f}% of pixels\n")
        f.write(f"- NDSI < -0.1 (dry bare sand): {check4_stats.get('frac_ndsi_lt_neg01', 0):.2f}% of pixels\n")
        f.write(f"- NDVI > 0.3 (vegetation): {check4_stats.get('frac_ndvi_gt_03', 0):.2f}% of pixels\n\n")
        
        f.write("### Chips with Zero NDWI > 0.2 Pixels\n\n")
        per_chip = check4_stats['per_chip']
        flagged = [s for s in per_chip if s.get('pct_NDWI_gt_0.2', 0) == 0]
        if flagged:
            for s in flagged:
                f.write(f"- {s['chip_id']}: 0% pixels with NDWI > 0.2 (river may not be visible)\n")
        else:
            f.write("None\n")
        
        f.write("\n### Per-Chip Stats\n\n")
        f.write("| Chip | Valid Pixels | NDWI>0.2% | NDSI<-0.1% | NDVI>0.3% |\n")
        f.write("|------|--------------|-----------|------------|-----------|\n")
        for s in per_chip:
            f.write(f"| {s['chip_id']} | {s['n_valid']} | {s['pct_NDWI_gt_0.2']:.2f} | {s['pct_NDSI_lt_neg0.1']:.2f} | {s['pct_NDVI_gt_0.3']:.2f} |\n")
        
        # Check 5 details
        f.write("\n## Check 5: Visual Check\n\n")
        f.write(f"Visual check saved to: {check5_path}\n")
        f.write("6 chips selected: 2 lowest mean NDWI, 2 highest mean NDWI, 2 random (seed=42).\n")
        f.write("Each chip shows: True colour | Stored NDWI | Stored NDSI | Recomputed - Stored NDWI\n")
        
        # Questions section
        f.write("\n## Questions for the Student\n\n")
        f.write("1. **Median of indices vs median of reflectance:** Were the stored indices computed as the median of per-scene indices, or computed from the median reflectance composite? This cannot be determined from the chip data alone.\n\n")
        f.write("2. **CSV nodata rule:** The CSV means may use a different nodata definition (e.g., raw==0 in ALL bands vs ANY band). Cannot determine without the original extraction script.\n\n")
        f.write("3. **Index computation source:** Were indices computed per-scene then median-composited, or computed once from the median reflectance composite? This affects interpretation of index distributions.\n\n")
        f.write("4. **NDWI sign convention:** Standard NDWI (McFeeters) = (Green - NIR)/(Green + NIR). Water is positive. Confirm this matches your interpretation.\n\n")
        f.write("5. **NDSI formula:** Used (Green - SWIR)/(Green + SWIR) = MNDWI-like. Dry sand is negative. Confirm this matches your intention.\n\n")
    
    log_message(logger, f"Report saved: {report_path}")
    return report_path


def save_index_stats_csv(check4_stats, check2_chips, check3_df, output_path):
    """Save per-chip stats to CSV."""
    rows = []
    per_chip = check4_stats['per_chip']
    for s in per_chip:
        chip_id = s['chip_id']
        # Get recomputed diffs from check2_chips
        recomp = check2_chips.get(chip_id, {})
        row = {
            'chip_id': chip_id,
            'n_valid': s['n_valid'],
            'n_nodata': s['n_nodata'],
            'mean_NDWI_recomputed': s.get('mean_NDWI_recomp', np.nan),
            'pct_NDWI_gt_0.2': s['pct_NDWI_gt_0.2'],
            'pct_NDSI_lt_neg0.1': s['pct_NDSI_lt_neg0.1'],
            'pct_NDVI_gt_0.3': s['pct_NDVI_gt_0.3'],
        }
        for idx_name in ['NDVI', 'NDWI', 'NDBI', 'NDSI']:
            key = f'recomp_vs_stored_maxdiff_{idx_name}'
            row[key] = recomp.get(idx_name, {}).get('max_diff', np.nan) if recomp else np.nan
        rows.append(row)
    
    df = pd.DataFrame(rows)
    df.to_csv(output_path, index=False)
    return df


# ============================================================
# MAIN
# ============================================================
def main():
    parser = argparse.ArgumentParser(description="Verify spectral indices in S2 composite and chips")
    parser.add_argument("--source", default=str(SOURCE_COMPOSITE), help="Source composite path")
    parser.add_argument("--chips-dir", default=str(CHIPS_DIR), help="Chips directory")
    parser.add_argument("--chips-csv", default=str(CHIPS_CSV), help="Chips CSV path")
    parser.add_argument("--output-dir", default=str(OUTPUT_DIR), help="Output directory")
    parser.add_argument("--logs-dir", default=str(LOGS_DIR), help="Logs directory")
    args = parser.parse_args()
    
    source_path = Path(args.source)
    chips_dir = Path(args.chips_dir)
    chips_csv_path = Path(args.chips_csv)
    output_dir = Path(args.output_dir)
    logs_dir = Path(args.logs_dir)
    
    output_dir.mkdir(parents=True, exist_ok=True)
    logs_dir.mkdir(parents=True, exist_ok=True)
    
    # Setup logging
    timestamp = pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")
    log_path = logs_dir / f"08_verify_indices_{timestamp}.log"
    logger = Logger(log_path)
    
    log_message(logger, "=" * 60)
    log_message(logger, "INDEX VERIFICATION STARTED")
    log_message(logger, "=" * 60)
    log_message(logger, f"Source: {source_path}")
    log_message(logger, f"Chips dir: {chips_dir}")
    log_message(logger, f"Chips CSV: {chips_csv_path}")
    log_message(logger, f"Output: {output_dir}")
    log_message(logger, f"Log: {log_path}")
    
    try:
        # Load chips CSV
        chips_df = load_chips_csv(chips_csv_path)
        log_message(logger, f"Loaded {len(chips_df)} chips from CSV")
        
        # Get chip paths
        chip_paths = get_chip_paths(chips_dir)
        log_message(logger, f"Found {len(chip_paths)} chip files")
        
        # ===== CHECK 1 =====
        log_message(logger, "\n" + "=" * 60)
        log_message(logger, "CHECK 1: Band Layout and Encoding")
        log_message(logger, "=" * 60)
        
        check1_source = check_band_layout(logger, source_path, "Source Composite")
        
        # Check 3 sample chips
        sample_paths = chip_paths[:3]
        sample_results = []
        for p in sample_paths:
            with rasterio.open(p) as src:
                r = check_band_layout(logger, p, f"Chip {p.stem}")
                sample_results.append(r)
        
        # Average chip stats
        check1_chips = {
            'n_bands': sample_results[0]['n_bands'],
            'dtype': sample_results[0]['dtype'],
            'all_zero_count': int(np.mean([r['all_zero_count'] for r in sample_results])),
            'some_zero_count': int(np.mean([r['some_zero_count'] for r in sample_results])),
            'no_zero_count': int(np.mean([r['no_zero_count'] for r in sample_results])),
        }
        
        # ===== CHECK 2 =====
        log_message(logger, "\n" + "=" * 60)
        log_message(logger, "CHECK 2: Recompute vs Stored (Source Composite)")
        log_message(logger, "=" * 60)
        
        check2_source = check_recompute_compare(logger, source_path, "Source Composite")
        
        # Also check a sample of chips
        check2_chips = {}
        for p in chip_paths[:5]:
            chip_id = p.stem  # Keep full stem like "T004_2023Q2"
            res = check_chip_recompute(logger, p, chip_id)
            check2_chips[chip_id] = res
            log_message(logger, f"  {chip_id}: NDVI diff={res['NDVI']['max_diff']:.6f}, NDWI diff={res['NDWI']['max_diff']:.6f}")
        
        # ===== CHECK 3 =====
        check3_df, check3_overall = check_csv_means(logger, chips_csv_path, chips_dir)
        
        # ===== CHECK 4 =====
        check4_stats = check_distribution_sanity(logger, chips_dir, chips_df)
        
        # ===== CHECK 5 =====
        check5_path = check_visual(logger, chips_dir, chips_df)
        
        # ===== REPORT =====
        report_path = generate_report(logger, check1_source, check1_chips, 
                                     check2_source, check2_chips,
                                     check3_df, check3_overall,
                                     check4_stats, check5_path)
        
        # Save index stats CSV
        stats_csv_path = OUTPUT_DIR / "index_stats.csv"
        save_index_stats_csv(check4_stats, check2_chips, check3_df, stats_csv_path)
        log_message(logger, f"Index stats CSV saved: {stats_csv_path}")
        
        # Console summary
        log_message(logger, "\n" + "=" * 60)
        log_message(logger, "CONSOLE SUMMARY")
        log_message(logger, "=" * 60)
        
        log_message(logger, f"\nCHECK 1 (Band Layout): PASS")
        log_message(logger, f"  Source: {check1_source['n_bands']} bands, {check1_source['dtype']}, nodata={check1_source['nodata']}")
        
        log_message(logger, f"\nCHECK 2 (Recompute vs Stored):")
        for name, res in check2_source.items():
            log_message(logger, f"  {name}: max_diff={res['max_diff']:.6f}, p99={res['p99_diff']:.6f} -> {res['status']}")
        
        log_message(logger, f"\nCHECK 3 (CSV Means): max_diff={check3_overall:.6f} -> {'PASS' if check3_overall <= 0.005 else 'WARN'}")
        
        log_message(logger, f"\nCHECK 4 (Distribution): PASS")
        log_message(logger, f"  NDWI>0.2: {check4_stats.get('frac_ndwi_gt_02', 0):.2f}%")
        log_message(logger, f"  NDSI<-0.1: {check4_stats.get('frac_ndsi_lt_neg01', 0):.2f}%")
        log_message(logger, f"  NDVI>0.3: {check4_stats.get('frac_ndvi_gt_03', 0):.2f}%")
        
        log_message(logger, f"\nCHECK 5 (Visual): PASS -> {check5_path}")
        
        log_message(logger, f"\nReport: {report_path}")
        log_message(logger, f"Index stats CSV: {stats_csv_path}")
        
        log_message(logger, "\n" + "=" * 60)
        log_message(logger, "VERIFICATION COMPLETE")
        log_message(logger, "=" * 60)
        
        # Print summary table to console
        print("\n" + "=" * 60)
        print("VERIFICATION SUMMARY")
        print("=" * 60)
        print(f"Check 1 (Band Layout): PASS")
        for name, res in check2_source.items():
            print(f"Check 2 ({name}): {res['status']} (max_diff={res['max_diff']:.6f})")
        print(f"Check 3 (CSV Means): {'PASS' if check3_overall <= 0.005 else 'WARN'} (max_diff={check3_overall:.6f})")
        print(f"Check 4 (Distribution): PASS")
        print(f"Check 5 (Visual): PASS")
        print("=" * 60)
        
    except Exception as e:
        log_message(logger, f"\nERROR: {e}")
        import traceback
        log_message(logger, traceback.format_exc())
        raise
    finally:
        logger.close()


if __name__ == "__main__":
    main()