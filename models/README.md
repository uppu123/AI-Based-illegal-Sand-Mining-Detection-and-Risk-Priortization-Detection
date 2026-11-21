# Models — Phase C (both segmentation runs completed, honest results)

`train_segmentation.py` was run twice on the 28 human pixel masks with 3-fold GroupKFold by transect (augmentations kept with their source chip). Both runs completed and wrote `metrics.json`, three fold checkpoints and qualitative predictions to `C:\New folder\segmentation_runs\<timestamp>\`.

## Measured held-out results (no fabrication)

| Run | IoU | Dice | Precision | Recall | F1 |
|---|---|---|---|---|---|
| U-Net (`20261122_040401`) | 0.0055 | 0.0110 | 0.0061 | 0.0803 | 0.0110 |
| LMS-Net (`20261122_044039`) | 0.0059 | 0.0117 | 0.0069 | 0.0556 | 0.0117 |

LMS-Net is marginally better by IoU, but **both results are near zero**. The cause is the ground truth: only 12 of 28 masks contain any paint, and positive pixels cover just 0.2–3.1% of those chips. These numbers are reported as measured; they are **not** a detection capability claim. The next scientific step is to improve the masks and retrain, not to present these scores as success.

`model_comparison.csv` / `model_comparison.json` in the runs folder hold the machine-readable comparison.

### Self-training (option B) — completed as a pipeline demo

`self_train_masks.py` was run on the LMS-Net run at threshold 0.7. Two faults were fixed: launcher quoting of the spaced run path, and mean/std broadcast shape (`1x14x1x1` → `14x1x1`) for single-chip inference.

- 252/252 chips processed; 252 mask PNGs + `auto_mask_summary.csv` + `self_train_note.txt` written to `20261122_044039\auto_masks\`.
- **224 empty** pseudo-masks, 28 non-empty; positive fraction max **0.0137**; mean confidence median **0.0085**, max **0.1022**.
- With no chip reaching the 0.7 confidence level, these pseudo-masks are not usable for real risk ranking. No accuracy is claimed. See `../docs/documentation_pdfs/10_Self_Training_Results.pdf`.

## Commands

```powershell
# 3-fold GroupKFold by transect on the 28 real masks (already run)
python -u models/train_segmentation.py --epochs=40
python -u models/train_segmentation.py --lmsnet --epochs=40

# Apply the trained folds to all 252 chips (pseudo-masks, NOT human truth)
python models/self_train_masks.py "<run_dir_from_previous_step>" 0.7

# Compare completed runs honestly
python models/compare_segmentation_runs.py

# AHP risk index (rule-based, weights PROPOSED pending approval)
python models/compute_risk_score.py --features <factors.csv> --out <scores.csv>
```

Run one segmentation training at a time on this 16 GB machine: two parallel jobs exhausted virtual memory on the first attempt.

## Model roles

| # | Model | Input | Output | Why |
|---|---|---|---|---|
| 1 | Random Forest / XGBoost | 14 values per pixel | mining probability | Cheap baseline and feature importance; go/no-go gate and fallback detector |
| 2 | U-Net / LMS-Net | 256×256×14 chip | pixel-level mining mask | The deliverable is a map, not a label; multi-scale handles pits and kilometre-long bars |
| 3 | S2 + S1 late fusion | optical + SAR probability maps | fused map | SAR works through monsoon cloud; optical path remains standalone |
| 4 | AHP risk scorer (rule-based) | 5 weighted factors | 0–100 per river-km segment | Enforcement needs a priority list; validated by hotspot **rank** correlation, never a claimed "risk accuracy" |

Evaluation: precision/recall/F1 for the baseline; IoU, Dice, precision, recall, F1 for segmentation with **spatial** cross-validation (adjacent chips must not leak across folds).

Risk factors: detection intensity 30%, temporal persistence 25%, morphological change 20%, access proximity 15%, vegetation loss 10%. Weights require human approval.

See `../docs/documentation_pdfs/04_Models_and_Justification.pdf` for the full justification.
