# Stage 6 - RF Baseline Report

- Timestamp (UTC): 2026-11-22T14:25:06.847267+00:00
- Model: RandomForestClassifier (n_estimators=500, random_state=42, class_weight=balanced)
- Locked split: `C:\Users\upend\AI-Based-illegal-Sand-Mining-Detection-and-Risk-Priortization\metadata\test_split_LOCKED.csv`
- Features: `ndvi_mean, ndwi_mean, ndbi_mean, ndsi_mean, cmi_mean, water_frac, distance_mean_m`

## Data
- Train: 24 ({'NOT MINING': 12, 'MINING': 12})
- Test: 6 ({'MINING': 3, 'NOT MINING': 3})
- CV rows (2023 train only): 21; excluded 2024 train rows from CV: 3

## CV (GroupKFold by transect, 2023 train only)
- splits: 5
- accuracy: 0.9048
- f1_macro: 0.9028
- confusion_matrix (labels ['NOT MINING', 'MINING']): [[11, 1], [1, 8]]

## Locked Test
- accuracy: 1.0000
- f1_macro: 1.0000
- f1_mining: 1.0000
- f1_not_mining: 1.0000
- confusion_matrix (labels ['NOT MINING', 'MINING']): [[3, 0], [0, 3]]

## Feature importance
- distance_mean_m: 0.1696
- ndsi_mean: 0.1654
- cmi_mean: 0.1522
- ndvi_mean: 0.1503
- ndwi_mean: 0.1486
- ndbi_mean: 0.1356
- water_frac: 0.0783

## Protocol notes
- Locked test split used; test not used for CV/model selection.
- GroupKFold by transect for CV on 2023 train rows only; 2024 train rows excluded from CV/model selection but included in final train fit.
- No augmentation.
- Small n=30 total; metrics are indicative, not production accuracy.

## Classification report (test)
```
              precision    recall  f1-score   support

  NOT MINING       1.00      1.00      1.00         3
      MINING       1.00      1.00      1.00         3

    accuracy                           1.00         6
   macro avg       1.00      1.00      1.00         6
weighted avg       1.00      1.00      1.00         6

```