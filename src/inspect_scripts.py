# -*- coding: utf-8 -*-
"""For each pipeline script: docstring, CLI options, and declared outputs."""
import io, sys, os, re, ast
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

BASE = r"C:\New folder"
SC = os.path.join(BASE, "yamuna_work", "scripts")
FILES = [
    os.path.join(BASE, "extract_yamuna_data.py"),
    os.path.join(SC, "generate_centerline.py"),
    os.path.join(SC, "generate_centerline_s1.py"),
    os.path.join(SC, "01_verify_inventory.py"),
    os.path.join(SC, "02_validate_centerline.py"),
    os.path.join(SC, "03_make_transects.py"),
    os.path.join(SC, "04_extract_chips.py"),
    os.path.join(SC, "05_prepare_labeling.py"),
    os.path.join(SC, "extract_all_quarters.py"),
    os.path.join(SC, "extract_s1_chips.py"),
    os.path.join(SC, "08_verify_indices.py"),
    os.path.join(SC, "09_band_mapping_check.py"),
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
