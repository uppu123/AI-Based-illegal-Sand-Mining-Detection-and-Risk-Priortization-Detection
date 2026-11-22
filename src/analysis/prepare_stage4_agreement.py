# -*- coding: utf-8 -*-
"""Stage 4 prep: create agreement template and review package.

Does NOT generate final labels. Uses existing verified_labels.csv only as
SUGGESTED_PRIOR_LABEL for human review; agreed_label is left blank.
"""
from __future__ import annotations

import argparse, csv, logging
from pathlib import Path
import pandas as pd


def setup_logger(log_path: Path) -> logging.Logger:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger("stage4_prep")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()
    fmt = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
    for h in [logging.FileHandler(log_path, encoding="utf-8"), logging.StreamHandler()]:
        h.setFormatter(fmt)
        logger.addHandler(h)
    return logger


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--verified", type=Path, default=Path(r"C:\New folder\label_review\verified_labels.csv"))
    ap.add_argument("--features", type=Path, default=Path(r"C:\Users\upend\AI-Based-illegal-Sand-Mining-Detection-and-Risk-Priortization\metadata\features_v2.csv"))
    ap.add_argument("--out-dir", type=Path, default=Path(r"C:\New folder\annotation\agreement"))
    ap.add_argument("--log", type=Path, default=Path(r"C:\Users\upend\AI-Based-illegal-Sand-Mining-Detection-and-Risk-Priortization\reports\logs\stage4_prep.log"))
    ap.add_argument("--n-double", type=int, default=15)
    ap.add_argument("--n-mining", type=int, default=15)
    ap.add_argument("--n-not-mining", type=int, default=15)
    args = ap.parse_args()
    logger = setup_logger(args.log)
    args.out_dir.mkdir(parents=True, exist_ok=True)

    v = pd.read_csv(args.verified)
    f = pd.read_csv(args.features)
    df = v.merge(f[["chip_id","ndvi_mean","ndwi_mean","ndbi_mean","ndsi_mean","cmi_mean","water_frac","distance_mean_m"]], on="chip_id", how="left", suffixes=("","_f"))

    decisive = df[df["reviewer_final_label"].isin(["MINING","NOT MINING"])].copy()
    # Pick clear candidates: MINING with higher ndsi/cmi, NOT MINING with lower ndsi/cmi; deterministic.
    mining = decisive[decisive["reviewer_final_label"]=="MINING"].sort_values(["ndsi_mean","cmi_mean"], ascending=False).head(args.n_mining)
    not_mining = decisive[decisive["reviewer_final_label"]=="NOT MINING"].sort_values(["ndsi_mean","cmi_mean"], ascending=True).head(args.n_not_mining)
    selected = pd.concat([mining, not_mining], ignore_index=True)
    # double-label subset: 8 mining + 7 not mining from selected
    dbl_m = mining.head(8)
    dbl_n = not_mining.head(7)
    double_ids = set(pd.concat([dbl_m, dbl_n])["chip_id"])

    rows = []
    for _, r in selected.iterrows():
        rows.append({
            "chip_id": r["chip_id"],
            "quarter": r["quarter"],
            "transect_id": r["transect_id"],
            "double_label_required": "YES" if r["chip_id"] in double_ids else "NO",
            "label_a": "",
            "label_b": "",
            "agreed_label": "",  # must be filled by human
            "adjudication_notes": "",
            "suggested_prior_label_DO_NOT_USE_AS_FINAL": r["reviewer_final_label"],
            "proposal_status": "PRIOR_LABEL_IS_REFERENCE_ONLY_NOT_AGREED",
            "ndsi_mean": r.get("ndsi_mean", ""),
            "cmi_mean": r.get("cmi_mean", ""),
            "water_frac": r.get("water_frac", ""),
            "ndvi_mean": r.get("ndvi_mean", ""),
        })

    out = args.out_dir / "agreement_template.csv"
    pd.DataFrame(rows).to_csv(out, index=False)
    logger.info("wrote %s rows=%d double=%d", out, len(rows), len(double_ids))

    # also create all-decisive reference queue for possible expansion
    ref = decisive[["chip_id","quarter","transect_id","reviewer_final_label","ndsi_mean","cmi_mean","water_frac","ndvi_mean"]].copy()
    ref = ref.rename(columns={"reviewer_final_label":"suggested_prior_label_DO_NOT_USE_AS_FINAL"})
    ref["double_label_required"] = ""
    ref["label_a"] = ""
    ref["label_b"] = ""
    ref["agreed_label"] = ""
    ref["adjudication_notes"] = ""
    ref.to_csv(args.out_dir / "decisive_candidates_reference.csv", index=False)
    logger.info("wrote decisive reference")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
