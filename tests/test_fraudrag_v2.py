"""FraudRAG-v2 reproducibility and leakage/unit controls. No remote APIs."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"benchmark"))
from fraudrag_v2 import generate, TYPES, export
from evaluate_v2 import (
    balanced_holdout, authoritative_comparison, rule_result, parse_statement,
    evaluate_binary, export_results
)
from datetime import date
import json


def test_deterministic_customer_dataset():
    a=generate(120,seed=20261026)
    b=generate(120,seed=20261026)
    assert a==b
    assert len(a)==120*len(TYPES)
    assert a!=generate(120,seed=1)


def test_temporal_provenance_and_synthetic_labels():
    rows=generate(120,seed=20261026)
    for row in rows:
        ref=json.loads(row["graph_reference_json"])
        assert date.fromisoformat(ref["recorded_at"])<date.fromisoformat(row["submission_date"])
        assert row["fraud_label"] == int(row["tamper_type"] not in ("legitimate","hard_negative"))
        assert "fraud" not in row["historical_vector_corpus_text"].casefold()
        assert "fraud" not in row["graph_reference_json"].casefold()


def test_train_and_test_customer_disjoint_and_one_case_per_test_customer():
    train,test=balanced_holdout(generate(120,20261026),4,57)
    assert len(test)==28
    assert len({r["customer_group"] for r in test})==28
    assert set(r["customer_group"] for r in test).isdisjoint(
        {r["customer_group"] for r in train})
    assert set(r["tamper_type"] for r in test)==set(TYPES)


def test_rules_and_trusted_ledger_comparator():
    rows=generate(12,20261026)
    by={r["tamper_type"]:r for r in rows if r["customer_group"]=="C00000"}
    for kind in ("legitimate","hard_negative"):
        assert rule_result(by[kind])["prediction"] == 0
        assert authoritative_comparison(by[kind])["prediction"] == 0
    for kind in ("balance","date"):
        assert rule_result(by[kind])["prediction"] == 1
        assert authoritative_comparison(by[kind])["prediction"] == 1
    for kind in ("amount","entity","fabricated"):
        assert authoritative_comparison(by[kind])["prediction"] == 1
    # The synthetic amount edit was designed to maintain arithmetic consistency.
    assert rule_result(by["amount"])["prediction"] == 0


def test_source_documents_parse_and_metrics_account_for_abstain():
    rows=generate(12,20261026)
    assert all(parse_statement(r["statement_text"]) for r in rows)
    cases=rows[:5]
    metrics=evaluate_binary(cases,[None]*5,"empty")
    assert metrics["abstain"]==5 and metrics["accuracy"]==0
    assert metrics["tp"]+metrics["tn"]+metrics["fp"]+metrics["fn"]==5


def test_regenerate_results_twice(tmp_path):
    one=export_results(tmp_path/"first",120,4,57)
    two=export_results(tmp_path/"second",120,4,57)
    assert one==two
    assert one["n_distinct_evaluation_customers"]==28
    assert one["benchmark"]["csv_sha256"]==two["benchmark"]["csv_sha256"]
