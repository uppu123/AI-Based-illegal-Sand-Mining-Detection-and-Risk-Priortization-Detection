# Water Threshold Decision (Stage 2 Gate)

- **Date:** 2026-11-22
- **Approver:** Upendra Kumar (student)
- **Chosen threshold:** `NDSI > 0.0` (i.e., `water_threshold = 0.0`)
- **Status:** APPROVED

## Rationale
- NDSI in this project is `(B3 - B11)/(B3 + B11)` decoded as `raw/5000 - 1`, which is water-positive (MNDWI-style). `> 0.0` is a physically interpretable water boundary.
- 2023-only candidate evaluation (11,010,048 valid NDSI pixels) gave water pixel fraction 0.032684 at `t=0.0`, which is plausible for river chips and avoids over-including wet sand/mixed pixels seen at negative thresholds.
- Negative thresholds (-0.10, -0.05) were more permissive (13.85%, 5.24%) and risk labeling wet sand/mixed pixels as water; positive thresholds (0.05, 0.10) were more conservative and may miss shallow/turbid water.

## Protocol compliance
- 2024 chips/composites were **NOT** used for threshold selection. Candidates and histogram were computed from 2023 chips only.
- `metadata/features_v2.csv` `water_frac` populated after this decision using `NDSI > 0.0` on valid pixels.
