"""Check deterministic missing bank-ledger interpretation."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"benchmark"))
from fraudrag_v2 import generate
from evaluate_v2 import parse_statement
from incomplete_evidence_v2 import view_of_reference,score_partial
import json

def test_partial_reference_must_abstain_on_clean_statement():
    r=next(r for r in generate(12,20261026) if r["tamper_type"]=="legitimate")
    ref=json.loads(r["graph_reference_json"])
    assert score_partial(r,view_of_reference(ref,"no_reference",17)) is None
    assert score_partial(r,view_of_reference(ref,"identity_only",17)) is None
    assert score_partial(r,view_of_reference(ref,"partial_ledger",17)) is None
    assert score_partial(r,view_of_reference(ref,"complete",17))==0

def test_real_mismatch_in_available_fact_is_detected():
    r=next(r for r in generate(12,20261026) if r["tamper_type"]=="entity")
    ref=json.loads(r["graph_reference_json"])
    assert score_partial(r,view_of_reference(ref,"identity_only",17))==1
    assert score_partial(r,view_of_reference(ref,"no_reference",17)) is None
