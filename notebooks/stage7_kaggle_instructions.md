# Stage 7 U-Net Kaggle Instructions

## What to upload
Create a Kaggle dataset containing:
- `chips_fixed/` — 252 chip TIFs in quarter folders (from `C:\New folder\chips_fixed`)
- `annotation/chips.json` — 28 mask entries (from `C:\New folder\annotation\chips.json`)
- `annotation/masks/` — 28 `*_mask.png` files (from `C:\New folder\annotation\masks`)

Script: `notebooks/stage7_unet_kaggle.py` (copy into Kaggle notebook/script).

## Config env vars (optional)
- `YAMUNA_STAGE7_INPUT=/kaggle/input/<dataset>`
- `YAMUNA_STAGE7_CHIPS=/kaggle/input/<dataset>/chips_fixed`
- `YAMUNA_STAGE7_MASKS=/kaggle/input/<dataset>/annotation/masks`
- `YAMUNA_STAGE7_CHIPS_JSON=/kaggle/input/<dataset>/annotation/chips.json`
- `YAMUNA_STAGE7_OUTPUT=/kaggle/working/stage7_unet`
- `STAGE7_EPOCHS=40`

## Protocol enforced by script
- 2023 mask chips used for GroupKFold (by transect) CV/model selection.
- 2024 mask chips held out from selection; reported separately as `heldout_2024_summary_report_only`.
- Augmentation: flip/90° only, applied to training fold samples only.
- No test leakage.
- Single sequential run.

## Outputs
- `metrics.json`
- `cv_fold_metrics.csv`
- `fold_*.pt`
- `final_2023.pt`
- `heldout_2024_predictions.csv` (if 2024 mask chips present)

## After run
Download outputs to `reports/stage7_unet_kaggle/` in repo and share. I’ll update Stage 7 gate, TODO, and PROJECT_LOG.
