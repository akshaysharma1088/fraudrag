from ledgershift.generator import generate, LABELS
from ledgershift.verify import run_rules, escalation_request, apply_escalation, oracle_answers


def test_generator_is_deterministic():
    assert generate(5, 3, "x") == generate(5, 3, "x")


def test_labels_valid_and_balanced():
    rows = generate(20, 4, "x")
    assert all(r["truth"]["label"] in LABELS for r in rows)
    assert {r["truth"]["label"] for r in rows} == set(LABELS)


def test_exact_rules_perfect_on_clean():
    rows = [r for r in generate(20, 5, "x") if r["condition"] == "clean"]
    assert all(run_rules(r, "exact")["label"] == r["truth"]["label"] for r in rows)


def test_oracle_escalation_reaches_ceiling():
    rows = generate(15, 6, "x")
    for r in rows:
        p, l, pend = escalation_request(r, 0.9)
        assert apply_escalation(r, p, l, pend, oracle_answers(r, pend))["label"] == r["truth"]["label"], r["instance_id"]


def test_no_answers_never_clears_more_than_rules():
    # with an LLM that links nothing, escalation can only defer or flag, never clear a manipulated statement
    rows = generate(15, 7, "x")
    for r in rows:
        p, l, pend = escalation_request(r, 0.9)
        lab = apply_escalation(r, p, l, pend, {})["label"]
        if r["truth"]["label"] != "SUPPORTED":
            assert lab != "SUPPORTED"
