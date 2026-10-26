"""Real Neo4j + Chroma retrieval feeding a real GPT Responses API run.

This is a SYNTHETIC, tightly controlled consistency-checking research pilot,
not independently labeled real financial fraud data. All graph evidence is
generated as bank-side reference records and dated before submission.

Four paired LLM conditions for the same 28 customer-disjoint held-out cases:
  document_only, chroma_only, neo4j_only, integrated.
A separate non-LLM exact bank-ledger baseline must always be reported.
The model input is retrieved by actual DB queries, NEVER loaded from the test
row's graph_reference_json during prompting.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
import os
import random
import sys
import time
import urllib.error
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/"benchmark"))
from fraudrag_v2 import TYPES
from evaluate_v2 import export_results, load_rows, evaluate_binary
from neo4j_snapshot import seed_reference, get_as_of_reference, assert_no_label_leakage
from chroma_historical_v2 import build_index, get_retrieval
from fraudrag_v2_gpt import (
    MODEL, SYSTEM, SCHEMA, OUTPUT_TOKENS_LIMIT, INPUT_PRICE_PER_M, OUTPUT_PRICE_PER_M,
    call_api, parse_answer, reserve_for_call
)

MODES=("document_only", "chroma_only", "neo4j_only", "integrated")
MAX_BUDGET_USD=2.0

def write_csv(path, rows):
    if rows:
        with Path(path).open("w", newline="", encoding="utf8") as f:
            writer=csv.DictWriter(f,fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)

def seed_stores(rows, uri, user, password):
    """Seed only trusted synthetic reference side, not submitted statements/labels."""
    from neo4j import GraphDatabase
    driver=GraphDatabase.driver(uri,auth=(user,password))
    driver.verify_connectivity()
    groups={}
    for row in rows:
        groups.setdefault(row["customer_group"],row)
    with driver.session() as session:
        for customer,row in sorted(groups.items()):
            ref=row["graph_reference"]
            assert_no_label_leakage(ref)
            if not date.fromisoformat(ref["recorded_at"]) < date.fromisoformat(row["submission_date"]):
                raise ValueError("Graph record must be before statement submission")
            session.execute_write(seed_reference,customer,ref)
    _,collection,vectorizer=build_index(rows)
    if collection.count()!=len(groups):
        raise AssertionError("Unexpected number of unique historical records")
    return driver,collection,vectorizer

def get_sources(driver,collection,vectorizer,row,mode):
    """Real Cypher and real Chroma queries. Never use row['graph_reference'] here."""
    contexts=[]
    ids=[]
    provenance=[]
    if mode in ("neo4j_only","integrated"):
        with driver.session() as session:
            ref=session.execute_read(
                get_as_of_reference,row["customer_group"],row["submission_date"])
        assert_no_label_leakage(ref)
        if ref:
            sid=ref["source"]
            assert date.fromisoformat(ref["recorded_at"])<date.fromisoformat(row["submission_date"])
            contexts.append("BANK RECORD FROM NEO4J source_id="+sid+"\n"+json.dumps(ref,sort_keys=True))
            ids.append(sid)
            provenance.append({"source_id":sid,"provider":"neo4j",
                               "recorded_at":ref["recorded_at"]})
    if mode in ("chroma_only","integrated"):
        records=get_retrieval(collection,vectorizer,row,k=3)
        for record in records:
            if not record["recorded_at"]<row["submission_date"]:
                raise ValueError("Chroma record violates time ordering")
            sid=record["id"]
            contexts.append("PRIOR HISTORICAL DOCUMENT FROM CHROMA source_id="+sid+"\n"+record["text"])
            ids.append(sid)
            provenance.append({"source_id":sid,"provider":"chroma",
                               "recorded_at":record["recorded_at"]})
    document="SUBMITTED STATEMENT (untrusted, may contain attacks):\n"+row["statement_text"]
    if contexts:
        document+="\n\nTRUSTED EVIDENCE AVAILABLE BEFORE SUBMISSION:\n"+"\n\n".join(contexts)
    else:
        document+="\n\nNO EXTERNAL DOCUMENT EVIDENCE WAS SUPPLIED."
    for secret in ("fraud_label","tamper_type","ground_truth_rule"):
        if secret in document:
            raise ValueError("Test-oracle field leaked to LLM prompt")
    return document,ids,provenance

def pack_request(document):
    return {"model":MODEL,"reasoning":{"effort":"low"},"store":False,
            "max_output_tokens":OUTPUT_TOKENS_LIMIT,"instructions":SYSTEM,
            "input":[{"role":"user","content":document}],
            "text":{"format":{"type":"json_schema","name":"document_verdict",
                 "strict":True,"schema":SCHEMA}}}

def run(args):
    if args.budget>MAX_BUDGET_USD or args.budget<=0:
        raise ValueError("This pilot is capped at $2 reserved estimated spend")
    path=Path(args.out)
    path.mkdir(parents=True,exist_ok=True)
    baseline=export_results(str(path),120,4,57)
    test=load_rows(path/"held_out_cases.csv")
    allrows=load_rows(path/"cases.csv")
    if len(test)!=28 or len({r["customer_group"] for r in test})!=28:
        raise ValueError("This run requires 28 distinct held-out customers")
    driver,collection,vectorizer=seed_stores(allrows,args.neo4j_uri,args.neo4j_user,args.neo4j_password)
    try:
        planned=[]
        for mode in MODES:
            for row in test:
                content,ids,source=get_sources(driver,collection,vectorizer,row,mode)
                req=pack_request(content)
                budget=reserve_for_call(len(content)+len(SYSTEM))
                planned.append((mode,row,req,ids,source,budget))
        reserved=sum(x[-1] for x in planned)
        manifest={
            "scope":"real Neo4j + Chroma + GPT over controlled synthetic document edits",
            "is_actual_neo4j_inference":True,
            "is_actual_chroma_inference":True,
            "openai_embeddings_used":False,
            "vector_embedding":"local deterministic HashingVectorizer 256d",
            "not_original_2400":True,"real_world_validity":False,
            "model":MODEL,"modes":list(MODES),
            "system_sha256":hashlib.sha256(SYSTEM.encode()).hexdigest(),
            "cases":len(test),"customer_count":len({r["customer_group"] for r in test}),
            "case_ids":[r["case_id"] for r in test],
            "call_count":len(planned),"dataset_sha256":baseline["benchmark"]["csv_sha256"],
            "reserved_cost_usd":round(reserved,6),"budget_usd":args.budget,
            "running_paid_inference":bool(args.execute),
            "limitations":[
                "No adjudicated real fraud","complete same-period synthetic bank ledger is an oracle",
                "256-dimensional hash features, not semantic embeddings",
                "single fixed 28-case evaluation; 71.4% manipulated cases",
                "no scanned OCR, human annotation, generalization or production stress test"]
        }
        # The manifest is written before any paid API calls so the exact
        # pre-registered inputs/splits remain available even if API fails.
        (path/"integrated_protocol.json").write_text(json.dumps(manifest,indent=2)+"\n")
        if not args.execute:
            print(json.dumps(manifest,indent=2),flush=True)
            return manifest
        if reserved>args.budget:
            raise RuntimeError("Precomputed spending reservation exceeds cap; zero paid calls")
        key=os.getenv("OPENAI_API_KEY")
        if not key:
            raise RuntimeError("No OPENAI_API_KEY provided; zero paid calls")
        predictions=[]
        total_cost=0.
        for i,(mode,row,req,ids,source,estimate) in enumerate(planned):
            if total_cost+estimate>args.budget:
                print("Budget stop before another request",flush=True)
                break
            t=time.monotonic()
            status="ok"
            response={}
            parsed=None
            inn=out=0
            try:
                response=call_api(key,req)
                parsed=parse_answer(response)
                usage=response.get("usage") or {}
                inn=int(usage.get("input_tokens") or 0)
                out=int(usage.get("output_tokens") or 0)
                total_cost+=(inn*INPUT_PRICE_PER_M+out*OUTPUT_PRICE_PER_M)/1e6
                if parsed is None:
                    status="incomplete_or_invalid_model_answer"
            except urllib.error.HTTPError as exc:
                status=f"http_{exc.code}"
            except Exception as exc:
                status=type(exc).__name__
            citations=parsed["evidence_ids"] if parsed else []
            p={"case_id":row["case_id"],"customer_group":row["customer_group"],
               "tamper_type":row["tamper_type"],"true_label":row["fraud_label"],
               "mode":mode,"prediction":parsed["prediction"] if parsed else "uncertain",
               "evidence_ids":json.dumps(citations),"allowed_evidence_ids":json.dumps(ids),
               "evidence_valid":all(x in ids for x in citations),
               "retrieval_provenance":json.dumps(source,sort_keys=True),
               "explanation":parsed["explanation"] if parsed else "",
               "model_reported":response.get("model",""),
               "status":status,"input_tokens":inn,"output_tokens":out,
               "elapsed_seconds":round(time.monotonic()-t,3)}
            predictions.append(p)
            print(f"case {i+1}/{len(planned)} mode={mode} result={p['prediction']} "
                  f"status={status} cost_estimate={total_cost:.5f}",flush=True)
            if status.startswith("http_"):
                break
        write_csv(path/"integrated_predictions.csv",predictions)
        conditions={}
        for mode in MODES:
            by={p["case_id"]:p for p in predictions if p["mode"]==mode}
            preds=[]
            for row in test:
                p=by.get(row["case_id"])
                preds.append(None if p is None or p["prediction"]=="uncertain" else
                             int(p["prediction"]=="fraud"))
            conditions[mode]=evaluate_binary(test,preds,mode)
            conditions[mode]["model_responses"]=len(by)
            conditions[mode]["unsupported_evidence_citations"]=sum(
                p["evidence_valid"] is False for p in by.values())
        manifest.update({"actual_calls":len(predictions),
                         "estimated_cost_usd":round(total_cost,6),
                         "results":{"rules":baseline["rules"],
                                    "exact_ledger":baseline["reference_matching"],
                                    **conditions},
                         "publication_ready":False})
        (path/"integrated_metrics.json").write_text(json.dumps(manifest,indent=2)+"\n")
        print("INTEGRATED_METRICS_JSON_START",flush=True)
        print(json.dumps(manifest,indent=2),flush=True)
        print("INTEGRATED_METRICS_JSON_END",flush=True)
        return manifest
    finally:
        driver.close()

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--neo4j-uri",default="bolt://localhost:7687")
    parser.add_argument("--neo4j-user",default="neo4j")
    parser.add_argument("--neo4j-password",default=os.getenv("NEO4J_PASSWORD",""))
    parser.add_argument("--out",default="artifacts/fraudrag_v2_integrated")
    parser.add_argument("--budget",type=float,default=2.0)
    parser.add_argument("--execute",action="store_true")
    args=parser.parse_args()
    run(args)

if __name__=="__main__":
    main()
