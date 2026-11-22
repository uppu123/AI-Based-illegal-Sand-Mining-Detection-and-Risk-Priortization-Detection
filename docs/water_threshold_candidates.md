# Stage 2 - Water Threshold Candidates

Generated from 2023 chips only (2024 excluded from threshold selection).
Student must choose threshold and record decision in `docs/water_threshold_decision.md`.
Until decision: `water_frac` remains blank and water-dependent features are PROVISIONAL.

- 2023 NDSI pixels (valid, finite): 11010048
- NDSI percentiles (2023): p50=-0.1830, p75=-0.1288, p90=-0.0854, p95=-0.0464, p99=0.1304

## Candidates

| Candidate (NDSI > t) | 2023 water pixel fraction | Notes |
|---:|---:|---|
| -0.10 | 0.138480 | Very permissive; likely includes wet sand/mixed pixels |
| -0.05 | 0.052350 | Permissive |
| 0.00 | 0.032684 | Physical water-positive boundary (MNDWI>0 style); conservative |
| 0.05 | 0.022024 | Conservative |
| 0.10 | 0.013343 | Very conservative; may miss shallow/turbid water |

## Histogram
- `metadata/water_hist.png`

## Decision required
Create `docs/water_threshold_decision.md` with:
- chosen threshold (value)
- rationale
- date and approver (student)
- statement: 2024 was not used for threshold selection
