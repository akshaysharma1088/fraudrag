"""Smoke checks for synthetic evidence tooling; no external model or database."""
from decimal import Decimal
from benchmark.generate_synthetic import generate
from benchmark.evaluate_balance import evaluate, predict


def test_generation_reproducible():
    assert generate(90, 42) == generate(90, 42)
    assert generate(90, 42) != generate(90, 43)


def test_labels_and_balance_detection():
    rows = generate(90, 42)
    assert sum(int(r["label"]) for r in rows) == 30
    assert all(predict(row) == int(row["label"]) for row in rows)


def test_metric_calculation():
    rows = generate(30, 3)
    m = evaluate(rows)
    assert m["n"] == 30
    assert m["tp"] + m["tn"] + m["fp"] + m["fn"] == 30
    assert m["precision"] == 1
    assert m["recall"] == 1
    assert m["not_paper_results"]
