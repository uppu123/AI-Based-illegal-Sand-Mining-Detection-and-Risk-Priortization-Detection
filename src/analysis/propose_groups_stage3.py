# -*- coding: utf-8 -*-
"""Stage 3: percentile-based proposed groups (PROPOSALS ONLY).

Protocol constraints:
- NO final labels generated.
- Feature-based groups are PROPOSALS for human confirmation only.
- Cutoff not tied to percentile = TO BE SET, unused.
- Uses Stage 2 features_v2 (water threshold approved by student).
"""
from __future__ import annotations

import argparse, csv, json, logging
from pathlib import Path
import numpy as np
import pandas as pd


def setup_logger(log_path: Path) -> logging.Logger:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger("stage3_proposals")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()
    fmt = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
    for h in [logging.FileHandler(log_path, encoding="utf-8"), logging.StreamHandler()]:
        h.setFormatter(fmt)
        logger.addHandler(h)
    return logger


def pct(series: pd.Series, q: float) -> float:
    return float(series.quantile(q))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--features", type=Path, default=Path(r"C:\Users\upend\AI-Based-illegal-Sand-Mining-Detection-and-Risk-Priortization\metadata\features_v2.csv"))
    ap.add_argument("--out-dir", type=Path, default=Path(r"C:\Users\upend\AI-Based-illegal-Sand-Mining-Detection-and-Risk-Priortization\metadata"))
    ap.add_argument("--annotation-dir", type=Path, default=Path(r"C:\New folder\annotation"))
    ap.add_argument("--docs-dir", type=Path, default=Path(r"C:\Users\upend\AI-Based-illegal-Sand-Mining-Detection-and-Risk-Priortization\docs"))
    ap.add_argument("--log", type=Path, default=Path(r"C:\Users\upend\AI-Based-illegal-Sand-Mining-Detection-and-Risk-Priortization\reports\logs\stage3_proposals.log"))
    args = ap.parse_args()
    logger = setup_logger(args.log)

    df = pd.read_csv(args.features)
    # Derive percentile cutoffs from 2023 chips only to avoid 2024-driven thresholding drift; document explicitly.
    ref = df[df["quarter"].str.startswith("2023")].copy()
    cutoffs = {
        "ndsi_mean_high_p75_2023": pct(ref["ndsi_mean"], 0.75),
        "ndsi_mean_low_p25_2023": pct(ref["ndsi_mean"], 0.25),
        "cmi_mean_high_p75_2023": pct(ref["cmi_mean"], 0.75),
        "cmi_mean_low_p25_2023": pct(ref["cmi_mean"], 0.25),
        "water_frac_high_p75_2023": pct(ref["water_frac"], 0.75),
        "ndvi_mean_high_p75_2023": pct(ref["ndvi_mean"], 0.75),
        "distance_mean_m_near_p25_2023": pct(ref["distance_mean_m"], 0.25),
    }

    def propose(r):
        reasons = []
        score = 0
        # High NDSI/CMI can indicate exposed/sandy/bare signatures; proposal only.
        if r["ndsi_mean"] >= cutoffs["ndsi_mean_high_p75_2023"]:
            score += 1; reasons.append(f"ndsi_mean>=p75_2023({cutoffs['ndsi_mean_high_p75_2023']:.4f})")
        if r["cmi_mean"] >= cutoffs["cmi_mean_high_p75_2023"]:
            score += 1; reasons.append(f"cmi_mean>=p75_2023({cutoffs['cmi_mean_high_p75_2023']:.4f})")
        if r["water_frac"] <= cutoffs["water_frac_high_p75_2023"]:
            reasons.append(f"water_frac<=p75_2023({cutoffs['water_frac_high_p75_2023']:.4f})")
        # Not-mining-like proposal cues
        nscore = 0
        if r["ndvi_mean"] >= cutoffs["ndvi_mean_high_p75_2023"]:
            nscore += 1; reasons.append(f"ndvi_mean>=p75_2023({cutoffs['ndvi_mean_high_p75_2023']:.4f})")
        if r["ndsi_mean"] <= cutoffs["ndsi_mean_low_p25_2023"]:
            nscore += 1; reasons.append(f"ndsi_mean<=p25_2023({cutoffs['ndsi_mean_low_p25_2023']:.4f})")
        if r["cmi_mean"] <= cutoffs["cmi_mean_low_p25_2023"]:
            nscore += 1; reasons.append(f"cmi_mean<=p25_2023({cutoffs['cmi_mean_low_p25_2023']:.4f})")

        if score >= 2 and nscore == 0:
            group = "PROPOSAL_MINING_LIKE"
            conf = "MEDIUM"
        elif nscore >= 2 and score == 0:
            group = "PROPOSAL_NOT_MINING_LIKE"
            conf = "MEDIUM"
        elif score >= 2 and nscore >= 1:
            group = "PROPOSAL_MIXED_REVIEW"
            conf = "LOW"
        elif nscore >= 2 and score >= 1:
            group = "PROPOSAL_MIXED_REVIEW"
            conf = "LOW"
        else:
            group = "PROPOSAL_UNSURE_REVIEW"
            conf = "LOW"
        return group, conf, "; ".join(reasons)

    out_rows = []
    for _, r in df.iterrows():
        group, conf, reasons = propose(r)
        out_rows.append({
            "chip_id": r["chip_id"],
            "quarter": r["quarter"],
            "transect_id": r["transect_id"],
            "proposed_group": group,
            "proposal_confidence": conf,
            "proposal_reasons": reasons,
            "proposal_status": "PROPOSAL_FOR_HUMAN_CONFIRMATION_ONLY",
            "ndvi_mean": r["ndvi_mean"],
            "ndwi_mean": r["ndwi_mean"],
            "ndbi_mean": r["ndbi_mean"],
            "ndsi_mean": r["ndsi_mean"],
            "cmi_mean": r["cmi_mean"],
            "water_frac": r["water_frac"],
            "distance_mean_m": r["distance_mean_m"],
        })

    out = pd.DataFrame(out_rows)
    args.out_dir.mkdir(parents=True, exist_ok=True)
    args.annotation_dir.mkdir(parents=True, exist_ok=True)
    args.docs_dir.mkdir(parents=True, exist_ok=True)
    prop_path = args.out_dir / "proposed_groups.csv"
    out.to_csv(prop_path, index=False)

    # Review queue: prioritize mixed/unsure and mining-like proposals; no labels written
    rq = out.copy()
    priority = {
        "PROPOSAL_MINING_LIKE": 1,
        "PROPOSAL_MIXED_REVIEW": 2,
        "PROPOSAL_UNSURE_REVIEW": 3,
        "PROPOSAL_NOT_MINING_LIKE": 4,
    }
    rq["review_priority"] = rq["proposed_group"].map(priority).fillna(9).astype(int)
    rq = rq.sort_values(["review_priority", "quarter", "transect_id"])
    rq["human_decision"] = ""
    rq["human_notes"] = ""
    rq_path = args.annotation_dir / "review_queue.csv"
    rq.to_csv(rq_path, index=False)

    rules_path = args.docs_dir / "proposal_rules.md"
    lines = [
        "# Stage 3 - Proposal Rules (PROPOSALS ONLY)",
        "",
        "**No final labels generated.** Feature-based groups are PROPOSALS for human confirmation only.",
        "Do not copy `proposed_group` into `verified_labels.csv` or any final label field without human review.",
        "",
        "## Percentile cutoffs (derived from 2023 chips only; 2024 excluded from cutoff derivation)",
        "",
        "| Cutoff | Value |",
        "|---|---:|",
    ]
    for k,v in cutoffs.items():
        lines.append(f"| {k} | {v:.6f} |")
    lines += [
        "",
        "## Proposal logic",
        "- `PROPOSAL_MINING_LIKE`: ndsi_mean >= p75_2023 AND cmi_mean >= p75_2023 AND no not-mining cues.",
        "- `PROPOSAL_NOT_MINING_LIKE`: >=2 not-mining cues (ndvi_mean>=p75_2023, ndsi_mean<=p25_2023, cmi_mean<=p25_2023) AND no mining-like score.",
        "- `PROPOSAL_MIXED_REVIEW`: mining-like and not-mining cues conflict.",
        "- `PROPOSAL_UNSURE_REVIEW`: insufficient/ambiguous cues.",
        "",
        "## Outputs",
        "- `metadata/proposed_groups.csv`",
        "- `annotation/review_queue.csv` (human_decision/human_notes blank)",
        "",
        "## Caveats",
        "- Proposals are heuristic, percentile-based, and not ground truth.",
        "- 2024 chips receive proposals using 2023-derived cutoffs; this is for review prioritization only, not model/threshold selection.",
    ]
    rules_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    summary = {
        "rows": int(len(out)),
        "cutoffs_2023": cutoffs,
        "group_counts": out["proposed_group"].value_counts().to_dict(),
        "status": "PROPOSALS_ONLY",
    }
    (args.out_dir / "proposed_groups_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    logger.info("wrote %s", prop_path)
    logger.info("wrote %s", rq_path)
    logger.info("wrote %s", rules_path)
    logger.info("groups: %s", summary["group_counts"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
