"""Deterministic, synthetic *unit-scale* fraud benchmark; not the historical FraudRAG-2400 study.

No model calls, no financial PII, and no invented AUC metrics. Records are generated
with known arithmetic labels to test the deterministic Silver-layer validator.
"""
import argparse
import csv
import json
import random
from pathlib import Path


def generate(n: int = 2400, seed: int = 2026):
    if n < 2:
        raise ValueError("n must be at least 2")
    rng = random.Random(seed)
    records = []
    for i in range(n):
        opening = rng.randint(10000, 500000) / 100
        credit = rng.randint(100, 50000) / 100
        debit = rng.randint(100, 50000) / 100
        fraud = int(i % 3 == 0)
        correct_closing = round(opening + credit - debit, 2)
        closing = round(correct_closing + (rng.choice([-1, 1]) * rng.randint(100, 10000) / 100 if fraud else 0), 2)
        records.append({
            "case_id": f"synthetic-{i:05d}",
            "group_id": f"entity-{i // 4:05d}",
            "opening_balance": f"{opening:.2f}",
            "total_credits": f"{credit:.2f}",
            "total_debits": f"{debit:.2f}",
            "closing_balance": f"{closing:.2f}",
            "label": fraud,
        })
    rng.shuffle(records)
    return records


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--n", type=int, default=2400)
    parser.add_argument("--seed", type=int, default=2026)
    parser.add_argument("--out", default="artifacts/synthetic_balance_cases.csv")
    args = parser.parse_args()
    rows = generate(args.n, args.seed)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    metadata = {"generator": "benchmark/generate_synthetic.py", "version": 1,
                "n": args.n, "seed": args.seed, "scope": "arithmetic manipulation ONLY",
                "not_original_study": True}
    out.with_suffix(".json").write_text(json.dumps(metadata, indent=2) + "\n")
    print(f"Wrote {len(rows)} explicitly synthetic cases to {out}")


if __name__ == "__main__":
    main()
