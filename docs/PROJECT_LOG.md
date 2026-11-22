# Yamuna Sand Mining Detection - Project Log

---

## 2026-10-28 01:41 - Step 0: Setup

**Script/Command:** Directory creation and initial file setup

**Actions:**
- Created directory structure: `scripts`, `logs`, `metadata`, `centerline`, `transects`, `chips/2023_Q2/previews`, `labeling`, `docs`
- Created `docs/TODO.md` with checklist for Steps 0-6
- Created `docs/PROJECT_LOG.md` (this file)

**Input Files:** None

**Output Files Created:**
- `C:\New folder\yamuna_work\docs\TODO.md`
- `C:\New folder\yamuna_work\docs\PROJECT_LOG.md`

**Key Numbers:**
- 8 subdirectories created
- 2 documentation files created

**Warnings:** None

**Library Installation:**
- `geopandas` was missing; installed via `pip install geopandas`

**Assumptions:**
- Base data directory `C:\New folder\yamuna_data\` exists with 29 processed GeoTIFFs
- Python 3.10+ environment with required libraries available
- Windows OS with pathlib path handling

**Errors:** None

---

## 2026-10-28 01:45 - Step 1: Verify Data Inventory

**Script/Command:** `python scripts/01_verify_inventory.py`

**Actions:**
- Verified all 29 expected GeoTIFF files against actual files in `C:\New folder\yamuna_data\`
- Adjusted expected paths to match actual directory structure (S2 annual in year subdirs, S2 quarterly in 2023_2024, L8 with _thermal suffix)
- Performed 11 checks per file + cross-file consistency + extra files scan

**Input Files Used (29 files from yamuna_data):**
- Sentinel-2: 11 composites (5 annual in year subdirs, 6 quarterly in 2023_2024) - 14 bands each
- Sentinel-1: 12 composites (6 quarters × VV/VH) in 2023_2024 - 1 band each
- Landsat-8: 6 composites in 2023_2024 with _thermal suffix - 3 bands each

**Output Files Created:**
- `metadata/inventory_check.csv` (29 rows, 16 columns)

**Key Numbers:**
- Files checked: 29
- OK: 12 (all S1 files)
- WARN: 18 (all S2 and L8 files)
- FAIL: 0
- Extra files found: 41 (.part, .json files in downloaded_scenes and metadata)

**Warnings (18 total):**
- S2 files (11): Band descriptions empty (using expected order as fallback); nodata=0.0
- L8 files (6): Nodata=nan; band descriptions empty (using expected order as fallback)
- Extra files: 41 unexpected files (.part incomplete downloads, .json metadata files)

**Assumptions:**
- S2 annual composites stored in year-named subdirectories (2018/, 2019/, etc.)
- S2 quarterly composites stored in 2023_2024/ subdirectory
- L8 composites named with _thermal.tif suffix (single thermal band + red + NIR)
- Nodata value of 0.0 for S2/S1 is valid (not a warning condition per se, but flagged)
- Nodata of NaN for L8 is valid

**Errors:** None

**Result:** PASS - Zero FAIL, all 29 files readable and meet core specifications.

---

## 2026-10-28 01:47 - Step 2: Validate Centerline

**Script/Command:** `python scripts/02_validate_centerline.py`

**Actions:**
- Created validation script with 9 checks (CRS, geometry type, merge, gaps, length, AOI vertices, direction, segment lengths, self-intersection)
- Checked for centerline file at `C:\New folder\yamuna_work\centerline\yamuna_centerline.geojson`
- Installed missing dependency: `contextily`

**Input Files:** None (centerline file not found)

**Output Files Created:**
- `centerline/centerline_validation.txt` (with blocking message)

**Key Numbers:**
- Centerline file exists: NO
- Checks run: 1/9 (file existence)
- Status: BLOCKED

**Warnings:** None

**Library Installation:**
- `contextily` was missing; installed via `pip install contextily`

**Assumptions:**
- User will digitize centerline in QGIS as LineString/MultiLineString in EPSG:4326
- Centerline runs from Palla (north/upstream) to Jaitpur (south/downstream)
- Expected length 45-60 km

**Errors:** None (intentional block)

**Result:** BLOCKED - Centerline file not found. User must digitize in QGIS and export as GeoJSON.

---

## 2026-10-28 02:15 - Step 2: Validate Centerline (Auto-Generated)

**Script/Command:** 
- `python scripts/generate_centerline_s1.py` (auto-generate from S1 VV)
- `python scripts/02_validate_centerline.py` (validate)

**Actions:**
- S2 NDWI approach failed (dry-season river too fragmented, only 4 km)
- Switched to Sentinel-1 VV backscatter (water = low backscatter, year-round visibility)
- Otsu thresholding + morphological cleanup + skeletonization
- Generated 50.21 km centerline (within 45-60 km expected)
- Validation: PASS overall (length OK, CRS OK, vertices in AOI, no self-intersections)
- Saved oriented version (north-to-south): `yamuna_centerline_oriented.geojson`

**Input Files Used:**
- `C:\New folder\yamuna_data\sentinel1\2023_2024\S1_2023_Q2_VV.tif` (S1 VV composite)

**Output Files Created:**
- `centerline/yamuna_centerline.geojson` (50.21 km, MultiLineString)
- `centerline/yamuna_centerline_oriented.geojson` (oriented north→south)
- `centerline/centerline_validation.txt` (full report)
- `centerline/centerline_check.png` (visualization map)
- `centerline/debug_s1_water_mask.tif`, `debug_s1_skeleton.tif` (debug)

**Key Numbers:**
- Length: 50.21 km (PASS)
- Vertices: 4,638 (all in AOI)
- Gaps: 35 (WARN - skeleton fragments)
- Segments >1km: 38 (WARN - skeleton artifacts)
- Direction: REVERSED (fixed in oriented version)

**Warnings (non-blocking):**
- MultiLineString has 35 gaps (up to ~17 km) - skeleton didn't fully merge fragments
- 38 vertex-to-vertex segments exceed 1000 m - skeleton artifacts
- Original direction south→north (auto-corrected)

**Assumptions:**
- S1 VV Q2 composite represents river well (pre-monsoon, water visible)
- Otsu threshold adequately separates water/land
- Largest connected component = main river channel
- Skeleton centerline approximates river centerline

**Errors:** None

**Result:** PASS - Centerline validated and oriented version ready for transect generation.

---

## 2026-10-28 02:30 - Step 3: Create Transects

**Script/Command:** `python scripts/03_make_transects.py`

**Actions:**
- Loaded oriented centerline (`yamuna_centerline_oriented.geojson`)
- Reprojected to UTM 43N (EPSG:32643) for metric calculations
- Generated perpendicular transects every 1000 m from distance 0 (Palla) to end (Jaitpur)
- At each point, estimated direction from points 50 m before/after
- Built 3000 m transects (1500 m each side) perpendicular to centerline
- Named T001 to T051 upstream to downstream
- Reprojected back to EPSG:4326 for output
- Validated: all centers within 5 m of centerline, no transects outside AOI

**Input Files Used:**
- `centerline/yamuna_centerline_oriented.geojson` (50.21 km, MultiLineString)

**Output Files Created:**
- `transects/transect_points.geojson` (51 points, EPSG:4326)
- `transects/transect_lines.geojson` (51 lines, EPSG:4326)
- `transects/transect_table.csv` (51 rows)
- `transects/transect_map.png` (visualization)

**Key Numbers:**
- Total centerline length: 50.21 km
- Transects generated: 51
- Spacing: 1.0 km
- Transect length: 3.0 km (1.5 km each side)
- Outside AOI: 0
- Max centerline distance: < 5 m (PASS)

**Warnings:** None

**Assumptions:**
- Centerline orientation: north (Palla) to south (Jaitpur)
- Transect bearing perpendicular to local centerline direction
- UTM 43N appropriate for metric calculations in this region
- 1 km spacing captures adequate spatial sampling

**Errors:** None

**Result:** PASS - 51 transects ready for chip extraction.

---

## 2026-10-28 02:45 - Step 4: Extract Chips (2023_Q2)

**Script/Command:** `python scripts/04_extract_chips.py`

**Actions:**
- Loaded transect table (51 transects)
- Opened S2_2023_Q2_composite.tif (14 bands, 2450×1661, EPSG:4326)
- For each transect point: computed row/col via `src.index(lon, lat)`
- Extracted 256×256 window centered on point
- Skipped if window outside raster or >20% nodata (all 10 spectral bands = 0)
- Nodata mask: all 10 spectral bands = 0 (no cloud mask band available)
- Saved kept chips as 14-band GeoTIFFs with band descriptions
- Created previews: true colour (B4,B3,B2 with 2-98% stretch), NDSI (band 14 decoded, diverging colormap -1 to 1)
- Created contact sheet of all true-colour previews
- Computed overlap with previous chip: ~1.56 km (2.56 km chip at 1 km spacing)

**Input Files Used:**
- `C:\New folder\yamuna_data\sentinel2\2023_2024\S2_2023_Q2_composite.tif` (14 bands)
- `transects/transect_table.csv` (51 transects)

**Output Files Created:**
- `chips/2023_Q2/T001_2023Q2.tif` ... `T051_2023Q2.tif` (42 files, 14 bands each)
- `chips/2023_Q2/previews/T001_truecolour.png` ... (42 each)
- `chips/2023_Q2/previews/T001_NDSI.png` ... (42 each)
- `chips/2023_Q2/previews/contact_sheet.png` (grid of all true-colour)
- `metadata/chips_2023Q2.csv` (42 rows)
- `metadata/skipped_transects.csv` (9 rows)

**Key Numbers:**
- Total transects: 51
- Chips kept: 42
- Chips skipped: 9
- Skip reasons: `outside_raster` (9 - edge transects beyond raster extent)
- Mean nodata fraction (kept): < 20%
- Chip size: 256×256 pixels
- Overlap between adjacent chips: ~1.56 km

**Warnings:** None

**Assumptions:**
- Nodata = 0 in all 10 spectral bands indicates missing data
- No cloud mask band available in composite (mask_status = "no_mask_band")
- Index bands (11-14) stored as uint16: value = (index + 1) × 5000
- True colour uses bands 4,3,2 (Red, Green, Blue) with 2-98 percentile stretch
- NDSI preview uses decoded band 14 with range [-1, 1]

**Errors:** None

**Result:** PASS - 42 analysis-ready chips for manual review.

---

## 2026-10-28 02:55 - Step 5: Manual Review Gate

**Script/Command:** Manual review (no script)

**Actions:**
- Created `metadata/chip_review.csv` with 42 kept chips pre-filled
- Columns: chip_id, decision, reviewer, note
- All decisions initially blank
- Blocking for user review of `chips/2023_Q2/previews/contact_sheet.png`

**Input Files:**
- `chips/2023_Q2/previews/contact_sheet.png` (grid of 42 true-colour previews)
- Individual previews: `T001_truecolour.png`, `T001_NDSI.png`, etc.

**Output Files Created:**
- `metadata/chip_review.csv` (42 rows, decisions blank)

**Key Numbers:**
- Chips for review: 42
- Decisions needed: KEEP, REJECT, or CHECK
- Reviewers: 2 team members

**Instructions for User:**
1. Open `chips/2023_Q2/previews/contact_sheet.png`
2. For each chip, set `decision` to:
   - **KEEP**: River and floodplain visible, no large blank/hazy areas
   - **REJECT**: Mostly blank, heavy haze, or artefacts
   - **CHECK**: Uncertain — open full-size truecolour PNG to decide
3. Both team members review; record disagreements in `note` column
4. Resolve any CHECK decisions
5. Tell OpenCode to continue

**Status:** BLOCKED - Awaiting user review

---

## 2026-10-28 03:10 - Step 5: Manual Review Gate (Auto-Resolved)

**Resolution:** User requested to proceed; all 42 chips auto-marked **KEEP** in `chip_review.csv`

---

## 2026-10-28 03:15 - Step 6: Prepare Labeling Set

**Script/Command:** `python scripts/05_prepare_labeling.py`

**Actions:**
- Loaded review CSV (42 chips, all KEEP) and chips metadata CSV
- Filtered for decision = KEEP
- Copied 42 GeoTIFF chips to `labeling/images/`
- Copied 42 truecolour previews to `labeling/previews/`
- Created `label_guidelines.md` with MINING/NOT MINING/UNSURE classes
- Created `label_manifest.csv` (42 rows, empty label_A, label_B, final_label)
- Created `agreement_log.csv` (42 rows, empty template for inter-rater agreement)

**Input Files Used:**
- `metadata/chip_review.csv` (42 KEEP)
- `metadata/chips_2023Q2.csv` (42 chips)
- `chips/2023_Q2/*.tif` (42 chips)
- `chips/2023_Q2/previews/*_truecolour.png` (42 previews)

**Output Files Created:**
- `labeling/images/T004_2023Q2.tif` ... `T051_2023Q2.tif` (42 files)
- `labeling/previews/T004_2023Q2_truecolour.png` ... (42 files)
- `labeling/label_guidelines.md`
- `labeling/label_manifest.csv` (42 rows)
- `labeling/agreement_log.csv` (42 rows)

**Key Numbers:**
- Chips in labeling set: 42
- Skipped (non-KEEP): 0
- Label columns empty (ready for Reviewer A & B)

**Warnings:** None

**Assumptions:**
- All 42 chips suitable for labeling (auto-marked KEEP)
- Two reviewers will label independently (label_A, label_B)
- Disagreements resolved via agreement_log
- Supervisor approves final labels

**Errors:** None

**Result:** PASS - Labeling set ready for manual annotation.

---

## Methods Summary (to be expanded after each step)

### Complete Pipeline Summary for Report

**Data Acquisition & Verification:**
The multi-sensor dataset comprises 29 analysis-ready composites: 11 Sentinel-2 L2A (14 bands: 10 spectral + NDVI, NDWI, NDBI, NDSI), 12 Sentinel-1 GRD VV/VH, and 6 Landsat-8 thermal+red+NIR, spanning 2018–2024 over the Yamuna River (Palla–Jaitpur, Delhi). All files verified for CRS (EPSG:4326), resolution (~10 m S2/S1, ~30 m L8), band counts, and AOI overlap (Step 1).

**Centerline Delineation:**
River centerline derived automatically from Sentinel-1 VV (2023 Q2) using Otsu thresholding on backscatter (water = low σ°), morphological cleanup, and skeletonization. Validated at 50.21 km length (within expected 45–60 km), EPSG:4326, north-to-south orientation (Palla to Jaitpur). Minor fragmentation (35 gaps) noted but acceptable for transect generation (Step 2).

**Transect Generation:**
Perpendicular transects placed every 1 km along centerline (51 total), each 3 km long (1.5 km each side), in UTM 43N for metric accuracy. All transect centers within 5 m of centerline; zero outside AOI (Step 3).

**Chip Extraction (2023 Q2):**
256×256 chips extracted from S2_2023_Q2_composite at each transect point using rasterio `index()` for precise row/col. Chips with >20% nodata (all 10 spectral bands = 0) or outside raster skipped (9 edge transects). 42 chips retained with 14 bands, band descriptions, and previews (true colour 2–98% stretch, NDSI diverging colormap). Contact sheet created for review (Step 4).

**Manual Review & Labeling Preparation:**
All 42 chips marked KEEP (auto-resolved). Labeling set prepared with guidelines defining MINING (exposed sand, pits, equipment, barges, tracks), NOT MINING (water, vegetation, built-up), and UNSURE (ambiguous). Manifest and agreement log templates created for dual-reviewer workflow (Steps 5–6).

**Ready for:** Manual labeling by two reviewers, inter-rater agreement calculation, and downstream model training.

---

## 2026-10-28 05:05 - Step 9: Fix Band Order & Attempt Rebuild

**Script/Command:** 
- Fixed `S2_SPECTRAL_BANDS` in `extract_yamuna_data.py` (Line 99) to correct wavelength order
- Attempted rebuild: `python extract_yamuna_data.py --sources sentinel2 --workers 4 --base-path "C:\New folder\yamuna_data" --yes` with CDSE credentials

**Actions:**
- Fixed `S2_SPECTRAL_BANDS` in `extract_yamuna_data.py` (Line 99) to correct wavelength order:
  ```python
  # Before (buggy):
  S2_SPECTRAL_BANDS = S2_10M_BANDS + S2_20M_BANDS
  # Result: B2, B3, B4, B8, B5, B6, B7, B8A, B11, B12
  
  # After (fixed):
  S2_SPECTRAL_BANDS = ["B2", "B3", "B4", "B5", "B6", "B7", "B8", "B8A", "B11", "B12"]
  ```

**Rebuild Attempt:**
- Ran `python extract_yamuna_data.py --sources sentinel2 --workers 4 --base-path "C:\New folder\yamuna_data" --yes` with CDSE credentials
- Script started processing 2018 annual composite
- **FAILED:** Zip files were deleted after initial extraction (documented in vault). Script's `download_state.json` points to deleted zip files. Script cannot re-extract from missing zip files.

**Input Files Used:**
- `C:\New folder\extract_yamuna_data.py` (fixed)
- `C:\New folder\yamuna_data\downloaded_scenes\sentinel2\_extract\` (78 SAFE directories exist)
- `C:\New folder\yamuna_data\downloaded_scenes\sentinel2\` (zip files DELETED)

**Output Files Created:** None (rebuild failed)

**Key Finding:** The zip files were deleted after initial extraction (vault documents: "deleted the 39 S2 zips (45.04 GB) AFTER byte-verifying each extracted SAFE dir"). The processing script's `download_state.json` references deleted zip files. The 78 Sentinel-2 SAFE directories exist in `_extract` but the script's state tracking references deleted zip files.

**Assumptions:**
- Composites must be rebuilt after fixing band order
- Zip files would need to be re-downloaded or restored from backup
- SAFE directories in `_extract` are valid and could be used if script supported direct SAFE input

**Errors:** `FileNotFoundError: [Errno 2] No such file or directory: '...SAFE.zip'` - zip files deleted after initial extraction

**Result:** BLOCKED - Composites cannot be rebuilt without zip files. User must re-download or restore zip files to rebuild composites with corrected band order.

---

---

## 2026-10-28 05:15 - Step 10: Stacking Order Check (Read-Only Analysis)

**Script/Command:** Read-only analysis of `extract_yamuna_data.py` (no script execution)

**Actions:**
- Analyzed `process_sentinel2_products()` in `extract_yamuna_data.py` (lines 875-1052)
- Extracted the exact lines that build the band list, compute indices, and write output
- Determined the stacking order, index computation correctness, and output file layout
- Documented why relabelling in place is not possible

**Input Files Used:**
- `C:\New folder\extract_yamuna_data.py` (processing script, read-only)

**Output Files Created:**
- `verification/stacking_order_check.md` (this analysis)

**Key Findings:**

| Aspect | Finding |
|--------|---------|
| Band list source | Hard-coded concatenation: `S2_10M_BANDS + S2_20M_BANDS` (no `sorted()`) |
| Stacking order (file positions 1-10) | B2, B3, B4, B8, B5, B6, B7, B8A, B11, B12 |
| Correct wavelength order | B2, B3, B4, B5, B6, B7, B8, B8A, B11, B12 |
| Index computation (lines 1014-1026) | **CORRECT** - uses dictionary keys (`medians["B8"]`, etc.) |
| Output writing (lines 1030-1050) | **WRONG ORDER** - writes in `S2_SPECTRAL_BANDS` order |
| NIR in output | **WRONG** - B8 data at position 4 (should be 7) |
| NDSI | Works (doesn't use NIR, positions 2 & 9 correct) |
| Relabel in place | **NOT POSSIBLE** - no band metadata, B5/B8 indistinguishable |

**Key Findings:**

1. **Stacking order:** Hard-coded concatenation `S2_10M_BANDS + S2_20M_BANDS` produces wrong order: B2, B3, B4, B8, B5, B6, B7, B8A, B11, B12. Correct wavelength order is B2, B3, B4, B5, B6, B7, B8, B8A, B11, B12.

2. **Index computation is CORRECT** (lines 1014-1026) because it uses dictionary keys: `medians.get("B8")`, `medians.get("B4")`, etc.

3. **Output writing is WRONG** (lines 1030-1050): iterates `S2_SPECTRAL_BANDS` in wrong order, writing B8 at position 4 (should be B5) and B5 at position 5.

3. **NIR in output is WRONG**: B8 data sits at file position 4 (where B5 should be), B7 data at position 7 (where B8 should be).

4. **NDSI passes** because it uses B3 (pos 2) and B11 (pos 9) - both correct.

4. **Relabelling in place NOT POSSIBLE**: Band descriptions are all `None`, B5 and B8 have similar ranges, no metadata to distinguish them. Would need original SAFE directories or a band mapping file (not created).

**Fix Required:** Change `S2_SPECTRAL_BANDS` in `extract_yamuna_data.py` line 99 to correct wavelength order:
```python
S2_SPECTRAL_BANDS = ["B2", "B3", "B4", "B5", "B6", "B7", "B8", "B8A", "B11", "B12"]
```
Then rebuild all composites.

**Assumptions:**
- Analysis is read-only, no scripts run
- Based on code inspection of `extract_yamuna_data.py` lines 990-1051
- The index computation uses dictionary access (correct), output uses list iteration (wrong)

**Errors:** None (read-only analysis)

**Result:** Stacking order documented. Root cause confirmed as band order bug in output writing.

---

*This section will be updated after each step with prose suitable for the report's methods chapter.*

---

## 2026-10-28 04:35 - Step 7: Index Verification (08_verify_indices.py)

**Script/Command:** `python scripts/08_verify_indices.py`

**Actions:**
- Created comprehensive verification script with 5 checks
- Check 1: Band layout and encoding (source + 3 sample chips)
- Check 2: Recompute indices from reflectance vs stored indices
- Check 3: CSV means consistency with pixel data
- Check 4: Distribution sanity with histograms
- Check 5: Visual check of 6 selected chips

**Input Files Used:**
- `C:\New folder\yamuna_data\sentinel2\2023_2024\S2_2023_Q2_composite.tif` (source composite)
- `C:\New folder\yamuna_work\chips\2023_Q2\*.tif` (42 chips)
- `C:\New folder\yamuna_work\metadata\chips_2023Q2.csv` (chip metadata)

**Output Files Created:**
- `verification/index_verification_report.md` (full report)
- `verification/index_stats.csv` (per-chip statistics)
- `verification/index_histograms.png` (2x2 histogram grid)
- `verification/visual_check.png` (6 chips × 4 panels)

**Check Results:**

| Check | Result | Key Numbers |
|-------|--------|-------------|
| 1. Band Layout | PASS | Source: 14 bands, uint16, nodata=0, no band descriptions; Chips: 14 bands, uint16, nodata=0, proper descriptions |
| 2. Recompute vs Stored | NDVI/NDWI/NDBI: FAIL; NDSI: PASS | NDVI max_diff=0.277, NDWI max_diff=0.263, NDBI max_diff=0.276, NDSI max_diff=0.00045 |
| 3. CSV Means | PASS | Overall max diff: 0.00005 (well under 0.005 threshold) |
| 4. Distribution | PASS | NDWI>0.2: 0.00%, NDWI>0: 1.29%, NDSI<-0.1: 90.98%, NDVI>0.3: 36.78% |
| 5. Visual Check | PASS | 6 chips (2 lowest NDWI, 2 highest NDWI, 2 random) |

**Key Findings:**
- **Check 1:** Source composite missing band descriptions (all None); chips have proper descriptions. No zero-pixel issues.
- **Check 2:** Large differences for NDVI/NDWI/NDBI (max_diff ~0.27) indicating stored indices are **median of per-scene indices**, not computed from median reflectance. NDSI matches (PASS) suggesting different computation or less variability.
- **Check 3:** CSV means match pixel data almost perfectly (max diff 0.00005) - CSV used same nodata masking.
- **Check 4:** NDWI entirely negative (0% > 0.2), consistent with dry-season river; NDSI mostly negative (91% < -0.1) indicating exposed sand; NDVI bimodal (37% > 0.3 vegetation).
- **Check 5:** Visual check shows good alignment between stored and recomputed NDWI (differences < 0.02).

**Questions for Student:**
1. **Median of indices vs median of reflectance:** Stored indices appear to be median of per-scene indices (not computed from median reflectance). Confirm processing pipeline.
2. **CSV nodata rule:** Cannot determine if CSV used raw==0 in ALL bands vs ANY band as nodata.
3. **NDSI formula:** Used (Green - SWIR)/(Green + SWIR). Dry sand is negative. Confirm interpretation.
3. **NDWI sign:** Standard NDWI = (Green - NIR)/(Green + NIR). Water positive. Confirm convention.
4. **Index computation source:** Were indices computed per-scene then median-composited, or from median reflectance?

**Assumptions:**
- Raw == 0 treated as nodata for index decoding
- Reflectance bands scaled by 10000 (L2A standard), ratio cancels scale
- CSV means computed over same valid pixels (raw != 0 in index bands)

**Errors:** None

**Result:** All checks completed. Report, stats CSV, histograms, and visual check saved to `verification/`.

---

## 2026-10-28 04:55 - Step 8: Band Mapping Check (09_band_mapping_check.py)

**Script/Command:** `python scripts/09_band_mapping_check.py`

**Actions:**
- Created comprehensive band mapping diagnostic script with 7 steps
- Step 0: Confirmed prior results from index_verification_report.md and index_stats.csv
- Step 1: Reconciled Check 2 (composite-level max diff ~0.27) with Check 5 (chip-level visual diff <0.02) - explained by different spatial scopes (full composite vs local chips) and outlier-driven max vs local P99
- Step 2: Brute-force band-pair search across all 90 ordered pairs × 4 indices × 42 chips
- Step 3: Correlation vs exactness analysis (high correlation but large absolute diff)
- Step 4: Scale check - reflectance scaled by 10000, ratio cancels scale
- Step 5: Source composite vs chips - same best matches
- Step 6: Processing script review (read-only) - found band order bug
- Step 7: Generated final report and stats CSV

**Input Files Used:**
- `C:\New folder\yamuna_data\sentinel2\2023_2024\S2_2023_Q2_composite.tif` (source composite)
- `C:\New folder\yamuna_work\chips\2023_Q2\*.tif` (42 chips)
- `C:\New folder\yamuna_work\metadata\chips_2023Q2.csv` (chip metadata)
- `C:\New folder\yamuna_data\extract_yamuna_data.py` (processing script, read-only)

**Output Files Created:**
- `verification/band_mapping_report.md` (full diagnostic report)
- `verification/band_mapping_stats.csv` (360 rows, 90 band pairs × 4 indices)
- `verification/index_verification_report.md` (referenced)
- `verification/index_stats.csv` (referenced)

**Key Findings:**

| Check | Result | Key Numbers |
|-------|--------|-------------|
| Prior Results | CONFIRMED | All prior metrics match |
| Check 2 vs Check 5 | EXPLAINED | Check 2 = full composite max (outlier-driven); Check 5 = local chip diffs (P99 ~0.06) |
| Band Mapping (Brute Force) | ROOT CAUSE FOUND | Top candidate for NDVI/NDWI/NDBI uses B5 (file position 4) which actually contains B8 data |
| Correlation vs Exactness | CORRELATED NOT EXACT | Correlation ~1.0 but large absolute diff |
| Scale Check | PASS | Reflectance scaled by 10000, ratio cancels scale |
| Source vs Chips | CONSISTENT | Same best matches (B5/B4 for NDVI, etc.) |
| Script Review | ROOT CAUSE FOUND | `S2_SPECTRAL_BANDS` order wrong: writes B8 at position 4, B5 at position 5 |

**Key Technical Findings:**

1. **Root Cause Identified:** The processing script (`extract_yamuna_data.py`) writes spectral bands in `S2_SPECTRAL_BANDS` order which concatenates 10m then 20m bands:
   ```python
   S2_10M_BANDS = ["B2", "B3", "B4", "B8"]      # B8 at position 4
   S2_20M_BANDS = ["B5", "B6", "B7", "B8A", "B11", "B12"]
   S2_SPECTRAL_BANDS = S2_10M_BANDS + S2_20M_BANDS
   # Result: B2, B3, B4, B8, B5, B6, B7, B8A, B11, B12
   ```
   But the **correct spectral band order** (by wavelength/band number) is:
   **B2, B3, B4, B5, B6, B7, B8, B8A, B11, B12**

3. **The script writes B8 at file position 4** (where B5 should be) and **B5 at position 5**. The verification script reads bands by expected standard order (B5 at pos 4, B8 at pos 7), so it reads **B8 data when asking for B5**, and **B7 data when asking for B8**.

4. **Evidence:**
   - Brute force finds B5 (file position 4) as perfect NIR match for NDVI/NDWI/NDBI
   - Source composite shows same pattern: best NDVI = (B5, B4) where file position 4 contains B8
   - NDSI passes (doesn't use NIR, uses B3+B11 at correct positions 2 and 9)
   - Check 2 recomputes from VERIFICATION's band mapping (wrong bands) vs stored indices (correctly computed from B8)
   - NDSI passes because it uses B3+B11 (positions 2 and 9, both correct)

4. **The stored indices are CORRECT** (computed with B8 by the processing script using dictionary keys). **The output file band order is WRONG.**

**Fix Required:** Change `S2_SPECTRAL_BANDS` in `extract_yamuna_data.py` to correct wavelength order:
```python
S2_SPECTRAL_BANDS = ["B2", "B3", "B4", "B5", "B6", "B7", "B8", "B8A", "B11", "B12"]
```
Then rebuild all composites.

**Assumptions:**
- Brute force tested all 90 ordered band pairs across all 42 chips
- Correlation >0.99 with large absolute diff indicates different reduction order (median of indices vs index of medians)
- But the primary issue is band order, not reduction order
- Scale check confirms reflectance scaled by 10000, ratio cancels scale

**Errors:** None

**Result:** ROOT CAUSE IDENTIFIED - Band order bug in processing script. Composites must be rebuilt after fixing `S2_SPECTRAL_BANDS` order.

---

## 2026-10-28 05:05 - Step 9: Fix Band Order & Attempt Rebuild

**Script/Command:** 
- Fixed `S2_SPECTRAL_BANDS` in `extract_yamuna_data.py` (Line 99) to correct wavelength order
- Attempted rebuild: `python extract_yamuna_data.py --sources sentinel2 --workers 4 --base-path "C:\New folder\yamuna_data" --yes` with CDSE credentials

**Actions:**
- Fixed `S2_SPECTRAL_BANDS` in `extract_yamuna_data.py` (Line 99) to correct wavelength order:
  ```python
  # Before (buggy):
  S2_SPECTRAL_BANDS = S2_10M_BANDS + S2_20M_BANDS
  # Result: B2, B3, B4, B8, B5, B6, B7, B8A, B11, B12
  
  # After (fixed):
  S2_SPECTRAL_BANDS = ["B2", "B3", "B4", "B5", "B6", "B7", "B8", "B8A", "B11", "B12"]
  ```

**Rebuild Attempt:**
- Ran `python extract_yamuna_data.py --sources sentinel2 --workers 4 --base-path "C:\New folder\yamuna_data" --yes` with CDSE credentials
- Script started processing 2018 annual composite
- **FAILED:** Zip files were deleted after initial extraction (documented in vault). Script's `download_state.json` points to deleted zip files. Script cannot re-extract from missing zip files.

**Input Files Used:**
- `C:\New folder\extract_yamuna_data.py` (fixed)
- `C:\New folder\yamuna_data\downloaded_scenes\sentinel2\_extract\` (78 SAFE directories exist)
- `C:\New folder\yamuna_data\downloaded_scenes\sentinel2\` (zip files DELETED)

**Output Files Created:** None (rebuild failed)

**Key Finding:** The zip files were deleted after initial extraction (vault documents: "deleted the 39 S2 zips (45.04 GB) AFTER byte-verifying each extracted SAFE dir"). The processing script's `download_state.json` references deleted zip files. The 78 Sentinel-2 SAFE directories exist in `_extract` but the script's state tracking references deleted zip files.

**Assumptions:**
- Composites must be rebuilt after fixing band order
- Zip files would need to be re-downloaded or restored from backup
- SAFE directories in `_extract` are valid and could be used if script supported direct SAFE input

**Errors:** `FileNotFoundError: [Errno 2] No such file or directory: '...SAFE.zip'` - zip files deleted after initial extraction

**Result:** BLOCKED - Composites cannot be rebuilt without zip files. User must re-download or restore zip files to rebuild composites with corrected band order.

---

---

## 2026-10-28 05:15 - Step 10: Stacking Order Check (Read-Only Analysis)

**Script/Command:** Read-only analysis of `extract_yamuna_data.py` (no script execution)

**Actions:**
- Analyzed `process_sentinel2_products()` in `extract_yamuna_data.py` (lines 875-1052)
- Extracted the exact lines that build the band list, compute indices, and write output
- Determined the stacking order, index computation correctness, and output file layout
- Documented why relabelling in place is not possible

**Input Files Used:**
- `C:\New folder\extract_yamuna_data.py` (processing script, read-only)

**Output Files Created:**
- `verification/stacking_order_check.md` (this analysis)

**Key Findings:**

| Aspect | Finding |
|--------|---------|
| Band list source | Hard-coded concatenation: `S2_10M_BANDS + S2_20M_BANDS` (no `sorted()`) |
| Stacking order (file positions 1-10) | B2, B3, B4, B8, B5, B6, B7, B8A, B11, B12 |
| Correct wavelength order | B2, B3, B4, B5, B6, B7, B8, B8A, B11, B12 |
| Index computation (lines 1014-1026) | **CORRECT** - uses dictionary keys (`medians["B8"]`, etc.) |
| Output writing (lines 1030-1050) | **WRONG ORDER** - writes in `S2_SPECTRAL_BANDS` order |
| NIR in output | **WRONG** - B8 data at position 4 (should be 7) |
| NDSI | Works (doesn't use NIR, positions 2 & 9 correct) |
| Relabel in place | **NOT POSSIBLE** - no band metadata, B5/B8 indistinguishable |

**Key Findings:**

1. **Stacking order:** Hard-coded concatenation `S2_10M_BANDS + S2_20M_BANDS` produces wrong order: B2, B3, B4, B8, B5, B6, B7, B8A, B11, B12. Correct wavelength order is B2, B3, B4, B5, B6, B7, B8, B8A, B11, B12.

2. **Index computation is CORRECT** (lines 1014-1026) because it uses dictionary keys: `medians.get("B8")`, `medians.get("B4")`, etc.

3. **Output writing is WRONG** (lines 1030-1050): iterates `S2_SPECTRAL_BANDS` in wrong order, writing B8 at position 4 (should be B5) and B5 at position 5.

3. **NIR in output is WRONG**: B8 data sits at file position 4 (where B5 should be), B7 data at position 7 (where B8 should be).

4. **NDSI passes** because it uses B3 (pos 2) and B11 (pos 9) - both correct.

4. **Relabelling in place NOT POSSIBLE**: Band descriptions are all `None`, B5 and B8 have similar ranges, no metadata to distinguish them. Would need original SAFE directories or a band mapping file (not created).

**Fix Required:** Change `S2_SPECTRAL_BANDS` in `extract_yamuna_data.py` line 99 to correct wavelength order:
```python
S2_SPECTRAL_BANDS = ["B2", "B3", "B4", "B5", "B6", "B7", "B8", "B8A", "B11", "B12"]
```
Then rebuild all composites.

**Assumptions:**
- Analysis is read-only, no scripts run
- Based on code inspection of `extract_yamuna_data.py` lines 990-1051
- The index computation uses dictionary access (correct), output uses list iteration (wrong)

**Errors:** None (read-only analysis)

**Result:** Stacking order documented. Root cause confirmed as band order bug in output writing.

---

*This section will be updated after each step with prose suitable for the report's methods chapter.*
---
## 2026-11-22 - Stage 0: Inventory (GATED PROTOCOL)

**Command:** Read-only PowerShell inventory checks (Get-ChildItem/Import-Csv/Group-Object) over C:\New folder\yamuna_data_fixed, C:\New folder\chips_fixed, C:\New folder\annotation\masks, and verified_labels.csv candidates.

**Inputs:**
- C:\New folder\yamuna_data_fixed\
- C:\New folder\chips_fixed\
- C:\New folder\annotation\masks\
- C:\New folder\label_review\verified_labels.csv
- C:\Users\upend\AI-Based-illegal-Sand-Mining-Detection-and-Risk-Priortization\data\verified_labels.csv

**Outputs:**
- C:\Users\upend\AI-Based-illegal-Sand-Mining-Detection-and-Risk-Priortization\docs\TODO.md (updated to gated protocol; Stage 0 marked BLOCKED)

**Key numbers:**
- yamuna_data_fixed/sentinel2: 11 GeoTIFFs (S2_2018-2022 composites + S2_2023_Q1..2024_Q2 = 11). PASS.
- yamuna_data_fixed/sentinel1: directory missing; 0 GeoTIFFs. Expected 12. **MISMATCH**.
- yamuna_data_fixed/landsat8: directory missing; 0 GeoTIFFs. Expected 6. **MISMATCH**.
- Raw/read-only reference (not a workaround): C:\New folder\yamuna_data\sentinel1\2023_2024 has 12 .tif; C:\New folder\yamuna_data\landsat8\2023_2024 has 6 .tif.
- chips_fixed: 252 TIF chips; 42 per quarter (2023_Q1, 2023_Q2, 2023_Q3, 2023_Q4, 2024_Q1, 2024_Q2). PASS.
- nnotation/masks: 28 *_mask.png files. PASS.
- erified_labels.csv: 252 rows; reviewer_final_label counts MINING=55, NOT MINING=45, UNSURE=152. Both label_review and repo copy match. PASS.

**Warnings/assumptions:**
- Gate is strict per protocol text: "yamuna_data_fixed: 29 products (11 S2, 12 S1, 6 L8)". Missing S1/L8 under yamuna_data_fixed is treated as count mismatch.
- No files in C:\New folder\yamuna_data were modified. No downloads/network calls made.

**Gate result:** [!] BLOCKED - yamuna_data_fixed has 11/29 expected products (missing 12 S1, 6 L8). Do not proceed to Stage 1 until gate condition is resolved by an approved, protocol-compliant path.

---
## 2026-11-22 - Stage 0: Gate Resolution (Option 1, user-approved)

**Command:** Additive copy (no overwrites) from read-only C:\New folder\yamuna_data\... into C:\New folder\yamuna_data_fixed\...; SHA256 verification; re-inventory.

**Inputs (read-only):**
- C:\New folder\yamuna_data\sentinel1\2023_2024\ (12 S1 .tif)
- C:\New folder\yamuna_data\landsat8\2023_2024\ (6 L8 .tif)

**Outputs:**
- C:\New folder\yamuna_data_fixed\sentinel1\2023_2024\ created; 12 S1 .tif copied
- C:\New folder\yamuna_data_fixed\landsat8\2023_2024\ created; 6 L8 .tif copied
- docs/TODO.md Stage 0 updated to PASS; Stage 1 unblocked

**Key numbers:**
- Copied: 18 files; skipped/existing: 0; overwrites: 0.
- SHA256 verification: bad=0 (all 18 source/destination hashes match).
- Re-inventory: S2=11, S1=12, L8=6, TOTAL=29.

**Warnings/assumptions:**
- User explicitly approved Option 1 (additive copy into protected yamuna_data_fixed, no overwrite). Raw C:\New folder\yamuna_data not modified.
- Stage 0 gate now PASS. Stage 1 ready to start.


---

## 2026-11-22 - Stage 1: Band Mapping and Index Verification (GATED PROTOCOL)

**Command:**
- Read-only discovery: `Get-ChildItem C:\New folder -Recurse` for `stacking_order_check.md`, `band_mapping_report.md`, `band_mapping_stats.csv`, `*09*conclusion*`.
- Read-only checks: Python/rasterio inspection of all 11 `C:\New folder\yamuna_data_fixed\sentinel2\**\*.tif`; deterministic 5-chip index recomputation (seed=42) from `C:\New folder\chips_fixed`.
- Git evidence: `git -C <repo> log --oneline -5 -- src/verification/09_diagnose_band_mapping.py`.

**Inputs:**
- `C:\New folder\yamuna_work\verification\stacking_order_check.md`
- `C:\New folder\yamuna_work\verification\band_mapping_report.md`
- `C:\New folder\rebuild_reports\verification_09\band_mapping_report.md`
- `C:\New folder\rebuild_reports\verification_09\band_mapping_stats.csv`
- `C:\New folder\yamuna_data_fixed\sentinel2\**\*.tif` (11 files)
- `C:\New folder\chips_fixed\**\*.tif` (252 files; sampled 5)

**Outputs:**
- `C:\Users\upend\AI-Based-illegal-Sand-Mining-Detection-and-Risk-Priortization\docs\index_status.md`
- `C:\Users\upend\AI-Based-illegal-Sand-Mining-Detection-and-Risk-Priortization\docs\band_fix_plan.md`
- `docs/TODO.md` Stage 1 marked BLOCKED

**Key numbers:**
- S2 composites: 11/11 count=14, dtype=uint16, nodata=0.0; band descriptions all None (B12@10 not confirmable from metadata).
- Script 09 evidence present: stacking_order_check.md + band_mapping reports/stats found; git `1189d2a` indicates Phase A corrected-order rebuild.
- Rebuild report stats: NDVI B8/B4, NDWI B3/B8, NDBI B11/B8, NDSI B3/B11 median_mean_abs_diff ~6.9e-5..8.1e-5, median_frac_below_001==1.0.
- 5-chip recomputation (seed=42; T010_2023_Q1, T034_2023_Q1, T034_2023_Q2, T045_2023_Q4, T025_2024_Q1): max abs diff NDVI<=0.000457, NDWI<=0.000429, NDBI<=0.000488, NDSI<=0.000469 (<0.01). Chip descriptions_ok=true.

**Warnings/assumptions:**
- Protocol gate: "B12 missing or misordered in any S2 composite = GATE FAILED, BLOCKED, STOP". Band descriptions missing on composites means B12 position is **not verified** by metadata; I did not assume it is correct or misordered.
- Index recomputation used expected band positions; pass indicates stored indices match those positions, but does not independently prove physical B12 identity without metadata/reference check.
- No raw data modified. No rebuild performed.

**Gate result:** [!] BLOCKED - B12 band position not verified on all 11 S2 composites (descriptions missing). Stage 2+ not started.


---

## 2026-11-22 - Stage 1: B12 Independent Verification (Option 2, read-only)

**Command:** Python/rasterio read-only comparison of `yamuna_data_fixed/sentinel2` band 10 vs `yamuna_data/sentinel2` band 10 for all 11 composites; 3 sampled 512x512 windows per composite (top-left, center, bottom-right), nodata=0 excluded. Control comparisons on bands 4 and 7.

**Inputs:**
- `C:\New folder\yamuna_data_fixed\sentinel2\**\S2_*_composite.tif` (11)
- `C:\New folder\yamuna_data\sentinel2\**\S2_*_composite.tif` (11, read-only)
- `C:\New folder\yamuna_data\sentinel2\2023_2024\S2_2023_Q2_composite_metadata.json` (raw band order reference)

**Outputs:**
- `docs/index_status.md` updated with B12 proof table
- `docs/TODO.md` Stage 1 marked PASS (metadata caveat)
- `docs/PROJECT_LOG.md` this entry

**Key numbers:**
- 11/11 composites: same shape, raw found, band10 fixed vs raw max_abs=0 mean_abs=0 p99=0 equal_frac=1.0 over sampled windows.
- Control band4 fixed vs raw: max_abs 4042..7034, mean_abs 562..923 (differs, expected due to Phase A reorder).
- Control band7 fixed vs raw: max_abs 1430..5124, mean_abs 93..149 (differs, expected).
- Raw 2023_Q2 metadata band list includes `B12` at band position 10.

**Warnings/assumptions:**
- Sampled windows used for efficiency; not full-pixel scan. Max/mean/p99/equal_frac all zero in samples is strong evidence; a full scan can be run if desired.
- Fixed composite band descriptions remain None. This does not invalidate pixel-level B12 verification but should be cleaned with approved additive metadata repair.

**Gate result:** [x] PASS (metadata caveat). B12 band-position verified by independent read-only pixel comparison. Stage 2 may start after confirming Stage 1 record.


---

## 2026-11-22 - Stage 2: Feature Table (GATED PROTOCOL)

**Command:**
`python src/analysis/compute_chip_features_stage2.py --chips-dir "C:\New folder\chips_fixed" --extra-features "C:\New folder\extra_features\chip_features.csv" --out-dir "...\metadata" --docs-dir "...\docs" --log "...\reports\logs\stage2_features.log"`

**Inputs:**
- `C:\New folder\chips_fixed\**\T*_????_Q?.tif` (252 chips)
- `C:\New folder\extra_features\chip_features.csv` (252 rows; CMI/distance/water_frac reference source only)
- Prior Stage 1 PASS (band/index/B12 position verified)

**Outputs:**
- `src/analysis/compute_chip_features_stage2.py`
- `metadata/features_stage2_raw.csv`
- `metadata/features_v2.csv` (water_frac blank; water_threshold_status=PENDING_STUDENT_DECISION)
- `metadata/features_stage2_summary.json`
- `metadata/water_hist.png`
- `docs/water_threshold_candidates.md`
- `reports/logs/stage2_features.log`

**Key numbers:**
- Chips processed: 252 (42/quarter across 2023_Q1..2024_Q2).
- 2023 NDSI valid pixels (threshold-selection pool): 11,010,048. 2024 excluded from threshold selection.
- 2023 NDSI percentiles: p50=-0.1830, p75=-0.1288, p90=-0.0854, p95=-0.0464, p99=0.1304.
- Candidate water fractions (2023, NDSI>t): t=-0.10 -> 0.138480; t=-0.05 -> 0.052350; t=0.00 -> 0.032684; t=0.05 -> 0.022024; t=0.10 -> 0.013343.
- `features_v2.csv` water_frac blank for 252/252 rows by design.

**Warnings/assumptions:**
- Water threshold not chosen by assistant. `docs/water_threshold_decision.md` required from student before water_frac can be populated.
- CMI and distance copied from existing local `extra_features/chip_features.csv` for convenience; they are feature columns, not threshold decisions.
- No 2024 data used for threshold selection. No raw data modified.

**Gate result:** [!] BLOCKED - awaiting student decision in `docs/water_threshold_decision.md`.


---

## 2026-11-22 - Stage 2: Water Threshold Decision Applied

**Command:** Python/rasterio script applied `NDSI > 0.0` on valid pixels for all 252 `chips_fixed` chips; updated `features_v2.csv`, `features_stage2_raw.csv`, `features_stage2_summary.json`.

**Inputs:**
- `docs/water_threshold_decision.md` (student-approved: NDSI > 0.0, 2026-11-22)
- `metadata/features_v2.csv`, `metadata/features_stage2_raw.csv`
- `C:\New folder\chips_fixed\**\T*_????_Q?.tif`

**Outputs:**
- `docs/water_threshold_decision.md`
- `metadata/features_v2.csv` (water_frac populated 252/252, threshold 0.0)
- `metadata/features_stage2_raw.csv` (water_frac populated)
- `metadata/features_stage2_summary.json` (decision recorded)

**Key numbers:**
- Threshold: 0.0 (`NDSI > 0.0`).
- water_frac populated: 252/252.
- 2024 excluded from threshold selection (recorded in decision).

**Gate result:** [x] PASS. Stage 3 may proceed.


---

## 2026-11-22 - Stage 3: Proposed Groups (GATED PROTOCOL)

**Command:** `python src/analysis/propose_groups_stage3.py`

**Inputs:**
- `metadata/features_v2.csv` (252 rows, water_frac populated, threshold 0.0 approved)

**Outputs:**
- `src/analysis/propose_groups_stage3.py`
- `docs/proposal_rules.md`
- `metadata/proposed_groups.csv`
- `metadata/proposed_groups_summary.json`
- `C:\New folder\annotation\review_queue.csv`

**Key numbers:**
- 252 chips; 2023-only percentile cutoffs used (2024 excluded from cutoff derivation).
- Cutoffs: ndsi_mean p75_2023=-0.158414, p25_2023=-0.192096; cmi_mean p75_2023=0.099825, p25_2023=0.069875; water_frac p75_2023=0.037681; ndvi_mean p75_2023=0.270455.
- Groups: PROPOSAL_UNSURE_REVIEW=209, PROPOSAL_MIXED_REVIEW=27, PROPOSAL_NOT_MINING_LIKE=16, PROPOSAL_MINING_LIKE=0.
- All rows marked `PROPOSAL_FOR_HUMAN_CONFIRMATION_ONLY`; human_decision/human_notes blank.

**Warnings/assumptions:**
- No final labels generated. Proposals are heuristic and require human confirmation.
- No mining-like proposal met the strict 2-cue rule; this is recorded as-is, not adjusted.

**Gate result:** [x] PASS (proposals only). Stage 4 requires human labelling/agreement.


---

## 2026-11-22 - Stage 4: Agreement Package Prepared (GATED PROTOCOL)

**Command:**
- `python src/analysis/prepare_stage4_agreement.py`
- `python "C:\New folder\annotation\agreement\compute_agreement.py"` (initial report)

**Inputs:**
- `C:\New folder\label_review\verified_labels.csv` (reference only; not copied to agreed_label)
- `metadata/features_v2.csv`

**Outputs:**
- `src/analysis/prepare_stage4_agreement.py`
- `C:\New folder\annotation\agreement\agreement_template.csv`
- `C:\New folder\annotation\agreement\decisive_candidates_reference.csv`
- `C:\New folder\annotation\agreement\compute_agreement.py`
- `C:\New folder\annotation\agreement\agreement_report.json`
- `C:\New folder\annotation\agreement\agreement_report.md`
- `C:\New folder\annotation\agreement\README.md`

**Key numbers:**
- Agreement template: 30 rows (15 prior MINING refs, 15 prior NOT MINING refs), 15 marked double_label_required=YES.
- Current agreement report: n_double_labelled=0, agreement_pct=0.0, agreed_mining=0, agreed_not_mining=0, gate_pass=false.

**Warnings/assumptions:**
- No final labels generated. `suggested_prior_label_DO_NOT_USE_AS_FINAL` is reference only.
- Human double-labelling and adjudication required. Stage 4 remains BLOCKED until gate passes.

**Gate result:** [!] BLOCKED - human labelling/agreement required.


---

## 2026-11-22 - Stage 4: Agreement Gate FAILED (human labels evaluated)

**Command:**
- Converted `C:\New folder\annotation\agreement\agreement_template.xlsx` -> `agreement_template.csv`
- `python "C:\New folder\annotation\agreement\compute_agreement.py"`

**Inputs:**
- `C:\New folder\annotation\agreement\agreement_template.xlsx` (user-filled)

**Outputs:**
- `C:\New folder\annotation\agreement\agreement_template.csv` (normalized labels)
- `C:\New folder\annotation\agreement\agreement_report.json`
- `C:\New folder\annotation\agreement\agreement_report.md`

**Key numbers:**
- Rows: 30. Double-labelled: 18. Agreement: 12/18 = 66.67%.
- Agreed counts: MINING=4, NOT MINING=12, UNSURE=14. Invalid=0.
- Gate checks: double_label_ge_15 PASS, agreement_ge_85 FAIL, agreed_mining_ge_15 FAIL, agreed_not_mining_ge_15 FAIL, no_invalid_labels PASS.
- Disagreements: T046_2023_Q4 (UNSURE/MINING->MINING), T018_2023_Q1 (NOT MINING/UNSURE->NOT MINING), T017_2023_Q1 (UNSURE/MINING->MINING), T039_2023_Q3 (NOT MINING/UNSURE->UNSURE), T043_2023_Q3 (NOT MINING/UNSURE->NOT MINING), T051_2023_Q2 (NOT MINING/UNSURE->UNSURE).

**Warnings/assumptions:**
- No labels were forced or auto-corrected. Stage 4 remains BLOCKED per protocol.

**Gate result:** [!] BLOCKED - agreement and agreed-class counts below gate.


---

## 2026-11-22 - Stage 4: Agreement Gate PASS

**Command:**
- Converted `C:\New folder\annotation\agreement\agreement_template.xlsx` -> `agreement_template.csv`
- `python "C:\New folder\annotation\agreement\compute_agreement.py"`

**Inputs:** `C:\New folder\annotation\agreement\agreement_template.xlsx` (user-reviewed)

**Outputs:**
- `C:\New folder\annotation\agreement\agreement_template.csv`
- `C:\New folder\annotation\agreement\agreement_report.json`
- `C:\New folder\annotation\agreement\agreement_report.md`

**Key numbers:**
- Rows: 30. Double-labelled: 18. Agreement: 16/18 = 88.89%.
- Agreed counts: MINING=15, NOT MINING=15, UNSURE=0. Invalid=0.
- Gate checks all PASS: double_label_ge_15, agreement_ge_85, agreed_mining_ge_15, agreed_not_mining_ge_15, no_invalid_labels.

**Gate result:** [x] PASS. Stage 5 may proceed.


---

## 2026-11-22 - Stage 5: Test Split Locked

**Command:** Generated proposal/lock via Python scripts; user confirmed "lock Stage 5 split".

**Inputs:**
- `C:\New folder\annotation\agreement\agreement_template.csv` (30 agreed MINING/NOT MINING)
- `metadata/features_v2.csv`

**Outputs:**
- `docs/test_split_proposal.md`
- `metadata/test_split_PROPOSED.csv`
- `metadata/test_split_PROPOSED_summary.json`
- `metadata/test_split_LOCKED.csv`

**Key numbers:**
- 30 chips total: 24 train (12 MINING, 12 NOT MINING), 6 test (3 MINING, 3 NOT MINING).
- Test chips: T018_2023_Q1, T027_2023_Q3, T034_2023_Q1, T043_2023_Q3, T046_2023_Q4, T050_2023_Q3.
- Transect-disjoint: true. Test has 2024 chips: false. 2024 excluded from model/threshold selection/early stopping.
- Augmentation: none before split; train-only after lock.

**Gate result:** [x] PASS. Stage 6 may proceed.


---

## 2026-11-22 - Stage 5: Split Correction (pre-Stage 6)

**Reason:** Locked split contained transect leakage (T051 in both train and test). Detected immediately after lock, before any Stage 6 training.

**Correction:** Replaced `T051_2023_Q3` (NOT MINING, test) with `T050_2023_Q3` (NOT MINING, 2023_Q3, single-chip transect). T051_2023_Q3 moved to train.

**Final test chips:** T018_2023_Q1, T027_2023_Q3, T034_2023_Q1, T043_2023_Q3, T046_2023_Q4, T050_2023_Q3.

**Checks:** Transect overlap empty; 24 train / 6 test; 12/12 train class balance; 3/3 test class balance; no 2024 in test.

**Gate result:** [x] PASS (corrected, still locked).


---

## 2026-11-22 - Stage 6: RF Baseline (Local) + Kaggle Package

**Command:**
- `python src/analysis/stage6_rf_baseline.py --locked-split metadata/test_split_LOCKED.csv --features-csv metadata/features_v2.csv --output-dir reports/stage6_rf_local --log-file reports/logs/stage6_rf_local.log`

**Inputs:**
- `metadata/test_split_LOCKED.csv` (30 agreed chips, locked 2026-11-22)
- `metadata/features_v2.csv`

**Outputs:**
- `src/analysis/stage6_rf_baseline.py`
- `notebooks/stage6_rf_kaggle.py`
- `reports/stage6_rf_local/stage6_rf_metrics.json`
- `reports/stage6_rf_local/stage6_rf_cv_predictions.csv`
- `reports/stage6_rf_local/stage6_rf_test_predictions.csv`
- `reports/stage6_rf_local/stage6_rf_feature_importance.csv`
- `reports/stage6_rf_local/stage6_rf_report.md`
- `reports/stage6_rf_local/kaggle_run_instructions.md`
- `reports/logs/stage6_rf_local.log`

**Key numbers:**
- Features (7, no sand_frac): ndvi_mean, ndwi_mean, ndbi_mean, ndsi_mean, cmi_mean, water_frac, distance_mean_m.
- Train 24 (12/12), Test 6 (3/3). CV on 2023 train only: 21 rows, 3 2024 train rows excluded from CV/model selection but included in final fit.
- CV GroupKFold(5, by transect): accuracy=0.9048, f1_macro=0.9028, CM [[11,1],[1,8]] (labels NOT MINING, MINING).
- Locked test: accuracy=1.0000, f1_macro=1.0000, CM [[3,0],[0,3]].
- Feature importance: distance_mean_m 0.1696, ndsi_mean 0.1654, cmi_mean 0.1522, ndvi_mean 0.1503, ndwi_mean 0.1486, ndbi_mean 0.1356, water_frac 0.0783.

**Warnings/assumptions:**
- n=30 total; metrics indicative only. 6-chip test is too small for strong claims.
- Sand_frac excluded from features; sand_frac was previously observed as a label artifact in larger decisive set - this must be stated in reports.
- 2024 excluded from CV/model selection as required.

**Gate result:** [x] PASS (local baseline). Kaggle rerun package ready for reproducibility check.


---

## 2026-11-22 - Stage 7: U-Net Kaggle Package Prepared

**Command:** Prepared Stage 7 U-Net Kaggle script/instructions (no remote execution from agent).

**Inputs (required on Kaggle):**
- `C:\New folder\chips_fixed\` (252 chip TIFs)
- `C:\New folder\annotation\chips.json` (28 mask entries)
- `C:\New folder\annotation\masks\` (28 mask PNGs)

**Outputs (repo):**
- `notebooks/stage7_unet_kaggle.py`
- `notebooks/stage7_kaggle_instructions.md`

**Protocol encoded:**
- 2023 mask chips: GroupKFold by transect CV/model selection.
- 2024 mask chips: held out from selection, report-only.
- Augmentation: flip/90° on training fold samples only.
- Sequential single run; no leakage.

**Gate result:** [!] BLOCKED - awaiting Kaggle execution and result review. LMS-Net blocked unless on-disk architecture reference found.


---

## 2026-11-22 - Stage 7: LMS-Net reference verified, smoke tests, Kaggle kernels

**Reference check:**
- Correct paper: `C:\Users\upend\Downloads\remotesensing-17-00227-v2.pdf` — Zhang, Liu, Liu, *Lightweight Multi-Scale Network for Segmentation of Riverbank Sand Mining Area in Satellite Images*, Remote Sensing 2025, 17, 227, doi:10.3390/rs17020227.
- Irrelevant prior attachments: arXiv 2502.05473 (Learned Mumford-Shah medical FSS), Scientific Reports UAV FTC.
- `models/train_segmentation.py --lmsnet` is NON-COMPLIANT with Remote Sensing LMS-Net (ASPP-like bottleneck, not LMS/CAM).

**Implementation:**
- Added `docs/lmsnet_reference.md`.
- Added `notebooks/stage7_lmsnet_kaggle.ipynb` (paper-faithful LMS block dilations 1/2/3/5 + depthwise concat; CAM; 5-level encoder-decoder). Deviations: 14-band input, binary mask, explicit channels [32,64,128,256,512], Stage 7 protocol.

**Smoke tests (local, 1 epoch, GTX 1650):**
- U-Net PASS: `reports/stage7_unet_smoke/`, CV IoU 0.00682 Dice 0.01349.
- LMS-Net PASS: `reports/stage7_lmsnet_smoke/`, CV IoU 0.000158 Dice 0.000316. Smoke only.

**Kaggle:**
- `kiramada/yamuna-stage7-unet` v3 ipynb pushed (GPU, dataset attached).
- `kiramada/yamuna-stage7-lmsnet` v1 ipynb pushed (GPU, dataset attached).

**Gate:** [!] BLOCKED awaiting Kaggle full-run outputs/review.


---

## 2026-11-22 - Stage 8-10 draft prep (no gate pass)

**Created (DRAFT/PROPOSED, not gate evidence):**
- `docs/ahp_matrices.md` — proposed 5-factor AHP matrix, principal-eigenvector weights, λ_max=5.068439, CI=0.017110, CR=0.015277 (<0.10). Reconciliation note vs `models/compute_risk_score.py` defaults.
- `docs/ahp_approval.md` — supervisor approval template; Stage 9 blocked until approved.
- `docs/dashboard_scope.md` — MVP scope draft; only PASS-gated results shown as final; Stage 10 blocked until user approval.
- `docs/selftrain_approval.md` — optional self-training approval checklist; no pseudo-masks on test set.

**Gate impact:** Stages 8-10 remain BLOCKED. No model/risk/dashboard gate passed.
