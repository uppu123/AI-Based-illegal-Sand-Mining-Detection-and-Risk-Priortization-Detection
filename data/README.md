# Data location

The satellite imagery is **not stored in this repository**.

- Size: about **134.4 GB**, 5,293 files.
- Local location: `C:\New folder\yamuna_data` (imagery + products) and `C:\New folder\yamuna_work\chips` (chip rasters).
- Controlled by `config/project_config.py`: set `YAMUNA_WORKSPACE` to move the whole dataset elsewhere.

## What is in git instead

- `reports/` — inventory CSV, verification reports, logs, centreline GeoJSON, transect tables, data summaries.
- `labeling/` — rubric, candidate manifest, agreement log and 42 small truecolour preview PNGs.

## Inventory summary

| Sensor | Scenes | Products |
|---|---|---|
| Sentinel-2A/B | 39 | 11 composites (5 annual, 6 quarterly), 14 bands each |
| Sentinel-1A | 55 | 12 rasters (VV/VH × 6 quarters) |
| Landsat-8/9 | 6 | 6 thermal rasters |

Chips: 252 optical + 252 SAR, 256×256 px, 42 transects × 6 quarters.

## Constraint

Do not modify `yamuna_data` or `chips`. The Phase A rebuild writes to `yamuna_data_fixed`, `chips_fixed` and `verification_fixed` instead.
