"""FraudRAG-EAC service unit tests: no real bank data, no model calls."""
import pytest

from backend.services.eac_service import run_sandbox, SandboxProvider
from benchmark.provenance_certificate_v4 import (
    MATCH, DIFFERENCE, CONFLICT, INSUFFICIENT, UNTRUSTED
)


@pytest.mark.parametrize("policy", ["adaptive_dp", "greedy", "fixed"])
def test_consistent_fixture_gets_complete_certificate(policy):
    output = run_sandbox(scenario="consistent", strategy=policy, budget_units=4.0)
    assert output["sandbox_only"] is True
    assert output["certificate"]["document_status"] == MATCH
    assert output["completed_field_coverage"] is True
    assert output["spent_units"] <= 4.0
    assert output["queries"] == len(output["trace"])
    assert output["certificate"]["preconditions"]["source_issuer_attestation_supplied_not_verified_by_code"]


@pytest.mark.parametrize("policy", ["adaptive_dp", "greedy", "fixed"])
def test_deliberate_balance_edit_detected_without_fraud_judgment(policy):
    result = run_sandbox(scenario="altered", strategy=policy, budget_units=4.0)
    assert result["certificate"]["document_status"] == DIFFERENCE
    assert "fraud" not in result["certificate"]["document_status"].lower()
    assert result["certificate"]["field_results"]["closing"]["witness_source_ids"]
    assert result["spent_units"] <= result["budget_units"]


def test_missing_required_transaction_never_results_in_supported_match():
    for mode in ("adaptive_dp", "greedy", "fixed"):
        result = run_sandbox(scenario="partial", strategy=mode, budget_units=8.0)
        assert result["completed_field_coverage"] is False
        assert result["certificate"]["document_status"] in (INSUFFICIENT, UNTRUSTED)
        assert "transaction" in result["certificate"]["unresolved_fields"]


def test_future_dated_issuer_records_not_validated_at_decision_cutoff():
    output = run_sandbox(scenario="future", strategy="fixed", budget_units=8.0)
    assert output["completed_field_coverage"] is False
    assert output["certificate"]["document_status"] in (UNTRUSTED, INSUFFICIENT)
    assert all(not r["newly_covered_fields"] for r in output["trace"])


def test_conflicting_fictional_issuer_sources_are_explicitly_visible():
    output = run_sandbox(scenario="conflicting", strategy="adaptive_dp")
    assert output["certificate"]["document_status"] == CONFLICT
    assert output["queries"] == 0
    assert output["spent_units"] == 0
    assert len(output["certificate"]["field_results"]["closing"]["witness_source_ids"]) == 2


@pytest.mark.parametrize("scenario", ["consistent", "altered", "partial", "conflicting", "future"])
def test_endpoints_never_claim_independent_bank_authentication(scenario):
    output = run_sandbox(scenario=scenario)
    assert output["sandbox_only"]
    assert "fictional" in output["disclaimer"].lower()
    assert output["certificate"]["preconditions"]["no_real_fraud_inference"]


def test_replaying_same_scenario_produces_identical_certificate_and_action_trace():
    a = run_sandbox(scenario="consistent")
    b = run_sandbox(scenario="consistent")
    assert a == b


@pytest.mark.parametrize("scenario,policy,budget", [
    ("invalid", "fixed", 4),
    ("consistent", "unknown", 4),
    ("consistent", "adaptive_dp", 9),
    ("consistent", "adaptive_dp", 0),
    ("consistent", "adaptive_dp", 3.14),
])
def test_invalid_scopes_and_unbounded_inputs_fail_closed(scenario, policy, budget):
    with pytest.raises(ValueError):
        run_sandbox(scenario=scenario, strategy=policy, budget_units=budget)


def test_source_fixtures_cannot_be_clobbered_by_request_content():
    provider = SandboxProvider("consistent")
    with pytest.raises(ValueError):
        provider.fetch("https://external-bank.example/ledger")
