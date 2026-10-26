"""Independent post-run audit for the 28-case GPT synthetic-doc experiment.

Reads saved held-out cases and raw per-condition GPT outputs. Recomputes binary
metrics and paired uncertainty. No LLM calls; no use of hard-coded scores.
"""
import argparse
import csv
import json
import math
import random
from collections import Counter, defaultdict
from pathlib import Path

MODES=("gpt_only","vector_only","graph_only","hybrid")
SEED=42

def read_csv(path):
    with Path(path).open(newline="",encoding="utf8") as f:
        return list(csv.DictReader(f))

def verify(cases,predictions):
    cases_by_id={r["case_id"]:r for r in cases}
    if len(cases_by_id)!=len(cases):
        raise ValueError("Duplicate held-out case IDs")
    groups=[r["customer_group"] for r in cases]
    if len(groups)!=len(set(groups)):
        raise ValueError("The held-out design must have one case per customer")
    keylist=[(r["case_id"],r["mode"]) for r in predictions]
    if len(keylist)!=len(set(keylist)):
        raise ValueError("Duplicate model predictions for case/mode")
    if any(m not in MODES or i not in cases_by_id for i,m in keylist):
        raise ValueError("Prediction not in the fixed evaluation protocol")
    if any(not bool(r["all_citations_known"].lower()=="true") for r in predictions):
        raise ValueError("Model cited source IDs absent from supplied context")
    return cases_by_id

def outcome(y,p):
    if p not in ("fraud","legitimate"):
        return False
    return (p=="fraud")==bool(int(y))

def score(cases_by_id,predictions,mode):
    pred={r["case_id"]:r for r in predictions if r["mode"]==mode}
    n=len(cases_by_id)
    tp=fp=tn=fn=abstain=0
    delays=[]
    for cid,row in cases_by_id.items():
        p=pred.get(cid)
        label=p["predicted"] if p else "uncertain"
        truth=int(row["fraud_label"])
        if label not in ("fraud","legitimate"):
            abstain+=1
            if truth: fn+=1
            else: fp+=1
        elif label=="fraud":
            if truth: tp+=1
            else: fp+=1
        elif truth: fn+=1
        else: tn+=1
        if p and p.get("latency_s"):
            delays.append(float(p["latency_s"]))
    precision=tp/(tp+fp) if tp+fp else 0.
    recall=tp/(tp+fn) if tp+fn else 0.
    lat=sorted(delays)
    return {"n":n,"tp":tp,"fp":fp,"tn":tn,"fn":fn,"abstain":abstain,
            "accuracy":(tp+tn)/n if n else 0,
            "precision":precision,"recall":recall,
            "f1":2*precision*recall/(precision+recall) if precision+recall else 0,
            "latency_p50_seconds":lat[len(lat)//2] if lat else None,
            "latency_p95_seconds":lat[math.ceil(0.95*len(lat))-1] if lat else None}

def paired_bootstrap(cases_by_id,predictions,mode_a="hybrid",mode_b="gpt_only",
                     repeats=2000,seed=SEED):
    # Resample held-out customer groups, not individual identical statement variants.
    by={(r["case_id"],r["mode"]):r for r in predictions}
    ids=sorted(cases_by_id)
    rng=random.Random(seed)
    observed=[]
    for cid in ids:
        y=cases_by_id[cid]["fraud_label"]
        a=by.get((cid,mode_a))
        b=by.get((cid,mode_b))
        observed.append((
            int(outcome(y,a["predicted"]) if a else False),
            int(outcome(y,b["predicted"]) if b else False)))
    def delta(values):
        return sum(a-b for a,b in values)/len(values)
    observed_delta=delta(observed)
    distribution=[]
    for _ in range(repeats):
        subsample=[observed[rng.randrange(len(observed))] for _ in observed]
        distribution.append(delta(subsample))
    distribution.sort()
    return {"comparison":f"{mode_a} vs {mode_b}",
            "metric":"paired proportion correctly classified including abstentions as errors",
            "observed_difference":observed_delta,
            "bootstrap_95_percentile_interval": [
                distribution[int(0.025*(repeats-1))],
                distribution[int(0.975*(repeats-1))]],
            "repeats":repeats,"seed":seed,
            "exploratory_not_inferential_confirmation":True}

def run(folder):
    folder=Path(folder)
    cases=read_csv(folder/"held_out_cases.csv")
    preds=read_csv(folder/"gpt_predictions.csv")
    by=verify(cases,preds)
    stats={mode:score(by,preds,mode) for mode in MODES}
    per_type={}
    for mode in MODES:
        pred={(r["case_id"],r["mode"]):r for r in preds}
        per_type[mode]={}
        for typ in sorted(set(r["tamper_type"] for r in cases)):
            subset=[r for r in cases if r["tamper_type"]==typ]
            per_type[mode][typ]={
                "n":len(subset),
                "correct":sum(int(outcome(r["fraud_label"],pred.get((r["case_id"],mode),{}).get("predicted")))
                              for r in subset)
            }
    report={"source":"executed real GPT calls on entirely synthetic documents",
            "not_legacy_fraudrag_2400":True,
            "all_cases_same_across_modes":True,
            "data_cases":len(cases),
            "mode_scores":stats,"per_type":per_type,
            "paired_uncertainty":paired_bootstrap(by,preds),
            "limitations":["n=28 is exploratory","full same-period ledger oracle",
                           "synthetic case prevalence 71.4%","no real document scans",
                           "graph reference serialized in prompt, not Neo4j inference",
                           "historical vector TF-IDF, not ChromaDB"]}
    output=folder/"independent_post_run_audit.json"
    output.write_text(json.dumps(report,indent=2)+"\n",encoding="utf8")
    print(json.dumps(report,indent=2))
    return report

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--folder",default="artifacts/fraudrag_v2_gpt")
    args=p.parse_args()
    run(args.folder)

if __name__=="__main__":
    main()
