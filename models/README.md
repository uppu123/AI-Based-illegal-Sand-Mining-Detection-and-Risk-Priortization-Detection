# Models — Phase C (training code ready; no metrics yet)

Nothing has been trained yet. `train_segmentation.py` refuses to start until all 16 human pixel masks exist in `C:\New folder\annotation\masks\`. Metrics will be added here only after a real held-out evaluation run.

```powershell
# 3-fold GroupKFold by transect on the 16 real masks
python models/train_segmentation.py --lmsnet --epochs 40
# apply the trained folds to all 252 chips (pseudo-masks, not human truth)
python models/self_train_masks.py "<run_dir_from_previous_step>" 0.7
```

Outputs go to `C:\New folder\segmentation_runs\<timestamp>\`: `metrics.json`, `config.json`, `fold_*.pt`, qualitative prediction PNGs, then `auto_masks\` + `auto_mask_summary.csv` after self-training.

| # | Model | Input | Output | Why |
|---|---|---|---|---|
| 1 | Random Forest / XGBoost | 14 values per pixel | mining probability | Cheap baseline and feature importance; go/no-go gate and fallback detector |
| 2 | U-Net / LMS-Net | 256×256×14 chip | pixel-level mining mask | The deliverable is a map, not a label; multi-scale handles pits and kilometre-long bars |
| 3 | S2 + S1 late fusion | optical + SAR probability maps | fused map | SAR works through monsoon cloud; optical path remains standalone |
| 4 | Risk-score regressor | 5 AHP-weighted factors | 0–100 per river-km segment | Enforcement needs a priority list; validated by hotspot rank correlation |

Evaluation: precision/recall/F1 for the baseline; IoU, F1, per-class PR and confusion matrix for segmentation; **spatial** cross-validation (adjacent chips must not leak across folds).

Risk factors: detection intensity 30%, temporal persistence 25%, morphological change 20%, access proximity 15%, vegetation loss 10%. Weights require human approval.

See `../docs/documentation_pdfs/04_Models_and_Justification.pdf` for the full justification.
