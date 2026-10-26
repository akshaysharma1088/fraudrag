"""Offline guardrail tests for the external TAT-QA test-set paired QA protocol."""
from experiments.tatqa_test_v7 import normalize, token_f1, sha1_git, select_cases


def test_normalization_and_f1():
    assert normalize("Net revenue: $1,234.") == "net revenue 1 234"
    assert token_f1("Operating profit increased", "operating profit increased")==1.0
    assert 0 <= token_f1("a", "b") <= 1


def test_no_overlap_and_no_label_in_selection():
    dev=[{"table":{"uid":"dev-01"}}]
    test=[]
    for i in range(72):
        test.append({
            "table":{"uid":f"test-{i:03d}"},
            "paragraphs":[{"uid":f"p-{i}","text":"Annual financial report text"}],
            "questions":[{"uid":f"q-{i}","question":"What is the reported change?",
                          "answer_from":"text","answer_type":"span",
                          "answer":["change"]}]})
    cases,groups=select_cases(test,dev)
    assert len(cases)==64
    assert len({x["group"] for x in cases})==64
    assert not any("dev-01"==x["group"] for x in cases)
    assert groups==1
    assert all(x["question"] == "What is the reported change?" for x in cases)


def test_git_blob_hash():
    import hashlib
    raw=b"xyz"
    expected=hashlib.sha1(b"blob 3"+bytes([0])+raw).hexdigest()
    assert sha1_git(raw)==expected
