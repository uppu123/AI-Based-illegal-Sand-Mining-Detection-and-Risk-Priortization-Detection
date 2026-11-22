# Yamuna Sand Mining Detection - Gated Protocol TODO

Protocol: strict gated stages (2026-11-22). Status legend: `[x] PASS`, `[!] BLOCKED (reason)`, `[ ] NOT RUN`.

## Stage 0: Inventory
- [x] PASS (after approved Option 1 additive copy) - `yamuna_data_fixed` now contains 29 products (11 S2, 12 S1, 6 L8).
  - `yamuna_data_fixed/sentinel2`: 11 TIFs (PASS)
  - `yamuna_data_fixed/sentinel1/2023_2024`: 12 TIFs (PASS) - copied additively from `C:\New folder\yamuna_data\sentinel1\2023_2024` with user approval; SHA256 verified, 0 overwrites.
  - `yamuna_data_fixed/landsat8/2023_2024`: 6 TIFs (PASS) - copied additively from `C:\New folder\yamuna_data\landsat8\2023_2024` with user approval; SHA256 verified, 0 overwrites.
  - `chips_fixed`: 252 chips, 42/quarter across 2023_Q1..2024_Q2 (PASS)
  - `annotation/masks`: 28 `*_mask.png` files (PASS)
  - `verified_labels.csv` (canonical checked: `C:\New folder\label_review\verified_labels.csv`, repo copy matches): 252 rows, MINING=55, NOT MINING=45, UNSURE=152 (PASS)

## Stage 1: Band Mapping and Index Verification
- [x] PASS (with metadata caveat) - Script 09 conclusion/stacking order evidence found (`C:\New folder\yamuna_work\verification\stacking_order_check.md`, `band_mapping_report.md`; `C:\New folder\rebuild_reports\verification_09\band_mapping_report.md`, `band_mapping_stats.csv`; git `1189d2a` Phase A rebuild). 14-band layout present for all 11 S2 composites (uint16, nodata=0.0). Independent Option 2 read-only check: band10 fixed vs raw identical on 3 sampled 512x512 windows for 11/11 composites (max_abs=0, equal_frac=1.0); control bands 4/7 differ as expected. Raw 2023_Q2 metadata lists B12 at band 10. 5-chip deterministic recomputation (seed=42) PASS: NDVI/NDWI/NDBI/NDSI max abs diff <= 0.000488 (<0.01). See `docs/index_status.md`, `docs/band_fix_plan.md`.
  - Caveat: fixed S2 composite band descriptions are all None (metadata hygiene). Pixel-level B12 position verified; optional additive metadata repair needs approval.

## Stage 2: Feature Table
- [x] PASS - Computed 252-chip features on valid pixels from `C:\New folder\chips_fixed` + existing `C:\New folder\extra_features\chip_features.csv` (CMI/distance). Wrote `metadata/features_stage2_raw.csv`, `metadata/features_v2.csv`, `metadata/water_hist.png`, `metadata/features_stage2_summary.json`, `docs/water_threshold_candidates.md`. 2023-only NDSI pixels: 11,010,048; candidates evaluated: -0.10, -0.05, 0.0, 0.05, 0.10. 2024 excluded from threshold selection.
  - Student decision recorded in `docs/water_threshold_decision.md`: `NDSI > 0.0` approved by Upendra Kumar on 2026-11-22. `water_frac` populated for 252/252 chips in `features_v2.csv`.

## Stage 3: Proposed Groups (Proposals Only)
- [x] PASS (proposals only, no final labels) - Percentile cutoffs derived from 2023 chips only; 2024 excluded from cutoff derivation. Wrote `docs/proposal_rules.md`, `metadata/proposed_groups.csv` (252 rows, all `PROPOSAL_FOR_HUMAN_CONFIRMATION_ONLY`), `annotation/review_queue.csv` (human_decision/human_notes blank), `metadata/proposed_groups_summary.json`.
  - Groups: PROPOSAL_UNSURE_REVIEW=209, PROPOSAL_MIXED_REVIEW=27, PROPOSAL_NOT_MINING_LIKE=16, PROPOSAL_MINING_LIKE=0. No labels written to `verified_labels.csv`.
  - Gate note: no cutoff used without percentile basis; water-threshold-dependent water_frac is now populated after approved Stage 2 decision.

## Stage 4: Labelling and Agreement
- [x] PASS - `C:\New folder\annotation\agreement\agreement_report.md/json`:
  - double_labelled=18 (>=15), agreement=88.89% (>=85%), agreed MINING=15, agreed NOT MINING=15, UNSURE=0, invalid=0. gate_pass=true.
  - Source: user-reviewed `agreement_template.xlsx` converted to CSV; labels treated as human-confirmed.

## Stage 5: Locked Test Split
- [x] PASS - `metadata/test_split_LOCKED.csv` created (30 agreed chips: 24 train / 6 test, 3 MINING + 3 NOT MINING in test). Transect-disjoint, 2023-only test, 2024 kept in train. Corrected pre-Stage-6: replaced T051_2023_Q3 with T050_2023_Q3 to remove transect leakage.
  - Locked 2026-11-22 by Upendra Kumar ("lock Stage 5 split"). Proposal: `docs/test_split_proposal.md`.
  - Augmentation policy: no augmentation before split; augmentation only on train split/folds after lock, never test.

## Stage 6: Baseline Model
- [x] PASS (local RF baseline complete; Kaggle package prepared) - `src/analysis/stage6_rf_baseline.py` run on locked split.
  - Local run (`reports/stage6_rf_local/`): CV (2023 train, GroupKFold by transect, 5 splits, n=21) accuracy=0.9048 f1_macro=0.9028, CM [[11,1],[1,8]]; Locked test (n=6, 2023-only) accuracy=1.0000 f1_macro=1.0000, CM [[3,0],[0,3]].
  - Protocol: locked test unused for selection; 2024 train rows (3) excluded from CV/model selection but included in final fit; no augmentation; features exclude sand_frac.
  - Caveat: n=30 total (24 train/6 test) - metrics indicative only, not production accuracy. Feature importances spread (distance/ndsi/cmi/ndvi/ndwi/ndbi/water_frac).
  - Kaggle: `notebooks/stage6_rf_kaggle.py` + `reports/stage6_rf_local/kaggle_run_instructions.md` prepared; user can run same split on Kaggle and place outputs in `reports/stage6_rf_kaggle/`.

## Stage 7: Deep Learning Segmentation
- [!] BLOCKED (aug45 reruns complete, gate not passed) - Gate-compliant augmented reruns completed on Colab (40 epochs, 3-fold GroupKFold by transect, 2023 CV; 2024 held-out report-only; augmentation only on training fold samples after split; val/held-out real-only; no leakage).
  - Augmentation: 1 real + rot 45/90/135/180 + pixel shifts ±16px x/y = 9 samples per real training chip; image bilinear/reflect, mask nearest/reflect + re-binarized; 45/135 interpolation artifacts documented.
  - U-Net aug45 (`reports/stage7_unet_aug45_colab/`): CV IoU 0.03381, Dice 0.06540, P 0.04773, R 0.11520, F1 0.06540; held-out 2024 report-only IoU 0.07779, Dice 0.13463. Improved over prior U-Net but still low/weak.
  - LMS-Net aug45 (`reports/stage7_lmsnet_aug45_colab/`, paper-faithful, explicit deviations in `docs/lmsnet_reference.md`): CV IoU 0.03063, Dice 0.05943, P 0.06369, R 0.06831, F1 0.05943; held-out 2024 report-only IoU 0.05124, Dice 0.08504. Improved over prior LMS-Net but still low/weak.
  - Prior non-aug baseline: U-Net CV IoU 0.01592/Dice 0.03134; LMS-Net CV IoU 0.01605/Dice 0.03158 (`reports/stage7_unet_colab/`, `reports/stage7_lmsnet_colab/`).
  - **Gate decision**: NOT PASS. Augmentation helped, but metrics remain low on sparse 28-mask dataset; not defensible as strong segmentation evidence. No overclaim. Before Stage 8/9, decide: improve labels/data/model, or explicitly accept weak baseline with caveats.

## Stage 8: Self-Training (Optional, Gated)
- [!] BLOCKED (approval/template ready) - `docs/selftrain_approval.md` drafted. Still blocked until Stage 7 PASS/stable and explicit approval; no pseudo-masks on test set.

## Stage 9: Morphology and Risk Scoring
- [!] BLOCKED (draft prep ready) - `docs/ahp_matrices.md` and `docs/ahp_approval.md` drafted (PROPOSED, CR=0.01528 < 0.10). Blocked until prior gates PASS, supervisor approval recorded, and weights reconciled with `models/compute_risk_score.py`. No 40/30/20/10, no risk accuracy.

## Stage 10: Dashboard MVP
- [ ] DROPPED (user decision, 2026-11-22) - Dashboard plan dropped for now. `docs/dashboard_scope.md` retained as draft reference; revisit only if user explicitly requests.

## Stage 11: Documentation
- [ ] NOT RUN
