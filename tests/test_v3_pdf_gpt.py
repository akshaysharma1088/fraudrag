import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"benchmark"))
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"experiments"))
from v3_pdf_gpt import MODES,prepare,pack,parse,reserve,summarize

def test_precommitted_references():
    row={"source_id":"bsb-001","text":"X 123.45","case_id":"bsb-001:unchanged","injected_change":0}
    for mode in MODES:
        content,allowed=prepare(row,"X 123.45",mode)
        assert "UNTRUSTED SUBMITTED" in content
        assert "injected_change" not in content
        assert len(allowed)==(0 if mode=="document_only" else 1)
        assert pack(content)["store"] is False
    assert reserve(1000)>0

def test_json_and_abstention():
    rsp={"status":"completed","output":[{"type":"message","content":[{"type":"output_text","text":'{"verdict":"uncertain","evidence_ids":[],"explanation":"No reference"}'}]}]}
    assert parse(rsp)["verdict"]=="uncertain"
    assert parse({"status":"incomplete","output":[]}) is None
    sample=[{"case_id":"x","injected_change":1},{"case_id":"y","injected_change":0}]
    assert summarize(sample,[],"document_only")["abstain"]==2
