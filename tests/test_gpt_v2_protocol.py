"""No-API safety checks for the precommitted GPT evaluation protocol."""
import sys
from pathlib import Path
from types import SimpleNamespace
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"benchmark"))
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"experiments"))
from fraudrag_v2 import generate
from evaluate_v2 import balanced_holdout
from fraudrag_v2_gpt import prompt, payload, parse_answer, run, MODES, MODEL, reserve_for_call


def _rows():
    train,test=balanced_holdout(generate(120,20261026),4,57)
    for r in test:
        import json
        r["graph_reference"]=json.loads(r["graph_reference_json"])
    unique={r["customer_group"]:r for r in generate(120,20261026)}
    return test,list(unique.values())


def test_prompt_never_injects_oracle_label():
    rows,historical=_rows()
    for mode in MODES:
        txt,available=prompt(rows[0],mode,historical)
        assert rows[0]["statement_text"] in txt
        assert "fraud_label" not in txt
        assert "tamper_type" not in txt
        if mode=="gpt_only":
            assert not available
        if mode=="graph_only":
            assert len(available)==1
        if mode=="vector_only":
            assert len(available)==3
        if mode=="hybrid":
            assert len(available)==4


def test_responses_api_payload_and_parsing():
    rows,historical=_rows()
    p,ids=payload(rows[0],"graph_only",historical)
    assert p["model"]==MODEL and p["store"] is False
    assert p["text"]["format"]["strict"] is True
    assert parse_answer({"status":"incomplete","output":[]}) is None
    assert parse_answer({"status":"completed","output":[
        {"type":"message","content":[{"type":"output_text",
         "text":'{"prediction":"legitimate","evidence_ids":[],"explanation":"no evidence"}'}]}]
    })["prediction"]=="legitimate"
    assert reserve_for_call(len(p["input"][0]["content"]))>0


def test_dry_run_requires_no_api_secret(tmp_path,monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY",raising=False)
    config=run(SimpleNamespace(out=str(tmp_path),n_per_type=4,budget=2.,execute=False))
    assert config["sample_count"]==28
    assert config["planned_calls"]==4*28
    assert config["budget_reservation_usd"]<2
    assert not config["real_api_executed"]
    assert (tmp_path/"gpt_protocol.json").exists()
    assert not (tmp_path/"gpt_metrics.json").exists()
