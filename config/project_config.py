# -*- coding: utf-8 -*-
"""Central configuration for the Yamuna sand-mining detection project.

Why this module exists
----------------------
Every pipeline script used to contain a hard-coded path such as
``C:\\New folder\\yamuna_work\\chips``. That made the code impossible to move
or present cleanly. All filesystem locations are defined here once, and each
script imports the names it needs.

Portability
-----------
Set the environment variable ``YAMUNA_WORKSPACE`` to point at the folder that
holds ``yamuna_data`` and ``yamuna_work``. If it is not set, the historical
development location (``C:\\New folder``) is used as a fallback so the existing
data keeps working.

Nothing in this module downloads, writes or modifies data. It only defines
paths and constants.
"""

from __future__ import annotations

import os
from pathlib import Path

# ---------------------------------------------------------------------------
# Workspace root
# ---------------------------------------------------------------------------
WORKSPACE_ROOT = Path(
    os.environ.get("YAMUNA_WORKSPACE", r"C:\New folder")
).expanduser().resolve()

# Repository root (this file is config/project_config.py)
REPO_ROOT = Path(__file__).resolve().parents[1]

# ---------------------------------------------------------------------------
# Raw and derived data locations
# ---------------------------------------------------------------------------
DATA_ROOT = WORKSPACE_ROOT / "yamuna_data"          # 134 GB - NOT in git
WORK_DIR = WORKSPACE_ROOT / "yamuna_work"

S2_DIR = DATA_ROOT / "sentinel2"
S1_DIR = DATA_ROOT / "sentinel1"
L8_DIR = DATA_ROOT / "landsat8"

S2_ANNUAL_DIR = S2_DIR                              # year folders: 2018 .. 2022
S2_QUARTERLY_DIR = S2_DIR / "2023_2024"
S1_QUARTERLY_DIR = S1_DIR / "2023_2024"

METADATA_DIR = WORK_DIR / "metadata"
LOG_DIR = WORK_DIR / "logs"
CENTERLINE_DIR = WORK_DIR / "centerline"
TRANSECT_DIR = WORK_DIR / "transects"
VERIFICATION_DIR = WORK_DIR / "verification"
LABELING_DIR = WORK_DIR / "labeling"
SCRIPTS_DIR = REPO_ROOT / "src"                     # clean source tree

CHIPS_S2_DIR = WORK_DIR / "chips"
CHIPS_S1_DIR = WORK_DIR / "chips_s1"
CHIPS_S2_Q2_DIR = CHIPS_S2_DIR / "2023_Q2"

# ---------------------------------------------------------------------------
# Frequently used individual files
# ---------------------------------------------------------------------------
S2_Q2_COMPOSITE = S2_QUARTERLY_DIR / "S2_2023_Q2_composite.tif"
S1_Q2_VV = S1_QUARTERLY_DIR / "S1_2023_Q2_VV.tif"

CENTERLINE_PATH = CENTERLINE_DIR / "yamuna_centerline.geojson"
CENTERLINE_ORIENTED = CENTERLINE_DIR / "yamuna_centerline_oriented.geojson"
VALIDATION_TXT = CENTERLINE_DIR / "centerline_validation.txt"
VALIDATION_PNG = CENTERLINE_DIR / "centerline_check.png"

TRANSECT_TABLE = TRANSECT_DIR / "transect_table.csv"
TRANSECT_POINTS = TRANSECT_DIR / "transect_points.geojson"

CHIPS_CSV = METADATA_DIR / "chips_2023Q2.csv"
REVIEW_CSV = METADATA_DIR / "chip_review.csv"

PROCESSING_SCRIPT = SCRIPTS_DIR / "acquisition" / "extract_yamuna_data.py"

# ---------------------------------------------------------------------------
# Study area and sensing constants
# ---------------------------------------------------------------------------
AOI_WEST, AOI_SOUTH, AOI_EAST, AOI_NORTH = 77.15, 28.54, 77.32, 28.76
AOI_BOUNDS = (AOI_WEST, AOI_SOUTH, AOI_EAST, AOI_NORTH)   # W, S, E, N (EPSG:4326)

# Correct Sentinel-2 band order (wavelength order). B8 must be at position 7.
# The original build wrote B8 at position 4; see reports/verification/band_mapping_report.md
S2_SPECTRAL_BANDS = [
    "B2", "B3", "B4", "B5", "B6", "B7", "B8", "B8A", "B11", "B12",
]
S2_INDEX_BANDS = ["NDVI", "NDWI", "NDBI", "NDSI"]

CHIP_SIZE_PX = 256            # 256 x 10 m = 2.56 km per chip
TRANSECT_SPACING_M = 1000     # one decision unit per river kilometre
TRANSECT_LENGTH_M = 3000
STUDY_QUARTERS = [
    "2023_Q1", "2023_Q2", "2023_Q3", "2023_Q4", "2024_Q1", "2024_Q2",
]


def ensure_directories() -> None:
    """Create the small output folders that hold reports and metadata.

    Never creates or modifies the large imagery folders themselves.
    """
    for folder in (
        METADATA_DIR, LOG_DIR, CENTERLINE_DIR, TRANSECT_DIR,
        VERIFICATION_DIR, LABELING_DIR,
    ):
        folder.mkdir(parents=True, exist_ok=True)
