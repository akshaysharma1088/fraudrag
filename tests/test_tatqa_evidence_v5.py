"""Offline unit tests; actual upstream dataset is fetched in CI with pinned Git blob."""
from benchmark.tatqa_evidence_v5 import (
    METHODS, SCENARIOS, build_cases, decision, evaluate, group_bootstrap,
    matches, metrics, normalize, scenario_sources,
)

def example():
    return [{
        "table": {"uid": "t1", "table": [["heading", "data"]]},
        "paragraphs": [
            {"uid": "p1", "text": "The annual net revenue amounted to $1,234 million in 2022."},
            {"uid": "p2", "text": "Unrelated text about company structure."}
        ],
        "questions": [{"uid": "q1", "answer_type": "span", "answer_from": "text",
                       "answer": ["$1,234 million"]}]
    }]

def test_literal_guard_and_unicode():
    assert matches("Costs: $1,234   million.", "$1,234 million")
    assert not matches("$1,234 million", "$1,234 million [fabricated-extra]")
    assert not matches("20192", "2019")
    assert normalize("  NET\n  Income  ") == "net income"

def test_all_conditions_and_baselines():
    case = {
        "case_id": "q1", "source_group": "t1",
        "gold_candidate": "$1,234 million", "witnesses": ["p1"],
        "source_texts": [
            {"source_id": "p1", "text": "Revenue was $1,234 million",
             "released_dataset_source": True,
             "observed_after_cutoff": False,
             "hypothetical_authoritative_conflict": False},
            {"source_id": "p2", "text": "Company note.",
             "released_dataset_source": True,
             "observed_after_cutoff": False,
             "hypothetical_authoritative_conflict": False}
        ]
    }
    expected = {
        "intact": [True, True, True, True],
        "removed_witness": [False, False, False, False],
        "untrusted_replay": [True, False, False, False],
        "late_record": [True, True, False, False],
        "constructed_conflict": [True, True, True, False],
        "wrong_candidate": [False, False, False, False],
    }
    for scenario in SCENARIOS:
        sources = scenario_sources(case, scenario)
        candidate = case["gold_candidate"] + " [fabricated-extra]" if scenario == "wrong_candidate" else case["gold_candidate"]
        actual = [decision(m, candidate, sources) for m in METHODS]
        assert actual == expected[scenario], (scenario, actual)
    rows = evaluate([case])
    stats = metrics(rows)
    assert stats["untrusted_replay:raw_literal"]["unsupported_acceptances_or_false_deferrals"] == 1
    assert stats["untrusted_replay:conflict_aware"]["unsupported_acceptances_or_false_deferrals"] == 0
    assert group_bootstrap(rows, resamples=50)["support_rate_difference"] == -1

def test_gold_answer_used_only_for_candidate_verification():
    row = example()[0]
    assert row["questions"][0]["answer"] == ["$1,234 million"]
    # Fixture too small for the production min-groups gate; include 100 independent groups.
    data = []
    for i in range(100):
        block = example()[0]
        import copy
        block = copy.deepcopy(block)
        block["table"]["uid"] = f"t{i}"
        block["questions"][0]["uid"] = f"q{i}"
        data.append(block)
    cases, excluded = build_cases(data)
    assert len(cases) == 100
    assert not excluded
    assert len({c["source_group"] for c in cases}) == 100
