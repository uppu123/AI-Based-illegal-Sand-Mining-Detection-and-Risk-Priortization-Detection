#!/usr/bin/env python3
"""Stage 6: Random Forest baseline on locked test split.

Protocol constraints:
- Uses metadata/test_split_LOCKED.csv (student-approved). Never modifies it.
- 2024 excluded from model selection / early stopping / threshold selection.
  2024 rows present in locked train are kept in train fit but CV/model-selection
  metrics are computed on 2023 train folds only and reported separately.
- No augmentation. No test leakage. GroupKFold by transect for train CV.
- Reports honest metrics; sand_frac separability is flagged as artifact risk.

Outputs:
- reports/stage6_rf_metrics.json
- reports/stage6_rf_cv_predictions.csv
- reports/stage6_rf_test_predictions.csv
- reports/stage6_rf_feature_importance.csv
- reports/stage6_rf_report.md
- reports/logs/stage6_rf_baseline.log
"""
from __future__ import annotations

import argparse
import json
import logging
import platform
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)
from sklearn.model_selection import GroupKFold


DEFAULT_FEATURES = [
    "ndvi_mean", "ndwi_mean", "ndbi_mean", "ndsi_mean",
    "cmi_mean", "water_frac", "distance_mean_m",
]


def setup_logger(log_path: Path) -> logging.Logger:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger("stage6_rf")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()
    fmt = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
    fh = logging.FileHandler(log_path, encoding="utf-8")
    sh = logging.StreamHandler()
    fh.setFormatter(fmt)
    sh.setFormatter(fmt)
    logger.addHandler(fh)
    logger.addHandler(sh)
    return logger


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Stage 6 RF baseline")
    p.add_argument("--locked-split", type=Path, required=True, help="Path to test_split_LOCKED.csv")
    p.add_argument("--features-csv", type=Path, required=True, help="Path to features_v2.csv")
    p.add_argument("--output-dir", type=Path, required=True, help="Directory for reports/outputs")
    p.add_argument("--log-file", type=Path, default=None, help="Log file path")
    p.add_argument("--n-estimators", type=int, default=500)
    p.add_argument("--max-depth", type=int, default=None)
    p.add_argument("--min-samples-leaf", type=int, default=1)
    p.add_argument("--random-state", type=int, default=42)
    p.add_argument("--cv-splits", type=int, default=5)
    p.add_argument("--include-sand-frac", action="store_true",
                   help="Include sand_frac as feature (artifact risk; reported separately)")
    return p.parse_args()


def load_data(locked_split: Path, features_csv: Path, feature_cols: list[str], logger: logging.Logger):
    split = pd.read_csv(locked_split)
    feats = pd.read_csv(features_csv)
    # merge features; locked split already has some feature cols but use features_v2 as canonical
    feat_cols_available = [c for c in feature_cols if c in feats.columns]
    missing = [c for c in feature_cols if c not in feats.columns]
    if missing:
        raise ValueError(f"Missing feature columns in features_v2: {missing}")
    keep = ["chip_id"] + feature_cols
    merged = split.merge(feats[keep], on="chip_id", how="left", suffixes=("", "_f"))
    # prefer features_v2 values
    for c in feature_cols:
        cf = c + "_f"
        if cf in merged.columns:
            merged[c] = merged[cf].where(merged[cf].notna(), merged[c])
            merged = merged.drop(columns=[cf])
    # checks
    if merged[feature_cols].isna().any().any():
        bad = merged[merged[feature_cols].isna().any(axis=1)]["chip_id"].tolist()
        raise ValueError(f"NaN features for chips: {bad}")
    if not merged["agreed_label"].isin(["MINING", "NOT MINING"]).all():
        raise ValueError("agreed_label must be MINING/NOT MINING")
    logger.info("Loaded %d rows: %s", len(merged), merged["split"].value_counts().to_dict())
    return merged, feat_cols_available


def compute_metrics(y_true, y_pred, labels=("NOT MINING", "MINING")) -> dict:
    return {
        "n": int(len(y_true)),
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "precision_macro": float(precision_score(y_true, y_pred, labels=list(labels), average="macro", zero_division=0)),
        "recall_macro": float(recall_score(y_true, y_pred, labels=list(labels), average="macro", zero_division=0)),
        "f1_macro": float(f1_score(y_true, y_pred, labels=list(labels), average="macro", zero_division=0)),
        "f1_mining": float(f1_score(y_true, y_pred, pos_label="MINING", zero_division=0)),
        "f1_not_mining": float(f1_score(y_true, y_pred, pos_label="NOT MINING", zero_division=0)),
        "confusion_matrix_labels": list(labels),
        "confusion_matrix": confusion_matrix(y_true, y_pred, labels=list(labels)).tolist(),
    }


def run_cv(train_df: pd.DataFrame, feature_cols: list[str], args: argparse.Namespace, logger: logging.Logger):
    # CV/model selection uses 2023 train rows only (2024 excluded from model selection).
    cv_df = train_df[~train_df["quarter"].astype(str).str.startswith("2024")].copy()
    excluded_2024 = train_df[train_df["quarter"].astype(str).str.startswith("2024")].copy()
    logger.info("CV train rows (2023 only): %d, excluded 2024 train rows: %d", len(cv_df), len(excluded_2024))

    X = cv_df[feature_cols].values
    y = cv_df["agreed_label"].values
    groups = cv_df["transect_id"].values

    n_groups = len(pd.unique(groups))
    n_splits = min(args.cv_splits, n_groups)
    if n_splits < 2:
        raise ValueError(f"Need >=2 groups for GroupKFold, got {n_groups}")
    gkf = GroupKFold(n_splits=n_splits)

    preds = np.empty(len(cv_df), dtype=object)
    fold_rows = []
    for fold, (tr_idx, va_idx) in enumerate(gkf.split(X, y, groups), start=1):
        model = RandomForestClassifier(
            n_estimators=args.n_estimators,
            max_depth=args.max_depth,
            min_samples_leaf=args.min_samples_leaf,
            random_state=args.random_state,
            n_jobs=-1,
            class_weight="balanced",
        )
        model.fit(X[tr_idx], y[tr_idx])
        p = model.predict(X[va_idx])
        preds[va_idx] = p
        m = compute_metrics(y[va_idx], p)
        m["fold"] = fold
        m["train_n"] = int(len(tr_idx))
        m["val_n"] = int(len(va_idx))
        fold_rows.append(m)
        logger.info("Fold %d: val_n=%d f1_macro=%.3f acc=%.3f", fold, m["val_n"], m["f1_macro"], m["accuracy"])

    cv_df = cv_df.copy()
    cv_df["cv_pred"] = preds
    overall = compute_metrics(y, preds)
    overall["cv_splits"] = n_splits
    overall["excluded_2024_train_rows"] = int(len(excluded_2024))
    return cv_df, fold_rows, overall


def fit_final(train_df: pd.DataFrame, feature_cols: list[str], args: argparse.Namespace, logger: logging.Logger):
    # Final model fit uses all locked train rows (including 2024 train rows) because they are training data;
    # 2024 was not used for model selection/CV above. This is explicit.
    X = train_df[feature_cols].values
    y = train_df["agreed_label"].values
    model = RandomForestClassifier(
        n_estimators=args.n_estimators,
        max_depth=args.max_depth,
        min_samples_leaf=args.min_samples_leaf,
        random_state=args.random_state,
        n_jobs=-1,
        class_weight="balanced",
    )
    model.fit(X, y)
    logger.info("Final model fit on %d train rows", len(train_df))
    return model


def main() -> None:
    args = parse_args()
    out = args.output_dir
    out.mkdir(parents=True, exist_ok=True)
    log_file = args.log_file or (out / "logs" / "stage6_rf_baseline.log")
    logger = setup_logger(log_file)

    feature_cols = list(DEFAULT_FEATURES)
    if args.include_sand_frac:
        feature_cols.append("sand_frac")

    logger.info("Stage 6 RF baseline start")
    logger.info("Args: %s", vars(args))
    logger.info("Features: %s", feature_cols)

    df, feat_used = load_data(args.locked_split, args.features_csv, feature_cols, logger)
    train_df = df[df["split"] == "train"].copy()
    test_df = df[df["split"] == "test"].copy()

    cv_df, fold_rows, cv_overall = run_cv(train_df, feature_cols, args, logger)
    model = fit_final(train_df, feature_cols, args, logger)

    # evaluate on locked test (2023 only in this split)
    X_test = test_df[feature_cols].values
    y_test = test_df["agreed_label"].values
    test_pred = model.predict(X_test)
    test_df = test_df.copy()
    test_df["pred_label"] = test_pred
    test_metrics = compute_metrics(y_test, test_pred)

    # artifact warning: sand_frac
    artifact_note = None
    if "sand_frac" in feature_cols:
        artifact_note = "sand_frac included; prior analysis showed decisive labels separable by sand_frac>0.575 - treat accuracy as potential artifact."
        logger.warning(artifact_note)
    else:
        # check separability on this dataset for reporting only
        if "sand_frac" in df.columns:
            mine = df[df.agreed_label=="MINING"]["sand_frac"]
            nmn = df[df.agreed_label=="NOT MINING"]["sand_frac"]
            if len(mine) and len(nmn) and mine.min() > nmn.max():
                artifact_note = f"WARNING: labels perfectly separable by sand_frac in this split (MINING min={mine.min():.4f}, NOT MINING max={nmn.max():.4f}). RF without sand_frac may still learn correlated indices."
                logger.warning(artifact_note)

    # feature importance
    importances = pd.DataFrame({
        "feature": feature_cols,
        "importance": model.feature_importances_,
    }).sort_values("importance", ascending=False)

    # save outputs
    cv_df.to_csv(out / "stage6_rf_cv_predictions.csv", index=False)
    test_df.to_csv(out / "stage6_rf_test_predictions.csv", index=False)
    importances.to_csv(out / "stage6_rf_feature_importance.csv", index=False)

    metrics = {
        "stage": 6,
        "model": "RandomForestClassifier",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "platform": platform.platform(),
        "python": platform.python_version(),
        "locked_split": str(args.locked_split),
        "features_csv": str(args.features_csv),
        "feature_cols": feature_cols,
        "n_train": int(len(train_df)),
        "n_test": int(len(test_df)),
        "train_class_counts": train_df["agreed_label"].value_counts().to_dict(),
        "test_class_counts": test_df["agreed_label"].value_counts().to_dict(),
        "cv": {"overall": cv_overall, "folds": fold_rows},
        "test": test_metrics,
        "feature_importance": importances.to_dict(orient="records"),
        "artifact_note": artifact_note,
        "protocol_notes": [
            "Locked test split used; test not used for CV/model selection.",
            "GroupKFold by transect for CV on 2023 train rows only; 2024 train rows excluded from CV/model selection but included in final train fit.",
            "No augmentation.",
            "Small n=30 total; metrics are indicative, not production accuracy."
        ],
    }
    (out / "stage6_rf_metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")

    # report
    report = []
    report.append("# Stage 6 - RF Baseline Report")
    report.append("")
    report.append(f"- Timestamp (UTC): {metrics['timestamp_utc']}")
    report.append(f"- Model: RandomForestClassifier (n_estimators={args.n_estimators}, random_state={args.random_state}, class_weight=balanced)")
    report.append(f"- Locked split: `{args.locked_split}`")
    report.append(f"- Features: `{', '.join(feature_cols)}`")
    report.append("")
    report.append("## Data")
    report.append(f"- Train: {len(train_df)} ({train_df['agreed_label'].value_counts().to_dict()})")
    report.append(f"- Test: {len(test_df)} ({test_df['agreed_label'].value_counts().to_dict()})")
    report.append(f"- CV rows (2023 train only): {cv_overall['n']}; excluded 2024 train rows from CV: {cv_overall['excluded_2024_train_rows']}")
    report.append("")
    report.append("## CV (GroupKFold by transect, 2023 train only)")
    report.append(f"- splits: {cv_overall['cv_splits']}")
    report.append(f"- accuracy: {cv_overall['accuracy']:.4f}")
    report.append(f"- f1_macro: {cv_overall['f1_macro']:.4f}")
    report.append(f"- confusion_matrix (labels {cv_overall['confusion_matrix_labels']}): {cv_overall['confusion_matrix']}")
    report.append("")
    report.append("## Locked Test")
    report.append(f"- accuracy: {test_metrics['accuracy']:.4f}")
    report.append(f"- f1_macro: {test_metrics['f1_macro']:.4f}")
    report.append(f"- f1_mining: {test_metrics['f1_mining']:.4f}")
    report.append(f"- f1_not_mining: {test_metrics['f1_not_mining']:.4f}")
    report.append(f"- confusion_matrix (labels {test_metrics['confusion_matrix_labels']}): {test_metrics['confusion_matrix']}")
    report.append("")
    report.append("## Feature importance")
    for _, r in importances.iterrows():
        report.append(f"- {r['feature']}: {r['importance']:.4f}")
    report.append("")
    if artifact_note:
        report.append("## Artifact warning")
        report.append(f"- {artifact_note}")
        report.append("")
    report.append("## Protocol notes")
    for n in metrics["protocol_notes"]:
        report.append(f"- {n}")
    report.append("")
    report.append("## Classification report (test)")
    report.append("```")
    report.append(classification_report(y_test, test_pred, labels=["NOT MINING","MINING"], zero_division=0))
    report.append("```")
    (out / "stage6_rf_report.md").write_text("\n".join(report), encoding="utf-8")

    logger.info("CV f1_macro=%.4f test f1_macro=%.4f", cv_overall["f1_macro"], test_metrics["f1_macro"])
    logger.info("Wrote outputs to %s", out)


if __name__ == "__main__":
    main()
