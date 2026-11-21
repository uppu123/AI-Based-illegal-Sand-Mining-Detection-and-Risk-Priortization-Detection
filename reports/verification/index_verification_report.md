# Index Verification Report

Generated: 2026-10-28 04:37:49

## Summary Table

| Check | Result | Key Numbers |
|-------|--------|-------------|
| 1. Band Layout | PASS | Source: 14 bands, uint16, nodata=0.0; Chips: 14 bands |
| 2. Recompute vs Stored | FAIL | NDVI: max_diff=0.276880 (FAIL); NDWI: max_diff=0.263187 (FAIL); NDBI: max_diff=0.276105 (FAIL); NDSI: max_diff=0.000454 (PASS); |
| 3. CSV Means | PASS | Overall max diff: 0.000050 |
| 4. Distribution | PASS | NDWI>0.2: 0.00%, NDSI<-0.1: 90.98%, NDVI>0.3: 36.78% |
| 5. Visual Check | PASS | 6 chips saved to C:\New folder\yamuna_work\verification\visual_check.png |

## Check 1: Band Layout and Encoding

### Source Composite (S2_2023_Q2_composite.tif)
- Bands: 14 (expected 14)
- dtype: uint16 (expected uint16)
- nodata: 0.0 (expected 0)
- Band descriptions: Band 1: 'None' (exp 'B2') ✗; Band 2: 'None' (exp 'B3') ✗; Band 3: 'None' (exp 'B4') ✗; Band 4: 'None' (exp 'B5') ✗; Band 5: 'None' (exp 'B6') ✗; Band 6: 'None' (exp 'B7') ✗; Band 7: 'None' (exp 'B8') ✗; Band 8: 'None' (exp 'B8A') ✗; Band 9: 'None' (exp 'B11') ✗; Band 10: 'None' (exp 'B12') ✗; Band 11: 'None' (exp 'NDVI') ✗; Band 12: 'None' (exp 'NDWI') ✗; Band 13: 'None' (exp 'NDBI') ✗; Band 14: 'None' (exp 'NDSI') ✗; 
- Zero-pixel analysis:
  - All 10 spectral bands == 0: 0
  - Some but not all == 0: 0
  - No zero bands: 4069450

### Sample Chips (3 checked)
- Bands: 14
- Zero-pixel analysis:
  - All 10 spectral bands == 0: 0
  - Some but not all == 0: 0
  - No zero bands: 65536

## Check 2: Recompute vs Stored

Recomputed indices from reflectance bands (B8, B4, B3, B11) using:
- NDVI = (B8 - B4) / (B8 + B4)
- NDWI = (B3 - B8) / (B3 + B8)
- NDBI = (B11 - B8) / (B11 + B8)
- NDSI = (B3 - B11) / (B3 + B11)

Decoded stored indices: raw / 5000 - 1 (raw==0 → NaN)

| Index | Max Abs Diff | P99 Abs Diff | Valid Pixels | Status |
|-------|--------------|--------------|--------------|--------|
| NDVI | 0.276880 | 0.061302 | 4069450 | FAIL |
| NDWI | 0.263187 | 0.061518 | 4069450 | FAIL |
| NDBI | 0.276105 | 0.064102 | 4069450 | FAIL |
| NDSI | 0.000454 | 0.000237 | 4069450 | PASS |

**Note:** Reflectance bands are uint16 (typically scaled by 10000 for L2A). The ratio cancels the scale, so comparison is valid without rescaling.
**Question:** Stored indices could be median of per-scene indices OR computed from median reflectance. Cannot determine from chip data alone - requires scene-level processing logs.

## Check 3: CSV Means Consistency

Overall max difference: 0.000050

| Chip | Max Diff | NDVI Diff | NDWI Diff | NDBI Diff | NDSI Diff |
|------|----------|-----------|-----------|-----------|-----------|
| T004_2023Q2 | 0.000039 | 0.000035 | 0.000039 | 0.000002 | 0.000010 |
| T005_2023Q2 | 0.000034 | 0.000026 | 0.000034 | 0.000015 | 0.000017 |
| T006_2023Q2 | 0.000047 | 0.000047 | 0.000031 | 0.000026 | 0.000000 |
| T007_2023Q2 | 0.000026 | 0.000005 | 0.000001 | 0.000021 | 0.000026 |
| T008_2023Q2 | 0.000039 | 0.000033 | 0.000039 | 0.000031 | 0.000001 |
| T009_2023Q2 | 0.000048 | 0.000047 | 0.000048 | 0.000040 | 0.000039 |
| T010_2023Q2 | 0.000048 | 0.000048 | 0.000005 | 0.000029 | 0.000008 |
| T011_2023Q2 | 0.000038 | 0.000020 | 0.000025 | 0.000015 | 0.000038 |
| T012_2023Q2 | 0.000031 | 0.000018 | 0.000020 | 0.000031 | 0.000017 |
| T013_2023Q2 | 0.000043 | 0.000006 | 0.000034 | 0.000018 | 0.000043 |
| T014_2023Q2 | 0.000044 | 0.000044 | 0.000034 | 0.000033 | 0.000018 |
| T015_2023Q2 | 0.000035 | 0.000023 | 0.000035 | 0.000012 | 0.000013 |
| T016_2023Q2 | 0.000049 | 0.000038 | 0.000038 | 0.000000 | 0.000049 |
| T017_2023Q2 | 0.000036 | 0.000030 | 0.000036 | 0.000021 | 0.000010 |
| T018_2023Q2 | 0.000047 | 0.000026 | 0.000047 | 0.000002 | 0.000007 |
| T019_2023Q2 | 0.000048 | 0.000043 | 0.000048 | 0.000013 | 0.000002 |
| T020_2023Q2 | 0.000041 | 0.000033 | 0.000041 | 0.000022 | 0.000029 |
| T021_2023Q2 | 0.000047 | 0.000011 | 0.000031 | 0.000003 | 0.000047 |
| T022_2023Q2 | 0.000028 | 0.000028 | 0.000011 | 0.000028 | 0.000013 |
| T023_2023Q2 | 0.000031 | 0.000024 | 0.000024 | 0.000022 | 0.000031 |
| T024_2023Q2 | 0.000047 | 0.000046 | 0.000047 | 0.000040 | 0.000030 |
| T025_2023Q2 | 0.000045 | 0.000015 | 0.000044 | 0.000045 | 0.000042 |
| T026_2023Q2 | 0.000043 | 0.000026 | 0.000021 | 0.000019 | 0.000043 |
| T027_2023Q2 | 0.000043 | 0.000026 | 0.000043 | 0.000013 | 0.000037 |
| T028_2023Q2 | 0.000046 | 0.000046 | 0.000045 | 0.000007 | 0.000017 |
| T031_2023Q2 | 0.000041 | 0.000013 | 0.000040 | 0.000012 | 0.000041 |
| T032_2023Q2 | 0.000041 | 0.000019 | 0.000032 | 0.000041 | 0.000020 |
| T033_2023Q2 | 0.000045 | 0.000008 | 0.000034 | 0.000045 | 0.000015 |
| T034_2023Q2 | 0.000036 | 0.000001 | 0.000003 | 0.000036 | 0.000035 |
| T035_2023Q2 | 0.000050 | 0.000034 | 0.000050 | 0.000026 | 0.000035 |
| T036_2023Q2 | 0.000036 | 0.000016 | 0.000036 | 0.000018 | 0.000011 |
| T039_2023Q2 | 0.000031 | 0.000023 | 0.000031 | 0.000009 | 0.000013 |
| T040_2023Q2 | 0.000025 | 0.000025 | 0.000018 | 0.000010 | 0.000004 |
| T041_2023Q2 | 0.000044 | 0.000044 | 0.000011 | 0.000036 | 0.000043 |
| T042_2023Q2 | 0.000045 | 0.000032 | 0.000039 | 0.000026 | 0.000045 |
| T043_2023Q2 | 0.000048 | 0.000032 | 0.000048 | 0.000000 | 0.000021 |
| T044_2023Q2 | 0.000050 | 0.000041 | 0.000007 | 0.000006 | 0.000050 |
| T045_2023Q2 | 0.000050 | 0.000030 | 0.000019 | 0.000024 | 0.000050 |
| T046_2023Q2 | 0.000042 | 0.000041 | 0.000020 | 0.000005 | 0.000042 |
| T049_2023Q2 | 0.000046 | 0.000036 | 0.000046 | 0.000027 | 0.000019 |
| T050_2023Q2 | 0.000026 | 0.000025 | 0.000026 | 0.000008 | 0.000022 |
| T051_2023Q2 | 0.000035 | 0.000010 | 0.000001 | 0.000012 | 0.000035 |

**Note:** Cannot determine exact nodata rule used for CSV. Tested if including raw==0 pixels matches CSV - cannot determine without original script.

## Check 4: Distribution Sanity

### Pooled Percentiles (all chips)

| Index | P1 | P5 | P25 | P50 | P75 | P95 | P99 |
|-------|----|----|-----|-----|-----|-----|-----|
(See log for detailed percentiles)

### Expected Sign Behaviour

- NDWI > 0.2 (open water): 0.00% of pixels
- NDWI > 0.0: 1.29% of pixels
- NDSI < -0.1 (dry bare sand): 90.98% of pixels
- NDVI > 0.3 (vegetation): 36.78% of pixels

### Chips with Zero NDWI > 0.2 Pixels

- T004_2023Q2: 0% pixels with NDWI > 0.2 (river may not be visible)
- T005_2023Q2: 0% pixels with NDWI > 0.2 (river may not be visible)
- T006_2023Q2: 0% pixels with NDWI > 0.2 (river may not be visible)
- T007_2023Q2: 0% pixels with NDWI > 0.2 (river may not be visible)
- T008_2023Q2: 0% pixels with NDWI > 0.2 (river may not be visible)
- T009_2023Q2: 0% pixels with NDWI > 0.2 (river may not be visible)
- T010_2023Q2: 0% pixels with NDWI > 0.2 (river may not be visible)
- T011_2023Q2: 0% pixels with NDWI > 0.2 (river may not be visible)
- T012_2023Q2: 0% pixels with NDWI > 0.2 (river may not be visible)
- T013_2023Q2: 0% pixels with NDWI > 0.2 (river may not be visible)
- T014_2023Q2: 0% pixels with NDWI > 0.2 (river may not be visible)
- T015_2023Q2: 0% pixels with NDWI > 0.2 (river may not be visible)
- T016_2023Q2: 0% pixels with NDWI > 0.2 (river may not be visible)
- T017_2023Q2: 0% pixels with NDWI > 0.2 (river may not be visible)
- T018_2023Q2: 0% pixels with NDWI > 0.2 (river may not be visible)
- T019_2023Q2: 0% pixels with NDWI > 0.2 (river may not be visible)
- T020_2023Q2: 0% pixels with NDWI > 0.2 (river may not be visible)
- T021_2023Q2: 0% pixels with NDWI > 0.2 (river may not be visible)
- T022_2023Q2: 0% pixels with NDWI > 0.2 (river may not be visible)
- T023_2023Q2: 0% pixels with NDWI > 0.2 (river may not be visible)
- T024_2023Q2: 0% pixels with NDWI > 0.2 (river may not be visible)
- T025_2023Q2: 0% pixels with NDWI > 0.2 (river may not be visible)
- T026_2023Q2: 0% pixels with NDWI > 0.2 (river may not be visible)
- T027_2023Q2: 0% pixels with NDWI > 0.2 (river may not be visible)
- T028_2023Q2: 0% pixels with NDWI > 0.2 (river may not be visible)
- T031_2023Q2: 0% pixels with NDWI > 0.2 (river may not be visible)
- T032_2023Q2: 0% pixels with NDWI > 0.2 (river may not be visible)
- T033_2023Q2: 0% pixels with NDWI > 0.2 (river may not be visible)
- T034_2023Q2: 0% pixels with NDWI > 0.2 (river may not be visible)
- T035_2023Q2: 0% pixels with NDWI > 0.2 (river may not be visible)
- T036_2023Q2: 0% pixels with NDWI > 0.2 (river may not be visible)
- T039_2023Q2: 0% pixels with NDWI > 0.2 (river may not be visible)
- T040_2023Q2: 0% pixels with NDWI > 0.2 (river may not be visible)
- T041_2023Q2: 0% pixels with NDWI > 0.2 (river may not be visible)
- T042_2023Q2: 0% pixels with NDWI > 0.2 (river may not be visible)
- T043_2023Q2: 0% pixels with NDWI > 0.2 (river may not be visible)
- T044_2023Q2: 0% pixels with NDWI > 0.2 (river may not be visible)
- T045_2023Q2: 0% pixels with NDWI > 0.2 (river may not be visible)
- T046_2023Q2: 0% pixels with NDWI > 0.2 (river may not be visible)
- T049_2023Q2: 0% pixels with NDWI > 0.2 (river may not be visible)
- T050_2023Q2: 0% pixels with NDWI > 0.2 (river may not be visible)
- T051_2023Q2: 0% pixels with NDWI > 0.2 (river may not be visible)

### Per-Chip Stats

| Chip | Valid Pixels | NDWI>0.2% | NDSI<-0.1% | NDVI>0.3% |
|------|--------------|-----------|------------|-----------|
| T004_2023Q2 | 65536 | 0.00 | 87.45 | 26.05 |
| T005_2023Q2 | 65536 | 0.00 | 90.17 | 13.09 |
| T006_2023Q2 | 65536 | 0.00 | 78.24 | 51.81 |
| T007_2023Q2 | 65536 | 0.00 | 85.14 | 55.00 |
| T008_2023Q2 | 65536 | 0.00 | 86.88 | 10.78 |
| T009_2023Q2 | 65536 | 0.00 | 86.80 | 11.67 |
| T010_2023Q2 | 65536 | 0.00 | 83.70 | 29.21 |
| T011_2023Q2 | 65536 | 0.00 | 83.10 | 37.13 |
| T012_2023Q2 | 65536 | 0.00 | 90.57 | 30.58 |
| T013_2023Q2 | 65536 | 0.00 | 93.47 | 20.89 |
| T014_2023Q2 | 65536 | 0.00 | 90.66 | 31.35 |
| T015_2023Q2 | 65536 | 0.00 | 91.45 | 39.87 |
| T016_2023Q2 | 65536 | 0.00 | 93.08 | 35.86 |
| T017_2023Q2 | 65536 | 0.00 | 93.92 | 30.59 |
| T018_2023Q2 | 65536 | 0.00 | 87.97 | 36.34 |
| T019_2023Q2 | 65536 | 0.00 | 88.07 | 40.33 |
| T020_2023Q2 | 65536 | 0.00 | 89.36 | 50.94 |
| T021_2023Q2 | 65536 | 0.00 | 89.91 | 28.75 |
| T022_2023Q2 | 65536 | 0.00 | 82.56 | 33.96 |
| T023_2023Q2 | 65536 | 0.00 | 90.42 | 29.53 |
| T024_2023Q2 | 65536 | 0.00 | 90.50 | 22.84 |
| T025_2023Q2 | 65536 | 0.00 | 92.95 | 36.11 |
| T026_2023Q2 | 65536 | 0.00 | 92.86 | 35.08 |
| T027_2023Q2 | 65536 | 0.00 | 93.00 | 44.41 |
| T028_2023Q2 | 65536 | 0.00 | 88.73 | 49.98 |
| T031_2023Q2 | 65536 | 0.00 | 96.41 | 56.10 |
| T032_2023Q2 | 65536 | 0.00 | 93.65 | 38.38 |
| T033_2023Q2 | 65536 | 0.00 | 93.29 | 38.65 |
| T034_2023Q2 | 65536 | 0.00 | 92.05 | 37.05 |
| T035_2023Q2 | 65536 | 0.00 | 93.16 | 33.72 |
| T036_2023Q2 | 65536 | 0.00 | 92.52 | 38.61 |
| T039_2023Q2 | 65536 | 0.00 | 97.06 | 61.85 |
| T040_2023Q2 | 65536 | 0.00 | 92.47 | 15.43 |
| T041_2023Q2 | 65536 | 0.00 | 95.27 | 46.25 |
| T042_2023Q2 | 65536 | 0.00 | 95.24 | 46.86 |
| T043_2023Q2 | 65536 | 0.00 | 95.47 | 46.46 |
| T044_2023Q2 | 65536 | 0.00 | 91.54 | 16.06 |
| T045_2023Q2 | 65536 | 0.00 | 92.80 | 49.42 |
| T046_2023Q2 | 65536 | 0.00 | 91.31 | 17.73 |
| T049_2023Q2 | 65536 | 0.00 | 96.25 | 57.90 |
| T050_2023Q2 | 65536 | 0.00 | 95.23 | 49.36 |
| T051_2023Q2 | 65536 | 0.00 | 96.57 | 62.60 |

## Check 5: Visual Check

Visual check saved to: C:\New folder\yamuna_work\verification\visual_check.png
6 chips selected: 2 lowest mean NDWI, 2 highest mean NDWI, 2 random (seed=42).
Each chip shows: True colour | Stored NDWI | Stored NDSI | Recomputed - Stored NDWI

## Questions for the Student

1. **Median of indices vs median of reflectance:** Were the stored indices computed as the median of per-scene indices, or computed from the median reflectance composite? This cannot be determined from the chip data alone.

2. **CSV nodata rule:** The CSV means may use a different nodata definition (e.g., raw==0 in ALL bands vs ANY band). Cannot determine without the original extraction script.

3. **Index computation source:** Were indices computed per-scene then median-composited, or computed once from the median reflectance composite? This affects interpretation of index distributions.

4. **NDWI sign convention:** Standard NDWI (McFeeters) = (Green - NIR)/(Green + NIR). Water is positive. Confirm this matches your interpretation.

5. **NDSI formula:** Used (Green - SWIR)/(Green + SWIR) = MNDWI-like. Dry sand is negative. Confirm this matches your intention.

