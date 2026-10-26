"""Evaluate deterministic balance inconsistencies from synthetic CSV.

Use group-disjoint evaluation for any fitted method. Here no training occurs.
This is a reproducible smoke benchmark, NOT validation of FraudRAG AUC=0.943.
"""
import argparse
import csv
import json
from decimal import Decimal
from pathlib import Path


def predict(row, tolerance=Decimal("0.50")):
    expected = Decimal(row["opening_balance"]) + Decimal(row["total_credits"]) - Decimal(row["total_debits"])
    return int(abs(expected - Decimal(row["closing_balance"])) >= tolerance)


def evaluate(rows):
    counts = {"tp": 0, "tn": 0, "fp": 0, "fn": 0}
    for row in rows:
        y, yhat = int(row["label"]), predict(row)
        counts[{(1, 1): "tp", (0, 0): "tn", (0, 1): "fp", (1, 0): "fn"}[(y, yhat)]] += 1
    tp, fp, fn, tn = (counts[k] for k in ("tp", "fp", "fn", "tn"))
    precision = tp / (tp + fp) if tp + fp else 0
    recall = tp / (tp + fn) if tp + fn else 0
    return {**counts, "precision": precision, "recall": recall,
            "f1": 2 * precision * recall / (precision + recall) if precision + recall else 0,
            "accuracy": (tp + tn) / len(rows) if rows else 0,
            "n": len(rows), "scope": "synthetic balance arithmetic only", "not_paper_results": True}


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--input", default="artifacts/synthetic_balance_cases.csv")
    p.add_argument("--out", default="artifacts/synthetic_balance_metrics.json")
    args = p.parse_args()
    with Path(args.input).open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    result = evaluate(rows)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
