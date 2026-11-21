#!/usr/bin/env python3
"""
05_prepare_labeling.py

Prepare labeling set from reviewer-approved chips (decision = KEEP).
Copies chips and previews to labeling/ folder.
Creates label_guidelines.md, label_manifest.csv, agreement_log.csv.
"""

import argparse
import sys
from pathlib import Path
import shutil
import pandas as pd


# ============================================================
# CONFIGURATION
# ============================================================
CHIPS_CSV = Path(r"C:\New folder\yamuna_work\metadata\chips_2023Q2.csv")
REVIEW_CSV = Path(r"C:\New folder\yamuna_work\metadata\chip_review.csv")
CHIPS_DIR = Path(r"C:\New folder\yamuna_work\chips\2023_Q2")
PREVIEWS_DIR = CHIPS_DIR / "previews"

LABELING_DIR = Path(r"C:\New folder\yamuna_work\labeling")
IMAGES_DIR = LABELING_DIR / "images"
PREVIEWS_OUT_DIR = LABELING_DIR / "previews"

GUIDELINES_PATH = LABELING_DIR / "label_guidelines.md"
MANIFEST_PATH = LABELING_DIR / "label_manifest.csv"
AGREEMENT_PATH = LABELING_DIR / "agreement_log.csv"


# ============================================================
# LABEL GUIDELINES CONTENT
# ============================================================
GUIDELINES = """# Labeling Guidelines: Yamuna Sand Mining Detection

## Objective
Label each 256×256 chip (2023 Q2 Sentinel-2) for presence of **sand mining activity**.

## Classes

### MINING
**Evidence of active or recent sand extraction:**
- Exposed bare sand bars / riverbed sediment (bright in NDSI, low NDVI)
- Excavated pits or depressions in river channel
- Spoil heaps / stockpiles along banks
- Equipment: excavators, loaders, trucks (small bright specs)
- Barges / boats on river (elongated shapes in water)
- Tracks / haul roads on riverbed or banks (linear features)
- Sudden river channel widening or braiding

### NOT MINING
**Natural or non-mining features:**
- Open water (dark in true colour, blue in NDSI)
- Vegetated floodplain / agriculture (green in true colour, high NDVI)
- Natural vegetated river banks
- Built-up areas / settlements away from active channel
- Dry sand bars with no equipment/activity (context: seasonal)
- Clouds / haze / artefacts

### UNSURE
**Use when you cannot confidently decide:**
- Ambiguous features (could be natural or mining)
- Heavy haze/cloud obscuring >30% of chip
- Edge chips with partial coverage
- Low contrast / poor visibility
- **Count separately — do not guess.**

---

## Decision Process

1. **Open truecolour PNG** — assess overall scene
2. **Check NDSI PNG** — sand = red, water = blue, vegetation = green
3. **Look for mining signatures** (see MINING above)
4. **Assign label:** MINING / NOT MINING / UNSURE
5. **If unsure → UNSURE** (don't force a decision)

---

## Disagreements and Agreed Rules
*(Filled during agreement check between Reviewer A and Reviewer B)*

| Chip ID | Reviewer A | Reviewer B | Agreed Rule / Resolution |
|---------|------------|------------|--------------------------|
|         |            |            |                          |
|         |            |            |                          |

---

## Approved by Supervisor
**Name:** ________________________  
**Date:** ________________________
"""


def main():
    parser = argparse.ArgumentParser(description="Prepare labeling set from KEEP chips")
    parser.add_argument("--review-csv", default=str(REVIEW_CSV), help="Chip review CSV")
    parser.add_argument("--chips-csv", default=str(CHIPS_CSV), help="Chips metadata CSV")
    args = parser.parse_args()

    review_df = pd.read_csv(args.review_csv)
    chips_df = pd.read_csv(args.chips_csv)

    # Merge on chip_id
    merged = review_df.merge(chips_df, on="chip_id", how="inner")
    print(f"Total reviewed chips: {len(merged)}")

    # Filter KEEP
    keep_df = merged[merged["decision"] == "KEEP"].copy()
    skipped_ids = merged[merged["decision"] != "KEEP"]["chip_id"].tolist()
    
    print(f"KEEP: {len(keep_df)}")
    print(f"Skipped (non-KEEP): {len(skipped_ids)}")
    if skipped_ids:
        print(f"  Skipped IDs: {skipped_ids}")

    # Create output directories
    IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    PREVIEWS_OUT_DIR.mkdir(parents=True, exist_ok=True)

    # Copy files
    print("\nCopying chips and previews...")
    for _, row in keep_df.iterrows():
        chip_id = row["chip_id"]
        
        # Copy GeoTIFF
        src_tif = CHIPS_DIR / f"{chip_id}.tif"
        dst_tif = IMAGES_DIR / f"{chip_id}.tif"
        if src_tif.exists():
            shutil.copy2(src_tif, dst_tif)
        else:
            print(f"  WARNING: Missing chip: {src_tif}")

        # Copy truecolour preview
        src_png = PREVIEWS_DIR / f"{row['transect_id']}_truecolour.png"
        dst_png = PREVIEWS_OUT_DIR / f"{chip_id}_truecolour.png"
        if src_png.exists():
            shutil.copy2(src_png, dst_png)
        else:
            print(f"  WARNING: Missing preview: {src_png}")

    print(f"  Copied {len(keep_df)} chips to {IMAGES_DIR}")
    print(f"  Copied {len(keep_df)} previews to {PREVIEWS_OUT_DIR}")

    # Create label_guidelines.md
    with open(GUIDELINES_PATH, "w", encoding="utf-8") as f:
        f.write(GUIDELINES)
    print(f"Created: {GUIDELINES_PATH}")

    # Create label_manifest.csv
    manifest = keep_df[["chip_id", "transect_id"]].copy()
    manifest["image_path"] = manifest["chip_id"].apply(lambda x: f"images/{x}.tif")
    manifest["preview_path"] = manifest["chip_id"].apply(lambda x: f"previews/{x}_truecolour.png")
    manifest["label_A"] = ""
    manifest["label_B"] = ""
    manifest["final_label"] = ""
    
    manifest.to_csv(MANIFEST_PATH, index=False)
    print(f"Created: {MANIFEST_PATH} ({len(manifest)} rows)")

    # Create agreement_log.csv (empty template)
    agreement = pd.DataFrame({
        "chip_id": manifest["chip_id"],
        "label_A": "",
        "label_B": "",
        "agree": "",
        "note": ""
    })
    agreement.to_csv(AGREEMENT_PATH, index=False)
    print(f"Created: {AGREEMENT_PATH} ({len(agreement)} rows)")

    # Summary
    print(f"\n=== SUMMARY ===")
    print(f"Labeling set prepared: {len(keep_df)} chips")
    print(f"Images: {IMAGES_DIR}")
    print(f"Previews: {PREVIEWS_OUT_DIR}")
    print(f"Guidelines: {GUIDELINES_PATH}")
    print(f"Manifest: {MANIFEST_PATH}")
    print(f"Agreement log: {AGREEMENT_PATH}")

    # Print first 5 manifest rows
    print(f"\nFirst 5 manifest rows:")
    print(manifest.head().to_string(index=False))

    sys.exit(0)


if __name__ == "__main__":
    main()