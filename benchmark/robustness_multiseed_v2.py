"""Precommitted multi-seed, customer-disjoint synthetic robustness study.

This evaluates deterministic controls and incomplete-reference abstentions on
larger test sets. It does not constitute independent real financial data.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
import statistics
import sys
from pathlib import Path

from fraudrag_v2 import generate, TYPES
from evaluate_v2 import balanced_holdout, rule_result, authoritative_comparison, evaluate_binary
from incomplete_evidence_v2 import view_of_reference, score_partial

SEEDS=(57,61,83)
CUSTOMERS=700
PER_TYPE=25
CONDITIONS=("rules","complete_ledger","identity_only","partial_ledger","no_reference")

def evaluate():
    rows=generate(CUSTOMERS,20261026)
    results=[]
    raw=[]
    for seed in SEEDS:
        train,test=balanced_holdout(rows,PER_TYPE,seed)
        assert len(test)==len(TYPES)*PER_TYPE
        assert len({r["customer_group"] for r in test})==len(test)
        assert {r["customer_group"] for r in test}.isdisjoint(
            {r["customer_group"] for r in train})
        scores={}
        for condition in CONDITIONS:
            preds=[]
            for row in test:
                if condition=="rules":
                    pred=rule_result(row)["prediction"]
                elif condition=="complete_ledger":
                    pred=authoritative_comparison(row)["prediction"]
                else:
                    ref=json.loads(row["graph_reference_json"])
                    available=view_of_reference(ref,condition,int(row["customer_group"][1:])+17)
                    pred=score_partial(row,available)
                preds.append(pred)
                raw.append({"split_seed":seed,"case_id":row["case_id"],
                            "customer_group":row["customer_group"],
                            "type":row["tamper_type"],"label":row["fraud_label"],
                            "method":condition,"prediction":"ABSTAIN" if pred is None else pred})
            scores[condition]=evaluate_binary(test,preds,condition)
        results.append({"split_seed":seed,"test_n":len(test),"train_n":len(train),
                        "customer_disjoint":True,"scores":scores})
    summary={
        "task":"synthetic document manipulation, not real bank fraud",
        "generator_seed":20261026,"n_generated_cases":len(rows),
        "n_fictional_customers":CUSTOMERS,
        "holdout_per_type":PER_TYPE,"test_count_per_seed":PER_TYPE*len(TYPES),
        "split_seeds":list(SEEDS),
        "independent_real_labels":False,
        "repeated_customers_across_seeds_possible":True,
        "per_seed_results":results,
        "aggregate_descriptive":{
            method:{
                "accuracy_mean_across_seeds":statistics.mean(r["scores"][method]["accuracy"] for r in results),
                "f1_mean_across_seeds":statistics.mean(r["scores"][method]["f1"] for r in results),
                "abstentions_total":sum(r["scores"][method]["abstain"] for r in results)
            } for method in CONDITIONS
        },
        "note":"Synthetic generator designs an exact complete ledger. Performance is not representative of real fraud or incomplete institution records."
    }
    return summary,raw

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--out",default="artifacts/fraudrag_v2_multiseed")
    args=p.parse_args()
    result,raw=evaluate()
    out=Path(args.out)
    out.mkdir(parents=True,exist_ok=True)
    with (out/"predictions.csv").open("w",newline="",encoding="utf8") as f:
        writer=csv.DictWriter(f,fieldnames=list(raw[0]))
        writer.writeheader()
        writer.writerows(raw)
    result["predictions_sha256"]=hashlib.sha256((out/"predictions.csv").read_bytes()).hexdigest()
    (out/"results.json").write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps(result,indent=2))

if __name__=="__main__":
    main()
