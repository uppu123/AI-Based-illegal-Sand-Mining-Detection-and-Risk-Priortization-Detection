# Stage 7 U-Net Colab Review

- **Run**: Colab GPU, 2026-11-22, 40 epochs, seed 42, base 16, batch 4
- **Protocol**: 2023 mask chips GroupKFold-by-transect CV/selection; 2024 held out report-only; flip/90° on training fold samples only; no leakage.
- **Data**: 28 mask entries total; 24 CV 2023; 4 held-out 2024; CV dataset (192,14,256,256), 13 groups.

## Metrics

| Split | IoU | Dice | Precision | Recall | F1 |
|---|---:|---:|---:|---:|---:|
| CV overall (2023) | 0.01592 | 0.03134 | 0.01967 | 0.10054 | 0.03134 |
| Held-out 2024 (report-only) | 0.04729 | 0.08627 | 0.11476 | 0.06919 | 0.08627 |

## Caveats / gate note

- **Not strong segmentation performance**; near-zero/low IoU expected risk given tiny/sparse mask set (28 masks). Reported as-is.
- Held-out 2024 is **report-only**; not used for selection/early stopping.
- Checkpoints (`fold_*.pt`, `final_2023.pt`) were produced on Colab but not downloaded to repo due size; metrics/CSVs are the review evidence.
- Stage 7 gate evidence is present for protocol execution; metrics are honest and low - do not overclaim model quality.
