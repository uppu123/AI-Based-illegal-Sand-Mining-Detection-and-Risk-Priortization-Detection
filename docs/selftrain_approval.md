# Self-Training Approval (Stage 8 Gate)

**Status**: NOT APPROVED. Stage 8 remains BLOCKED.

## Required before any Stage 8 run

- [ ] Stage 7 is PASS and stable (reviewed Kaggle outputs in `reports/stage7_unet_kaggle/` and/or `reports/stage7_lmsnet_kaggle/`).
- [ ] User explicitly approves self-training as optional experiment.
- [ ] Scope defined: which model/checkpoint, which unlabeled chips, confidence threshold, max iterations.
- [ ] **No pseudo-masks on test set.** Locked test split (`metadata/test_split_LOCKED.csv`) excluded from pseudo-label generation/training.
- [ ] 2024 excluded from model selection/early stopping.
- [ ] Output paths and caveat labels defined (`pseudo`, not human ground truth).

## Approval record

| Field | Value |
|---|---|
| Approved | NO |
| Approver |  |
| Date |  |
| Model/checkpoint |  |
| Confidence threshold |  |
| Iterations |  |
| Notes |  |

## Non-negotiable

- Pseudo-masks are **not** human ground truth.
- Any self-training result must be labeled experimental unless separately gated.