# Stage 7 LMS-Net Aug45 (Gate-Compliant) - Colab Review

- **Run**: Colab GPU, 2026-11-22, 40 epochs, seed 42, channels [32,64,128,256,512]
- **Reference**: Zhang et al., *Remote Sensing* 2025, 17, 227, doi:10.3390/rs17020227. Paper-faithful structure with explicit deviations (14-band input, binary mask, explicit channels, Stage 7 protocol).
- **Protocol**: Split first on real 2023 mask chips (GroupKFold by transect, 3 folds); 2024 held out report-only; no leakage.
- **Augmentation (train-fold only, after split)**: 1 real + rot 45/90/135/180 + pixel shifts (±16px x/y) = 9 samples per real training chip. 45/135 interpolation/corner artifacts documented. Val/held-out 2024 real-only.

## Metrics

| Split | IoU | Dice | Precision | Recall | F1 |
|---|---:|---:|---:|---:|---:|
| CV overall (2023) | 0.03063 | 0.05943 | 0.06369 | 0.06831 | 0.05943 |
| Held-out 2024 (report-only) | 0.05124 | 0.08504 | 0.10906 | 0.06969 | 0.08504 |

## Caveats

- Improved over prior non-augmented LMS-Net run, but still **low/weak segmentation** on sparse 28-mask dataset; not strong evidence.
- Held-out 2024 report-only. Checkpoints not committed due size.
- NOT a gate PASS by itself; honest review required. Old `models/train_segmentation.py --lmsnet` remains NON-COMPLIANT with the paper.
