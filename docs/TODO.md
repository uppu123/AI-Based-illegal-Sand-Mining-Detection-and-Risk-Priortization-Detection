# Yamuna Sand Mining Detection - Project TODO

## Step 0: Setup
- [x] Create directory structure (scripts, logs, metadata, centerline, transects, chips/2023_Q2/previews, labeling, docs)
- [x] Create docs/TODO.md
- [x] Create docs/PROJECT_LOG.md
- [x] Verify required libraries import (rasterio, numpy, pandas, geopandas, shapely, pyproj, matplotlib, pillow)
- [x] Install missing library: geopandas
- [x] Create docs/README.md

## Step 1: Verify Data Inventory (01_verify_inventory.py)
- [x] Create script 01_verify_inventory.py
- [x] Run script and verify all 29 expected files
- [x] Generate inventory_check.csv
- [x] Check: PASS (zero FAIL) - 12 OK, 18 WARN, 0 FAIL

## Step 2: Validate Centerline (02_validate_centerline.py)
- [x] Create script 02_validate_centerline.py
- [x] Check if centerline GeoJSON exists - **NOT FOUND**
- [x] **Blocked by: user** - need to digitize in QGIS
- [x] Created auto-generation script using S1 VV (generate_centerline_s1.py)
- [x] Generated centerline (50.21 km, within 45-60 km range)
- [x] Run validation checks - **PASS**
- [x] Generate centerline_validation.txt and centerline_check.png
- [x] Oriented version saved (north-to-south)

## Step 3: Create Transects (03_make_transects.py)
- [x] Create script 03_make_transects.py
- [x] Generate transect points, lines, table, and map
- [x] Validate transects - 51 transects, 0 outside AOI, all centers within 5m of centerline

## Step 4: Extract Chips 2023_Q2 (04_extract_chips.py)
- [x] Create script 04_extract_chips.py
- [x] Extract 256x256 chips for each transect point
- [x] Generate chips, previews, contact sheet
- [x] Generate chips_2023Q2.csv and skipped_transects.csv
- [x] Results: 42 kept, 9 skipped (outside_raster)

## Step 8: Band Mapping Check (09_band_mapping_check.py)
- [x] Create script 09_band_mapping_check.py
- [x] Run all 7 steps
- [x] Generate band_mapping_report.md
- [x] Generate band_mapping_stats.csv
- [x] Results: Root cause found - band order bug in processing script (B8 written at position 4 instead of 7)

## Step 9: Fix Band Order & Rebuild Composites
- [x] Fix band order in extract_yamuna_data.py (S2_SPECTRAL_BANDS corrected to wavelength order)
- [ ] Rebuild Sentinel-2 composites - **BLOCKED: zip files deleted after extraction**
- [ ] Re-run verification (script 08) on rebuilt composites

## Step 6: Prepare Labeling Set (05_prepare_labeling.py)
- [x] Create script 05_prepare_labeling.py
- [x] Copy KEEP chips to labeling/images/
- [x] Copy previews to labeling/previews/
- [x] Create label_guidelines.md
- [x] Create label_manifest.csv
- [x] Create agreement_log.csv template

## Final Step
- [ ] Mark all TODO items complete or blocked with reason
- [ ] Print directory tree
- [ ] Print KEEP/skipped counts and first 5 manifest rows
- [ ] Print last 40 lines of PROJECT_LOG.md
- [ ] List all assumptions
- [ ] Create memory vault in Obsidian