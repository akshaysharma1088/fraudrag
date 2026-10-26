"""Synthetic missing-reference stress test; no LLM, no real customer data.

Shows how much the complete bank-side oracle influences the baseline.
Missing evidence cannot be treated as proof that a submitted statement is
legitimate. The synthetic bank record availability model is hypothetical.
"""
from __future__ import annotations
import argparse
import csv
import json
import random
from decimal import Decimal
from pathlib import Path

from evaluate_v2 import export_results, load_rows, parse_statement, evaluate_binary

CONDITIONS=("complete","identity_only","partial_ledger","no_reference")

def view_of_reference(ref,condition,seed):
    if condition=="complete":
        return dict(ref)
    if condition=="no_reference":
        return None
    if condition=="identity_only":
        return {"source":ref["source"],"institution":ref["institution"],
                "account":ref["account"],"recorded_at":ref["recorded_at"]}
    if condition=="partial_ledger":
        rng=random.Random(seed)
        known=[dict(x) for x in rng.sample(ref["reference_transactions"],2)]
        # No closing or complete transaction list: never infer all facts match.
        return {"source":ref["source"],"institution":ref["institution"],
                "account":ref["account"],"recorded_at":ref["recorded_at"],
                "reference_transactions":known}
    raise ValueError(condition)

def score_partial(row,ref_view):
    if ref_view is None:
        return None
    p=parse_statement(row["statement_text"])
    if p is None:
        return None
    if "institution" in ref_view and p["institution"]!=ref_view["institution"]:
        return 1
    if "account" in ref_view and p["account"]!=ref_view["account"]:
        return 1
    if ("reference_closing_balance" in ref_view and
        p["closing"]!=Decimal(ref_view["reference_closing_balance"])):
        return 1
    by={t["id"]:t for t in p["transactions"]}
    for rt in ref_view.get("reference_transactions",[]):
        t=by.get(rt["id"])
        if t is None or t["amount"]!=Decimal(rt["amount"]) or t["kind"]!=rt["direction"] or t["day"]!=rt["date"]:
            return 1
    if "reference_transactions" in ref_view and "reference_closing_balance" in ref_view:
        if len(by)!=len(ref_view["reference_transactions"]):
            return 1
        return 0
    # A match against incomplete evidence cannot establish authenticity.
    return None

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--out",default="artifacts/fraudrag_v2_incomplete")
    args=p.parse_args()
    folder=Path(args.out)
    folder.mkdir(parents=True,exist_ok=True)
    export_results(str(folder),120,4,57)
    rows=load_rows(folder/"held_out_cases.csv")
    report={"task":"reliability when synthetic authoritative evidence is absent or partial",
            "n":len(rows),"synthetic_only":True,
            "conditions":{},"labels_not_used_in_evidence":True,
            "limitations":["missingness distribution is hypothetical",
                           "no real bank availability logs",
                           "no external validation",
                           "28 samples only","no LLM involved"]}
    records=[]
    for condition in CONDITIONS:
        preds=[]
        for row in rows:
            ref=row["graph_reference"]
            view=view_of_reference(ref,condition,seed=int(row["customer_group"][1:])+17)
            predicted=score_partial(row,view)
            preds.append(predicted)
            records.append({"case_id":row["case_id"],"type":row["tamper_type"],
                            "condition":condition,"truth":row["fraud_label"],
                            "predicted": "ABSTAIN" if predicted is None else predicted})
        report["conditions"][condition]=evaluate_binary(rows,preds,condition)
    (folder/"missing_reference_metrics.json").write_text(json.dumps(report,indent=2)+"\n")
    with (folder/"missing_reference_predictions.csv").open("w",newline="",encoding="utf8") as f:
        writer=csv.DictWriter(f,fieldnames=list(records[0]))
        writer.writeheader()
        writer.writerows(records)
    print(json.dumps(report,indent=2))


if __name__=="__main__":
    main()
