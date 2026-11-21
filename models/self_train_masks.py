# -*- coding: utf-8 -*-
"""Apply the trained fold models to all 252 chips and save high-confidence masks.

This is pseudo-labeling, NOT human ground truth. Every output mask is
accompanied by a confidence score and is intended for risk ranking only.
"""
import csv
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image
import rasterio
import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import config.project_config as cfg  # noqa: E402
from train_segmentation import UNet  # noqa: E402


def load_chip(path):
    with rasterio.open(path) as ds:
        arr = ds.read().astype(np.float32)
    arr[:10] /= 10000.0
    arr[10:] = arr[10:] / 5000.0 - 1.0
    return arr


def main():
    if len(sys.argv) < 2:
        raise SystemExit("usage: python models/self_train_masks.py <run_dir> [threshold=0.7]")
    run_dir = Path(sys.argv[1])
    threshold = float(sys.argv[2]) if len(sys.argv) > 2 else 0.7
    cfg_run = json.loads((run_dir / "config.json").read_text(encoding="utf-8"))
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    folds = []
    for p in sorted(run_dir.glob("fold_*.pt")):
        ck = torch.load(p, map_location=device, weights_only=False)
        model = UNet(base=ck["base"], multiscale=(ck["arch"] == "lmsnet")).to(device)
        model.load_state_dict(ck["state"])
        model.eval()
        folds.append((model, ck["mean"], ck["std"]))
    if not folds:
        raise SystemExit("No fold_*.pt checkpoints in " + str(run_dir))

    out_dir = run_dir / "auto_masks"
    out_dir.mkdir(parents=True, exist_ok=True)
    rows = []
    with torch.no_grad():
        for quarter in cfg.STUDY_QUARTERS:
            qdir = cfg.CHIPS_FIXED_DIR / quarter
            paths = sorted(qdir.glob("T*.tif"))
            for p in paths:
                arr = load_chip(p)
                probs = []
                for model, mean, std in folds:
                    x = ((arr - mean) / std).astype(np.float32)[None]
                    pr = torch.sigmoid(model(torch.from_numpy(x).to(device)))
                    probs.append(pr.cpu().numpy()[0, 0])
                prob = np.mean(probs, axis=0)
                mask = (prob >= threshold).astype(np.uint8) * 255
                Image.fromarray(mask).save(out_dir / (p.stem + "_mask.png"))
                rows.append(dict(chip_id=p.stem, quarter=quarter,
                                 positive_fraction=round(float((prob >= threshold).mean()), 4),
                                 mean_confidence=round(float(prob.mean()), 4)))
            print(quarter, len(paths), "chips masked")

    csv_path = run_dir / "auto_mask_summary.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["chip_id", "quarter", "positive_fraction", "mean_confidence"])
        w.writeheader()
        w.writerows(rows)
    (run_dir / "self_train_note.txt").write_text(
        "Pseudo-masks only. Threshold %.2f. Not human ground truth; use for risk ranking only.\n"
        "Architecture: %s\nFolds: %d\nChips: %d\n" %
        (threshold, cfg_run["arch"], len(folds), len(rows)), encoding="utf-8")
    print("masks:", len(rows), "->", out_dir)
    print("summary:", csv_path)


if __name__ == "__main__":
    main()
