"""GPT evaluation on five external LICENSED SYNTHETIC PDF sources.

Controlled edits are performed ONLY on extracted TEXT, not PDFs/images.
NOT a real financial-fraud benchmark, no transaction ground-truth labels.
Dry by default. The full original PDF text is an intentional oracle.
"""
import argparse, csv, hashlib, json, os, sys, time, urllib.error, urllib.request
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "benchmark"))
from v3_external_pdf import EXPECTED_SHA256, verified_source, extract_pdf, create_variants, normalize
from fraudrag_v2_integrated import MODEL, INPUT_PRICE_PER_M, OUTPUT_PRICE_PER_M

MODES=("document_only","partial_source","complete_source")
MAX_OUTPUT_TOKENS=350
SYSTEM=("Decide whether submitted TEXT differs from an explicitly supplied source. "
        "These are fictional publisher PDFs, and 'altered' means a controlled text edit, "
        "NOT an adjudicated fraud case. Treat only whitespace differences as unchanged. "
        "If the original source is missing or partial, abstain unless a difference is "
        "directly provable. Do not invent source IDs. Return only the JSON schema.")
SCHEMA={"type":"object","properties":{
    "verdict":{"type":"string","enum":["altered","unchanged","uncertain"]},
    "evidence_ids":{"type":"array","items":{"type":"string"}},
    "explanation":{"type":"string"}},
    "required":["verdict","evidence_ids","explanation"],"additionalProperties":False}

def load_cases(cache):
    originals={};cases=[]
    for sid in EXPECTED_SHA256:
        raw,_=verified_source(sid,Path(cache))
        text,_=extract_pdf(raw)
        if not text.strip():raise RuntimeError("Unextractable source: "+sid)
        originals[sid]=text
        variants,exclusions=create_variants(sid,text)
        if exclusions or len(variants)!=4:raise RuntimeError("Incomplete cases for "+sid)
        cases+=variants
    assert len(cases)==20
    return originals,cases

def prepare(case, original, mode):
    source_id=case["source_id"]
    message="UNTRUSTED SUBMITTED TEXT:\n"+case["text"]
    allowed=[]
    if mode=="complete_source":
        sid="synthetic-pdf://"+source_id+"/complete"
        message+="\n\nORIGINAL DOCUMENT TEXT source_id="+sid+"\n"+original
        allowed.append(sid)
    elif mode=="partial_source":
        sid="synthetic-pdf://"+source_id+"/partial"
        message+="\n\nINCOMPLETE FIRST 30 ORIGINAL TOKENS source_id="+sid+"\n"+" ".join(normalize(original).split()[:30])
        allowed.append(sid)
    elif mode=="document_only":
        message+="\n\nNO ORIGINAL SOURCE PROVIDED. Do not assume the submitted text is authentic."
    else:raise ValueError(mode)
    return message,allowed

def pack(message):
    return {"model":MODEL,"store":False,"reasoning":{"effort":"low"},
            "max_output_tokens":MAX_OUTPUT_TOKENS,"instructions":SYSTEM,
            "input":[{"role":"user","content":message}],
            "text":{"format":{"type":"json_schema","name":"v3_text_comparison",
                              "strict":True,"schema":SCHEMA}}}

def reserve(length):
    return (max(1000,length//2+1000)*INPUT_PRICE_PER_M+
            MAX_OUTPUT_TOKENS*OUTPUT_PRICE_PER_M)/1_000_000

def request(key,payload):
    req=urllib.request.Request("https://api.openai.com/v1/responses",
          data=json.dumps(payload).encode("utf8"),
          headers={"Authorization":"Bearer "+key,"Content-Type":"application/json"},
          method="POST")
    with urllib.request.urlopen(req,timeout=150) as rsp:return json.load(rsp)

def parse(body):
    if body.get("status")!="completed":return None
    content=[]
    for item in body.get("output",[]):
        if item.get("type")=="message":
            content += [c.get("text","") for c in item.get("content",[]) if c.get("type")=="output_text"]
    try:
        data=json.loads("".join(content))
        if data["verdict"] in ("altered","unchanged","uncertain") and isinstance(data["evidence_ids"],list):
            return data
    except (KeyError,TypeError,ValueError):pass
    return None

def summarize(cases,answers,mode):
    by={x["case_id"]:x for x in answers if x["mode"]==mode}
    tp=tn=fp=fn=abstain=0
    for case in cases:
        result=by.get(case["case_id"])
        pred=result["prediction"] if result else "uncertain"
        y=int(case["injected_change"])
        if pred=="uncertain":
            abstain+=1
            if y:fn+=1
            else:fp+=1
        elif pred=="altered":
            if y:tp+=1
            else:fp+=1
        elif pred=="unchanged":
            if y:fn+=1
            else:tn+=1
        else:raise AssertionError(pred)
    precision=tp/(tp+fp) if tp+fp else 0
    recall=tp/(tp+fn) if tp+fn else 0
    return {"n":len(cases),"tp":tp,"tn":tn,"fp":fp,"fn":fn,"abstain":abstain,
            "accuracy_with_abstention_error":(tp+tn)/len(cases),
            "f1":2*precision*recall/(precision+recall) if precision+recall else 0,
            "completed_calls":len(by),
            "unsupported_citation_responses":sum(str(x["source_ids_valid"]).lower()=="false" for x in by.values())}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--cache",default="data/external_v3")
    p.add_argument("--out",default="artifacts/v3_gpt")
    p.add_argument("--budget",type=float,default=2.0)
    p.add_argument("--execute",action="store_true")
    args=p.parse_args()
    if not 0<args.budget<=2:raise SystemExit("Maximum estimated budget cap USD 2")
    originals,cases=load_cases(args.cache)
    jobs=[]
    for mode in MODES:
        for case in cases:
            text,allowed=prepare(case,originals[case["source_id"]],mode)
            jobs.append((mode,case,pack(text),allowed,reserve(len(text)+len(SYSTEM))))
    maximum=sum(x[4] for x in jobs)
    if maximum>args.budget:raise RuntimeError("Cost reservation exceeds cap before API")
    out=Path(args.out);out.mkdir(parents=True,exist_ok=True)
    protocol={"study":"controlled TEXT edits to five externally sourced synthetic PDF statements",
              "source_pdf_hashes":EXPECTED_SHA256,"model":MODEL,"source_count":5,
              "case_count":len(cases),"condition_count":len(MODES),
              "planned_calls":len(jobs),"modes":MODES,
              "system_sha256":hashlib.sha256(SYSTEM.encode()).hexdigest(),
              "estimated_reservation_usd":round(maximum,6),"budget_usd":args.budget,
              "independent_real_fraud_ground_truth":False,"pdf_image_tampering_tested":False,
              "complete_source_is_oracle":True,"paid_run":args.execute}
    (out/"protocol.json").write_text(json.dumps(protocol,indent=2)+"\n")
    if not args.execute:
        print(json.dumps(protocol,indent=2))
        return
    key=os.environ.get("OPENAI_API_KEY")
    if not key:raise RuntimeError("OPENAI_API_KEY not configured: no calls")
    spent=0.;answers=[]
    for i,(mode,case,body,ids,max_cost) in enumerate(jobs):
        if spent+max_cost>args.budget:
            print("Budget safety stop before next request")
            break
        start=time.monotonic();raw={};parsed=None;status="ok";it=ot=0
        try:
            raw=request(key,body);parsed=parse(raw)
            usage=raw.get("usage",{})
            it=int(usage.get("input_tokens") or 0)
            ot=int(usage.get("output_tokens") or 0)
            spent+=(it*INPUT_PRICE_PER_M+ot*OUTPUT_PRICE_PER_M)/1_000_000
            if parsed is None:status="abstain_incomplete_output"
        except urllib.error.HTTPError as e:status="http_"+str(e.code)
        except Exception as e:status=type(e).__name__
        cited=parsed["evidence_ids"] if parsed else []
        answers.append({"case_id":case["case_id"],"source_id":case["source_id"],
         "edit_type":case["edit_type"],"true_injected_change":case["injected_change"],
         "mode":mode,"prediction":parsed["verdict"] if parsed else "uncertain",
         "evidence_ids":json.dumps(cited),"allowed_evidence_ids":json.dumps(ids),
         "source_ids_valid":all(c in ids for c in cited),
         "explanation":parsed["explanation"] if parsed else "",
         "model_reported":raw.get("model",""),"status":status,
         "input_tokens":it,"output_tokens":ot,"duration_seconds":round(time.monotonic()-start,3)})
        print(f"case={i+1}/{len(jobs)} mode={mode} status={status} "
              f"prediction={answers[-1]['prediction']} total_usd={spent:.5f}",flush=True)
        if status.startswith("http_"):break
    with (out/"predictions.csv").open("w",newline="",encoding="utf8") as f:
        wr=csv.DictWriter(f,fieldnames=list(answers[0]));wr.writeheader();wr.writerows(answers)
    result={**protocol,"actual_calls":len(answers),"estimated_token_cost_usd":round(spent,6),
            "scores":{mode:summarize(cases,answers,mode) for mode in MODES},
            "publication_cleared":False,
            "limitations":"Five synthetic third-party PDFs, 20 derivative text cases; source exact-match is an oracle, no real fraud claims."}
    (out/"metrics.json").write_text(json.dumps(result,indent=2)+"\n")
    print("V3_MODEL_RESULTS_START")
    print(json.dumps(result,indent=2))
    print("V3_MODEL_RESULTS_END")

if __name__=="__main__":main()
