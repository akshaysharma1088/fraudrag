"""Bounded GPT pilot: TAT-QA gold answers are NEVER part of model inputs.

Actual QA on public dev reports (not bank fraud); paired intact vs missing
evidence with ordinary-answer and explicit-abstain prompting. 24 context-
distinct questions, 96 calls maximum; controlled API cost cap USD 1.50.
"""
import argparse,csv,hashlib,json,os,sys,time,urllib.request
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"benchmark"))
from tatqa_evidence_v5 import load_external_data,build_cases,matches,normalize

MODEL="gpt-6.1-sol"
N=24
CAP=1.5
PRICE_IN=2.0
PRICE_OUT=10.0
MAX_OUTPUT=280
POLICIES=("ordinary","abstain")
CONDITIONS=("intact","witness_removed")
SCHEMA={"type":"object","properties":{
 "status":{"type":"string","enum":["answered","abstain"]},
 "answer":{"type":"string"},
 "source_ids":{"type":"array","items":{"type":"string"}}},
 "required":["status","answer","source_ids"],"additionalProperties":False}
ORDINARY=("Answer the question based on the supplied excerpts. "
          "Include exact supporting source IDs. If uncertain, you may abstain. "
          "No fabricated citations.")
STRICT=("Only answer when the supplied excerpts directly justify your answer. "
        "Otherwise return status abstain, answer empty, and no source IDs. "
        "Never use memorized report details or invent a citation.")

def choose(data,n=N):
    cases,_=build_cases(data)
    q={q["uid"]:q["question"] for doc in data for q in doc.get("questions",[])}
    group={}
    for c in sorted(cases,key=lambda x:hashlib.sha256(x["case_id"].encode()).hexdigest()):
        group.setdefault(c["source_group"],c)
    selected=sorted(group.values(),key=lambda x:hashlib.sha256(x["source_group"].encode()).hexdigest())[:n]
    if len(selected)!=n:raise RuntimeError("Too few independent table contexts")
    for c in selected:c["question"]=q[c["case_id"]]
    return selected

def get_sources(c,cond):
    w=set(c["witnesses"])
    s=[x for x in c["source_texts"] if cond=="intact" or x["source_id"] not in w]
    return [{"source_id":x["source_id"],"text":x["text"][:3000]} for x in s]

def make_request(c,pol,cond):
    s=get_sources(c,cond)
    if cond=="witness_removed" and any(matches(x["text"],c["gold_candidate"]) for x in s):
        raise RuntimeError("Answer witness leakage into withheld input")
    msg=json.dumps({"question":c["question"],"sources":s},ensure_ascii=False)
    payload={"model":MODEL,"store":False,"reasoning":{"effort":"low"},
      "max_output_tokens":MAX_OUTPUT,"instructions":STRICT if pol=="abstain" else ORDINARY,
      "input":[{"role":"user","content":msg}],
      "text":{"format":{"type":"json_schema","name":"evidence_qa",
          "strict":True,"schema":SCHEMA}}}
    return payload,s

def estimate(payload):
    return ((len(json.dumps(payload))/2+850)*PRICE_IN+MAX_OUTPUT*PRICE_OUT)/1000000

def api(key,payload):
    r=urllib.request.Request("https://api.openai.com/v1/responses",
      data=json.dumps(payload).encode(),method="POST",
      headers={"Authorization":"Bearer "+key,"Content-Type":"application/json"})
    with urllib.request.urlopen(r,timeout=150) as f:return json.load(f)

def extract(raw):
    t="".join(z.get("text","") for x in raw.get("output",[])
       if x.get("type")=="message" for z in x.get("content",[])
       if z.get("type")=="output_text")
    try:
        obj=json.loads(t)
        if obj["status"] in ("answered","abstain") and isinstance(obj["answer"],str) and isinstance(obj["source_ids"],list):
            return obj
    except (ValueError,KeyError,TypeError):pass
    return {"status":"abstain","answer":"","source_ids":[]}

def run(data,out,execute=False,budget=CAP):
    if budget>CAP or budget<=0:raise RuntimeError("Cost limit exceeded")
    cases=choose(data)
    jobs=[]
    for c in cases:
        for cond in CONDITIONS:
            for policy in POLICIES:
                payload,sources=make_request(c,policy,cond)
                jobs.append((c,cond,policy,payload,sources))
    reserved=sum(estimate(x[3]) for x in jobs)
    out.mkdir(parents=True,exist_ok=True)
    protocol={"model":MODEL,"public_dev":True,"unique_table_contexts":len(cases),
      "planned_calls":len(jobs),"estimated_maximum_usd":round(reserved,5),
      "budget_usd":budget,"actual_bank_fraud_labels":False,
      "gold_answer_given_to_model":False,
      "source_witnesses_deleted_using_gold_annotations":True,
      "note":"Dev pilot on financial-report text-span QA. Not bank fraud or institution-held-out; does not establish novelty."}
    (out/"protocol.json").write_text(json.dumps(protocol,indent=2)+"\n")
    if reserved>budget:raise RuntimeError("Total budget reservation exceeds user-authorized cap")
    if not execute:
        print(json.dumps(protocol,indent=2));return
    key=os.getenv("OPENAI_API_KEY")
    if not key:
        (out/"metrics.json").write_text(json.dumps({**protocol,"status":"no_key_no_calls"},indent=2)+"\n")
        print("No stored API key: zero calls");return
    rows=[];cumulative=0.0
    for i,(c,cond,policy,payload,sources) in enumerate(jobs):
        reserve=estimate(payload)
        if cumulative+reserve>budget:break
        tic=time.monotonic()
        error="";usage={};observed=""
        try:
            raw=api(key,payload);x=extract(raw);usage=raw.get("usage",{});observed=raw.get("model","")
            if raw.get("status")!="completed":error="not_completed"
        except Exception as e:
            error=type(e).__name__+":"+str(e)[:100]
            x={"status":"abstain","answer":"","source_ids":[]}
        cumulative+=reserve
        ids={s["source_id"]:s["text"] for s in sources}
        answer=x["answer"].strip()
        responded=x["status"]=="answered" and bool(answer)
        cited=bool(x["source_ids"]) and all(y in ids for y in x["source_ids"])
        grounded=responded and cited and any(matches(ids[y],answer) for y in x["source_ids"])
        correct=responded and normalize(answer).strip(". ")==normalize(c["gold_candidate"]).strip(". ")
        rows.append({"case_id":c["case_id"],"table_context":c["source_group"],
          "condition":cond,"policy":policy,"answer":answer,"gold":c["gold_candidate"],
          "answered":int(responded),"normalized_exact_gold":int(correct),
          "literal_source_supported":int(grounded),"source_ids":json.dumps(x["source_ids"]),
          "model":observed,"input_tokens":usage.get("input_tokens",0),
          "output_tokens":usage.get("output_tokens",0),
          "duration_seconds":round(time.monotonic()-tic,3),"error":error})
        print(f"GPT {i+1}/{len(jobs)} {cond} {policy}: {x['status']} err={error}",flush=True)
        if error:break
    if rows:
        with (out/"predictions.csv").open("w",newline="") as f:
            wr=csv.DictWriter(f,fieldnames=list(rows[0]));wr.writeheader();wr.writerows(rows)
    scores={}
    for cond in CONDITIONS:
        for pol in POLICIES:
            subset=[x for x in rows if x["condition"]==cond and x["policy"]==pol]
            scores[cond+":"+pol]={"n":len(subset),
                "answered":sum(x["answered"] for x in subset),
                "normalized_exact_gold":sum(x["normalized_exact_gold"] for x in subset),
                "literal_source_supported":sum(x["literal_source_supported"] for x in subset)}
    report={**protocol,"status":"completed" if len(rows)==len(jobs) and not any(x["error"] for x in rows) else "partial",
      "observed_calls":len(rows),"reserved_usd":round(cumulative,5),"scores":scores,
      "interpretation":"Exploratory 24-context real LLM dev pilot; no real fraud detection or held-out institutional inference."}
    (out/"metrics.json").write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps(report,indent=2))

def main():
    p=argparse.ArgumentParser();p.add_argument("--execute",action="store_true")
    p.add_argument("--budget-usd",type=float,default=CAP)
    p.add_argument("--out",type=Path,default=Path("artifacts/tatqa_gpt_v5"))
    p.add_argument("--dataset",type=Path,default=Path("artifacts/tatqa/tatqa_dataset_dev.json"))
    a=p.parse_args()
    data,_=load_external_data(a.dataset)
    run(data,a.out,execute=a.execute,budget=a.budget_usd)
if __name__=="__main__":main()
