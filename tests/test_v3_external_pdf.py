"""No-network v3 unit tests. Runtime integration actually downloads 5 PDFs."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"benchmark"))
from v3_external_pdf import create_variants, normalize, classify, rates, mutate_number, EXPECTED_SHA256


def test_five_immutable_publisher_hashes():
    assert len(EXPECTED_SHA256) == 5
    assert all(len(s)==64 for s in EXPECTED_SHA256.values())


def test_controlled_edits_and_ground_truth_are_distinct_from_actual_fraud():
    sample="Account Test\nStatement\n2026-08-01 1,230.40 debit\n2026-08-02 10.99 credit\n"
    rows,exclusions=create_variants("bsb-001",sample)
    assert len(rows)==4
    assert not exclusions
    assert sum(row["injected_change"] for row in rows)==2
    assert all("fraud" not in row["ground_truth_origin"] or
               "NOT a fraud label" in row["ground_truth_origin"] for row in rows)
    for row in rows:
        expected=int(row["injected_change"])
        assert classify(row["text"],sample,"full_original")==expected
        assert classify(row["text"],sample,"no_source") is None
    assert len({row["text"] for row in rows})==4


def test_format_only_edit_is_not_a_positive():
    sample="First field   Second field 1,234.56\n"
    rows,_=create_variants("bsb-001",sample)
    benign=next(r for r in rows if r["edit_type"]=="benign_spacing")
    assert normalize(benign["text"]) == normalize(sample)


def test_partial_reference_never_certifies_legitimate():
    statement="Original row with value 111.00 and next item 900.00"
    assert classify(statement,statement,"first_30_tokens") is None
    assert classify(statement,statement,"no_source") is None
    changed=statement.replace("111.00","211.00")
    assert classify(changed,statement,"first_30_tokens")==1


def test_abstentions_are_not_silently_scored_as_legitimate():
    rows=[{"injected_change":0},{"injected_change":1}]
    o=rates(rows,[None,None])
    assert o["abstentions"]==2 and o["accuracy_with_abstentions_as_errors"]==0
    assert o["fp"]==1 and o["fn"]==1

def test_partial_reference_ignores_long_benign_whitespace_shift():
    source = " ".join(["header"] * 90) + " Balance 10.99"
    noisy = source.replace(" ", "    ", 1)
    assert classify(noisy, source, "first_30_tokens") is None
    late_edit = source.replace("10.99", "10.98")
    assert classify(late_edit, source, "first_30_tokens") is None
