import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"research"))
from submission_readiness_gate import review

def test_real_world_fraud_claims_never_auto_promoted():
    r=review(Path(__file__).resolve().parents[1])
    assert r["overall_status"]=="NOT_APPROVED_FOR_JOURNAL_SUBMISSION"
    assert r["real_world_financial_document_fraud_claims_allowed"] is False
    assert "externally_adjudicated_bank_statement_data" in r["scientific_blockers"]
    assert not r["missing_mandatory_files"]
    assert r["evidence_presence"]["v3_60_model_calls_source_audited"]
    assert r["evidence_presence"]["v2_112_actual_integrated_calls_source_audited"]
