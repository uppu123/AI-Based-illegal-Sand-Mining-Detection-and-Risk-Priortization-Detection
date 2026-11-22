# Dashboard Scope (DRAFT — PROPOSED, NOT APPROVED)

**Status**: DROPPED FOR NOW (user decision, 2026-11-22). Retained as draft reference only. **Not gate evidence.**  
**Stage 10 gate requires**: user-approved `docs/dashboard_scope.md`; show only PASS-gated results as final.

## Goal (MVP)

A simple review dashboard for the BTech project that displays **only gate-PASS, reviewed outputs** as final, and clearly labels drafts/pilot/non-compliant results as non-final.

## In-scope (MVP)

| View | Data source | Final-status rule |
|---|---|---|
| Project status | `docs/TODO.md`, `docs/PROJECT_LOG.md` | Show gate status as-is (`PASS`/`BLOCKED`/`NOT RUN`) |
| Stage 2-6 metrics | `metadata/features_v2.csv`, `reports/stage6_rf_local/*` | Stage 6 can show as PASS with caveats (n=30, indicative) |
| Stage 7 results | `reports/stage7_unet_kaggle/*`, `reports/stage7_lmsnet_kaggle/*` | **Only after Stage 7 gate review**; until then label “AWAITING REVIEW / NOT FINAL” |
| Maps/previews | existing `reports/figures`, `reports/centerline`, `reports/transects`, approved preview PNGs | Only derived from protected/approved inputs |
| Risk ranking | Stage 9 outputs (`reports/stage9_risk/*`, TBD) | **Only after AHP approved + Stage 9 PASS**; rank-only, no risk accuracy |

## Out-of-scope (MVP)

- Live model training/inference from UI
- Editing raw data/protected files
- Public deployment/auth hardening beyond local demo
- Any “risk accuracy”, probability-of-illegal-mining claim, or unreviewed model output labeled final
- 2024-driven model selection display

## Data contract (proposed)

- Read-only inputs from repo/report/metadata paths.
- Every displayed metric card includes: `source file`, `timestamp/run id`, `gate status`, `caveat`.
- Protected/read-only: `C:\New folder\yamuna_data`, `chips_fixed`, `annotation/masks`, `verified_labels.csv`, `test_split_LOCKED.csv`.

## UX/labels required

- Banner: “Results shown as final only when corresponding stage gate is PASS.”
- Stage 7/LMS-Net/U-Net results before review: **NOT FINAL**.
- Risk view: “Prioritization index; rank-only validation; no risk accuracy.”

## Approval

| Field | Value |
|---|---|
| Approved | NO |
| Approver (user) |  |
| Date |  |
| MVP scope changes |  |

Stage 10 implementation starts only after this file is approved.