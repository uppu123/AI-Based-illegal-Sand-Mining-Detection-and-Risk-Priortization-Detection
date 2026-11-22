# %% [markdown]
# # Stage 6 - RF Baseline (Kaggle)
# 
# Protocol: uses locked split only; GroupKFold by transect on 2023 train rows for CV/model selection;
# 2024 train rows excluded from CV/model selection but included in final fit; no augmentation; no test leakage.
# Small n=30 - metrics indicative only.

# %%
import json, os, platform
from pathlib import Path
from datetime import datetime, timezone
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, confusion_matrix, f1_score, precision_score, recall_score, classification_report
from sklearn.model_selection import GroupKFold

# %% [markdown]
# ## Config - edit these paths for Kaggle dataset mount

# %%
# Kaggle: mount a dataset containing these files, or place them in /kaggle/input/<dataset-name>/
INPUT_DIR = Path(os.environ.get("YAMUNA_STAGE6_INPUT", "/kaggle/input/yamuna-stage6"))
LOCKED_SPLIT = INPUT_DIR / "test_split_LOCKED.csv"
FEATURES_CSV = INPUT_DIR / "features_v2.csv"
OUTPUT_DIR = Path(os.environ.get("YAMUNA_STAGE6_OUTPUT", "/kaggle/working/stage6_rf"))
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

FEATURE_COLS = ["ndvi_mean","ndwi_mean","ndbi_mean","ndsi_mean","cmi_mean","water_frac","distance_mean_m"]
RANDOM_STATE = 42
N_ESTIMATORS = 500
CV_SPLITS = 5

# %%
split = pd.read_csv(LOCKED_SPLIT)
feats = pd.read_csv(FEATURES_CSV)
df = split.merge(feats[["chip_id"]+FEATURE_COLS], on="chip_id", how="left", suffixes=("","_f"))
for c in FEATURE_COLS:
    cf=c+"_f"
    if cf in df.columns:
        df[c]=df[cf].where(df[cf].notna(), df[c]); df=df.drop(columns=[cf])
assert df[FEATURE_COLS].isna().sum().sum()==0
train_df = df[df.split=="train"].copy()
test_df = df[df.split=="test"].copy()
cv_df = train_df[~train_df["quarter"].astype(str).str.startswith("2024")].copy()
print("train", len(train_df), "test", len(test_df), "cv_2023", len(cv_df))

# %%
def compute_metrics(y_true, y_pred, labels=("NOT MINING","MINING")):
    return {
        "n": int(len(y_true)),
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "precision_macro": float(precision_score(y_true, y_pred, labels=list(labels), average="macro", zero_division=0)),
        "recall_macro": float(recall_score(y_true, y_pred, labels=list(labels), average="macro", zero_division=0)),
        "f1_macro": float(f1_score(y_true, y_pred, labels=list(labels), average="macro", zero_division=0)),
        "confusion_matrix_labels": list(labels),
        "confusion_matrix": confusion_matrix(y_true, y_pred, labels=list(labels)).tolist(),
    }

X=cv_df[FEATURE_COLS].values; y=cv_df["agreed_label"].values; groups=cv_df["transect_id"].values
gkf=GroupKFold(n_splits=min(CV_SPLITS, len(pd.unique(groups))))
preds=np.empty(len(cv_df),dtype=object)
folds=[]
for fold,(tr,va) in enumerate(gkf.split(X,y,groups), start=1):
    m=RandomForestClassifier(n_estimators=N_ESTIMATORS, random_state=RANDOM_STATE, n_jobs=-1, class_weight="balanced")
    m.fit(X[tr],y[tr]); p=m.predict(X[va]); preds[va]=p
    fm=compute_metrics(y[va],p); fm["fold"]=fold; fm["train_n"]=int(len(tr)); fm["val_n"]=int(len(va)); folds.append(fm)
cv_df=cv_df.copy(); cv_df["cv_pred"]=preds
cv_overall=compute_metrics(y,preds)
cv_overall["excluded_2024_train_rows"]=int(len(train_df)-len(cv_df))

# %%
final=RandomForestClassifier(n_estimators=N_ESTIMATORS, random_state=RANDOM_STATE, n_jobs=-1, class_weight="balanced")
final.fit(train_df[FEATURE_COLS].values, train_df["agreed_label"].values)
test_pred=final.predict(test_df[FEATURE_COLS].values)
test_df=test_df.copy(); test_df["pred_label"]=test_pred
test_metrics=compute_metrics(test_df["agreed_label"].values, test_pred)
imp=pd.DataFrame({"feature":FEATURE_COLS,"importance":final.feature_importances_}).sort_values("importance",ascending=False)

# %%
metrics={
    "stage":6,"model":"RandomForestClassifier","timestamp_utc":datetime.now(timezone.utc).isoformat(),
    "platform":platform.platform(),"python":platform.python_version(),
    "locked_split":str(LOCKED_SPLIT),"features_csv":str(FEATURES_CSV),"feature_cols":FEATURE_COLS,
    "n_train":int(len(train_df)),"n_test":int(len(test_df)),
    "cv":{"overall":cv_overall,"folds":folds},"test":test_metrics,
    "feature_importance":imp.to_dict(orient="records"),
    "protocol_notes":["Locked test split only.","GroupKFold by transect on 2023 train rows for CV; 2024 train rows excluded from CV/model selection but included in final fit.","No augmentation.","Small n=30; indicative only."]
}
(OUTPUT_DIR/"stage6_rf_metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
cv_df.to_csv(OUTPUT_DIR/"stage6_rf_cv_predictions.csv", index=False)
test_df.to_csv(OUTPUT_DIR/"stage6_rf_test_predictions.csv", index=False)
imp.to_csv(OUTPUT_DIR/"stage6_rf_feature_importance.csv", index=False)
(OUTPUT_DIR/"stage6_rf_report.md").write_text(
    f"# Stage 6 RF Baseline (Kaggle)\n\n- CV f1_macro: {cv_overall['f1_macro']:.4f}\n- Test f1_macro: {test_metrics['f1_macro']:.4f}\n- Test accuracy: {test_metrics['accuracy']:.4f}\n- Test CM {test_metrics['confusion_matrix_labels']}: {test_metrics['confusion_matrix']}\n\n```{classification_report(test_df['agreed_label'], test_df['pred_label'], labels=['NOT MINING','MINING'], zero_division=0)}```\n",
    encoding="utf-8")
print(json.dumps({"cv_f1_macro":cv_overall["f1_macro"], "test_f1_macro":test_metrics["f1_macro"], "test_cm":test_metrics["confusion_matrix"]}, indent=2))
