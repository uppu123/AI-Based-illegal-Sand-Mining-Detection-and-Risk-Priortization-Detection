# Pipeline execution guide

Run commands from the repository root. All paths default to `config/project_config.py`, so you normally pass no path flags.

## 0. Environment

```powershell
# Optional: point at a different data location
$env:YAMUNA_WORKSPACE = "C:\New folder"

pip install -r requirements.txt
```

The imagery itself is **not** in git. It must already exist at `$YAMUNA_WORKSPACE\yamuna_data`.

## 1. Acquisition (already executed — do not repeat without need)

```powershell
python src/acquisition/extract_yamuna_data.py --dry-run          # plan only
python src/acquisition/extract_yamuna_data.py --sources sentinel2 --workers 4 --yes
```

Output: 39 S2 SAFE products, 55 S1 products, 6 L8 products, 29 GeoTIFF products.

## 2. Verification and geometry

| # | Command | Output |
|---|---|---|
| 01 | `python src/verification/01_verify_data_inventory.py` | `reports/metadata/inventory_check.csv` |
| 02 | `python src/geometry/build_centerline_from_sar.py` | `reports/centerline/yamuna_centerline.geojson` (50.21 km) |
| 03 | `python src/verification/02_validate_river_centerline.py` | centreline validation report + map |
| 04 | `python src/geometry/03_generate_transects.py` | 51 transects in `reports/transects/` |

`src/experiments/legacy_centerline_from_ndwi.py` is the superseded optical attempt (NDWI failed in the dry season). It is kept only for the audit trail.

## 3. Chips and labeling

| # | Command | Output |
|---|---|---|
| 05 | `python src/processing/04_extract_training_chips.py` | 42 chips for the demo quarter |
| 06 | `python src/processing/extract_chips_all_quarters.py` | 252 optical chips (6 quarters) |
| 07 | `python src/processing/extract_sar_chips.py` | 252 SAR chips (6 quarters) |
| 08 | `python src/labeling/05_prepare_labeling_set.py` | rubric + candidate labels in `labeling/` |
| 09 | `python src/labeling/06_generate_reviewer_sheet.py` | 6 quarterly review packages (252 chips) |
| 10 | `python src/labeling/07_finalize_labels.py` | `data/verified_labels.csv` — 55 MINING / 45 NOT / 152 UNSURE |
| 11 | `python src/labeling/08_select_annotation_chips.py` | 16 chips for human pixel masks (unique transects) |
| 12 | `python src/labeling/annotation_server.py` | browser tool at `http://127.0.0.1:8765` → `C:\New folder\annotation\masks\` |

**Human gate:** chip labels are frozen (252 rows, validated). The remaining human input is **16 pixel masks** in the browser tool; U-Net/LMS-Net training starts only after 16/16 masks are saved. The NDSI rules are in `docs/documentation_pdfs/09_Annotation_Guide_for_Mining_Masks.pdf` and embedded in the tool.

## 4. Index and band checks (hard gate)

```powershell
python src/verification/08_verify_spectral_indices.py
python src/verification/09_diagnose_band_mapping.py
```

All five checks must PASS before any model is trained. Today they expose the band-order defect; Phase A of `06_Remaining_Steps.pdf` fixes it.

## 5. Presentation artifacts

```powershell
python presentation/build_progress_deck.py        # rebuild 4-slide deck
python presentation/build_script_document.py      # rebuild script doc + notes
python presentation/build_documentation_pack.py   # rebuild 7 documentation PDFs
powershell -File presentation/export_all_pdfs.ps1
```

## 6. Phase A reminder — rebuild safely

The rebuild must write to **new** folders (`yamuna_data_fixed`, `chips_fixed`, `verification_fixed`). Do not modify `yamuna_data` or `chips`. Override the defaults with the CLI flags shown in `--help`, or set a separate workspace and copy only the small metadata files.
