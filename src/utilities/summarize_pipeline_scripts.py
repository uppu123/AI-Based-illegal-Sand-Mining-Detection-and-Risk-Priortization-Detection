# -*- coding: utf-8 -*-
"""For each pipeline script: docstring, CLI options, and declared outputs."""
# --- central configuration (no hard-coded paths in pipeline scripts) ---
from pathlib import Path as _Path
import sys as _sys
_sys.path.insert(0, str(_Path(__file__).resolve().parents[2]))
from config import project_config as _cfg



import io, sys, os, re, ast
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

REPO_ROOT = _Path(__file__).resolve().parents[2]
FILES = [
    REPO_ROOT / "src/acquisition/extract_yamuna_data.py",
    REPO_ROOT / "src/geometry/build_centerline_from_sar.py",
    REPO_ROOT / "src/experiments/legacy_centerline_from_ndwi.py",
    REPO_ROOT / "src/verification/01_verify_data_inventory.py",
    REPO_ROOT / "src/verification/02_validate_river_centerline.py",
    REPO_ROOT / "src/geometry/03_generate_transects.py",
    REPO_ROOT / "src/processing/04_extract_training_chips.py",
    REPO_ROOT / "src/labeling/05_prepare_labeling_set.py",
    REPO_ROOT / "src/processing/extract_chips_all_quarters.py",
    REPO_ROOT / "src/processing/extract_sar_chips.py",
    REPO_ROOT / "src/verification/08_verify_spectral_indices.py",
    REPO_ROOT / "src/verification/09_diagnose_band_mapping.py",
]

for path in FILES:
    if not os.path.exists(path):
        print("!! missing:", path)
        continue
    src = io.open(path, "r", encoding="utf-8", errors="replace").read()
    print("=" * 96)
    print(os.path.basename(path), "|", len(src.splitlines()), "lines")

    try:
        doc = ast.get_docstring(ast.parse(src)) or ""
    except Exception:
        doc = ""
    lines = [l.rstrip() for l in doc.splitlines() if l.strip()]
    print("--- docstring ---")
    for l in lines[:16]:
        print("   ", l[:110])

    args = sorted(set(re.findall(r'add_argument\(\s*"(--[a-z0-9\-]+)"', src)))
    if args:
        print("--- cli ---")
        print("   ", " ".join(args))
