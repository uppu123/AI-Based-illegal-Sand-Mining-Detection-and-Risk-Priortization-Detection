# -*- coding: utf-8 -*-
"""Rebuild Sentinel-2 composites from the local SAFE directories.

This is the Phase A repair driver. It NEVER reads from or writes to the
original ``yamuna_data`` tree except for reading the extracted SAFE folders;
all output goes to ``yamuna_data_fixed``.

Usage:
    python src/acquisition/rebuild_composites_from_local.py --dry-run
    python src/acquisition/rebuild_composites_from_local.py
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

# Make the repo root and src/ importable; load central configuration.
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from config import project_config as cfg

from acquisition.extract_yamuna_data import process_sentinel2_products

ANNUAL_YEARS = (2018, 2019, 2020, 2021, 2022)
QUARTERS = ("2023_Q1", "2023_Q2", "2023_Q3", "2023_Q4", "2024_Q1", "2024_Q2")

SAFE_ROOT = cfg.DATA_ROOT / "downloaded_scenes" / "sentinel2" / "_extract"
OUTPUT_ROOT = cfg.WORKSPACE_ROOT / "yamuna_data_fixed" / "sentinel2"
REPORT_DIR = cfg.WORKSPACE_ROOT / "rebuild_reports"

DATE_RE = re.compile(r"_(20\d{2})(\d{2})(\d{2})T")


def discover_safe_dirs() -> list[Path]:
    found = []
    for root, dirs, _files in os.walk(SAFE_ROOT):
        for d in dirs:
            if d.endswith(".SAFE"):
                found.append(Path(root) / d)
    return sorted(found)


def group_scenes(safe_dirs: list[Path]) -> dict[str, list[str]]:
    groups: dict[str, list[str]] = {str(y): [] for y in ANNUAL_YEARS}
    groups.update({q: [] for q in QUARTERS})
    for p in safe_dirs:
        m = DATE_RE.search(p.name)
        if not m:
            continue
        year, month = int(m.group(1)), int(m.group(2))
        if year in ANNUAL_YEARS:
            groups[str(year)].append(str(p))
        elif (year, month) >= (2023, 1) and (year, month) <= (2024, 6):
            groups[f"{year}_Q{(month - 1) // 3 + 1}"].append(str(p))
    return groups


def output_path(label: str) -> Path:
    folder = OUTPUT_ROOT / label if label in {str(y) for y in ANNUAL_YEARS} else OUTPUT_ROOT / "2023_2024"
    return folder / f"S2_{label}_composite.tif"


def main() -> int:
    parser = argparse.ArgumentParser(description="Rebuild S2 composites with the corrected band order")
    parser.add_argument("--dry-run", action="store_true", help="list the plan only")
    parser.add_argument("--only", nargs="*", default=None, help="process only these labels (e.g. 2023_Q2)")
    args = parser.parse_args()

    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger("yamuna_rebuild")
    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter("%(asctime)s  %(message)s", "%H:%M:%S"))
    logger.handlers = [handler]

    safes = discover_safe_dirs()
    groups = group_scenes(safes)
    labels = [str(y) for y in ANNUAL_YEARS] + list(QUARTERS)
    if args.only:
        labels = [l for l in labels if l in args.only]

    print("SAFE_ROOT:", SAFE_ROOT)
    print("OUTPUT_ROOT:", OUTPUT_ROOT)
    print("discovered SAFE dirs:", len(safes))
    for label in labels:
        print("  %-8s %2d scene(s) -> %s" % (label, len(groups.get(label, [])), output_path(label)))

    if args.dry_run:
        print("\nDRY RUN - nothing written.")
        return 0

    started = time.time()
    results = []
    for label in labels:
        paths = groups.get(label, [])
        if not paths:
            print("!! no scenes for", label)
            results.append({"label": label, "status": "NO_SCENES"})
            continue
        dest = output_path(label)
        if dest.exists():
            print("== skip existing:", dest)
            results.append({"label": label, "status": "ALREADY_EXISTS", "path": str(dest)})
            continue
        print("\n>> building", label, "from", len(paths), "scene(s) ...")
        t0 = time.time()
        ok = process_sentinel2_products(paths, str(dest), label, logger=logger)
        results.append({
            "label": label,
            "status": "OK" if ok else "FAILED",
            "scenes": len(paths),
            "path": str(dest),
            "seconds": round(time.time() - t0, 1),
            "bytes": dest.stat().st_size if dest.exists() else 0,
        })
        print("   ->", "OK" if ok else "FAILED", "in", round(time.time() - t0, 1), "s")

    report = {
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "safe_root": str(SAFE_ROOT),
        "output_root": str(OUTPUT_ROOT),
        "band_order": cfg.S2_SPECTRAL_BANDS + cfg.S2_INDEX_BANDS,
        "elapsed_seconds": round(time.time() - started, 1),
        "results": results,
    }
    rp = REPORT_DIR / "A3_rebuild_report.json"
    rp.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print("\nreport:", rp)
    print("total seconds:", report["elapsed_seconds"])
    return 0 if all(r["status"] in ("OK", "ALREADY_EXISTS") for r in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
