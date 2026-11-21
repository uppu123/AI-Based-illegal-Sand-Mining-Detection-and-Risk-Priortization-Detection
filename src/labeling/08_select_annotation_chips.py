# -*- coding: utf-8 -*-
"""Select 16 chips for human pixel-mask annotation (Option B).

Choices are spread across quarters and transects so that 3-fold spatial CV
(by transect) is meaningful. Copies truecolour + NDSI previews into the
annotation tool's images/ folder and writes chips.json.

Quotas: 8 MINING, 6 NOT MINING, 2 UNSURE.
"""
from __future__ import annotations

import csv
import json
import shutil
import sys
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
from config import project_config as cfg  # noqa: E402

LABELS = cfg.WORKSPACE_ROOT / "label_review" / "verified_labels.csv"
CHIPS_ROOT = cfg.WORKSPACE_ROOT / "chips_fixed"
OUT = cfg.WORKSPACE_ROOT / "annotation"
IMAGES = OUT / "images"
MASKS = OUT / "masks"

QUARTERS = ("2023_Q1", "2023_Q2", "2023_Q3", "2023_Q4", "2024_Q1", "2024_Q2")
# how many of each label to take from each quarter
QUOTA = {
    "MINING": {"2023_Q1": 2, "2023_Q2": 1, "2023_Q4": 1,
               "2024_Q1": 2, "2024_Q2": 2},
    "NOT MINING": {"2023_Q1": 1, "2023_Q2": 1, "2023_Q3": 2,
                   "2023_Q4": 1, "2024_Q1": 1},
    "UNSURE": {"2023_Q2": 1, "2024_Q2": 1},
}


def main() -> int:
    IMAGES.mkdir(parents=True, exist_ok=True)
    MASKS.mkdir(parents=True, exist_ok=True)

    with LABELS.open(newline="", encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))

    by_q_lab = defaultdict(list)
    for r in rows:
        by_q_lab[(r["quarter"], r["reviewer_final_label"])].append(r)

    chosen = []
    used_transects = set()
    for lab, qmap in QUOTA.items():
        for q, n in qmap.items():
            pool = sorted(by_q_lab.get((q, lab), []),
                          key=lambda r: float(r["sand_frac"]))
            # prefer median-magnitude examples, unique transects
            pool = [r for r in pool if r["transect_id"] not in used_transects]
            if len(pool) < n:
                print(f"WARN {lab}/{q}: only {len(pool)} free chips, need {n}")
            picked = []
            if pool:
                step = max(1, len(pool) // n)
                for i in range(0, len(pool), step):
                    if len(picked) >= n:
                        break
                    r = pool[i]
                    if r["transect_id"] in used_transects:
                        continue
                    picked.append(r)
                    used_transects.add(r["transect_id"])
            chosen.extend(picked)

    # copy previews
    entries = []
    for r in chosen:
        q = r["quarter"]
        cid = r["chip_id"]
        for suffix in ("truecolour", "NDSI"):
            src = CHIPS_ROOT / q / "previews" / f"{cid}_{suffix}.png"
            if src.exists():
                shutil.copy2(src, IMAGES / f"{cid}_{suffix}.png")
            else:
                print("MISSING preview:", src)
        entries.append({
            "chip_id": cid,
            "quarter": q,
            "transect_id": r["transect_id"],
            "label_hint": r["reviewer_final_label"],
            "sand_frac": float(r["sand_frac"]),
        })

    (OUT / "chips.json").write_text(
        json.dumps(entries, indent=2), encoding="utf-8")
    print(f"selected {len(entries)} chips, unique transects: {len(used_transects)}")
    for e in entries:
        print("  ", e["chip_id"], e["label_hint"], "sand=%.3f" % e["sand_frac"])
    print("images:", IMAGES)
    print("masks :", MASKS)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
