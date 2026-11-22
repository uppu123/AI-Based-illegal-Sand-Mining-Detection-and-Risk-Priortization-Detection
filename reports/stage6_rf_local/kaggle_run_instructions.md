# Stage 6 RF Baseline - Kaggle Run Instructions

## Files to upload as Kaggle dataset (or input)
- `metadata/test_split_LOCKED.csv` (from repo)
- `metadata/features_v2.csv` (from repo)
- `notebooks/stage6_rf_kaggle.py` (script) or copy into a Kaggle notebook

## Kaggle setup
1. Create a new Kaggle notebook (Python). No GPU required.
2. Add a dataset containing `test_split_LOCKED.csv` and `features_v2.csv`.
3. Set env/path in first config cell if needed:
   - `YAMUNA_STAGE6_INPUT=/kaggle/input/<your-dataset-name>`
   - `YAMUNA_STAGE6_OUTPUT=/kaggle/working/stage6_rf`
4. Run all cells.

## Expected outputs in `/kaggle/working/stage6_rf`
- `stage6_rf_metrics.json`
- `stage6_rf_cv_predictions.csv`
- `stage6_rf_test_predictions.csv`
- `stage6_rf_feature_importance.csv`
- `stage6_rf_report.md`

## After run
Download outputs and place under `reports/stage6_rf_kaggle/` in repo, then I will compare with local run and mark Stage 6 gate.
