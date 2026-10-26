"""FraudRAG V6: no-source abstention control on the SAME 24 V5 TAT-QA questions.

The model receives zero passages. No gold answer is in its prompt. Any
answered response is unsupported by PROVIDED sources, even when it happens
to match the external gold answer. This is financial QA, not bank fraud.
"""
import argparse,csv,json,os,time
from pathlib import Path
from tatqa_gpt_v5 import (MODEL,N,CAP,PRICE_IN,PRICE_OUT,MAX_OUTPUT,
                          SCHEMA,ORDINARY,STRICT,choose,api,extract)
from sys import path as sys_path
sys_path.insert(0,str(Path(__file__).resolve().parents[1]/"benchmark"))
from tatqa_evidence_v5 import load_external_data,normalize

def request(c,policy):
    return {"model":MODEL,"store":False,"reasoning":{"effort":"low"},
        "max_output_tokens":MAX_OUTPUT,
        "instructions":ORDINARY if policy=="ordinary" else STRICT,
        "input":[{"role":"user","content":json.dumps({"question":c["question"],
                                                       "sources":[]})}],
        "text":{"format":{"type":"json_schema","name":"evidence_qa",
                          "strict":True,"schema":SCHEMA}}}

def cost(body):
    return ((len(json.dumps(body))/2+850)*PRICE_IN+MAX_OUTPUT*PRICE_OUT)/1_000_000

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--execute",action="store_true")
    p.add_argument("--budget-usd",type=float,default=1.5)
    p.add_argument("--out",type=Path,default=Path("artifacts/tatqa_no_source_v6"))
    p.add_argument("--dataset",type=Path,default=Path("artifacts/tatqa/tatqa_dataset_dev.json"))
    a=p.parse_args()
    if not (0<a.budget_usd<=1.5):raise RuntimeError("Budget cap breached")
    data,sha=load_external_data(a.dataset)
    cases=choose(data,N)
    jobs=[(c,policy,request(c,policy)) for c in cases for policy in ("ordinary","abstain")]
    reserved=sum(cost(body) for _,_,body in jobs)
    if reserved>a.budget_usd:raise RuntimeError("Call reserve exceeds cost cap")
    a.out.mkdir(parents=True,exist_ok=True)
    protocol={"status":"preview","model":MODEL,"question_groups":len(cases),
              "planned_calls":len(jobs),"policy_pair":["ordinary","abstain"],
              "source_condition":"NO SOURCE RECORDS OF ANY KIND",
              "source_sha256":sha,"reserved_usd":round(reserved,6),
              "not_bank_fraud":True,"gold_not_given_to_model":True,
              "same_question_ids_as_v5":True}
    (a.out/"protocol.json").write_text(json.dumps(protocol,indent=2)+"\n")
    if not a.execute:
        print(json.dumps(protocol,indent=2));return
    key=os.getenv("OPENAI_API_KEY")
    if not key:
        (a.out/"metrics.json").write_text(json.dumps({**protocol,"status":"no_key_no_calls"},indent=2)+"\n")
        print("Zero calls: credential unavailable");return
    rows=[];spent=0.
    for i,(c,policy,payload) in enumerate(jobs):
        if spent+cost(payload)>a.budget_usd:break
        t=time.monotonic();error=""
        try:
            raw=api(key,payload);x=extract(raw);usage=raw.get("usage",{})
            if raw.get("status")!="completed":error="not_completed"
        except Exception as e:
            error=type(e).__name__+":"+str(e)[:80]
            x={"status":"abstain","answer":"","source_ids":[]};usage={}
        spent+=cost(payload)
        answered=x["status"]=="answered" and bool(x["answer"].strip())
        rows.append({"case_id":c["case_id"],"source_group":c["source_group"],
          "policy":policy,"answer":x["answer"],"status":x["status"],
          "answered_without_evidence":int(answered),
          "has_invented_source_id":int(bool(x["source_ids"])),
          "matches_external_gold":int(answered and normalize(x["answer"]).strip(". ")==normalize(c["gold_candidate"]).strip(". ")),
          "source_ids":json.dumps(x["source_ids"]),"input_tokens":usage.get("input_tokens",0),
          "output_tokens":usage.get("output_tokens",0),
          "duration_seconds":round(time.monotonic()-t,3),"error":error})
        print(f"V6 {i+1}/{len(jobs)} {policy} {x['status']} err={error}",flush=True)
        if error:break
    if rows:
        with (a.out/"predictions.csv").open("w",newline="") as f:
            w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    result={**protocol,"status":"completed" if len(rows)==len(jobs) and not any(r["error"] for r in rows) else "partial",
        "observed_calls":len(rows),"reserved_actual_usd":round(spent,6),
        "answer_counts":{p:sum(r["answered_without_evidence"] for r in rows if r["policy"]==p) for p in ("ordinary","abstain")},
        "invented_citation_counts":{p:sum(r["has_invented_source_id"] for r in rows if r["policy"]==p) for p in ("ordinary","abstain")},
        "limitations":"No-source condition is unambiguously unsupported by provided evidence; cannot claim factual hallucination, real fraud detection or external institution generalization."}
    (a.out/"metrics.json").write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps(result,indent=2))
if __name__=="__main__":main()
