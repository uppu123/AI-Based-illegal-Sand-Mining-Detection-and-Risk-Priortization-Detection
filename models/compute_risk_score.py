# -*- coding: utf-8 -*-
"""AHP-weighted risk score per river-km segment (transect).

IMPORTANT: the weights below are PROPOSED and still require the user's sign-off.
The score is a prioritisation index, not a probability and not an 'accuracy'.
Validation is by rank against known hotspots, never by a claimed risk accuracy.

Input CSV must contain one row per transect with these factor columns:
    detection    mining-mask intensity (e.g. mean positive fraction)
    persistence  fraction of quarters with detected extraction
    morphology   morphological change magnitude
    access       distance to the river centreline (metres; lower = riskier)
    vegetation   vegetation-loss magnitude

Each factor is min-max scaled to 0-1 (access is inverted before scaling).
"""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import numpy as np
from scipy.stats import spearmanr

# Proposed AHP weights - pending user approval.
WEIGHTS = {
    "detection": 0.30,
    "persistence": 0.25,
    "morphology": 0.20,
    "access": 0.15,
    "vegetation": 0.10,
}
FACTORS = list(WEIGHTS)


def scale(values: np.ndarray, invert: bool = False) -> np.ndarray:
    v = values.astype(float)
    if np.allclose(v, v[0]):
        return np.zeros_like(v)
    if invert:
        v = -v
    lo, hi = float(np.nanmin(v)), float(np.nanmax(v))
    return (v - lo) / (hi - lo)


def tier(score: float) -> str:
    if score >= 70:
        return "High"
    if score >= 40:
        return "Medium"
    return "Low"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--features", required=True, help="CSV with transect_id + 5 factor columns")
    ap.add_argument("--out", required=True, help="output CSV path")
    ap.add_argument("--hotspots", default="", help="comma-separated known hotspot transect IDs")
    ap.add_argument("--weights", default="", help="optional JSON override of the 5 weights")
    args = ap.parse_args()

    weights = dict(WEIGHTS)
    if args.weights:
        weights.update(json.loads(Path(args.weights).read_text(encoding="utf-8")))
    assert abs(sum(weights.values()) - 1.0) < 1e-6, "weights must sum to 1"

    with Path(args.features).open(encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    missing = [c for c in FACTORS if c not in rows[0]]
    if missing:
        raise SystemExit("missing factor columns: " + ", ".join(missing))

    scaled = {}
    for c in FACTORS:
        scaled[c] = scale(np.array([float(r[c]) for r in rows]),
                          invert=(c == "access"))

    out_rows = []
    for i, r in enumerate(rows):
        score = 100.0 * sum(weights[c] * scaled[c][i] for c in FACTORS)
        out_rows.append({
            "transect_id": r["transect_id"],
            **{c: round(float(r[c]), 4) for c in FACTORS},
            "risk_score": round(score, 2),
            "tier": tier(score),
            "rank": 0,
        })
    out_rows.sort(key=lambda x: -x["risk_score"])
    for i, r in enumerate(out_rows, 1):
        r["rank"] = i

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["transect_id", *FACTORS,
                                          "risk_score", "tier", "rank"])
        w.writeheader()
        w.writerows(out_rows)

    report = {
        "weights": weights,
        "weights_status": "PROPOSED - pending user approval",
        "n_segments": len(out_rows),
        "tiers": {t: sum(r["tier"] == t for r in out_rows)
                  for t in ("High", "Medium", "Low")},
        "validation": "rank only; no risk accuracy claim",
    }
    if args.hotspots:
        ids = {x.strip() for x in args.hotspots.split(",") if x.strip()}
        ranks = np.array([r["rank"] for r in out_rows if r["transect_id"] in ids])
        if len(ranks) >= 2:
            ideal = np.arange(1, len(ranks) + 1)
            rho, p = spearmanr(ideal, np.sort(ranks))
            report["hotspot_rank_check"] = {
                "hotspots_found": len(ranks),
                "spearman_rho": round(float(rho), 4) if np.isfinite(rho) else None,
                "p_value": round(float(p), 4) if np.isfinite(p) else None,
            }
        else:
            report["hotspot_rank_check"] = {"error": "need >=2 matching hotspots"}
    (out.with_suffix(".json")).write_text(
        json.dumps(report, indent=2), encoding="utf-8")
    print("risk scores:", out)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
