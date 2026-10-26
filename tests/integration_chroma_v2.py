"""Actual Chroma query integration using data generated from scratch."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"benchmark"))
from fraudrag_v2 import generate
from chroma_historical_v2 import build_index,get_retrieval


def main():
    rows=generate(16,20261026)
    _,index,vectorizer=build_index(rows)
    assert index.count()==16
    rows=sorted(rows,key=lambda x:x["case_id"])
    checked=0
    for row in rows[:40]:
        matches=get_retrieval(index,vectorizer,row,k=3)
        assert matches
        assert all(m["recorded_at"]<row["submission_date"] for m in matches)
        assert all("fraud_label" not in m["text"] and "tamper_type" not in m["text"]
                   for m in matches)
        assert all(m["id"].startswith("history://") for m in matches)
        checked+=1
    print(f"PASS: real Chroma collection with 16 customer histories; "
          f"{checked} historical retrieval queries obey as-of-date and no-label constraints")

if __name__=="__main__":
    main()
