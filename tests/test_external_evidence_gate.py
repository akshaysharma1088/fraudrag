"""Test illegal data promotion never becomes publication evidence."""
import hashlib,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"benchmark"))
from external_evidence_gate import assess

def fixture(tmp_path):
    raw=b"FAKE PUBLIC SYNTHETIC TEST CONTENT"
    (tmp_path/"sample.txt").write_bytes(raw)
    sample={"sample_id":"fixture_001","relative_path":"sample.txt",
       "sha256":hashlib.sha256(raw).hexdigest(),"document_group":"source1",
       "source_institution_group":"institution1","label":"tampered",
       "split":"test","label_origin":"controlled_synthetic_edit",
       "label_evidence_id":"test-manipulation-1",
       "reference_as_of_date":"2026-01-01","submission_date":"2026-01-02"}
    return {"dataset_id":"demo-dataset","version":"1","task":"synthetic_text_edit",
       "description":"Fake test fixture","rights":{"license_or_permission_url":"https://example.com/permission",
       "permitted_research_use":"noncommercial","approval_reference":"fixture-test-only",
       "data_controller":"fictional test","third_party_redistribution_allowed":False},
       "split_policy":"source_document_group_disjoint",
       "independent_annotation_protocol":{"method":"controlled algorithmic label"},
       "files":[sample]}

def test_noncommercial_synthetic_can_pass_structure_but_never_promotion(tmp_path):
    record=fixture(tmp_path)
    assert assess(record,tmp_path)["pass"]
    promoted=assess(record,tmp_path,promotion=True)
    assert not promoted["pass"]
    assert "wrong_task_for_bank_fraud" in {x["code"] for x in promoted["issues"]}
    assert "not_independently_adjudicated" in {x["code"] for x in promoted["issues"]}

def test_cross_split_source_identity_is_rejected(tmp_path):
    record=fixture(tmp_path)
    second=dict(record["files"][0]);second.update(sample_id="fixture_002",split="train")
    record["files"].append(second)
    result=assess(record,tmp_path)
    assert not result["pass"]
    assert "group_leakage" in {x["code"] for x in result["issues"]}

def test_source_integrity_catches_modified_bytes(tmp_path):
    record=fixture(tmp_path)
    (tmp_path/"sample.txt").write_text("CHANGED")
    assert "hash_mismatch" in {x["code"] for x in assess(record,tmp_path)["issues"]}

def test_future_reference_is_blocked(tmp_path):
    record=fixture(tmp_path)
    record["files"][0]["reference_as_of_date"]="2026-12-31"
    assert "reference_temporal_leakage" in {x["code"] for x in assess(record,tmp_path)["issues"]}

def test_traversal_and_missing_rights_are_blocked(tmp_path):
    record=fixture(tmp_path)
    record["files"][0]["relative_path"]="../secret.txt"
    record["rights"]["approval_reference"]="pending"
    codes={x["code"] for x in assess(record,tmp_path)["issues"]}
    assert "unsafe_path" in codes and "permission_not_granted" in codes
