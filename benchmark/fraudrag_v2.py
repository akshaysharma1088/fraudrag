"""FraudRAG-v2: REPLACEMENT synthetic statement-verification benchmark.

Synthetic cases only. Not the lost FraudRAG-2400 data. Generated labels
describe known edits to otherwise consistent source statements, not adjudicated
real-world fraud. Historical and independently held reference information are
timed *before* the customer statement submission, never after it.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import random
from datetime import date, timedelta
from pathlib import Path

FRAUD_TYPES = ("balance", "amount", "date", "entity", "fabricated")
TYPES = ("legitimate", "hard_negative") + FRAUD_TYPES
FORMAT_STYLES = ("classic", "compact", "tabular")
INSTITUTIONS = ("Northfield Credit Union", "Harbor Community Bank", "Cedar Valley Bank", "Fairview Savings")
TERMS = ("Rent", "Payroll", "Groceries", "Utilities", "Insurance", "Transit", "Medical", "Refund")


def money(cents):
    return f"{cents / 100:.2f}"


def generate(n_customers=120, seed=20261026):
    if n_customers < 10:
        raise ValueError("Need at least ten independent customers")
    rng = random.Random(seed)
    records = []
    epoch = date(2026, 1, 1)
    # One customer can have multiple statements, all assigned to same split.
    for ci in range(n_customers):
        customer_id = f"C{ci:05d}"
        customer = f"Fictional Customer {ci:05d}"
        institution = INSTITUTIONS[ci % len(INSTITUTIONS)]
        account = f"{10000000 + ci}"
        opening_cents = rng.randint(300000, 2000000)
        day = epoch + timedelta(days=(ci % 150) + 45)
        period_start = day - timedelta(days=29)
        known_day = day - timedelta(days=1)
        txns = []
        for j in range(4):
            amount = rng.randint(2500, 140000)
            # Deliberately include mixed debit and credit, all directions explicit.
            direction = "credit" if j == 0 else "debit"
            txns.append({"id": f"T{ci:05d}-{j}", "day": (period_start + timedelta(days=2+j*6)).isoformat(),
                         "kind": direction, "cents": amount, "label": TERMS[(ci+j) % len(TERMS)]})
        correct_close = opening_cents + sum(t["cents"] * (1 if t["kind"] == "credit" else -1) for t in txns)
        if correct_close < 0:
            # Opening is always large enough under the chosen ranges, but assert.
            raise AssertionError("invalid source ledger balance")

        # These are *independent, bank-side* synthetic observations created
        # earlier than the customer's submitted document. Not output labels.
        bank_ref = {
            "institution": institution,
            "account": account,
            "recorded_at": known_day.isoformat(),
            "customer": customer,
            "reference_closing_balance": money(correct_close),
            "reference_transactions": [
                {"id": t["id"], "amount": money(t["cents"]), "direction": t["kind"],
                 "date": t["day"]} for t in txns
            ],
            "source": f"bank-ledger://{customer_id}/{known_day.isoformat()}",
            "relationship": "ACCOUNT_OWNED_BY_CUSTOMER"
        }
        historic = (
            f"Previous-period bank record, customer {customer}, account {account}, "
            f"institution {institution}. Verified relationship existed by {known_day.isoformat()}. "
            "This is not the submitted current-period statement."
        )
        for ti, kind in enumerate(TYPES):
            statement_id = f"S{ci:05d}-{ti}"
            style = FORMAT_STYLES[(ci+ti) % len(FORMAT_STYLES)]
            upload = {
                "customer": customer, "institution": institution, "account": account,
                "period_start": period_start.isoformat(), "period_end": day.isoformat(),
                "opening": opening_cents, "closing": correct_close,
                "transactions": [dict(t) for t in txns]
            }
            if kind == "balance":
                upload["closing"] += rng.choice([-1, 1]) * rng.randint(15000, 70000)
            elif kind == "amount":
                upload["transactions"][rng.randint(0,3)]["cents"] += 30000
                # Deliberately make a *numerically balanced* falsification,
                # so a basic arithmetic check does not trivially solve it.
                upload["closing"] = upload["opening"] + sum(
                    t["cents"] * (1 if t["kind"] == "credit" else -1)
                    for t in upload["transactions"]
                )
            elif kind == "date":
                upload["transactions"][2]["day"] = (day + timedelta(days=7)).isoformat()
            elif kind == "entity":
                upload["account"] = f"{80000000+ci}"
            elif kind == "fabricated":
                extra = {"id": f"F{ci:05d}", "day": (day - timedelta(days=1)).isoformat(),
                         "kind": "debit", "cents": 12000, "label": "Synthetic adjustment"}
                upload["transactions"].append(extra)
                upload["closing"] -= extra["cents"]
            elif kind == "hard_negative":
                # Genuine unusual-but-valid large credit, recorded in the
                # authoritative reference for this case too. Generate
                # additional fact independently from label; avoid false alarms.
                # Use a benign format change instead of changing bank truth.
                upload["transactions"][0]["label"] = "Annual adjustment (verified)"
            row_lines = [
                f"{'ACCOUNT STATEMENT' if style != 'compact' else 'Account activity'}",
                f"Institution: {upload['institution']}",
                f"Customer: {upload['customer']}",
                f"Account: {upload['account']}",
                f"Period: {upload['period_start']} to {upload['period_end']}",
                f"Opening balance: {money(upload['opening'])}",
                "Transactions:",
            ]
            for t in upload["transactions"]:
                row_lines.append(
                    f"{t['day']} | {t['id']} | {t['kind'].upper()} | "
                    f"{money(t['cents'])} | {t['label']}"
                )
            row_lines.append(f"Closing balance: {money(upload['closing'])}")
            submitted = "\n".join(row_lines)
            records.append({
                "case_id": statement_id, "customer_group": customer_id,
                "submission_date": (day + timedelta(days=1)).isoformat(),
                "tamper_type": kind, "fraud_label": int(kind in FRAUD_TYPES),
                "statement_text": submitted,
                "historical_vector_corpus_text": historic,
                "graph_reference_json": json.dumps(bank_ref, sort_keys=True),
                "format_style": style,
                "reference_recorded_before_submission": True,
                "ground_truth_rule": "controlled synthetic edit" if kind in FRAUD_TYPES else "synthetic unchanged",
            })
    rng.shuffle(records)
    return records


def export(n_customers=120, seed=20261026, out="artifacts/fraudrag_v2"):
    rows = generate(n_customers, seed)
    destination = Path(out)
    destination.mkdir(parents=True, exist_ok=True)
    csv_path = destination / "cases.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    digest = hashlib.sha256(csv_path.read_bytes()).hexdigest()
    manifest = {
        "title": "FraudRAG-v2 synthetic statement inconsistency feasibility benchmark",
        "not_original_fraudrag_2400": True, "not_real_statement_fraud": True,
        "seed": seed, "customer_count": n_customers, "total_cases": len(rows),
        "type_counts": {k: sum(r["tamper_type"] == k for r in rows) for k in TYPES},
        "csv_sha256": digest,
        "reference_timing": "recorded strictly before statement submission",
        "leakage_control": "split by customer group; never index held-out customer statements",
        "synthetic_oracle_warning": "Graph reference includes authoritative same-period bank ledger; graph-assisted comparisons may be artificially easier than real-world fraud investigation.",
        "missing_dimensions": ["scans", "OCR errors", "real formatting", "real fraud adjudications",
                               "unknown-bank ledger gaps", "financial institution diversity"]
    }
    (destination / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    return manifest


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--customers", type=int, default=120)
    p.add_argument("--seed", type=int, default=20261026)
    p.add_argument("--out", default="artifacts/fraudrag_v2")
    args = p.parse_args()
    print(json.dumps(export(args.customers, args.seed, args.out), indent=2))


if __name__ == "__main__":
    main()
