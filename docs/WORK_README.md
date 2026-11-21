# Yamuna Sand Mining Detection - Project Workspace

## Overview
This workspace contains scripts and outputs for preparing a satellite dataset for sand mining detection on the Yamuna River (Palla to Jaitpur, Delhi). The source data is in `C:\New folder\yamuna_data\` (read-only).

## Directory Structure
```
yamuna_work/
├── scripts/           # Python scripts (01-05)
├── logs/              # Script execution logs
├── metadata/          # CSV outputs, inventory checks
├── centerline/        # Centerline GeoJSON and validation outputs
├── transects/         # Transect GeoJSONs, CSV, map
├── chips/
│   └── 2023_Q2/
│       ├── *.tif      # Extracted 256x256 chips
│       └── previews/  # True-colour, NDSI, contact sheet
├── labeling/          # Labeling preparation outputs
│   ├── images/        # KEEP chip GeoTIFFs
│   ├── previews/      # KEEP chip true-colour PNGs
│   ├── label_guidelines.md
│   ├── label_manifest.csv
│   └── agreement_log.csv
└── docs/
    ├── TODO.md
    ├── PROJECT_LOG.md
    └── README.md
```

## Scripts (Run in Order)

### 01_verify_inventory.py
**Purpose:** Verify all 29 expected GeoTIFF files exist and meet specifications.

**Command:**
```bash
python scripts/01_verify_inventory.py
```

**Outputs:**
- `metadata/inventory_check.csv` - Detailed check results per file
- Console summary: PASS/FAIL with counts

**Expected Input Files (29 total):**
- `sentinel2/S2_2018_composite.tif` ... `S2_2022_composite.tif` (5 annual)
- `sentinel2/S2_2023_Q1_composite.tif` ... `S2_2024_Q2_composite.tif` (6 quarterly)
- `sentinel1/2023_2024/S1_2023_Q1_VV.tif` ... `S1_2024_Q2_VH.tif` (12)
- `landsat8/2023_2024/L8_2023_Q1.tif` ... `L8_2024_Q2.tif` (6)

---

### 02_validate_centerline.py
**Purpose:** Validate the digitized Yamuna centerline GeoJSON.

**Prerequisite:** User must create `centerline/yamuna_centerline.geojson` in QGIS first.

**Command:**
```bash
python scripts/02_validate_centerline.py
```

**Outputs:**
- `centerline/centerline_validation.txt` - All checks with values and status
- `centerline/centerline_check.png` - Visual verification map
- `centerline/yamuna_centerline_oriented.geojson` (if reversal needed)

**User Action Required:** Open `centerline_check.png`, confirm line follows river, then continue.

---

### 03_make_transects.py
**Purpose:** Generate perpendicular transects every 1 km along the centerline.

**Command:**
```bash
python scripts/03_make_transects.py
```

**Outputs:**
- `transects/transect_points.geojson` - Points with chainage, bearing
- `transects/transect_lines.geojson` - 3 km perpendicular lines
- `transects/transect_table.csv` - Tabular summary
- `transects/transect_map.png` - Visualization

---

### 04_extract_chips.py
**Purpose:** Extract 256×256 Sentinel-2 chips at each transect point for 2023_Q2.

**Command:**
```bash
python scripts/04_extract_chips.py
```

**Outputs:**
- `chips/2023_Q2/<transect_id>_2023Q2.tif` - 14-band chips
- `chips/2023_Q2/previews/<transect_id>_truecolour.png`
- `chips/2023_Q2/previews/<transect_id>_NDSI.png`
- `chips/2023_Q2/previews/contact_sheet.png`
- `metadata/chips_2023Q2.csv` - Chip metadata
- `metadata/skipped_transects.csv` - Skipped transects with reasons

---

### 05_prepare_labeling.py
**Purpose:** Prepare labeling set from reviewer-approved chips.

**Prerequisite:** User must complete `metadata/chip_review.csv` with decisions.

**Command:**
```bash
python scripts/05_prepare_labeling.py
```

**Outputs:**
- `labeling/images/` - KEEP chip GeoTIFFs
- `labeling/previews/` - KEEP chip true-colour PNGs
- `labeling/label_guidelines.md` - Labeling instructions
- `labeling/label_manifest.csv` - Manifest with empty label columns
- `labeling/agreement_log.csv` - Agreement tracking template

---

## Data Source (Read-Only)
```
C:\New folder\yamuna_data\
├── sentinel2\           # 11 files, 14 bands each
├── sentinel1\2023_2024\ # 12 files, 1 band each
└── landsat8\2023_2024\  # 6 files, 3 bands each
```

## Key Parameters
- **AOI:** West 77.15, South 28.54, East 77.32, North 28.76 (EPSG:4326)
- **Centerline CRS:** EPSG:4326 (WGS84)
- **Processing CRS:** EPSG:32643 (UTM 43N)
- **Transect spacing:** 1000 m
- **Transect length:** 3000 m (1500 m each side)
- **Chip size:** 256 × 256 pixels
- **Chip composite:** S2_2023_Q2_composite.tif (14 bands)

## Requirements
- Python 3.10+
- Libraries: rasterio, numpy, pandas, geopandas, shapely, pyproj, matplotlib, pillow
- Windows OS (pathlib with raw strings)