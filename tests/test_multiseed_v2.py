import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"benchmark"))
from robustness_multiseed_v2 import evaluate, CONDITIONS, SEEDS

def test_reproducibility_and_disjoint_customers():
    a,rows1=evaluate()
    b,rows2=evaluate()
    assert a==b and rows1==rows2
    assert a["n_generated_cases"]==4900
    assert all(r["test_n"]==175 and r["customer_disjoint"] for r in a["per_seed_results"])
    assert all(r["scores"]["complete_ledger"]["accuracy"]==1 for r in a["per_seed_results"])
    assert all(r["scores"]["no_reference"]["abstain"]==175 for r in a["per_seed_results"])
    assert len(rows1)==len(SEEDS)*175*len(CONDITIONS)
