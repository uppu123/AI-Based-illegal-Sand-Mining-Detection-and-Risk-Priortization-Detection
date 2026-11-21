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
| Phase A data repair | **Done** — 11 composites + 252 clean chips rebuilt; 11/11 band-position PASS, 5/5 index checks PASS |
| Chip-level labels | **Done** — 252 human-reviewed labels frozen: **55 MINING / 45 NOT MINING / 152 UNSURE** |
| Extra labeling features | **Done** — water fraction, CMI (bare-exposure ratio), river distance for 11 scenes + 252 chips |
| Human pixel masks | **In progress** — 28-chip browser annotation tool; **16/28 mask files saved** (12 new river chips + T015 repaint pending) |
| Detection / risk models | **Phase C** - U-Net and LMS-Net trained on 28 masks; honest held-out IoU 0.0055 / 0.0059 (near zero, sparse masks) |
| MERN dashboard | **Not started** |
| Progress figure shown in deck | **55%** = weighted block completion: data + labels ~55%, models 30%, dashboard 10%, reporting 5% |
| Strictly usable today | **55%** - data, labels and masks complete; models trained but not yet useful; dashboard and reporting remain |

## 3. What has been done so far

| # | Work | Evidence in this repo |
|---|---|---|
| 1 | Synopsis, problem definition, 5 core references | `presentation/Project_Synopsis_Final.docx` / `.pdf` |
| 2 | Literature review (20+ papers scanned → 5 selected, incl. Mukherjee CMI) | `docs/documentation_pdfs/05_Literature_and_Reasons.pdf` |
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
| 15 | Band order fixed, 11 composites + 252 chips rebuilt into NEW folders, all 5 checks PASS | `src/acquisition/rebuild_composites_from_local.py`, `src/processing/extract_chips_all_quarters.py` |
| 16 | 4-slide progress deck with 55% loader, DTU logo, speaker notes | `presentation/Project_Progress_Presentation.pptx` / `.pdf` |
| 17 | 13-page script + reasoning document | `presentation/Presentation_Script_and_Reasoning.docx` / `.pdf` |
| 18 | Deck audit (no overflow, opens without repair) | `presentation/helpers/audit_deck_geometry.py` |
| 19 | Full audit trail | `docs/PROJECT_LOG.md` |
| 20 | Extra features: water fraction (clamped Otsu), CMI = (B11−B12)/(B11+B12), distance to centreline | `src/processing/compute_extra_features.py`, `08_Extra_Features_and_Thresholds.pdf` |
| 21 | **252 human labels validated and frozen** (55/45/152); decisive labels perfectly separable by `sand_frac > 0.575` — documented as a transparent bare-sediment rule, **not** a genuine accuracy result | `src/labeling/07_finalize_labels.py`, `data/verified_labels.csv` |
| 22 | 6 quarterly reviewer packages (252 chips) with truecolour + NDSI previews and feature columns | `C:\New folder\label_review\<quarter>\` |
| 23 | 28-chip human pixel-mask annotation tool (Flask + canvas UI, cyan water overlay) | `src/labeling/annotation_server.py`, `annotation_ui.html`, `08_select_annotation_chips.py` |
| 24 | NDSI annotation guide PDF, also embedded in the annotation UI | `docs/documentation_pdfs/09_Annotation_Guide_for_Mining_Masks.pdf` |

## 4. What remains (execution plan)

Pixel-mask sign-off is complete (**28/28** masks saved) and the training hard gate passed. The remaining gate is **C15 risk validation**. A10 verification and B7 label sign-off are complete.

| Phase | Work | Owner |
|---|---|---|
| **A — Data repair** | **DONE** — 11 composites + 252 clean chips rebuilt, 11/11 band-position PASS, 5/5 index checks PASS | Assistant |
| **B — Labels** | **DONE** — 252 chip labels frozen, 28 human pixel masks saved (28/28), 3-fold GroupKFold by transect applied | Assistant + **You** (masks signed off) |
| **C - Models** | U-Net and LMS-Net trained on 28 masks (IoU 0.0055 / 0.0059 - honest, weak) then self-training all 252 chips, RF/XGBoost baseline, S1+S2 fusion, morphology, AHP-weighted risk score and hotspot **rank** validation | Assistant + **You** (approve weights) |
| **D — Dashboard** | React + Leaflet map, mining-mask overlay, sortable priority table; Node/Express API + MongoDB (SQLite fallback) | Assistant + **You** (freeze MVP, click-test) |
| **E — Reports** | Correct slide 2 (real script names), slide 4 (no fixed-day deadline), update literature to 5 references, re-export PDFs | Assistant |
| **F — Handover** | Timed rehearsal, 12-question Q&A, final checklist, present | **You** |

No fixed calendar target is claimed. Masks are signed off; your remaining input is roughly **15–30 min** (weight approval, MVP freeze, rehearsal). Two decisions are required from you: **approve AHP weights**, **freeze dashboard MVP scope**.

## 5. Repository structure

The code is organised by **role**, and files are named `snake_case` with an optional step number so the execution order is visible.

```
config/project_config.py   All paths, AOI, band order and sensing constants
src/
  acquisition/             Download + composite + index engine
  geometry/                Centreline from SAR, 51 transects
  processing/              Chip extractors + extra features (water/CMI/distance)
  labeling/                Reviewers, label freeze, pixel-mask annotation tool
  verification/            Inventory, geometry, index and band-mapping checks
  experiments/             Superseded NDWI centreline attempt
  utilities/               Read-only inspection helpers
models/                    Phase C: U-Net + LMS-Net trained (honest metrics), AHP risk scorer, self-trainer
dashboard/                 Phase D MERN plan (not started)
presentation/              Final deck + builders; archive/ holds old iterations
docs/                      Guides, project log, documentation PDFs 00-06
docs/documentation_pdfs/   PDFs 00-09 (07-09 copied from external generation)
reports/                   Verification, metadata, logs, centreline, transects
labeling/                  Rubric, manifest, agreement log, preview PNGs
data/                      verified_labels.csv + data-location note
```

Start with **[ARCHITECTURE.md](ARCHITECTURE.md)** for the data-flow diagram, then **[docs/PIPELINE_GUIDE.md](docs/PIPELINE_GUIDE.md)** for the exact commands. If someone asks for a script named on slide 2, use **[docs/CODE_MAP.md](docs/CODE_MAP.md)**.

## 6. Data availability — important

The **134 GB of satellite imagery is NOT in this repository** (GitHub per-file limit is 100 MB; total imagery is ~1,300× that). It lives locally at `C:\New folder\yamuna_data` and `C:\New folder\yamuna_work\chips`. Those folders are **read-only for this project** — rebuilds went to new folders (`yamuna_data_fixed`, `chips_fixed`).

The original band-order defect is **fixed in the rebuilt data**: 11 composites and 252 chips in the NEW folders have PASS on all band-position and index checks. Originals were left byte-identical. To regenerate from scratch: `src/acquisition/extract_yamuna_data.py` (needs CDSE + USGS credentials). Precomputed, small derivatives — inventory CSVs, verification reports, centreline GeoJSON, transect tables, labeling metadata — **are** in `reports/` and `labeling/`.

## 7. Models (both segmentation runs completed; risk score is rule-based)

1. **Random Forest / XGBoost** — cheap baseline on 14 bands + extra features; go/no-go gate and fallback detector. A model using `sand_frac` will look perfect on the 100 decisive labels; this is reported transparently as a bare-sediment rule, not as a genuine accuracy result.
2. **U-Net / LMS-Net** — pixel-level mining mask from 256×256×14 chips, BCE+Dice, 3-fold *spatial* GroupKFold by transect on the 28 human masks. LMS-Net multi-scale is chosen because mining patches range from pits to kilometre-long bars. Both held-out evaluations are real: U-Net IoU 0.0055 / Dice 0.0110 / F1 0.0110; LMS-Net IoU 0.0059 / Dice 0.0117 / F1 0.0117. They are near zero because the masks are sparse (0.2–3.1% positive pixels in 12 of 28 chips). No accuracy is inflated; see `C:\New folder\segmentation_runs\model_comparison.csv`.
3. **Self-training loop (run complete, pipeline demo only)** — the 3 LMS-Net folds were applied to all 252 chips at threshold 0.7: 224 pseudo-masks are empty, 28 are non-empty (max 1.37% positive pixels), median mean-confidence 0.0085. These are confidence-scored pseudo-masks, **not** human ground truth and too sparse for defensible risk ranking. See `docs/documentation_pdfs/10_Self_Training_Results.pdf`.
4. **S2 + S1 late fusion** — SAR all-weather path for cloudy monsoon months; optical path stays standalone.
5. **Risk scorer (rule-based, not a trained regressor)** — `models/compute_risk_score.py` applies AHP weights (detection 30%, persistence 25%, morphology 20%, access 15%, vegetation loss 10%) to min-max-scaled features. There is **no supervised risk model and no risk ground truth** here, so no risk accuracy or calibration can be claimed; validation is by **rank correlation against known hotspots only**. Weights are PROPOSED pending approval. Tiers: High ≥70, Medium 40–70, Low <40.

## 8. Papers behind the design

- **Zhang, Liu & Liu (2025), Remote Sensing 17(2):227 — LMS-Net** → lightweight multi-scale segmentation.
- **Kaur et al. (2025), Environmental Geochemistry and Health 47(11):459 — Sutlej** → morphometric change metrics (bank shift, width, erosion/deposition).
- **Nair et al. (2025), Geocarto International 40(1):2551261 — AHP + ML** → hybrid weighting + calibrated risk mapping.
- **JIIT Noida India-specific spectral-index study** → NDVI/NDWI/NDBI/NDSI threshold logic for semi-automatic labeling (manual-labeling model uses THIS paper, not IIT Kharagpur).
- **Mukherjee et al. — Coal Mine Index** → `CMI = (B11 − B12)/(B11 + B12)` used strictly as a **bare-exposure ratio**; SWIR-I = B11, SWIR-II = B12. Not a coal detector.

## 9. Documentation

Read `docs/documentation_pdfs/00_Documentation_Index.pdf` first. PDFs 01–06 cover work completed, data/sensors, scripts, models, literature, and the full remaining-step plan; 07 is the Phase A repair report, 08 the extra-features report, and 09 the NDSI annotation guide (also shown inside the annotation tool).

---

*This repository is a progress-review snapshot. "Designed" means code/report exists; "trained" would mean measured metrics — none are claimed here.*
