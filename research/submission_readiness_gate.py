"""Read-only FraudRAG scientific submission readiness decision.

A passing linter cannot prove publication quality. This file makes
unresolved high-stakes dependencies explicit and testable, and NEVER
allows synthetic generated bank ledgers or issuer-year AAER labels to be
promoted into evidence of independently adjudicated bank-document fraud.
"""
from __future__ import annotations
import argparse, json
from pathlib import Path

REQUIRED_FILES=(
 "docs/FraudRAG_VERIFIED_WORKING_DRAFT.md",
 "research/CLAIM_VERIFICATION_REGISTER.md",
 "research/LITERATURE_NOVELTY_AUDIT.md",
 "research/BENCHMARK_V3_PROTOCOL.md",
 "research/RESULTS_V3_EXTERNAL_PDF_2026-10-26.json",
 "research/verified_runs/fraudrag_v2_integrated_20261026/integrated_independent_audit.json",
 "research/verified_runs/fraudrag_v3_external_20261026/independent_audit.json",
)
BLOCKERS={
 "externally_adjudicated_bank_statement_data":"Unresolved: independent genuine/forged bank-statement document labels have not been obtained.",
 "authorized_use_and_privacy_review":"Unresolved: bank data-controller permission, privacy/ethics and noncommercial dataset rights not signed.",
 "non_oracle_external_validation":"Unresolved: no bank-statement experiment with bank-independent reference records and measured errors.",
 "independent_novelty_advantage":"Unresolved: no verified benefit over exact deterministic reconciliation under comparable reference availability.",
 "complete_bibliography_review":"Unresolved: the historical manuscript bibliography has not been verified entry by entry and author signed.",
 "journal_scope_and_author_approval":"Unresolved: journal fit, affiliation, conflict disclosures, author signoff and manuscript policy not finalized.",
}

def review(root:Path):
    missing=[s for s in REQUIRED_FILES if not (root/s).is_file()]
    evidence={}
    if (root/"research/RESULTS_V3_EXTERNAL_PDF_2026-10-26.json").is_file():
        x=json.loads((root/"research/RESULTS_V3_EXTERNAL_PDF_2026-10-26.json").read_text())
        evidence["v3_pdfs_source_verified"]=x.get("source_pdf_count")==5 and x.get("adjudicated_real_fraud_documents")==0
    if (root/"research/verified_runs/fraudrag_v3_external_20261026/independent_audit.json").is_file():
        x=json.loads((root/"research/verified_runs/fraudrag_v3_external_20261026/independent_audit.json").read_text())
        evidence["v3_60_model_calls_source_audited"]=x.get("all_precommitted_pairs_present") is True and x.get("actual_model_calls")==60
    if (root/"research/verified_runs/fraudrag_v2_integrated_20261026/integrated_independent_audit.json").is_file():
        x=json.loads((root/"research/verified_runs/fraudrag_v2_integrated_20261026/integrated_independent_audit.json").read_text())
        evidence["v2_112_actual_integrated_calls_source_audited"]=x.get("observed_pair_count")==112 and not x.get("missing_pairs")
    data_manifest=root/"research/REAL_BANK_FRAUD_APPROVED_MANIFEST.json"
    # A metadata file alone is not a source-and-license attestation.
    if data_manifest.exists():
        evidence["external_real_bank_manifest_claimed"]=True
        evidence["external_real_bank_manifest_verified"]=False
    return {
      "overall_status":"NOT_APPROVED_FOR_JOURNAL_SUBMISSION",
      "engineering_evidence_status":"VERIFIED_SYNTHETIC_COMPONENT_RESULTS",
      "real_world_financial_document_fraud_claims_allowed":False,
      "evidence_presence":evidence,"missing_mandatory_files":missing,
      "scientific_blockers":BLOCKERS,
      "signoff_policy":"Independent, licensed, source-adjudicated bank data plus new reproducible validation and explicit author/ethics/journal signoff required. Automated preflight cannot grant signoff.",
    }

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--root",type=Path,default=Path(__file__).resolve().parents[1])
    parser.add_argument("--assert-approved",action="store_true")
    args=parser.parse_args()
    status=review(args.root)
    print(json.dumps(status,indent=2))
    if status["missing_mandatory_files"]:
        raise SystemExit("Missing research evidence files.")
    if args.assert_approved:
        raise SystemExit("Scientific publication clearance denied: independent bank-fraud validation and human signoffs remain outstanding.")

if __name__=="__main__":
    main()
