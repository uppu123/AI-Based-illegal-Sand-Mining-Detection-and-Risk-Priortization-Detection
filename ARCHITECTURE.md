# Architecture and data flow

This document explains how the project fits together. It is the first page to show in a viva: one picture, then one table.

## 1. End-to-end data flow

```
 FREE SATELLITE ARCHIVES
   Copernicus Data Space Ecosystem (OData)      USGS EarthExplorer (M2M)
              |                                          |
              +--------------------+---------------------+
                                   v
              src/acquisition/extract_yamuna_data.py
              (search -> download -> SCL mask -> median composite -> indices)
                                   |
                    100 scenes -> 29 GeoTIFF products
                                   |
        +--------------------------+---------------------------+
        |                          |                           |
        v                          v                           v
 01_verify_data_inventory   build_centerline_from_sar    08_verify_spectral_indices
 (29 products checked)      (S1 VV + Otsu, 50.21 km)     (5-check index suite)
                                   |                           |
                                   v                           v
                       02_validate_river_centerline   09_diagnose_band_mapping
                                   |                   (B8-at-position-4 defect)
                                   v
                       03_generate_transects
                       (51 transects, 1 km apart)
                                   |
              +--------------------+--------------------+
              v                    v                    v
    04_extract_training_chips  extract_chips_all_quarters  extract_sar_chips
      (one demo quarter)        (252 optical chips)       (252 SAR chips)
              |
              v
    05_prepare_labeling_set  ->  06_generate_reviewer_sheet
    (rubric + 252 human labels -> 07_finalize_labels: 55/45/152)
              |
              v
    08_select_annotation_chips + annotation_server
    (16 human pixel masks -> U-Net/LMS-Net -> self-train 252)
              |
              v
        ___________________________________________________
       |  NEXT PHASE - no trained metrics yet             |
       |  models/  U-Net/LMS-Net -> self-training         |
       |           -> RF/XGBoost -> S2+S1 fusion          |
       |           -> morphology -> AHP risk score        |
       |  dashboard/ React + Leaflet + Express + MongoDB  |
       |___________________________________________________|
```

## 2. Module map

| Folder | Responsibility | Written to git? |
|---|---|---|
| `config/project_config.py` | Single source of truth for paths, AOI, band order and sensing constants | Yes |
| `src/acquisition/` | Download and processing of S2, S1 and L8 imagery | Yes (code) |
| `src/geometry/` | Centreline from SAR, transect generation | Yes (code) |
| `src/processing/` | Chip extraction for one quarter, all quarters, and SAR | Yes (code) |
| `src/labeling/` | Labeling rubric and manifest preparation | Yes (code + manifest in `labeling/`) |
| `src/verification/` | Inventory, geometry, index and band-mapping checks | Yes (code + reports) |
| `src/experiments/` | The failed NDWI centreline attempt, kept for the audit trail | Yes |
| `src/utilities/` | Small read-only inspection helpers | Yes |
| `models/` | Phase C: detection and risk models (placeholder with design) | Yes |
| `dashboard/` | Phase D: MERN dashboard (placeholder with plan) | Yes |
| `presentation/` | Final deck, script document, and the builders that generate them | Yes |
| `docs/` | Project log, guides, and the 7-PDF documentation pack | Yes |
| `reports/` | Verification reports, metadata CSVs, logs, centreline and transects | Yes |
| `labeling/` | Rubric, candidate manifest, agreement log, 42 preview PNGs | Yes |
| `data/` | Explanation of where the 134 GB imagery lives | Yes (README only) |
| `yamuna_data/`, `chips/` | Raw imagery and rasters — 134 GB, outside the repo | **No** |

## 3. Design rules used throughout

1. **No hard-coded paths in pipeline code.** Every script imports from `config/project_config.py`. Set `YAMUNA_WORKSPACE` to relocate the whole dataset.
2. **One script, one job.** Numbered scripts (`01_` … `09_`) are the ordered pipeline; named scripts are reusable variants.
3. **Read-only verification.** `08_` and `09_` never modify imagery — they only report.
4. **Every check leaves evidence.** Reports and logs land in `reports/`, not in temporary folders.
5. **Honest status wording.** "Designed" means code/plan exists; "trained" is reserved for measured metrics. No metric is invented.

## 4. Known defect (important for the viva)

The composites currently on disk contain spectral bands in the order `B2,B3,B4,**B8**,B5,B6,B7,B8A,B11,B12`. The correct order (now in `config/project_config.py`) is `B2,B3,B4,B5,B6,B7,**B8**,B8A,B11,B12`. The four index bands (11–14) are correct because they were computed by band name. Evidence: `reports/verification/band_mapping_report.md`. Rebuild is Phase A of the remaining work.
