# Stage 7 U-Net Aug45 (Gate-Compliant) - Colab Review

- **Run**: Colab GPU, 2026-11-22, 40 epochs, seed 42, base 16
- **Protocol**: Split first on real 2023 mask chips (GroupKFold by transect, 3 folds); 2024 held out report-only; no 2024 in selection/early stopping; no leakage.
- **Augmentation (train-fold only, after split)**: 1 real + rot 45/90/135/180 + pixel shifts (±16px x/y) = 9 samples per real training chip. Image: bilinear/reflect; mask: nearest/reflect, re-binarized. 45/135 include interpolation/corner artifacts (documented). Validation/held-out 2024 real-only.

## Metrics

| Split | IoU | Dice | Precision | Recall | F1 |
|---|---:|---:|---:|---:|---:|
| CV overall (2023) | 0.03381 | 0.06540 | 0.04773 | 0.11520 | 0.06540 |
| Held-out 2024 (report-only) | 0.07779 | 0.13463 | 0.19979 | 0.10153 | 0.13463 |

## Caveats

- Improved over non-augmented baseline but still **low/weak segmentation** on sparse 28-mask dataset; not defensible as strong production evidence.
- Held-out 2024 is report-only. Checkpoints not committed due size.
- NOT a gate PASS by itself; honest review required.
