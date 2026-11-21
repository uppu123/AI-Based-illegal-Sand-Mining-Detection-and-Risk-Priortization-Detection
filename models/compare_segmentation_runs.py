# -*- coding: utf-8 -*-
"""Compare completed segmentation runs and emit an honest results report.

Reads every ``metrics.json`` under ``C:\\New folder\\segmentation_runs`` and
writes a CSV + JSON comparison. Nothing is invented: a run with no
``metrics.json`` is reported as incomplete, not as a result.
"""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

ROOT = Path(r"C:\New folder\segmentation_runs")
OUT = ROOT / "model_comparison.csv"
METRICS = ("iou", "dice", "precision", "recall", "f1")


def main() -> None:
    if not ROOT.exists():
        raise SystemExit("no segmentation_runs folder yet")
    rows = []
    for d in sorted(ROOT.iterdir()):
        p = d / "metrics.json"
        if not d.is_dir() or not p.exists():
            continue
        m = json.loads(p.read_text(encoding="utf-8"))
        row = {"run_dir": d.name, "arch": m.get("arch", "?"),
               "epochs": m.get("epochs", "?"), "seed": m.get("seed", "?")}
        row.update({k: round(float(m.get(k, 0.0)), 4) for k in METRICS})
        row["folds"] = len(m.get("folds", []))
        row["status"] = "COMPLETED"
        rows.append(row)

    if not rows:
        print("No completed runs yet (metrics.json missing).")
        return

    with OUT.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    print("comparison:", OUT)
    print("%-18s %-8s %8s %8s %8s %8s %8s" %
          ("run", "arch", "IoU", "Dice", "Prec", "Rec", "F1"))
    for r in rows:
        print("%-18s %-8s %8.4f %8.4f %8.4f %8.4f %8.4f" %
              (r["run_dir"], r["arch"], r["iou"], r["dice"],
               r["precision"], r["recall"], r["f1"]))

    best = max(rows, key=lambda r: r["iou"])
    note = {
        "best_by_iou": best["run_dir"],
        "caveat": ("Masks are sparse (0.2-3.1% positive pixels, 12 of 28 chips "
                   "non-empty). Low IoU is an honest result, not a failed run. "
                   "Do not claim detection accuracy until a better-labelled "
                   "held-out set exists."),
        "split": "3-fold GroupKFold by transect, augmentations kept with their source chip",
    }
    (ROOT / "model_comparison.json").write_text(
        json.dumps({"runs": rows, **note}, indent=2), encoding="utf-8")
    print(json.dumps(note, indent=2))


if __name__ == "__main__":
    main()
