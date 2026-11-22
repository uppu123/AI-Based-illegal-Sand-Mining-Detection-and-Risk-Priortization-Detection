# Stage 1 - Index Status (2026-11-22)

## Scope
- S2 composites checked: `C:\New folder\yamuna_data_fixed\sentinel2\**\*.tif` (11 files)
- 5-chip deterministic recomputation: seed=42 from `C:\New folder\chips_fixed\**\*.tif` (252 total)

## 5-chip recomputation (expected band positions, uint16 decode `raw/5000 - 1`)
| Chip | NDVI max/mean | NDWI max/mean | NDBI max/mean | NDSI max/mean | desc_ok |
|---|---:|---:|---:|---:|---:|
| chips_fixed\2023_Q1\T010_2023_Q1.tif | 0.000457 / 0.000088 | 0.000429 / 0.000088 | 0.000488 / 0.000081 | 0.000469 / 0.000090 | true |
| chips_fixed\2023_Q1\T034_2023_Q1.tif | 0.000354 / 0.000087 | 0.000386 / 0.000087 | 0.000330 / 0.000078 | 0.000365 / 0.000090 | true |
| chips_fixed\2023_Q2\T034_2023_Q2.tif | 0.000286 / 0.000076 | 0.000282 / 0.000076 | 0.000269 / 0.000068 | 0.000319 / 0.000079 | true |
| chips_fixed\2023_Q4\T045_2023_Q4.tif | 0.000342 / 0.000083 | 0.000342 / 0.000082 | 0.000304 / 0.000074 | 0.000381 / 0.000089 | true |
| chips_fixed\2024_Q1\T025_2024_Q1.tif | 0.000385 / 0.000085 | 0.000395 / 0.000085 | 0.000349 / 0.000076 | 0.000397 / 0.000088 | true |

**Result:** All max abs diffs <= 0.000488 (< 0.01). **Index recomputation: PASS** on sampled chips.

## S2 composite layout check
- All 11 composites: `count=14, dtype=uint16, nodata=0.0`.
- **Band descriptions: all None on all 11 composites** (`desc_ok=False` metadata only). Chips sampled have `descriptions_ok=true`.

## Independent B12 position proof (read-only, Option 2, 2026-11-22)
Compared `yamuna_data_fixed/sentinel2` band 10 (1-based) against `yamuna_data/sentinel2` band 10 for all 11 composites, on 3 sampled 512x512 windows per composite (top-left, center, bottom-right; nodata=0 excluded). Raw 2023_Q2 metadata shows original band order included `B12` at band 10 in the raw composite file.

| Composite | raw found | shape match | band10 fixed vs raw max/mean/p99 | equal_frac | band4 fixed vs raw max/mean (control) | band7 fixed vs raw max/mean (control) |
|---|---:|---:|---:|---:|---:|---:|
| S2_2018_composite.tif | yes | yes | 0/0/0 | 1.0 | 7034/794.43 | 5113/129.93 |
| S2_2019_composite.tif | yes | yes | 0/0/0 | 1.0 | 4296/563.04 | 1618/93.16 |
| S2_2020_composite.tif | yes | yes | 0/0/0 | 1.0 | 5116/814.30 | 5124/148.74 |
| S2_2021_composite.tif | yes | yes | 0/0/0 | 1.0 | 4054/661.27 | 3169/133.23 |
| S2_2022_composite.tif | yes | yes | 0/0/0 | 1.0 | 4485/673.65 | 2447/113.72 |
| S2_2023_Q1_composite.tif | yes | yes | 0/0/0 | 1.0 | 4455/562.41 | 4262/138.92 |
| S2_2023_Q2_composite.tif | yes | yes | 0/0/0 | 1.0 | 4853/862.27 | 3103/114.61 |
| S2_2023_Q3_composite.tif | yes | yes | 0/0/0 | 1.0 | 5080/922.81 | 2004/149.08 |
| S2_2023_Q4_composite.tif | yes | yes | 0/0/0 | 1.0 | 4042/795.59 | 1498/122.08 |
| S2_2024_Q1_composite.tif | yes | yes | 0/0/0 | 1.0 | 4440/628.17 | 3196/145.78 |
| S2_2024_Q2_composite.tif | yes | yes | 0/0/0 | 1.0 | 4354/639.46 | 1430/98.39 |

**Interpretation:** Band 10 is bit-identical between fixed and raw in sampled windows for all 11 composites (max_abs=0, equal_frac=1.0). Control bands 4 and 7 differ strongly, consistent with the documented Phase A band-order correction. Raw 2023_Q2 metadata lists `B12` at band 10. This provides independent pixel-level evidence that B12 content is at band position 10 in fixed composites.

**Remaining caveat:** Band descriptions are still missing in fixed composite metadata; this is metadata hygiene, not a band-position mismatch. Option 1 (additive metadata-only description repair with pixel hash check) is a good follow-up if you approve.

## Status
- Index recomputation: **PASS (sampled)**.
- B12 band-position verification on composites: **PASS by independent read-only pixel comparison** (band10 fixed==raw, 3 windows/composite, 11/11 composites).
- Metadata descriptions: **MISSING** (non-blocking for band-position proof; recommended cleanup with approval).
