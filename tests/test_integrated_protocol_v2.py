"""Full synthetic integrated GPT protocol tests with real Neo4j + Chroma."""
import os
import sys
import json
from pathlib import Path
from types import SimpleNamespace
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"experiments"))
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"benchmark"))
from fraudrag_v2_integrated import run, get_sources, seed_stores, MODES
from fraudrag_v2 import generate

def test_real_database_retrieval_and_dry_run(tmp_path,monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY",raising=False)
    rows=generate(120,20261026)
    for row in rows:
        row["graph_reference"]=json.loads(row["graph_reference_json"])
    driver,collection,vec=seed_stores(
        rows,"bolt://localhost:7687","neo4j",os.environ["NEO4J_PASSWORD"])
    try:
        testrow=next(r for r in rows if r["customer_group"]=="C00019")
        for mode in MODES:
            content,ids,sources=get_sources(driver,collection,vec,testrow,mode)
            assert "SUBMITTED STATEMENT" in content
            assert "fraud_label" not in content and "tamper_type" not in content
            assert all(src["recorded_at"] < testrow["submission_date"] for src in sources)
            assert len(ids)==len(set(ids))
            if mode=="document_only":
                assert len(ids)==0
            if mode=="neo4j_only":
                assert len(ids)==1
                assert sources[0]["provider"]=="neo4j"
            if mode=="chroma_only":
                assert len(ids)==3
                assert all(src["provider"]=="chroma" for src in sources)
            if mode=="integrated":
                assert len(ids)==4
                assert {src["provider"] for src in sources}=={"chroma","neo4j"}
    finally:
        driver.close()

    settings=run(SimpleNamespace(
        neo4j_uri="bolt://localhost:7687",neo4j_user="neo4j",
        neo4j_password=os.environ["NEO4J_PASSWORD"],
        out=str(tmp_path),budget=2.0,execute=False))
    assert settings["call_count"]==112
    assert settings["cases"]==28
    assert settings["reserved_cost_usd"]<2
    assert settings["is_actual_neo4j_inference"] is True
    assert settings["is_actual_chroma_inference"] is True
    assert (tmp_path/"integrated_protocol.json").is_file()
    assert not (tmp_path/"integrated_predictions.csv").exists()
