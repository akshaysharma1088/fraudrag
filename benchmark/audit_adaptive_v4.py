"""Independent post-run consistency audit of V4 simulated acquisition results.

Reads frozen synthetic case truth, prelearned priors and all prediction rows,
recomputes source-query costs, revealed evidence masks, decisions and policy
aggregates. Does not claim actual issuer authentication or novel outcomes.
"""
from __future__ import annotations
import argparse,csv,hashlib,json,math,random
from collections import defaultdict
from pathlib import Path
from statistics import mean

ACTIONS={
 "single_account":(1,10),"single_closing":(2,10),
 "single_transaction":(4,10),"primary_bundle":(7,22),"backup_bundle":(7,31)
}
POLICIES=("fixed_order","naive_greedy","prior_greedy","adaptive_dp")
BUDGETS=(3.,4.,5.)
FULL=7

def read_csv(path):
    with path.open(newline="",encoding="utf8") as f:
        return list(csv.DictReader(f))

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def check(folder:Path):
    folder=Path(folder)
    bundle=json.loads((folder/"protocol_and_results.json").read_text())
    proto=bundle["protocol"]
    if not proto["all_planners_are_deterministic"] or not proto["dp_has_access_to_hidden_realized_issuer_outcomes"] is False:
        raise ValueError("Protocol cannot be reinterpreted as LLM or clairvoyant planner")
    if digest(folder/"synthetic_cases.csv") != proto["synthetic_cases_csv_sha256"]:
        raise ValueError("Source fixture hash mismatch")
    if digest(folder/"learned_action_priors.json") != proto["learned_action_priors_sha256"]:
        raise ValueError("Calibration prior hash mismatch")
    cases=read_csv(folder/"synthetic_cases.csv")
    if len(cases)!=proto["train_cases"]+proto["heldout_cases"]+proto["shift_cases"]:
        raise ValueError("Missing synthetic source truth rows")
    by_id={}
    groups=defaultdict(set)
    for case in cases:
        key=case["case_id"]
        if key in by_id:raise ValueError("Repeated case")
        by_id[key]=case
        groups[case["split"]].add(case["group_id"])
        if case["split"] not in ("train","test","shift"):
            raise ValueError("Invalid split")
        if int(case["controlled_edit"])!=(json.loads(case["original_issuer_values"])!=json.loads(case["submitted_values"])):
            raise ValueError("Fraud label was not produced by controlled text change")
        if len(json.loads(case["source_masks"]))!=len(ACTIONS):
            raise ValueError("Wrong number of simulated action results")
    for split in ("train","test","shift"):
        if len(groups[split])!=sum(x["split"]==split for x in cases):
            raise ValueError("Groups not unique in split")
    for x,y in (("train","test"),("train","shift"),("test","shift")):
        if groups[x]&groups[y]:raise ValueError("Leaked synthetic document group across train/test/shift")

    summary={}
    for split in ("test","shift"):
        rows=read_csv(folder/f"{split}_predictions.csv")
        expected={(x["case_id"],str(b),p) for x in cases if x["split"]==split
                  for b in BUDGETS for p in POLICIES}
        found=set()
        for row in rows:
            key=(row["case_id"],row["budget"],row["policy"])
            if key in found:raise ValueError("Duplicate policy prediction")
            found.add(key)
            if row["policy"] not in POLICIES or float(row["budget"]) not in BUDGETS:
                raise ValueError("Unexpected policy or budget")
            fixture=by_id.get(row["case_id"])
            if fixture is None or fixture["split"]!=split:
                raise ValueError("Prediction leak from another split")
            if int(row["truth_controlled_edit"])!=int(fixture["controlled_edit"]):
                raise ValueError("Tamper labels differ from source generator")
            action_outcomes=json.loads(fixture["source_masks"])
            actual_cost=0
            seen=set()
            union=0
            for action in filter(None,row["action_sequence"].split(";")):
                if action not in ACTIONS:raise ValueError("Unknown source request")
                if action in seen:raise ValueError("Repeated source request")
                if union==FULL:raise ValueError("Source request after complete coverage")
                seen.add(action)
                action_idx=list(ACTIONS).index(action)
                mask,cost=ACTIONS[action]
                if not (mask & ~union):
                    raise ValueError("Queried source with no remaining relevant attributes")
                union|=action_outcomes[action_idx]
                actual_cost+=cost
                if actual_cost>int(round(float(row["budget"])*10)):
                    raise ValueError("Policy spent more than its allowed budget")
            if union!=int(row["coverage_mask"]):
                raise ValueError("Recorded evidence mask inconsistent with exactly the requested sources")
            if actual_cost/10!=float(row["cost_units"]):
                raise ValueError("Cost does not match actual source-query sequence")
            if len(seen)!=int(row["queries"]):
                raise ValueError("Recorded query count inconsistent")
            iscomplete=union==FULL
            if iscomplete!=bool(int(row["complete"])):
                raise ValueError("Decision coverage mismatch")
            if not iscomplete and row["status"]!="ABSTAIN":
                raise ValueError("Unobserved statement was certified")
            if iscomplete and row["status"]!=(
                "DIFFERENCE_PROVEN" if int(fixture["controlled_edit"]) else "MATCH_SUPPORTED"
            ):
                raise ValueError("Certified claim contradicts synthetic trusted original")
            if int(row["error_against_synthetic_source"])!=0:
                raise ValueError("Simulated verifier accuracy claim not reproducible")
        if found!=expected:
            raise ValueError(f"{split}: {len(expected-found)} missing, {len(found-expected)} excess policy/seed pairs")
        metrics={}
        for budget in BUDGETS:
            for policy in POLICIES:
                records=[x for x in rows if x["budget"]==str(budget) and x["policy"]==policy]
                cost=sum(float(x["cost_units"]) for x in records)
                decided=sum(int(x["complete"]) for x in records)
                key=f"{budget:.1f}:{policy}"
                orig=bundle["observed"][split]["policy_metrics"][key]
                computed=dict(
                    n=len(records),
                    completed_certificates=decided,
                    certificate_coverage=decided/len(records),
                    mean_source_access_cost_synthetic_units=round(cost/len(records),6),
                    total_spent_synthetic_units=round(cost,6),
                    cost_per_completed_case_synthetic_units=round(cost/decided,6) if decided else None,
                    abstentions=len(records)-decided
                )
                for m,v in computed.items():
                    if isinstance(v,(int,str)) or v is None:
                        if v!=orig[m]:raise ValueError("Aggregate does not reproduce "+key+"/"+m)
                    elif not math.isclose(float(v),float(orig[m]),abs_tol=1e-5):
                        raise ValueError("Floating-point aggregate disagreement "+key+"/"+m)
                metrics[key]=computed
        summary[split]={
            "audited_prediction_rows":len(rows),
            "unique_case_groups":len(groups[split]),
            "all_policy_pairs_present":True,
            "queried_masks_and_costs_reproduced":True,
            "no_exceedance_or_premature_certificates":True,
            "recomputed_metrics_at_budget_4":{
                k:v for k,v in metrics.items() if k.startswith("4.0:")
            },
        }
    out={
        "audit":"independent post-run V4 simulated source acquisition",
        "source_sha256":proto["synthetic_cases_csv_sha256"],
        "prior_sha256":proto["learned_action_priors_sha256"],
        "all_planners_deterministic":True,
        "fairness":"same simulated availability outcomes, learned priors, budgets and exact record-consistency checker for all policies",
        "split_and_replay":summary,
        "genuine_financial_fraud_labels":0,
        "actual_bank_issuer_data":0,
        "algorithm_novelty_validated":False,
        "journal_ready":False,
    }
    (folder/"independent_audit.json").write_text(json.dumps(out,indent=2)+"\n")
    print(json.dumps(out,indent=2))
    return out

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--folder",default="artifacts/adaptive_v4")
    args=p.parse_args()
    check(Path(args.folder))

if __name__=="__main__":main()
