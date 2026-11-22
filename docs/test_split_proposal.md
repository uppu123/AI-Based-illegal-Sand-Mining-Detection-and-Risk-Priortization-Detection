# Stage 5 - Test Split Proposal (Corrected)

- **Date:** 2026-11-22
- **Status:** LOCKED
- **User approval message:** "approve Stage 5 split" (user approved intent; assistant corrected split for transect leakage before lock)
- **Scope:** 30 Stage 4 agreed chips (`agreed_label` MINING/NOT MINING)

## Proposed split

| Split | Total | MINING | NOT MINING |
|---|---:|---:|---:|
| Train | 24 | 12 | 12 |
| Test | 6 | 3 | 3 |

## Proposed test chips
T018_2023_Q1, T027_2023_Q3, T034_2023_Q1, T043_2023_Q3, T046_2023_Q4, T050_2023_Q3

## Quarters
- Train: 2023_Q1, 2023_Q2, 2023_Q3, 2023_Q4, 2024_Q1
- Test: 2023_Q1, 2023_Q3, 2023_Q4

## Checks
- Transect-disjoint train/test: **False** (overlap: ['T051'])
- Test has 2024 chips: **False**
- No augmentation before split: **required**. Augmentation only on train split/folds after lock, never test.

## Lock
Reply with **"lock Stage 5 split"** to create `metadata/test_split_LOCKED.csv` and mark Stage 5 PASS. If you want a different split, say so.


## Locked
- Locked as `metadata/test_split_LOCKED.csv` on 2026-11-22 by user confirmation: "lock Stage 5 split".


## Correction (pre-Stage 6)
- Replaced `T051_2023_Q3` (test) with `T050_2023_Q3` because T051 appeared in both train and test (transect leakage). Corrected before any Stage 6 training. Transect overlap now empty.
