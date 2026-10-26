import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"benchmark"))
from audit_adaptive_v4 import ACTIONS,POLICIES,BUDGETS
def test_protocol_has_four_deterministic_competitors():
    assert len(POLICIES)==4
    assert "adaptive_dp" in POLICIES and "prior_greedy" in POLICIES
    assert len(ACTIONS)==5 and BUDGETS==(3.,4.,5.)
