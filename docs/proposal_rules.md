# Stage 3 - Proposal Rules (PROPOSALS ONLY)

**No final labels generated.** Feature-based groups are PROPOSALS for human confirmation only.
Do not copy `proposed_group` into `verified_labels.csv` or any final label field without human review.

## Percentile cutoffs (derived from 2023 chips only; 2024 excluded from cutoff derivation)

| Cutoff | Value |
|---|---:|
| ndsi_mean_high_p75_2023 | -0.158414 |
| ndsi_mean_low_p25_2023 | -0.192096 |
| cmi_mean_high_p75_2023 | 0.099825 |
| cmi_mean_low_p25_2023 | 0.069875 |
| water_frac_high_p75_2023 | 0.037681 |
| ndvi_mean_high_p75_2023 | 0.270455 |
| distance_mean_m_near_p25_2023 | 546.600000 |

## Proposal logic
- `PROPOSAL_MINING_LIKE`: ndsi_mean >= p75_2023 AND cmi_mean >= p75_2023 AND no not-mining cues.
- `PROPOSAL_NOT_MINING_LIKE`: >=2 not-mining cues (ndvi_mean>=p75_2023, ndsi_mean<=p25_2023, cmi_mean<=p25_2023) AND no mining-like score.
- `PROPOSAL_MIXED_REVIEW`: mining-like and not-mining cues conflict.
- `PROPOSAL_UNSURE_REVIEW`: insufficient/ambiguous cues.

## Outputs
- `metadata/proposed_groups.csv`
- `annotation/review_queue.csv` (human_decision/human_notes blank)

## Caveats
- Proposals are heuristic, percentile-based, and not ground truth.
- 2024 chips receive proposals using 2023-derived cutoffs; this is for review prioritization only, not model/threshold selection.
