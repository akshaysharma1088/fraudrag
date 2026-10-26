"""Independent scientific re-evaluation of executed Neo4j/Chroma/GPT pilot.

No inference calls. Recomputes all confusion matrices from raw per-case
predictions, checks cited evidence against actually retrieved source manifests,
audits historical timestamps, and adds group-paired bootstrap uncertainty.
Missing or invalid predictions count as errors rather than being dropped.
"""
import argparse
import csv
import hashlib
import json
import math
import random
from collections import Counter
from pathlib import Path

MODES=("document_only","chroma_only","neo4j_only","integrated")
SEED=1047

def records(path):
    with Path(path).open(newline="",encoding="utf8") as f:
        return list(csv.DictReader(f))

def score(cases,by_pair,mode):
    tp=fp=tn=fn=abstain=0
    latency=[]
    for cid,row in cases.items():
        p=by_pair.get((cid,mode))
        answer=p["prediction"] if p else "uncertain"
        y=int(row["fraud_label"])
        if answer not in ("fraud","legitimate"):
            abstain+=1
            if y: fn+=1
            else: fp+=1
        elif answer=="fraud":
            if y: tp+=1
            else: fp+=1
        elif y: fn+=1
        else: tn+=1
        if p and p.get("elapsed_seconds"):
            latency.append(float(p["elapsed_seconds"]))
    precision=tp/(tp+fp) if tp+fp else 0
    recall=tp/(tp+fn) if tp+fn else 0
    latency.sort()
    return {"n":len(cases),"tp":tp,"tn":tn,"fp":fp,"fn":fn,"abstain":abstain,
            "accuracy":(tp+tn)/len(cases),
            "precision":precision,"recall":recall,
            "f1":2*precision*recall/(precision+recall) if precision+recall else 0,
            "p50_api_seconds":latency[len(latency)//2] if latency else None,
            "p95_api_seconds":latency[math.ceil(.95*len(latency))-1] if latency else None}

def correctness(label,response):
    if response not in ("fraud","legitimate"):
        return 0
    return int((response=="fraud")==bool(int(label)))

def paired_accuracy(cases,by_pair,a="integrated",b="document_only",replicates=2000):
    rng=random.Random(SEED)
    pairs=[]
    for cid,row in sorted(cases.items()):
        oa=by_pair.get((cid,a))
        ob=by_pair.get((cid,b))
        pairs.append((
            correctness(row["fraud_label"],oa["prediction"] if oa else "uncertain"),
            correctness(row["fraud_label"],ob["prediction"] if ob else "uncertain")
        ))
    diff=sum(x-y for x,y in pairs)/len(pairs)
    draws=[]
    for _ in range(replicates):
        sample=[pairs[rng.randrange(len(pairs))] for _ in pairs]
        draws.append(sum(x-y for x,y in sample)/len(sample))
    draws.sort()
    return {"comparison":f"{a} minus {b}","metric":"paired case accuracy",
            "observed_difference":diff,
            "exploratory_percentile_95_interval":[draws[int(.025*(replicates-1))],
                                                   draws[int(.975*(replicates-1))]],
            "replicates":replicates,"seed":SEED,
            "not_population_validity":True}

def audit(folder):
    folder=Path(folder)
    test=records(folder/"held_out_cases.csv")
    predictions=records(folder/"integrated_predictions.csv")
    logged=json.loads((folder/"integrated_metrics.json").read_text())
    cases={r["case_id"]:r for r in test}
    if len(cases)!=28 or len(set(r["customer_group"] for r in test))!=28:
        raise ValueError("Expected 28 unique customer-disjoint cases")
    by_pair={}
    violations=[]
    raw_tokens=0
    for p in predictions:
        key=(p["case_id"],p["mode"])
        if key in by_pair or key[0] not in cases or key[1] not in MODES:
            raise ValueError("Duplicate or out-of-protocol prediction")
        by_pair[key]=p
        if p["customer_group"]!=cases[p["case_id"]]["customer_group"]:
            raise ValueError("Customer-group mismatch")
        allowed=set(json.loads(p["allowed_evidence_ids"]))
        requested=json.loads(p["evidence_ids"])
        retrieved=json.loads(p["retrieval_provenance"])
        for source in retrieved:
            if source["source_id"] not in allowed:
                raise ValueError("Evidence not in retrieval manifest")
            if not source["recorded_at"]<cases[p["case_id"]]["submission_date"]:
                raise ValueError("Future evidence used")
            if source["provider"] not in ("neo4j","chroma"):
                raise ValueError("Unexpected evidence backend")
            if p["mode"]=="document_only" or (
                p["mode"]=="neo4j_only" and source["provider"]!="neo4j") or (
                p["mode"]=="chroma_only" and source["provider"]!="chroma"):
                raise ValueError("Context contaminated across protocol arms")
        if set(requested)-allowed:
            violations.append({"case":p["case_id"],"mode":p["mode"],
                               "unsupported_ids":sorted(set(requested)-allowed)})
        if p["mode"]=="document_only" and allowed:
            raise ValueError("Document-only arm received evidence")
        raw_tokens+=int(p["input_tokens"] or 0)+int(p["output_tokens"] or 0)
    expected={(cid,mode) for cid in cases for mode in MODES}
    missing=sorted(expected-set(by_pair))
    stats={m:score(cases,by_pair,m) for m in MODES}
    for m in MODES:
        historical=logged["results"][m]
        for field in ("tp","tn","fp","fn","abstain"):
            if stats[m][field]!=historical[field]:
                raise ValueError(f"Independent audit mismatch: {m}:{field}")
    output={
        "source":"Independent audit of actual executed Neo4j+Chroma+GPT research pilot",
        "study_is_synthetic_only":True,
        "n_unique_customers":len(cases),
        "planned_pair_count":len(expected),
        "observed_pair_count":len(by_pair),
        "missing_pairs":missing,
        "total_reported_tokens":raw_tokens,
        "unsupported_evidence_citation_count":len(violations),
        "unsupported_citation_details":violations,
        "per_condition":stats,
        "paired_bootstrap":paired_accuracy(cases,by_pair),
        "real_world_fraud_validity":False,
        "retrieval_note":"Provenance compared against source IDs returned by real Neo4j and ChromaDB queries. Their source records are still synthetically generated.",
        "no_performance_superiority_over_full_ledger_claim":True
    }
    (folder/"integrated_independent_audit.json").write_text(json.dumps(output,indent=2)+"\n")
    print(json.dumps(output,indent=2))
    return output

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--folder",default="artifacts/fraudrag_v2_integrated")
    a=p.parse_args()
    audit(a.folder)

if __name__=="__main__":
    main()
