"""External TAT-QA TEST gold-locked, document-group-disjoint answer-generation audit.

Published financial QA, not consumer bank fraud. Gold answer never appears in
prompts or deterministic case selection. Comparators have identical passage
access. Separate exact text scoring from unsupported-citation checks; exact
span metrics cannot adjudicate semantic paraphrase. Research dev experiment
selection and design precede any calls on this test condition.
"""
from __future__ import annotations
import argparse, csv, hashlib, json, os, random, re, time, unicodedata
import urllib.request
from collections import defaultdict
from pathlib import Path

UPSTREAM_SHA="870accc41953dcde885aabeb963d94aabdc0fbc3"
TEST_GIT_BLOB="3d5d3b691af572646ba9b1ac4d8f78c5dca09732"
DEV_GIT_BLOB="48075c812af3fe6698b1d5cb50d9dbf358d52784"
BASE="https://raw.githubusercontent.com/NExTplusplus/TAT-QA/"+UPSTREAM_SHA+"/dataset_raw/"
MODEL="gpt-6.1-sol"
N_GROUPS=64
MAX_OUTPUT=250
PRICE_INPUT_PER_M=2.0
PRICE_OUTPUT_PER_M=10.0
PROMPTS={
 "ordinary":"Answer the financial question based on the supplied source excerpts. Cite exact source IDs for evidence; when uncertain, return status abstain. Return schema only.",
 "evidence_cautious":"Only answer when supplied source excerpts warrant it. Do not rely on memorized report data or invent source IDs. Otherwise abstain with an empty answer and no sources. Return schema only."
}
SCHEMA={"type":"object","properties":{
 "status":{"type":"string","enum":["answered","abstain"]},
 "answer":{"type":"string"},
 "source_ids":{"type":"array","items":{"type":"string"}}},
 "required":["status","answer","source_ids"],"additionalProperties":False}


def sha1_git(raw):
    return hashlib.sha1(b"blob "+str(len(raw)).encode()+bytes([0])+raw).hexdigest()


def pinned_data(path:Path, url:str, expected_sha:str):
    path.parent.mkdir(parents=True,exist_ok=True)
    if not path.exists():
        with urllib.request.urlopen(url,timeout=80) as f:raw=f.read()
        if sha1_git(raw)!=expected_sha:
            raise RuntimeError("Unexpected upstream source blob")
        path.write_bytes(raw)
    raw=path.read_bytes()
    if sha1_git(raw)!=expected_sha:raise RuntimeError("Dataset integrity check failed")
    obj=json.loads(raw)
    if not isinstance(obj,list):raise ValueError("Expected context record list")
    return obj,hashlib.sha256(raw).hexdigest()


def select_cases(test,dev):
    dev_groups={str(d.get("table",{}).get("uid","")) for d in dev}
    candidates={}
    for context in test:
        group=str(context.get("table",{}).get("uid",""))
        if not group or group in dev_groups:continue
        sources=[{"id":str(p.get("uid","")), "text":str(p.get("text",""))[:3700]}
                 for p in context.get("paragraphs",[]) if p.get("uid") and p.get("text")]
        if not sources:continue
        for q in context.get("questions",[]):
            if q.get("answer_from")!="text" or q.get("answer_type")!="span":continue
            if not isinstance(q.get("answer"),list) or len(q["answer"])!=1:continue
            c={"id":str(q["uid"]),"group":group,"question":q["question"],
               "gold":str(q["answer"][0]),"sources":sources}
            if group not in candidates or hashlib.sha256(c["id"].encode()).hexdigest() < hashlib.sha256(candidates[group]["id"].encode()).hexdigest():
                candidates[group]=c
    groups=sorted(candidates,key=lambda x:hashlib.sha256(x.encode()).hexdigest())
    out=[candidates[g] for g in groups[:N_GROUPS]]
    if len(out)!=N_GROUPS:raise RuntimeError("Too few TEST groups with eligible text-span question: "+str(len(out)))
    if len({c["id"] for c in out})!=len(out):raise RuntimeError("Repeated question")
    return out,len(dev_groups)


def normalize(t):
    t=unicodedata.normalize("NFKC",str(t)).casefold()
    t=re.sub(r"[^a-z0-9 ]"," ",t)
    return " ".join(t.split())


def token_f1(answer,gold):
    a=normalize(answer).split()
    b=normalize(gold).split()
    if not a or not b:return 0.0
    from collections import Counter
    common=sum((Counter(a)&Counter(b)).values())
    return 2*common/(len(a)+len(b))


def pack(c,mode):
    payload={"model":MODEL,"store":False,"reasoning":{"effort":"low"},
     "max_output_tokens":MAX_OUTPUT,"instructions":PROMPTS[mode],
     "input":[{"role":"user","content":json.dumps({"question":c["question"],
                                    "passages":c["sources"]},ensure_ascii=False)}],
     "text":{"format":{"type":"json_schema","name":"external_financial_qa",
                      "strict":True,"schema":SCHEMA}}}
    return payload


def reserve(p):
    return ((len(json.dumps(p,ensure_ascii=False))/2 + 900)*PRICE_INPUT_PER_M+MAX_OUTPUT*PRICE_OUTPUT_PER_M)/1_000_000


def ask(key,payload):
    req=urllib.request.Request("https://api.openai.com/v1/responses",
      data=json.dumps(payload).encode(),method="POST",
      headers={"Authorization":"Bearer "+key,"Content-Type":"application/json"})
    with urllib.request.urlopen(req,timeout=150) as f:return json.load(f)


def parse(raw):
    texts=[p.get("text","") for x in raw.get("output",[]) if x.get("type")=="message"
           for p in x.get("content",[]) if p.get("type")=="output_text"]
    try:
        v=json.loads("".join(texts))
        if v["status"] in ("answered","abstain") and isinstance(v["answer"],str) and isinstance(v["source_ids"],list):
            return v
    except (KeyError,TypeError,ValueError):pass
    return {"status":"abstain","answer":"","source_ids":[]}


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--execute",action="store_true")
    parser.add_argument("--budget-usd",type=float,default=2.0)
    parser.add_argument("--out",type=Path,default=Path("artifacts/tatqa_test_v7"))
    args=parser.parse_args()
    if not (0<args.budget_usd<=2):raise ValueError("Hard safety cap USD 2")
    dev,_=pinned_data(Path("artifacts/tatqa/tatqa_dataset_dev.json"),
          BASE+"tatqa_dataset_dev.json",DEV_GIT_BLOB)
    test,test_sha=pinned_data(Path("artifacts/tatqa/tatqa_dataset_test_gold.json"),
          BASE+"tatqa_dataset_test_gold.json",TEST_GIT_BLOB)
    cases,dev_n=select_cases(test,dev)
    jobs=[(c,m,pack(c,m)) for c in cases for m in PROMPTS]
    reserved=sum(reserve(p) for _,_,p in jobs)
    args.out.mkdir(parents=True,exist_ok=True)
    protocol={"study":"TAT-QA published held-out test-group financial text QA",
     "source_commit":UPSTREAM_SHA,"test_blob":TEST_GIT_BLOB,
     "test_sha256":test_sha,"dev_context_groups":dev_n,
     "test_context_groups":len(cases),"planned_calls":len(jobs),
     "test_selection":"hash of test table context and question IDs after text/span metadata filter; no selection on answer value or witness matches",
     "source_group_disjoint_from_development":True,
     "gold_in_inputs":False,"source_type":"external published financial reports",
     "source_dataset_license":"CC BY 4.0; Zhu et al., ACL 2021",
     "model":MODEL,"modes":list(PROMPTS),"reserved_max_usd":round(reserved,6),
     "cap_usd":args.budget_usd,"real_bank_fraud":False,
     "sample_warning":"public test labels and model-contamination risk; table-context grouping is NOT issuer/institution grouping",
     "evaluation_warning":"normalized exact and token F1 are approximate span metrics, not official TAT-QA scorer or semantic adjudication"}
    (args.out/"protocol.json").write_text(json.dumps(protocol,indent=2)+"\n")
    if reserved>args.budget_usd:raise RuntimeError("Entire precommitted study over max budget")
    if not args.execute:
        print(json.dumps(protocol,indent=2));return
    key=os.getenv("OPENAI_API_KEY")
    if not key:
        print("No model key: zero inference")
        (args.out/"metrics.json").write_text(json.dumps({**protocol,"status":"no_key_no_calls"},indent=2)+"\n")
        return
    rows=[]
    for i,(c,mode,payload) in enumerate(jobs):
        t=time.monotonic();error=""
        try:
            raw=ask(key,payload);result=parse(raw)
            usage=raw.get("usage",{});model=raw.get("model","")
            if raw.get("status")!="completed":error="incomplete_response"
        except Exception as e:
            result={"status":"abstain","answer":"","source_ids":[]}
            usage={};model="";error=type(e).__name__+":"+str(e)[:80]
        answered=result["status"]=="answered" and bool(result["answer"].strip())
        by_id={s["id"]:s["text"] for s in c["sources"]}
        ids=result["source_ids"]
        citation_valid=bool(ids) and all(x in by_id for x in ids)
        literal_supported=answered and citation_valid and any(
          normalize(result["answer"]) in normalize(by_id[x]) for x in ids)
        score=token_f1(result["answer"],c["gold"]) if answered else 0.0
        rows.append({
          "case_id":c["id"],"source_group":c["group"],"mode":mode,
          "status":result["status"],"answer":result["answer"],"gold":c["gold"],
          "answered":int(answered),
          "normalized_exact_match":int(answered and normalize(result["answer"])==normalize(c["gold"])),
          "normalized_token_f1":round(score,6),
          "cites_valid_source_ids":int(answered and citation_valid),
          "answer_literal_in_cited_text":int(literal_supported),
          "source_ids":json.dumps(ids),"latency_s":round(time.monotonic()-t,3),
          "input_tokens":int(usage.get("input_tokens") or 0),
          "output_tokens":int(usage.get("output_tokens") or 0),
          "model_returned":model,"error":error})
        print("test sample",i+1,"/",len(jobs),"mode",mode,"answered",answered,"error",error,flush=True)
        if error:break
    with (args.out/"predictions.csv").open("w",newline="",encoding="utf8") as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    summary={}
    for mode in PROMPTS:
        v=[x for x in rows if x["mode"]==mode]
        n=len(v)
        summary[mode]={
          "n":n,"answers":sum(x["answered"] for x in v),
          "normalized_exact_matches":sum(x["normalized_exact_match"] for x in v),
          "macro_token_f1_including_abstentions":round(sum(x["normalized_token_f1"] for x in v)/n,6) if n else None,
          "valid_citation_response_count":sum(x["cites_valid_source_ids"] for x in v),
          "literal_supported_responses":sum(x["answer_literal_in_cited_text"] for x in v),
          "errors":sum(bool(x["error"]) for x in v)}
    report={**protocol,"status":"completed" if len(rows)==len(jobs) and all(not x["error"] for x in rows) else "incomplete",
            "actual_calls":len(rows),"metrics":summary,
            "observed_input_tokens":sum(x["input_tokens"] for x in rows),
            "observed_output_tokens":sum(x["output_tokens"] for x in rows)}
    (args.out/"metrics.json").write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps(report,indent=2))
if __name__=="__main__":main()
