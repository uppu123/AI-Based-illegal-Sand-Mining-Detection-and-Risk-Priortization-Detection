# AHP Matrices (DRAFT — PROPOSED, NOT APPROVED)

**Status**: DRAFT / PROPOSED. **Not gate evidence.**  
**Stage 9 gate requires**: supervisor-approved AHP matrices, CR < 0.10, recorded in `docs/ahp_approval.md`. No 40/30/20/10 shortcut. No risk accuracy claim.

## Factors

| Factor | Meaning | Direction |
|---|---|---|
| Detection | Mining-mask intensity / detection confidence (e.g., mean positive fraction) | Higher = riskier |
| Persistence | Fraction of quarters with detected extraction | Higher = riskier |
| Morphology | Morphological change magnitude | Higher = riskier |
| Access | Distance to river centreline / access proxy (m) | Lower = riskier (inverted before scaling) |
| Vegetation | Vegetation-loss magnitude | Higher = riskier |

## Proposed pairwise comparison matrix (Saaty 1–9 scale)

Order: [Detection, Persistence, Morphology, Access, Vegetation]

|  | Detection | Persistence | Morphology | Access | Vegetation |
|---|---:|---:|---:|---:|---:|
| **Detection** | 1 | 1 | 2 | 3 | 4 |
| **Persistence** | 1 | 1 | 1 | 2 | 3 |
| **Morphology** | 1/2 | 1 | 1 | 2 | 2 |
| **Access** | 1/3 | 1/2 | 1/2 | 1 | 2 |
| **Vegetation** | 1/4 | 1/3 | 1/2 | 1/2 | 1 |

## Computed result (principal eigenvector)

Computed by `numpy.linalg.eig` on the matrix above:

| Factor | Proposed weight |
|---|---:|
| Detection | 0.33513 |
| Persistence | 0.25408 |
| Morphology | 0.20487 |
| Access | 0.12409 |
| Vegetation | 0.08184 |
| **Sum** | **1.00000** |

- **λ_max** = 5.068439
- **CI** = (λ_max - n)/(n-1) = 0.017110
- **RI (n=5)** = 1.12
- **CR** = CI/RI = **0.015277 < 0.10** (PASS for consistency check only; approval still required)

## Reconciliation note

`models/compute_risk_score.py` currently contains older PROPOSED defaults: detection 0.30, persistence 0.25, morphology 0.20, access 0.15, vegetation 0.10. The matrix above yields slightly different normalized weights. **Before Stage 9 execution**, reconcile: either update matrix to match approved weights, or update code to approved matrix-derived weights. Do not run Stage 9 with ambiguous weights.

## Validation rules (locked by protocol)

- Risk output is a **prioritization index**, not probability.
- **No “risk accuracy” claim.** 
- Validation is rank-only against known hotspots (e.g., Spearman rank check), reported with caveats.
- 2024 excluded from model selection/early stopping; do not use 2024 for threshold/model selection in upstream model steps feeding risk.

## Approval

Supervisor approval must be recorded in `docs/ahp_approval.md` with date, approver name, approved matrix/weights, and any modifications.