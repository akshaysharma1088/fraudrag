"""Unit tests for read-only paired V4 sensitivity analysis."""
from benchmark.v4_paired_sensitivity import exact_mcnemar_p, summarize

def _pair(dp,greedy,profile="0",dc=1.0,gc=1.5):
    return ({"complete":str(dp),"cost_units":str(dc),"profile":profile},
            {"complete":str(greedy),"cost_units":str(gc),"profile":profile})

def test_mcnemar_exact():
    assert exact_mcnemar_p(0,0)==1
    assert exact_mcnemar_p(1,0)==1
    assert abs(exact_mcnemar_p(6,0) - 0.03125)<1e-12
    assert exact_mcnemar_p(5,5)==1

def test_paired_summary():
    result=summarize([_pair(1,1),_pair(1,0),_pair(0,1),_pair(0,0)])
    assert result["both_completed"]==1
    assert result["neither_completed"]==1
    assert result["dp_only_completed"]==1
    assert result["greedy_only_completed"]==1
    assert result["dp_coverage"]==result["greedy_coverage"]==0.5
    assert result["mean_cost_difference_all_cases_synthetic_units"]==-0.5
