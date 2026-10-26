import json,sys,csv
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"benchmark"))
from audit_v3_gpt import TYPES,MODES,EXPECTED
def test_unique_expected_cases():
    assert len(MODES)==3 and len(TYPES)==4 and len(EXPECTED)==5
    assert len({(s,t,m) for s in EXPECTED for t in TYPES for m in MODES})==60
    assert sorted(TYPES.values())==[0,0,1,1]
