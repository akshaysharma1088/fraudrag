"""Reproducible FraudRAG-v2 baselines over synthetically modified statements.

No LLM dependency. This runner computes rules-only, *authoritative-ledger*
deterministic comparison, and a temporal TF-IDF retrieval diagnostic.
It is a research feasibility evaluation, NOT real-world fraud performance.
"""
from __future__ import annotations
import argparse
import csv
import json
import random
import re
from collections import defaultdict
from datetime import date
from decimal import Decimal
from pathlib import Path

from fraudrag_v2 import FRAUD_TYPES, TYPES, export

def load_rows(path):
    with Path(path).open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    for r in rows:
        r["fraud_label"] = int(r["fraud_label"])
        r["graph_reference"] = json.loads(r["graph_reference_json"])
    return rows

def balanced_holdout(rows, n_per_type=4, seed=57):
    """Reserve 25% of customers as held-out; at most one case per customer.

    Each type receives disjoint customers. All selection is precommitted,
    without inspecting case outcomes or model predictions.
    """
    groups = sorted({r["customer_group"] for r in rows})
    rng = random.Random(seed)
    rng.shuffle(groups)
    n_test_groups = max(35, len(groups)//4)
    reserved = set(groups[:n_test_groups])
    by_type = defaultdict(list)
    for r in rows:
        if r["customer_group"] in reserved:
            by_type[r["tamper_type"]].append(r)
    chosen = []
    seen = set()
    for ty in TYPES:
        options = sorted(by_type[ty], key=lambda r:r["case_id"])
        rng.shuffle(options)
        current = [r for r in options if r["customer_group"] not in seen][:n_per_type]
        if len(current) < n_per_type:
            raise ValueError("Not enough distinct held-out customers for each fraud type")
        chosen.extend(current)
        seen.update(r["customer_group"] for r in current)
    chosen.sort(key=lambda r:r["case_id"])
    train = [r for r in rows if r["customer_group"] not in reserved]
    assert set(r["customer_group"] for r in train).isdisjoint(seen)
    assert len(chosen) == n_per_type * len(TYPES)
    return train, chosen

def parse_statement(s):
    start = re.search(r"Period: (\d{4}-\d\d-\d\d) to (\d{4}-\d\d-\d\d)", s)
    op = re.search(r"Opening balance: (\d+\.\d\d)", s)
    cl = re.search(r"Closing balance: (\d+\.\d\d)", s)
    inst = re.search(r"Institution: ([^\n]+)", s)
    acc = re.search(r"Account: (\d+)", s)
    lines = re.findall(
        r"(\d{4}-\d\d-\d\d) \| ([TF]\d{5}(?:-\d+)?) \| (DEBIT|CREDIT) \| (\d+\.\d\d) \| ([^\n]+)",
        s
    )
    if not all((start,op,cl,inst,acc)) or not lines:
        return None
    tx = [{"day":a, "id":b, "kind":c.lower(), "amount":Decimal(d),
           "description":e} for a,b,c,d,e in lines]
    return {
        "start": date.fromisoformat(start.group(1)), "end": date.fromisoformat(start.group(2)),
        "opening":Decimal(op.group(1)), "closing":Decimal(cl.group(1)),
        "account":acc.group(1), "institution":inst.group(1).strip(),
        "transactions":tx
    }

def rule_result(row):
    p = parse_statement(row["statement_text"])
    if p is None:
        return {"prediction": None, "basis":"parser_failed"}
    computed = p["opening"] + sum((t["amount"] if t["kind"]=="credit" else -t["amount"]
                                   for t in p["transactions"]), Decimal(0))
    mismatch = abs(computed-p["closing"]) >= Decimal("0.50")
    invalid_dates = any(not p["start"] <= date.fromisoformat(t["day"]) <= p["end"]
                        for t in p["transactions"])
    return {"prediction": int(mismatch or invalid_dates),
            "basis": "balance/date rules", "balance_mismatch":mismatch,
            "invalid_dates": invalid_dates}

def authoritative_comparison(row):
    """Strong comparison baseline with exactly same reference as graph-enhanced LLM.

    This should remain in paper: if simple exact matching wins, do not
    misattribute its gains to LLM reasoning or novel Graph-RAG.
    """
    p = parse_statement(row["statement_text"])
    if p is None:
        return {"prediction":None,"basis":"parser_failed"}
    ref=row.get("graph_reference") or json.loads(row["graph_reference_json"])
    ref_tx={t["id"]:(Decimal(t["amount"]),t["direction"],t["date"])
            for t in ref["reference_transactions"]}
    mismatch = (
        p["institution"] != ref["institution"] or p["account"] != ref["account"] or
        p["closing"] != Decimal(ref["reference_closing_balance"]) or
        {t["id"]:(t["amount"],t["kind"],t["day"]) for t in p["transactions"]} != ref_tx
    )
    return {"prediction":int(mismatch),"basis":"exact authoritative ledger comparison"}

def evaluate_binary(rows, predictions, name):
    """Do not silently remove failures: non-predictions count as incorrect."""
    if len(rows)!=len(predictions):
        raise ValueError("Number of predictions differs from rows")
    tp=tn=fp=fn=abstain=0
    for row,pred in zip(rows,predictions):
        y=row["fraud_label"]
        if pred is None:
            abstain += 1
            # missing output contributes an error without distorting precision
            if y: fn += 1
            else: fp += 1
        elif pred==1 and y==1: tp+=1
        elif pred==1 and y==0: fp+=1
        elif pred==0 and y==0: tn+=1
        else: fn+=1
    precision=tp/(tp+fp) if tp+fp else 0.
    recall=tp/(tp+fn) if tp+fn else 0.
    return {"name":name,"n":len(rows),"tp":tp,"tn":tn,"fp":fp,"fn":fn,
            "abstain":abstain,"accuracy":(tp+tn)/len(rows),
            "precision":precision,"recall":recall,
            "f1":2*precision*recall/(precision+recall) if precision+recall else 0.,
            "fraud_prevalence":sum(r["fraud_label"] for r in rows)/len(rows)}

def get_vector_context(row, historic_corpus, top_k=3):
    """TF-IDF over previous-period trusted records only. No current text or labels in index."""
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    corpus=[x["historical_vector_corpus_text"] for x in historic_corpus]
    vec=TfidfVectorizer(ngram_range=(1,2),sublinear_tf=True)
    matrix=vec.fit_transform(corpus)
    scores=cosine_similarity(vec.transform([row["statement_text"]]),matrix)[0]
    indices=sorted(range(len(scores)),key=lambda i:(-scores[i],historic_corpus[i]["customer_group"]))[:top_k]
    return [{"source_id":f"history://{historic_corpus[i]['customer_group']}",
             "recorded_before_submission": True,
             "text":corpus[i], "similarity":round(float(scores[i]),6)} for i in indices]

def export_results(output_dir, customers=120, n_per_type=4, seed=57):
    destination=Path(output_dir)
    destination.mkdir(parents=True,exist_ok=True)
    manifest=export(customers,20261026,str(destination))
    rows=load_rows(destination/"cases.csv")
    train,test=balanced_holdout(rows,n_per_type,seed)
    result={
        "scope":"controlled synthetic edits to machine-readable financial statements ONLY",
        "real_bank_fraud_evidence":False,"not_original_fraudrag_2400":True,
        "benchmark":manifest,"split_seed":seed,"n_train":len(train),
        "n_held_out_evaluated":len(test),
        "n_distinct_evaluation_customers":len(set(r["customer_group"] for r in test)),
        "rules":evaluate_binary(test,[rule_result(r)["prediction"] for r in test],"rules_only"),
        "reference_matching":evaluate_binary(test,[authoritative_comparison(r)["prediction"]
                                                    for r in test],"exact_authoritative_matching"),
        "limitations":["synthetic banks, customers, records, manipulations",
                      "authoritative ledger is an unusually strong oracle",
                      "text-native documents without OCR, layout or signatures",
                      "customer-grouped split but small test subset",
                      "known edit labels are not investigator-adjudicated fraud"],
    }
    with (destination/"held_out_cases.csv").open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=list(test[0]))
        w.writeheader()
        w.writerows(test)
    (destination/"baseline_results.json").write_text(json.dumps(result,indent=2)+"\n")
    return result

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--out",default="artifacts/fraudrag_v2")
    p.add_argument("--customers",type=int,default=120)
    p.add_argument("--n-per-type",type=int,default=4)
    p.add_argument("--split-seed",type=int,default=57)
    a=p.parse_args()
    print(json.dumps(export_results(a.out,a.customers,a.n_per_type,a.split_seed),indent=2))

if __name__=="__main__":
    main()
