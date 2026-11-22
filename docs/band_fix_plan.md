# Stage 1 - Band Mapping / B12 Verification Notes

## Evidence found (read-only)
- `C:\New folder\yamuna_work\verification\stacking_order_check.md` (2026-10-28): documents original `S2_SPECTRAL_BANDS` order as B2,B3,B4,B8,B5,B6,B7,B8A,B11,B12 (B8 misplaced at position 4) and states expected wavelength order B2,B3,B4,B5,B6,B7,B8,B8A,B11,B12.
- `C:\New folder\yamuna_work\verification\band_mapping_report.md` (2026-10-28): concluded band-order error; recommended rebuilding composites with corrected `S2_SPECTRAL_BANDS`.
- `C:\New folder\rebuild_reports\verification_09\band_mapping_report.md` (2026-11-21): post-rebuild diagnostic; `band_mapping_stats.csv` shows expected pairs (NDVI B8/B4, NDWI B3/B8, NDBI B11/B8, NDSI B3/B11) with median_mean_abs_diff ~7e-5 and median_frac_below_001==1.0.
- Git commit `1189d2a` (2026-11-21): "Phase A: rebuild S2 composites/chips with corrected band order" touching rebuild/composite/chip/verification scripts.

## Current Stage 1 checks (2026-11-22)
- All 11 `yamuna_data_fixed/sentinel2/**/*.tif` composites: count=14, dtype=uint16, nodata=0.0. **Band descriptions are all None** (B12@10 cannot be confirmed by metadata description).
- 5-chip deterministic recomputation (seed=42, chips_fixed, using expected band positions): NDVI/NDWI/NDBI/NDSI max abs diff <= 0.000488 (<0.01 threshold). PASS for index recomputation.
- B12 position: NOT VERIFIED from metadata (descriptions missing). Band 10 exists in 14-band files, but Stage 1 gate requires B12 in correct band position.

## Gate decision
- Stage 1 remains **BLOCKED** until B12 is explicitly verified in correct band position for all 11 S2 composites (e.g., set/confirm band descriptions, or run an explicit band-position check against known B12/reference and record evidence). No rebuild performed in this session.
