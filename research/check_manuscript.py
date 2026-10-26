"""Fail-closed screen for known unsupported claims in FraudRAG submission DOCX drafts.

This is a NEGATIVE gate. A clean result NEVER proves a paper is correct:
the claim register, source verification, experimental files, and independent
manual review remain mandatory.

Usage: python research/check_manuscript.py docs/*.docx
"""
from __future__ import annotations

import argparse
import re
import sys
import zipfile
from pathlib import Path
from xml.etree import ElementTree

NS = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
# Revisit / retire a rule only after adding experimental run links and raw data
# to research/CLAIM_VERIFICATION_REGISTER.md and obtaining human signoff.
BLOCKED = {
    "legacy_auc": (r"\b0\.943\b", "AUC 0.943 has no recoverable original benchmark."),
    "legacy_f1": (r"\b0\.883\b", "F1 0.883 has no per-sample predictions."),
    "legacy_dataset": (r"\b(?:fraudrag[- ]?2400|2,400(?:-sample|[- ]annotated)?(?: financial)? statements?)\b", "Historical synthetic dataset is missing."),
    "legacy_baseline_metrics": (r"\b0\.(?:741|819|877|893|921|962|951)\b", "Historic baseline, ablation and fraud-type scores lack experiment records."),
    "legacy_improvement": (r"(?:18\s*[-–]\s*24)\s*(?:percentage)?\s*points?", "Unsupported aggregate improvement claim."),
    "unsupported_novelty": (r"\b(?:the first|first ever|state of the art|three original contributions)\b", "Priority/novelty not established through systematic literature review."),
    "unsupported_scale": (r"\b(?:petabyte[- ]scale|scales? to petabyte|millions of documents per day)\b", "No reproducible scale benchmark or deployed evidence."),
    "unsupported_production": (r"\bproduction[- ](?:ready|grade)\b", "No external production validation."),
    "unmeasured_latency": (r"\b(?:sub[- ]3[- ]second|sub[- ]millisecond|<\s*1\s*ms|<\s*50\s*ms|2\.8\s*s|1\.9\s*s)\b", "No supporting system-level latency traces."),
    "wrong_embeddings": (r"\bAnthropic['’]s? (?:text )?embedd(?:ing|ings)\b", "Anthropic does not provide native embedding models; source code uses OpenAI or local embedding fallback."),
    "unverified_peer_review": (r"\bSubmitted to IEEE Transactions\b|(?:journal|publisher)\s*=\s*[\{\"]IEEE Transactions", "Journal submission or publication status must match editorial correspondence."),
    "unsupported_fraud_losses": (r"\b\$5\.38\s*trillion\b", "Cited ACFE source does not give this exact figure for financial document fraud."),
    "unsubstantiated_privacy": (r"\b(?:LLM receives masked|text is not persisted after Bronze layer TTL|SHA-256 hashing of SSN)\b", "Privacy and data-retention controls not demonstrated by repository code."),
    "coincidental_fraud_categories": (r"\bsix fraud types\b", "The historic type table enumerates five classes, and source dataset is missing."),
    "probability_assertion": (r"posterior probability P\(fraud", "LLM score is not empirically calibrated as posterior probability."),
}

def paragraphs(path: Path) -> list[str]:
    try:
        with zipfile.ZipFile(path) as docx:
            root = ElementTree.fromstring(docx.read("word/document.xml"))
    except (KeyError, OSError, zipfile.BadZipFile, ElementTree.ParseError) as exc:
        raise ValueError(f"Cannot read DOCX: {path}: {exc}") from exc
    lines = []
    for para in root.iter(f"{NS}p"):
        txt = "".join((n.text or "") for n in para.iter(f"{NS}t"))
        normalized = " ".join(txt.split())
        if normalized:
            lines.append(normalized)
    return lines

def check(path: Path):
    issues = []
    for idx, text in enumerate(paragraphs(path), start=1):
        for claim_id, (pattern, reason) in BLOCKED.items():
            if re.search(pattern, text, flags=re.IGNORECASE):
                issues.append({
                    "paragraph": idx, "claim_id": claim_id, "reason": reason,
                    "excerpt": text[:190]
                })
    return issues

def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("documents", nargs="+", type=Path)
    args = parser.parse_args(argv)
    total = 0
    for doc in args.documents:
        try:
            findings = check(doc)
        except ValueError as exc:
            print("BLOCK:", exc, file=sys.stderr)
            return 2
        print(f"{doc}: {len(findings)} unresolved unsupported-claim matches")
        for item in findings:
            print(f"  BLOCK {item['claim_id']}: paragraph {item['paragraph']} — {item['reason']}")
            print(f"    {item['excerpt']}")
        total += len(findings)
    if total:
        print(f"\nSUBMISSION BLOCKED: {total} unresolved claim instances. "
              "See research/CLAIM_VERIFICATION_REGISTER.md")
        return 1
    print("Known-claim screen passed; mandatory human and source audit STILL required.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
