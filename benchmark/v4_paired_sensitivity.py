"""Independent, read-only secondary analysis of frozen V4 synthetic acquisition traces.

This is a sensitivity analysis, not a new experiment, real-bank observation,
or proof of optimization novelty. Uses matched case ids across policies.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
from collections import defaultdict
from pathlib import Path

POLICIES = ("adaptive_dp", "prior_greedy")
BUDGETS = (3.0, 4.0, 5.0)
COUNTS = {"test": 720, "shift": 360}


def exact_mcnemar_p(dp_only: int, greedy_only: int) -> float:
    """Two-sided exact binomial discordance test under paired null."""
    n = dp_only + greedy_only
    if n == 0:
        return 1.0
    k = min(dp_only, greedy_only)
    return min(1.0, 2 * sum(math.comb(n, i) for i in range(k + 1)) / (2 ** n))


def load_pairs(path: Path, budget: float, *, expected_n: int) -> list[tuple[dict, dict]]:
    with path.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    mapping = defaultdict(dict)
    for r in rows:
        if float(r["budget"]) != budget:
            continue
        if r["policy"] not in POLICIES:
            continue
        key = r["case_id"]
        if r["policy"] in mapping[key]:
            raise ValueError("Repeated case and policy: " + key)
        mapping[key][r["policy"]] = r
    if len(mapping) != expected_n or any(set(pair) != set(POLICIES) for pair in mapping.values()):
        raise ValueError("Missing paired predictions or incorrect sample size")
    pairs = [(d["adaptive_dp"], d["prior_greedy"]) for _, d in sorted(mapping.items())]
    for dp, greedy in pairs:
        if dp["profile"] != greedy["profile"]:
            raise ValueError("Profile mismatch between paired methods")
        for r in (dp, greedy):
            if r["complete"] not in ("0", "1"):
                raise ValueError("Invalid completion indicator")
            if int(r["error_against_synthetic_source"]) != 0:
                raise ValueError("Unexpected synthetic-source contract error")
    return pairs


def summarize(pairs: list[tuple[dict, dict]]) -> dict:
    n = len(pairs)
    a = sum(int(d["complete"]) for d, _ in pairs)
    b = sum(int(g["complete"]) for _, g in pairs)
    only_a = sum(int(d["complete"]) == 1 and int(g["complete"]) == 0 for d, g in pairs)
    only_b = sum(int(d["complete"]) == 0 and int(g["complete"]) == 1 for d, g in pairs)
    both = [(d, g) for d, g in pairs if d["complete"] == g["complete"] == "1"]
    mean_delta = sum(float(d["cost_units"]) - float(g["cost_units"]) for d, g in pairs) / n
    by_profile = {}
    for profile in sorted({d["profile"] for d, _ in pairs}):
        subgroup = [(d, g) for d, g in pairs if d["profile"] == profile]
        by_profile[profile] = {
            "cases": len(subgroup),
            "dp_completed": sum(int(d["complete"]) for d, _ in subgroup),
            "greedy_completed": sum(int(g["complete"]) for _, g in subgroup),
            "discordant_dp_only": sum(d["complete"] == "1" and g["complete"] == "0" for d, g in subgroup),
            "discordant_greedy_only": sum(d["complete"] == "0" and g["complete"] == "1" for d, g in subgroup),
        }
    return {
        "n_simulated_groups": n,
        "dp_coverage": round(a / n, 8),
        "greedy_coverage": round(b / n, 8),
        "coverage_difference_dp_minus_greedy": round((a - b) / n, 8),
        "dp_only_completed": only_a,
        "greedy_only_completed": only_b,
        "both_completed": len(both),
        "neither_completed": n - only_a - only_b - len(both),
        "exploratory_exact_mcnemar_two_sided_p_uncorrected": exact_mcnemar_p(only_a, only_b),
        "mean_cost_difference_all_cases_synthetic_units": round(mean_delta, 8),
        "mean_cost_difference_when_both_complete_synthetic_units": (
            round(sum(float(d["cost_units"]) - float(g["cost_units"]) for d, g in both) / len(both), 8)
            if both else None
        ),
        "per_simulated_profile": by_profile,
    }


def analyze(folder: Path) -> dict:
    out = {
        "analysis_kind": "post_hoc_secondary_sensitivity_not_preregistered_primary_test",
        "method": "paired_exact_McNemar_with_unadjusted_exploratory_p_values",
        "generalization": "fictional sources, fictional costs, six shared simulated families; no independent institutions",
        "interpretation": "P-values exploratory over three budgets and two splits; do not infer real fraud accuracy.",
        "splits": {},
    }
    for split, expected_n in COUNTS.items():
        out["splits"][split] = {}
        for budget in BUDGETS:
            pairs = load_pairs(folder / f"{split}_predictions.csv", budget, expected_n=expected_n)
            out["splits"][split][f"{budget:.1f}"] = summarize(pairs)
    return out


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--folder", type=Path, default=Path("research/verified_runs/fraudrag_v4_adaptive_20261026"))
    p.add_argument("--out", type=Path, default=Path("artifacts/v4_secondary_analysis.json"))
    a = p.parse_args()
    report = analyze(a.folder)
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"written": str(a.out), "test_budget_4": report["splits"]["test"]["4.0"],
                      "shift_budget_4": report["splits"]["shift"]["4.0"]}, indent=2))


if __name__ == "__main__":
    main()
