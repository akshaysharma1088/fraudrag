"""Paired GPT experiment over FraudRAG-v2 synthetic statement cases.

Four GPT configurations: statement-only, trusted historic vector text,
bank-ledger graph context, and both contexts.
Non-LLM controls: statement arithmetic/date rules; exact authoritative ledger
comparison. All inferences use identical held-out case IDs and source evidence.
DO NOT call this 'validated real-world fraud detection' or a Neo4j benchmark:
graph context is a provenance-preserving serialized reference for this pilot.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
import os
import sys
import time
import urllib.error
import urllib.request
from datetime import date
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"benchmark"))
from evaluate_v2 import export_results, load_rows, balanced_holdout, rule_result, \
    authoritative_comparison, evaluate_binary, get_vector_context

MODEL = "gpt-6.1-sol"
MODES = ("gpt_only", "vector_only", "graph_only", "hybrid")
# As verified for preceding 2026-10-26 pilot; account charges may differ.
INPUT_PRICE_PER_M = 2.0
OUTPUT_PRICE_PER_M = 10.0
OUTPUT_TOKENS_LIMIT = 450
SYSTEM = (
    "You are a conservative financial document consistency checker. "
    "Assess if the submitted statement was likely manipulated. "
    "Use the document and ONLY explicitly supplied trusted evidence; "
    "do not claim graph context if none is supplied. "
    "Authoritative bank-side records, when present, represent facts recorded BEFORE "
    "the submitted statement arrived. Do NOT invent any facts. "
    "Label FRAUD if an arithmetic/date inconsistency or conflict with independently "
    "verified bank-side evidence is found; LEGITIMATE if available evidence supports "
    "consistency, and UNCERTAIN when information is insufficient. "
    "A fraud label here means 'known synthetic tampering', not a real allegation. "
    "Evidence IDs must be copied from supplied source identifiers exactly. "
    "Return a short plain-language explanation, not private chain of thought."
)
SCHEMA = {
    "type":"object",
    "properties":{
        "prediction":{"type":"string","enum":["fraud","legitimate","uncertain"]},
        "evidence_ids":{"type":"array","items":{"type":"string"}},
        "explanation":{"type":"string"}
    },
    "required":["prediction","evidence_ids","explanation"],
    "additionalProperties":False
}

def prompt(row, mode, historical):
    context=[]
    available_ids=[]
    if mode in ("graph_only","hybrid"):
        ref=row["graph_reference"]
        assert date.fromisoformat(ref["recorded_at"])<date.fromisoformat(row["submission_date"])
        available_ids.append(ref["source"])
        context.append("TRUSTED BANK GRAPH REFERENCE as-of-submission, source_id="
                       +ref["source"]+"\n"+json.dumps(ref,sort_keys=True))
    if mode in ("vector_only","hybrid"):
        # A prior-period, label-free corpus; no submitted documents or labels
        # are ever inserted into this retriever.
        retrieved=get_vector_context(row,historical,top_k=3)
        for ref in retrieved:
            available_ids.append(ref["source_id"])
            context.append("TRUSTED HISTORICAL DOCUMENT source_id="+ref["source_id"]
                           +"\n"+ref["text"])
    text="SUBMITTED DOCUMENT (do not assume truthful):\n"+row["statement_text"]
    if context:
        text+="\n\nRETRIEVED EVIDENCE (trusted provenance, not a fraud label):\n"+"\n\n".join(context)
    else:
        text+="\n\nNo bank-side verification record was supplied."
    return text,available_ids

def payload(row,mode,historical):
    user,allowed=prompt(row,mode,historical)
    return {
        "model":MODEL,
        "reasoning":{"effort":"low"},
        "store":False,
        "max_output_tokens":OUTPUT_TOKENS_LIMIT,
        "instructions":SYSTEM,
        "input":[{"role":"user","content":user}],
        "text":{"format":{"type":"json_schema","name":"document_verdict",
                          "strict":True,"schema":SCHEMA}}
    },allowed

def call_api(key, request_body):
    req=urllib.request.Request(
        "https://api.openai.com/v1/responses",
        headers={"Authorization":"Bearer "+key,"Content-Type":"application/json"},
        data=json.dumps(request_body).encode(),method="POST"
    )
    with urllib.request.urlopen(req,timeout=150) as response:
        return json.load(response)

def parse_answer(result):
    if result.get("status")!="completed":
        return None
    contents=[]
    for item in result.get("output",[]):
        if item.get("type")=="message":
            contents.extend(x.get("text","") for x in item.get("content",[])
                            if x.get("type")=="output_text")
    if not contents:
        return None
    try:
        output=json.loads("".join(contents))
        if output["prediction"] not in ("fraud","legitimate","uncertain"):
            return None
        if not isinstance(output["evidence_ids"],list):
            return None
        return output
    except (ValueError,KeyError,TypeError):
        return None

def reserve_for_call(prompt_chars):
    """Pessimistic reservation, not hard account billing enforcement."""
    input_reserve=max(1000,prompt_chars//2+700)
    return (input_reserve*INPUT_PRICE_PER_M+OUTPUT_TOKENS_LIMIT*OUTPUT_PRICE_PER_M)/1e6

def run(args):
    if not 1<=args.n_per_type<=4:
        raise ValueError("Use 1..4 examples per type in the pre-registered pilot")
    dest=Path(args.out)
    result=export_results(str(dest),120,args.n_per_type,57)
    test=load_rows(dest/"held_out_cases.csv")
    all_rows=load_rows(dest/"cases.csv")
    reference_corpus=[]
    seen=set()
    for row in all_rows:
        if row["customer_group"] not in seen:
            seen.add(row["customer_group"])
            reference_corpus.append(row)
    assert len(reference_corpus)==120
    assert all(r["graph_reference"]["recorded_at"]<r["submission_date"] for r in test)

    n_calls=len(test)*len(MODES)
    budget_preview=0.
    planned=[]
    for mode in MODES:
        for row in test:
            req,allowed=payload(row,mode,reference_corpus)
            estimate=reserve_for_call(len(req["input"][0]["content"])+len(SYSTEM))
            budget_preview+=estimate
            planned.append((mode,row,req,allowed,estimate))
    settings={"experiment":"FraudRAG-v2 synthetic documents: 4 paired GPT configurations",
              "model":MODEL,"system_sha256":hashlib.sha256(SYSTEM.encode()).hexdigest(),
              "modes":list(MODES),"sample_per_type":args.n_per_type,
              "sample_count":len(test),"planned_calls":n_calls,
              "customer_groups":len({r["customer_group"] for r in test}),
              "sample_case_ids":[r["case_id"] for r in test],
              "output_tokens_limit":OUTPUT_TOKENS_LIMIT,
              "graph_context_backend":"serialized synthetic bank ledger (NOT Neo4j query)",
              "vector_retriever":"TF-IDF from trusted previous-period corpus (NOT ChromaDB)",
              "prompt_includes_label":False,
              "new_generated_dataset_not_original_2400":True,
              "true_fraud_adjudications":False,
              "budget_reservation_usd":round(budget_preview,4),
              "budget_cap_usd":args.budget,
              "real_api_executed":args.execute,
              "limitations":result["limitations"]}
    (dest/"gpt_protocol.json").write_text(json.dumps(settings,indent=2)+"\n")
    if not args.execute:
        print(json.dumps(settings,indent=2),flush=True)
        return settings
    key=os.getenv("OPENAI_API_KEY")
    if not key:
        raise RuntimeError("OPENAI_API_KEY missing; no model calls")
    if budget_preview>args.budget:
        raise RuntimeError("Reserved budget exceeds cap, aborting before any model requests")
    predictions=[]
    spent=0.
    for i,(mode,row,body,available,est) in enumerate(planned):
        if spent+est>args.budget:
            print("Budget safety stop before next request",flush=True)
            break
        start=time.monotonic()
        raw=None; status="ok"; answer=None; it=ot=0
        try:
            raw=call_api(key,body)
            answer=parse_answer(raw)
            usage=raw.get("usage") or {}
            it=int(usage.get("input_tokens") or 0)
            ot=int(usage.get("output_tokens") or 0)
            spent+=(it*INPUT_PRICE_PER_M+ot*OUTPUT_PRICE_PER_M)/1e6
            if answer is None: status="invalid_or_incomplete_output"
        except urllib.error.HTTPError as e:
            status="http_"+str(e.code)
        except Exception as e:
            status=type(e).__name__
        cited=answer["evidence_ids"] if answer else []
        record={
            "case_id":row["case_id"],"customer_group":row["customer_group"],
            "tamper_type":row["tamper_type"],"true_label":row["fraud_label"],
            "mode":mode,"model":(raw or {}).get("model",""),
            "predicted":answer["prediction"] if answer else "uncertain",
            "evidence_ids":json.dumps(cited),
            "allowed_ids":json.dumps(available),
            "all_citations_known":all(x in available for x in cited),
            "explanation":answer["explanation"] if answer else "",
            "status":status,"input_tokens":it,"output_tokens":ot,
            "latency_s":round(time.monotonic()-start,3)
        }
        predictions.append(record)
        print(f"{i+1}/{n_calls} {mode} {row['case_id']} {record['predicted']} "
              f"{status} cost_so_far={spent:.4f}",flush=True)
        # No paid retry for a failing API or account
        if status.startswith("http_"):
            print("Stopping after HTTP failure; no automatic paid retries.",flush=True)
            break

    with (dest/"gpt_predictions.csv").open("w",newline="",encoding="utf8") as f:
        if predictions:
            wr=csv.DictWriter(f,fieldnames=list(predictions[0]))
            wr.writeheader()
            wr.writerows(predictions)
    by_mode={}
    for mode in MODES:
        pr={x["case_id"]:x for x in predictions if x["mode"]==mode}
        matched=[pr.get(r["case_id"]) for r in test]
        # If an API request failed or was skipped, count it as an error,
        # never as a negative "legitimate" result.
        labels=[(1 if p["predicted"]=="fraud" else 0 if p["predicted"]=="legitimate"
                 else None) if p is not None else None for p in matched]
        by_mode[mode]=evaluate_binary(test,labels,mode)
        by_mode[mode]["completed_calls"]=len(pr)
        by_mode[mode]["valid_decisions"]=sum(x is not None for x in labels)
        by_mode[mode]["invalid_evidence_citations"]=sum(
            x is not None and not x["all_citations_known"] for x in matched)
        by_mode[mode]["mean_api_latency_s"] = (
            sum(x["latency_s"] for x in pr.values())/len(pr) if pr else None)
    settings["estimated_recorded_api_cost_usd"]=round(spent,6)
    settings["actual_completed_calls"]=len(predictions)
    settings["results"]={"rules_only":result["rules"],
                         "deterministic_authoritative_ledger":result["reference_matching"],
                         **by_mode}
    settings["all_configs_same_heldout_cases"]=True
    settings["publication_clearance"]="NOT CLEARED: synthetic-only, small pilot, serialized graph"
    (dest/"gpt_metrics.json").write_text(json.dumps(settings,indent=2)+"\n")
    print("FRAUDRAG_V2_GPT_METRICS_BEGIN",flush=True)
    print(json.dumps(settings,indent=2),flush=True)
    print("FRAUDRAG_V2_GPT_METRICS_END",flush=True)
    return settings

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--out",default="artifacts/fraudrag_v2_gpt")
    p.add_argument("--n-per-type",type=int,default=4)
    p.add_argument("--budget",type=float,default=2.0)
    p.add_argument("--execute",action="store_true")
    args=p.parse_args()
    if not 0<args.budget<=2.0:
        p.error("Spending reservation cap must be >0 and <= $2")
    run(args)

if __name__=="__main__":
    main()
