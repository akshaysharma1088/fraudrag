import subprocess, sys, time
from ledgershift import generator_v2 as G2
from ledgershift import verify as V
from ledgershift.catalogue_v2 import MERCHANTS_V2


def test_v2_deterministic_and_payee_disjoint():
    assert G2.generate(4, 3, "x", "test") == G2.generate(4, 3, "x", "test")
    dev, test = G2.split_families()
    assert dev and test and not (dev & test)
    assert {m[3] for m in MERCHANTS_V2} == dev | test
    dev_names = {m[0] for m in G2.catalogue("dev")}
    for r in G2.generate(6, 5, "x", "test"):
        assert not ({ln["description"] for ln in r["statement"]["lines"]} & dev_names)


def test_v2_alterations_and_ceiling():
    rows = G2.generate(12, 9, "x", "test")
    for r in rows:
        n = len(r["truth"]["manipulations"])
        assert (n == 0) == (r["truth"]["manipulation"] is None) and n <= 3
        p, l, pend = V.escalation_request(r, 0.9)
        assert V.apply_escalation(r, p, l, pend, V.oracle_answers(r, pend))["label"] == r["truth"]["label"], r["instance_id"]


def test_template_regex_matches_generated_descriptors():
    import random
    rng = random.Random(1)
    for name, tmpls, _k, _f in MERCHANTS_V2:
        for t in tmpls:
            assert G2.template_regex(t).match(G2._descriptor(rng, [t])), (name, t)


def test_payee_batch_against_fake_server():
    srv = subprocess.Popen([sys.executable, "tests/fake_ollama.py", "11439"])
    try:
        time.sleep(0.8)
        from ledgershift import llm as L
        L.OLLAMA = "http://127.0.0.1:11439/api/chat"
        out = L.payee_batch("fake", [("Walmart", "WAL-MART #12"), ("Uber", "LYFT *RIDE")])
        assert out["error"] == "" and out["answers"] == {0: True, 1: False}
    finally:
        srv.terminate()
