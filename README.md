# AI-Based Illegal Sand Mining Detection and Risk Prioritization System on Yamuna River

**BTech Progress Review — Group 162**  
Department of Information Technology, Delhi Technological University  
Team: **Upendra Kumar (23/IT/165)** and **Somya Tripathi (23/IT/162)**  
Supervisor: **Dr. Anita Thakur**  
Academic year 2025–26

---

## 1. Objective

Detect illegal sand extraction along the Delhi stretch of the Yamuna (Palla → Jaitpur–Kondli, ~50 km) from free satellite imagery, and convert detections into a **prioritized risk list** for enforcement. The final deliverable is a lightweight detection pipeline plus a MERN dashboard showing mining masks and a segment-wise priority table.

## 2. Current status

| Item | Status |
|---|---|
| Data engineering (download, composites, centreline, transects, chips, indices) | **Done** |
| Labeling set-up | Done — 42 **candidate** labels (16 mining / 14 not / 12 unsure), **not human-verified** |
| Index verification | Found band-order defect; fix applied in code, **rebuild pending** |
| Detection / risk models | **Designed, not trained** |
| MERN dashboard | **Not started** |
| Progress figure shown in deck | **55%** (data + labeling block complete) |
| Strictly usable today | Closer to **50%** — do not claim more than 55% |

## 3. What has been done so far

| # | Work | Evidence in this repo |
|---|---|---|
| 1 | Synopsis, problem definition, 4 core references | `presentation/Project_Synopsis_Final.docx` / `.pdf` |
| 2 | Literature review (20+ papers scanned → 4 selected) | `docs/documentation_pdfs/05_Literature_and_Reasons.pdf` |
| 3 | Download/processing pipeline (~1,900 lines, CDSE OData + USGS M2M, resume, SCL median composite) | `src/acquisition/extract_yamuna_data.py` |
| 4 | **100 scenes downloaded** — 39 Sentinel-2, 55 Sentinel-1A, 6 Landsat-8/9 (134 GB) | `reports/logs/`, `reports/yamuna_data_report.pdf` |
| 5 | **29 GeoTIFF products** — 11 S2 (5 annual + 6 quarterly), 12 S1 (VV/VH × 6), 6 L8 thermal | `reports/metadata/inventory_check.csv` |
| 6 | Inventory validation (bands, dtype, CRS, resolution, nodata, AOI overlap) | `src/verification/01_verify_data_inventory.py` |
| 7 | Centreline: NDWI failed → S1 VV + Otsu → **50.21 km** | `src/geometry/build_centerline_from_sar.py`, `reports/centerline/` |
| 8 | Centreline validation | `src/verification/02_validate_river_centerline.py` |
| 9 | **51 transects** at 1 km spacing, 3 km long | `src/geometry/03_generate_transects.py`, `reports/transects/` |
| 10 | **252 S2 + 252 S1 chips** (256×256), 6 quarters, 42/quarter | `src/processing/04_extract_training_chips.py`, `extract_chips_all_quarters.py`, `extract_sar_chips.py` |
| 11 | NDVI, NDWI, NDBI, NDSI as bands 11–14 (×5000 encoding) | `src/acquisition/extract_yamuna_data.py` |
| 12 | Labeling rubric, manifest, agreement log | `labeling/` |
| 13 | 5-check index verification — found NDVI/NDWI/NDBI mismatch (~0.27) | `src/verification/08_verify_spectral_indices.py`, `reports/verification/` |
| 14 | Root-cause: B8 written at position 4 instead of 7 (indices themselves correct) | `src/verification/09_diagnose_band_mapping.py`, `reports/verification/band_mapping_report.md` |
| 15 | Band order fixed at line 99 of extractor — **products not yet rebuilt** | `src/acquisition/extract_yamuna_data.py` |
| 16 | 4-slide progress deck with 55% loader, DTU logo, speaker notes | `presentation/Project_Progress_Presentation.pptx` / `.pdf` |
| 17 | 13-page script + reasoning document | `presentation/Presentation_Script_and_Reasoning.docx` / `.pdf` |
| 18 | Deck audit (no overflow, opens without repair) | `presentation/helpers/audit_deck_geometry.py` |
| 19 | Full audit trail | `docs/PROJECT_LOG.md` |

## 4. What remains (execution plan)

Three hard gates cannot be skipped: **A10** verification, **B7** label sign-off, **C15** risk validation.

| Phase | Work | Owner |
|---|---|---|
| **A — Data repair** | Rebuild S2 composites/chips with corrected band order into NEW folders; remove 42 duplicate 2023_Q2 files; re-run all 5 verification checks | Assistant |
| **B — Labels** | Freeze rubric, regenerate candidates, build reviewer sheet; **verify 42 chips** (focus on 12 UNSURE), sign off | Assistant + **You** |
| **C — Models** | RF/XGBoost baseline → U-Net/LMS-Net with spatial CV → S2+S1 late fusion → morphology metrics → AHP-weighted risk score → hotspot rank validation | Assistant + **You** (approve weights) |
| **D — Dashboard** | React + Leaflet map, mining-mask overlay, sortable priority table; Node/Express API + MongoDB (SQLite fallback) | Assistant + **You** (freeze MVP, click-test) |
| **E — Reports** | Paper, thesis section, corrected slide 2 (real script names) and slide 4 (no stale 45-day claim), re-export all PDFs | Assistant |
| **F — Handover** | Timed rehearsal, 12-question Q&A, final checklist, present | **You** |

Estimated: ~22–27 h assistant work, ~2.5–3.5 h your time, 2–4 days calendar (shorter with a Colab T4 GPU).

Only three decisions are required from you: **verify labels**, **approve AHP weights**, **freeze dashboard MVP scope**.

## 5. Repository structure

The code is organised by **role**, and files are named `snake_case` with an optional step number so the execution order is visible.

```
config/project_config.py   All paths, AOI, band order and sensing constants
src/
  acquisition/             Download + composite + index engine
  geometry/                Centreline from SAR, 51 transects
  processing/              Chip extractors (one quarter, all quarters, SAR)
  labeling/                Labeling-set preparation
  verification/            Inventory, geometry, index and band-mapping checks
  experiments/             Superseded NDWI centreline attempt
  utilities/               Read-only inspection helpers
models/                    Phase C model design (not trained)
dashboard/                 Phase D MERN plan (not started)
presentation/              Final deck + builders; archive/ holds old iterations
docs/                      Guides, project log, 7-PDF documentation pack
reports/                   Verification, metadata, logs, centreline, transects
labeling/                  Rubric, manifest, agreement log, 42 preview PNGs
data/                      Data-location note (imagery itself is external)
```

Start with **[ARCHITECTURE.md](ARCHITECTURE.md)** for the data-flow diagram, then **[docs/PIPELINE_GUIDE.md](docs/PIPELINE_GUIDE.md)** for the exact commands. If someone asks for a script named on slide 2, use **[docs/CODE_MAP.md](docs/CODE_MAP.md)**.

## 6. Data availability — important

The **134 GB of satellite imagery is NOT in this repository** (GitHub per-file limit is 100 MB; total imagery is ~1,300× that). It lives locally at `C:\New folder\yamuna_data` and `C:\New folder\yamuna_work\chips`. Those folders are **read-only for this project** — rebuilds go to new folders (`yamuna_data_fixed`, `chips_fixed`, `verification_fixed`).

To regenerate from scratch: `src/acquisition/extract_yamuna_data.py` (needs CDSE + USGS credentials). Precomputed, small derivatives — inventory CSVs, verification reports, centreline GeoJSON, transect tables, labeling metadata — **are** in `reports/` and `labeling/`.

Known defect: raw spectral bands 4–7 of the current composites are permuted (B8 at position 4). Index bands 11–14 are correct. Fix is in code; rebuild pending.

## 7. Models (designed, not trained)

1. **Random Forest / XGBoost** — cheap baseline on 14 bands + feature importance; go/no-go gate and fallback detector.
2. **U-Net / LMS-Net** — pixel-level mining mask from 256×256×14 chips, BCE+Dice, 3-fold *spatial* CV (leak-free). LMS-Net multi-scale chosen because mining patches range from pits to kilometre-long bars, and it reaches ~98% accuracy at ~1/10 U-Net parameters.
3. **S2 + S1 late fusion** — SAR all-weather path for the cloudy monsoon months; optical path stays standalone.
4. **Risk-score regressor** — AHP weights (detection 30%, persistence 25%, morphology 20%, access 15%, vegetation loss 10%) + learned calibration; validated by **rank correlation** against known hotspots, never a fabricated "risk accuracy".

## 8. Papers behind the design

- **Zhang, Liu & Liu (2025), Remote Sensing 17(2):227 — LMS-Net** → lightweight multi-scale segmentation.
- **Kaur et al. (2025), Environmental Geochemistry and Health 47(11):459 — Sutlej** → morphometric change metrics (bank shift, width, erosion/deposition).
- **Nair et al. (2025), Geocarto International 40(1):2551261 — AHP + ML** → hybrid weighting + calibrated risk mapping.
- **JIIT Noida India-specific spectral-index study** → threshold logic for semi-automatic labeling without ground truth.

## 9. Documentation

Read `docs/documentation_pdfs/00_Documentation_Index.pdf` first. The other six PDFs cover work completed, data/sensors, scripts, models, literature, and the full remaining-step plan.

---

*This repository is a progress-review snapshot. "Designed" means code/report exists; "trained" would mean measured metrics — none are claimed here.*
