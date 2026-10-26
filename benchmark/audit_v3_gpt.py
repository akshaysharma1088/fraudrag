"""Independent fail-closed audit of real v3 GPT responses.

No new model calls or third-party PDF redistribution. Recomputes every score
from held-out fixed case IDs (5 synthetic source PDFs x 4 interventions x
3 settings), records all unsupported source claims and exceptions, and checks
the original source hashes for unchanged research design.
"""
import argparse,csv,json,math,hashlib
from pathlib import Path

TYPES={
    "unchanged":0,"benign_spacing":0,
    "edited_first_amount":1,"edited_later_amount":1
}
MODES=("document_only","partial_source","complete_source")
EXPECTED=("bsb-001","bsb-002","bsb-003","bsb-004","bsb-005")

def audit(folder):
    root=Path(folder)
    manifest=json.loads((root/"protocol.json").read_text())
    recorded=json.loads((root/"metrics.json").read_text())
    with (root/"predictions.csv").open(newline="",encoding="utf8") as f:
        rows=list(csv.DictReader(f))
    expected_pairs={(f"{sid}:{kind}",mode) for sid in EXPECTED for kind in TYPES for mode in MODES}
    keys=[(r["case_id"],r["mode"]) for r in rows]
    if len(keys)!=len(set(keys)):
        raise ValueError("Duplicated case/arm output")
    if not set(keys).issubset(expected_pairs):
        raise ValueError("Out-of-protocol case or GPT mode")
    if manifest.get("source_count")!=5 or manifest.get("case_count")!=20:
        raise ValueError("Source count does not match precommitted study")
    if manifest["source_pdf_hashes"]!=recorded["source_pdf_hashes"]:
        raise ValueError("Source PDF digest map changed after inference")
    per={}
    unsupported=[]
    for mode in MODES:
        by={r["case_id"]:r for r in rows if r["mode"]==mode}
        tp=tn=fp=fn=abst=0
        latency=[]
        for sid in EXPECTED:
            for kind,truth in TYPES.items():
                cid=f"{sid}:{kind}"
                result=by.get(cid)
                pred=result["prediction"] if result is not None else "uncertain"
                if result is not None:
                    if int(result["true_injected_change"])!=truth:
                        raise ValueError("Source label differs from precommitted intervention")
                    cited=json.loads(result["evidence_ids"])
                    allowed=json.loads(result["allowed_evidence_ids"])
                    if (mode=="document_only" and allowed) or (mode!="document_only" and len(allowed)!=1):
                        raise ValueError("A mode received the wrong amount of reference evidence")
                    invalid=sorted(set(cited)-set(allowed))
                    if invalid:unsupported.append({"case":cid,"mode":mode,"cited":invalid})
                    if result["duration_seconds"]:
                        latency.append(float(result["duration_seconds"]))
                if pred not in ("altered","unchanged","uncertain"):
                    raise ValueError("Unrecognized output label")
                if pred=="uncertain":
                    abst+=1
                    if truth:fn+=1
                    else:fp+=1
                elif pred=="altered":
                    if truth:tp+=1
                    else:fp+=1
                else:
                    if truth:fn+=1
                    else:tn+=1
        precision=tp/(tp+fp) if tp+fp else 0
        recall=tp/(tp+fn) if tp+fn else 0
        f1=2*precision*recall/(precision+recall) if precision+recall else 0
        latency.sort()
        summary={"n":20,"tp":tp,"tn":tn,"fp":fp,"fn":fn,"abstain":abst,
                 "accuracy_with_abstention_error":(tp+tn)/20,"f1":f1,
                 "completed_calls":len(by),
                 "p50_api_seconds":latency[len(latency)//2] if latency else None,
                 "p95_api_seconds":latency[math.ceil(.95*len(latency))-1] if latency else None}
        for item in ("tp","tn","fp","fn","abstain"):
            if summary[item]!=recorded["scores"][mode][item]:
                raise ValueError("Reported metric does not reproduce: "+mode+"/"+item)
        per[mode]=summary
    finished=set(keys)==expected_pairs
    out={
        "source":"independent verification of V3 5 synthetic publisher PDFs",
        "actual_model_calls":len(keys),
        "expected_unique_pairs":len(expected_pairs),
        "all_precommitted_pairs_present":finished,
        "missing_pairs":sorted(expected_pairs-set(keys)),
        "source_pdf_sha256":manifest["source_pdf_hashes"],
        "independent_mode_scores":per,
        "unsupported_evidence_citations":unsupported,
        "unsupported_citation_count":len(unsupported),
        "model_cost_estimate_usd":recorded["estimated_token_cost_usd"],
        "statistical_validity":"ONLY 5 original source documents; source-derived cases are correlated",
        "fraud_adjudications":0,
        "source_pdfs_are_synthetic":True,
        "paper_ready":False
    }
    (root/"independent_audit.json").write_text(json.dumps(out,indent=2)+"\n")
    print(json.dumps(out,indent=2))
    return out

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--folder",default="artifacts/v3_gpt")
    a=p.parse_args()
    audit(a.folder)

if __name__=="__main__":main()
