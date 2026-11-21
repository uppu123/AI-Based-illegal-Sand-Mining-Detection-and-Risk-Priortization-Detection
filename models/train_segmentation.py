# -*- coding: utf-8 -*-
"""Train U-Net / LMS-Net-style segmentation on the 16 human pixel masks.

Hard gate: all 16 masks must exist before any training starts. Metrics are
computed only on held-out transects (3-fold GroupKFold by transect) and are
written to JSON. Nothing in this script fabricates a result.
"""
import json
import random
import sys
from datetime import datetime
from pathlib import Path

import numpy as np
from PIL import Image
import rasterio
import torch
import torch.nn as nn
import torch.nn.functional as F
from sklearn.model_selection import GroupKFold
from torch.utils.data import DataLoader, TensorDataset

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import config.project_config as cfg  # noqa: E402

# --------------------------------------------------------------------------- model


class UNet(nn.Module):
    def __init__(self, in_ch=14, base=16, multiscale=False):
        super().__init__()
        self.multiscale = multiscale

        def block(i, o):
            return nn.Sequential(
                nn.Conv2d(i, o, 3, padding=1, bias=False),
                nn.BatchNorm2d(o), nn.ReLU(inplace=True),
                nn.Conv2d(o, o, 3, padding=1, bias=False),
                nn.BatchNorm2d(o), nn.ReLU(inplace=True),
            )

        self.e1, self.e2, self.e3, self.e4 = (
            block(in_ch, base), block(base, 2 * base),
            block(2 * base, 4 * base), block(4 * base, 8 * base),
        )
        self.bottleneck = block(8 * base, 16 * base)
        if multiscale:
            # LMS-Net-inspired multi-scale context at the bottleneck.
            self.aspp = nn.ModuleList([
                nn.Sequential(
                    nn.Conv2d(16 * base, 4 * base, 3, padding=d, dilation=d, bias=False),
                    nn.BatchNorm2d(4 * base), nn.ReLU(inplace=True),
                ) for d in (1, 2, 4)
            ])
            self.aspp_proj = nn.Conv2d(16 * base + 12 * base, 16 * base, 1)
        self.pool = nn.MaxPool2d(2)

        def up(i, o):
            return nn.Sequential(
                nn.Conv2d(i, o, 3, padding=1, bias=False),
                nn.BatchNorm2d(o), nn.ReLU(inplace=True),
                nn.Conv2d(o, o, 3, padding=1, bias=False),
                nn.BatchNorm2d(o), nn.ReLU(inplace=True),
            )

        self.d4 = up(16 * base + 8 * base, 8 * base)
        self.d3 = up(8 * base + 4 * base, 4 * base)
        self.d2 = up(4 * base + 2 * base, 2 * base)
        self.d1 = up(2 * base + base, base)
        self.out = nn.Conv2d(base, 1, 1)

    def forward(self, x):
        e1 = self.e1(x)
        e2 = self.e2(self.pool(e1))
        e3 = self.e3(self.pool(e2))
        e4 = self.e4(self.pool(e3))
        z = self.bottleneck(self.pool(e4))
        if self.multiscale:
            z = torch.cat([z] + [branch(z) for branch in self.aspp], dim=1)
            z = self.aspp_proj(z)
        z = self.d4(torch.cat([F.interpolate(z, size=e4.shape[2:], mode="bilinear",
                                             align_corners=False), e4], dim=1))
        z = self.d3(torch.cat([F.interpolate(z, size=e3.shape[2:], mode="bilinear",
                                             align_corners=False), e3], dim=1))
        z = self.d2(torch.cat([F.interpolate(z, size=e2.shape[2:], mode="bilinear",
                                             align_corners=False), e2], dim=1))
        z = self.d1(torch.cat([F.interpolate(z, size=e1.shape[2:], mode="bilinear",
                                             align_corners=False), e1], dim=1))
        return self.out(z)


def bce_dice(logits, target):
    bce = F.binary_cross_entropy_with_logits(logits, target)
    prob = torch.sigmoid(logits)
    inter = (prob * target).sum(dim=(2, 3))
    dice = (2 * inter + 1) / (prob.sum(dim=(2, 3)) + target.sum(dim=(2, 3)) + 1)
    return bce + (1 - dice).mean()


# --------------------------------------------------------------------------- data


def load_chip(entry):
    path = cfg.CHIPS_FIXED_DIR / entry["quarter"] / (entry["chip_id"] + ".tif")
    with rasterio.open(path) as ds:
        arr = ds.read().astype(np.float32)
    arr[:10] /= 10000.0
    arr[10:] = arr[10:] / 5000.0 - 1.0
    return arr


def load_mask(entry):
    path = cfg.ANNOTATION_MASKS_DIR / (entry["chip_id"] + "_mask.png")
    with Image.open(path) as im:
        m = np.asarray(im.convert("L"), dtype=np.float32)
    if m.shape != (256, 256):
        m = np.asarray(Image.fromarray(m.astype(np.uint8)).resize((256, 256)), dtype=np.float32)
    return (m > 127).astype(np.float32)


def augment(x, y):
    """Return 8 rotated/flipped variants of one chip-mask pair."""
    out = []
    for k in range(4):
        xr, yr = np.rot90(x, k, axes=(1, 2)), np.rot90(y, k)
        out.append((xr.copy(), yr.copy()))
        out.append((np.flip(xr, axis=2).copy(), np.flip(yr, axis=1).copy()))
    return out


def metrics(y_true, y_prob, threshold=0.5):
    pred = y_prob >= threshold
    truth = y_true.astype(bool)
    tp = int((pred & truth).sum())
    fp = int((pred & ~truth).sum())
    fn = int((~pred & truth).sum())
    tn = int((~pred & ~truth).sum())
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    iou = tp / (tp + fp + fn) if tp + fp + fn else 0.0
    dice = 2 * tp / (2 * tp + fp + fn) if 2 * tp + fp + fn else 0.0
    return dict(tp=tp, fp=fp, fn=fn, tn=tn, precision=precision,
                recall=recall, f1=f1, iou=iou, dice=dice,
                positive_fraction=float(truth.mean()))


# --------------------------------------------------------------------------- train


def main():
    arch = "lmsnet" if "--lmsnet" in sys.argv else "unet"
    epochs = int(next((a.split("=")[1] for a in sys.argv if a.startswith("--epochs=")), 40))
    base = int(next((a.split("=")[1] for a in sys.argv if a.startswith("--base=")), 16))
    seed = int(next((a.split("=")[1] for a in sys.argv if a.startswith("--seed=")), 42))
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)

    entries = json.loads(cfg.ANNOTATION_CHIPS_JSON.read_text(encoding="utf-8"))
    masks = {e["chip_id"]: cfg.ANNOTATION_MASKS_DIR / (e["chip_id"] + "_mask.png")
             for e in entries}
    missing = [k for k, p in masks.items() if not p.exists()]
    if missing:
        raise SystemExit(
            "HARD GATE: %d/%d masks saved; missing: %s" %
            (len(masks) - len(missing), len(masks), ", ".join(missing))
        )

    X, Y, G, CHIP = [], [], [], []
    for e in entries:
        x, y = load_chip(e), load_mask(e)
        for xa, ya in augment(x, y):
            X.append(xa)
            Y.append(ya)
            G.append(e["transect_id"])
            CHIP.append(e["chip_id"])
    X = np.stack(X)
    Y = np.stack(Y)[:, None]
    G = np.asarray(G)
    print("dataset:", X.shape, "masks:", len(entries), "groups:", len(set(G)))

    run_dir = cfg.SEGMENTATION_RUNS_DIR / datetime.now().strftime("%Y%m%d_%H%M%S")
    (run_dir / "predictions").mkdir(parents=True, exist_ok=True)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    fold_reports = []
    for fold, (tr, va) in enumerate(GroupKFold(n_splits=3).split(X, Y, G), 1):
        mean = X[tr].mean(axis=(0, 2, 3), keepdims=True)
        std = X[tr].std(axis=(0, 2, 3), keepdims=True) + 1e-6
        xtr = torch.from_numpy(((X[tr] - mean) / std).astype(np.float32))
        ytr = torch.from_numpy(Y[tr].astype(np.float32))
        xva = torch.from_numpy(((X[va] - mean) / std).astype(np.float32))
        yva = torch.from_numpy(Y[va].astype(np.float32))
        loader = DataLoader(TensorDataset(xtr, ytr), batch_size=4, shuffle=True)

        model = UNet(base=base, multiscale=(arch == "lmsnet")).to(device)
        opt = torch.optim.Adam(model.parameters(), lr=1e-3)
        best_iou, best_state, best_epoch = -1.0, None, -1
        for epoch in range(1, epochs + 1):
            model.train()
            loss_sum = 0.0
            for xb, yb in loader:
                xb, yb = xb.to(device), yb.to(device)
                opt.zero_grad()
                loss = bce_dice(model(xb), yb)
                loss.backward()
                opt.step()
                loss_sum += loss.item() * len(xb)
            model.eval()
            with torch.no_grad():
                p = torch.sigmoid(model(xva.to(device))).cpu().numpy()
            m = metrics(Y[va][:, 0], p)
            if m["iou"] > best_iou:
                best_iou, best_epoch = m["iou"], epoch
                best_state = {k: v.cpu().clone() for k, v in model.state_dict().items()}
            if epoch % 10 == 0 or epoch == 1:
                print("fold %d epoch %2d loss %.4f val IoU %.4f" %
                      (fold, epoch, loss_sum / len(xtr), m["iou"]))

        model.load_state_dict(best_state)
        model.eval()
        with torch.no_grad():
            prob = torch.sigmoid(model(xva.to(device))).cpu().numpy()
        m = metrics(Y[va][:, 0], prob)
        m.update(fold=fold, best_epoch=best_epoch,
                 val_chips=sorted(set(np.asarray(CHIP)[va].tolist())))
        fold_reports.append(m)
        torch.save(dict(state=best_state, arch=arch, base=base,
                        mean=mean, std=std, best_epoch=best_epoch),
                   run_dir / ("fold_%d.pt" % fold))
        # One qualitative prediction per held-out chip (first augmentation only).
        for i, idx in enumerate(va[::8][:4]):
            img = (np.clip(prob[i, 0], 0, 1) * 255).astype(np.uint8)
            Image.fromarray(img).save(
                run_dir / "predictions" / ("fold%d_%s.png" % (fold, CHIP[idx])))
        print("fold", fold, "IoU %.4f Dice %.4f F1 %.4f" %
              (m["iou"], m["dice"], m["f1"]))

    overall = {k: float(np.mean([f[k] for f in fold_reports]))
               for k in ("iou", "dice", "precision", "recall", "f1")}
    overall.update(arch=arch, folds=fold_reports, epochs=epochs, base=base,
                   seed=seed, device=str(device),
                   note="Held-out transects only; no metric claimed before this run.")
    (run_dir / "metrics.json").write_text(json.dumps(overall, indent=2), encoding="utf-8")
    (run_dir / "config.json").write_text(
        json.dumps(dict(run_dir=str(run_dir), arch=arch, base=base), indent=2),
        encoding="utf-8")
    print("RUN:", run_dir)
    print("OVERALL:", json.dumps({k: overall[k] for k in ("iou", "dice", "precision", "recall", "f1")}))


if __name__ == "__main__":
    main()
