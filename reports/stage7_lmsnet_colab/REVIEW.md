# Stage 7 LMS-Net Colab Review

- **Run**: Colab GPU, 2026-11-22, 40 epochs, seed 42, channels [32,64,128,256,512]
- **Reference**: Zhang et al., *Remote Sensing* 2025, 17, 227, doi:10.3390/rs17020227 (on disk; `docs/lmsnet_reference.md`).
- **Protocol**: 2023 mask chips GroupKFold-by-transect CV/selection; 2024 held out report-only; flip/90° on training fold samples only; no leakage.
- **Deviations**: 14-band S2 input, binary 1-channel mining mask output, explicit channel schedule [32,64,128,256,512], Stage 7 project protocol.

## Metrics

| Split | IoU | Dice | Precision | Recall | F1 |
|---|---:|---:|---:|---:|---:|
| CV overall (2023) | 0.01605 | 0.03158 | 0.01827 | 0.18645 | 0.03158 |
| Held-out 2024 (report-only) | 0.00000 | 0.00000 | 0.00000 | 0.00000 | 0.00000 |

## Caveats / gate note

- **Very low/near-zero performance** on sparse mask set; held-out 2024 all zeros reported as-is. Not suitable as strong segmentation evidence.
- LMS-Net implementation is paper-faithful in structure with explicit deviations documented; old `models/train_segmentation.py --lmsnet` remains NON-COMPLIANT.
- Checkpoints produced on Colab not downloaded to repo due size; metrics/CSVs are review evidence.
- Stage 7 requires honest review; do not claim LMS-Net superiority from this run.
