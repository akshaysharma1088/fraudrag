"""Strict NEGATIVE screen of only the new FraudRAG working manuscript.

Passing does not verify claims; the claim register and manual source review
remain mandatory. Historic archival DOCX is screened in a separate expected-
failure workflow. Exclude unsupported historical metrics from current paper.
"""
import argparse
import re
from pathlib import Path

BANNED={
  "lost_auc":r"\b(?:AUC\s*(?:=|of)?\s*0\.943|0\.943\s*AUC)\b",
  "lost_f1":r"\b(?:F1\s*(?:=|of)?\s*0\.883|0\.883\s*F1)\b",
  "unsupported_superiority":r"\b(?:state[- ]of[- ]the[- ]art|first[- ]of[- ]its[- ]kind|the first graph[- ]?rag)\b",
  "unsupported_scale":r"\b(?:petabyte[- ]scale (?:throughput|performance)|millions of statements per day)\b",
  "wrong_embeddings":r"\bAnthropic(?:'s)? (?:native )?(?:text )?embedding(?:s)?\b",
  "unmeasured_model_speed":r"\bsub[- ]three[- ]second real[- ]time fraud detection\b",
  "fake_org_loss":r"\b5\.38 trillion\b",
  "fraud_probabilities":r"\bposterior probability of fraud\b",
}
EVIDENCE_MARKERS=(
    "research/verified_runs/fraudrag_v2_20261026",
    "40362679991",
    "40363144409",
    "40366478963",
    "40366949592",
)

def check(p):
    text=Path(p).read_text(encoding="utf8")
    problems=[]
    for name,pat in BANNED.items():
        for m in re.finditer(pat,text,flags=re.IGNORECASE):
            problems.append((name,m.group(0)))
    if "NOT APPROVED FOR JOURNAL SUBMISSION" not in text:
        problems.append(("editorial_status","draft clearance banner missing"))
    if not any(m in text for m in EVIDENCE_MARKERS):
        problems.append(("provenance","no committed experiment references"))
    return problems

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("path",default="docs/FraudRAG_VERIFIED_WORKING_DRAFT.md",nargs="?")
    args=parser.parse_args()
    problems=check(args.path)
    for label,ex in problems:
        print("BLOCK:",label,repr(ex))
    if problems:
        raise SystemExit(f"Submission text not cleared: {len(problems)} unsafe claims")
    print("PASS: current manuscript excludes known prohibited legacy claims. Manual source and external validity review still required.")

if __name__=="__main__":
    main()
