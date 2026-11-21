# -*- coding: utf-8 -*-
"""Generate cyan water-highlight overlays for the annotation chips.

Water = NDSI/MNDWI > 0.0 after decoding ``raw/5000 - 1``. This is the same
clamped threshold used by ``compute_extra_features.py`` (raw Otsu was negative
on every scene and split the dominant sand class, so it was clamped to 0).

For every chip in ``annotation/chips.json`` this writes:

* ``annotation/images/<chip_id>_water.png`` - RGBA overlay, cyan where water is
  detected, fully transparent elsewhere. Layer it over the truecolour image in
  the browser so the dry-season channel is visible even without blue water.
* ``annotation/water_fractions.csv`` - per-chip water fraction for the UI.

Nothing is written to the protected ``yamuna_data`` / ``chips`` folders.
"""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

import numpy as np
import rasterio
from PIL import Image

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
import config.project_config as cfg  # noqa: E402

ROOT = cfg.WORKSPACE_ROOT / "annotation"
IMAGES = ROOT / "images"
WATER_THRESHOLD = 0.0  # applied threshold from extra_features/scene_features.csv

# Cyan, semi-transparent: visible over sand but does not hide the texture.
OVERLAY_RGBA = (0, 225, 255, 115)


def chip_water_fraction(chip_path: Path) -> tuple[float, np.ndarray]:
    """Return (fraction of NDSI>0 pixels, boolean water mask)."""
    with rasterio.open(chip_path) as ds:
        if ds.count < 14:
            raise ValueError(f"expected 14 bands, got {ds.count}: {chip_path}")
        ndsi = ds.read(14).astype(np.float32) / 5000.0 - 1.0
    water = ndsi > WATER_THRESHOLD
    return float(water.mean()), water


def write_overlay(water: np.ndarray, out_path: Path) -> None:
    rgba = np.zeros((*water.shape, 4), dtype=np.uint8)
    rgba[water] = OVERLAY_RGBA
    Image.fromarray(rgba, mode="RGBA").save(out_path)


def main() -> int:
    entries = json.loads((ROOT / "chips.json").read_text(encoding="utf-8"))
    IMAGES.mkdir(parents=True, exist_ok=True)
    rows = []
    for e in entries:
        chip = cfg.CHIPS_FIXED_DIR / e["quarter"] / (e["chip_id"] + ".tif")
        frac, water = chip_water_fraction(chip)
        write_overlay(water, IMAGES / f"{e['chip_id']}_water.png")
        e["water_frac"] = round(frac, 4)
        rows.append({"chip_id": e["chip_id"], "water_frac": round(frac, 4)})
        print(f"{e['chip_id']:<16} water={frac:.4f}")

    (ROOT / "chips.json").write_text(
        json.dumps(entries, indent=2), encoding="utf-8")
    with (ROOT / "water_fractions.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["chip_id", "water_frac"])
        w.writeheader()
        w.writerows(rows)
    print(f"overlays: {len(rows)} -> {IMAGES}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
