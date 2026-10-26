"""FraudRAG-V4 simulated adaptive issuer evidence acquisition.

Ablation / falsification study, NOT validated fraud detection or an original
cost-aware optimization theorem. All planners are DETERMINISTIC and get the
same budget, trained outcome distributions, metadata and latent issuer records.
The DP planner is an exact optimizer for its calibrated independent-action
*model*, not a clairvoyant oracle of unseen realized responses.

Cases, issuer records, successes, costs and timing are FICTIONAL. No API calls,
customer data, actual issuer trust, Neo4j/Chroma lookups or bank fees are used.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
import random
from collections import defaultdict
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from statistics import mean

from provenance_certificate_v4 import Claim, Reference, verify, MATCH, DIFFERENCE

CLAIMS=("account","closing","transaction")
FULL=(1<<len(CLAIMS))-1
ACTIONS=(
    ("single_account",1,10),
    ("single_closing",2,10),
    ("single_transaction",4,10),
    ("primary_bundle",7,22),
    ("backup_bundle",7,31),
)
N_ACTIONS=len(ACTIONS)
TRAIN_SEED=20261101
TEST_SEED=20261102
SHIFT_SEED=20261103
PROFILES=6
BASE_BUDGETS=(30,40,50)
REGRET_COST=0.035
SOURCE_REF="simulation://issuer-reference-not-externally-verified"

# Hypothetical probabilities of authenticated SOURCE AVAILABILITY, NOT learned
# from or representative of actual banks. Metadata is public to all policies.
# Each single source is only capable of one attribute; bundles cover all.
SINGLES_PROB=(
    (.72,.74,.75),(.94,.89,.91),(.32,.30,.41),
    (.73,.58,.79),(.46,.49,.52),(.82,.84,.62),
)
BUNDLE_PRIMARY=(.92,.22,.90,.55,.17,.81)
BUNDLE_BACKUP=(.83,.85,.77,.81,.95,.80)

@dataclass(frozen=True)
class Case:
    case_id: str
    group: str
    profile: int
    origin: tuple[str,str,str]
    submitted: tuple[str,str,str]
    source_masks: tuple[int,...]

def _create_case(profile: int, idx: int, rng: random.Random, *, shifted: bool=False, split="test")->Case:
    original=(f"ACC-{split}-{profile}-{idx:05d}",f"{100+idx%59}.00",f"TX-{split}-{profile}-{idx:05d}:25.00")
    altered=rng.random()<0.25
    submitted=list(original)
    if altered:
        col=rng.randrange(3)
        submitted[col]=original[col]+"-MODIFIED"
    primary_p=BUNDLE_PRIMARY[profile]
    if shifted:
        # Predeclared off-distribution stress: primary bundle reliability
        # collapses; independent single-source availability also drifts.
        primary_p*=.35
    masks=[]
    for a,(_,coverage,_) in enumerate(ACTIONS):
        if a<3:
            p=SINGLES_PROB[profile][a]*(.85 if shifted else 1)
            mask=coverage if rng.random()<p else 0
        else:
            p=primary_p if a==3 else BUNDLE_BACKUP[profile]
            if rng.random()<p:
                # A reachable bundle may have sporadic missing fields;
                # masked source response is discovered ONLY after querying.
                missing_prob=.08 if a==3 else .12
                mask=sum(1<<j for j in range(3) if rng.random()>missing_prob)
            else:
                mask=0
        masks.append(mask)
    return Case(f"{split}-{profile:02d}-{idx:05d}",f"{split}-{profile:02d}-{idx:05d}",profile,original,tuple(submitted),tuple(masks))

def generate(n_per_profile: int, seed:int, *, shifted=False, split="test")->list[Case]:
    rng=random.Random(seed)
    rows=[_create_case(p,i,rng,shifted=shifted,split=split)
          for p in range(PROFILES) for i in range(n_per_profile)]
    rng.shuffle(rows)
    return rows

def estimate_probs(training:list[Case])->dict[int,dict[int,tuple[tuple[int,float],...]]]:
    # Action-level categorical masks estimated ONLY from disjoint calibration
    # cases; no edit labels or sealed outcomes leak into decision policies.
    count=defaultdict(lambda: defaultdict(int))
    totals=defaultdict(int)
    for c in training:
        for idx,mask in enumerate(c.source_masks):
            count[(c.profile,idx)][mask]+=1
            totals[(c.profile,idx)]+=1
    out={}
    for p in range(PROFILES):
        out[p]={}
        for a in range(N_ACTIONS):
            # Laplace regularization over possible subsets of reachable fields
            support=[mask for mask in range(FULL+1) if mask & ~ACTIONS[a][1]==0]
            n=totals[(p,a)]
            out[p][a]=tuple((m,(count[(p,a)][m]+1)/(n+len(support)))
                            for m in support)
            assert abs(sum(x[1] for x in out[p][a])-1)<1e-9
    return out

def available(mask:int,used:int,budget:int)->list[int]:
    return [a for a,(_,_,cost) in enumerate(ACTIONS)
            if not (used & (1<<a)) and cost<=budget and ACTIONS[a][1] & ~mask]

def expected_new(mask:int,a:int,prior)->float:
    return sum(p*((returned & ~mask).bit_count())
               for returned,p in prior[a])

def planner_dp(prior, budget_limit:int):
    """Finite-horizon Bellman plan. Best possible policy under SAME learned
    action-mask probabilities and imposed conditional-independence assumption.
    It is NOT an oracle knowing actual query outputs or real bank truth.
    """
    @lru_cache(maxsize=None)
    def value(mask:int,used:int,budget:int):
        if mask==FULL:
            return 1.0
        best=0.0  # abstain/stop is always allowed
        for a in available(mask,used,budget):
            price=ACTIONS[a][2]
            next_used=used|(1<<a)
            expected=sum(p*value(mask|r,next_used,budget-price)
                         for r,p in prior[a])
            gain=expected-REGRET_COST*price/10
            if gain>best:
                best=gain
        return best

    def decide(mask:int,used:int,budget:int)->int|None:
        if mask==FULL:
            return None
        best=value(mask,used,budget)
        if best<=0:
            return None
        for a in available(mask,used,budget):
            price=ACTIONS[a][2]
            potential=sum(p*value(mask|r,used|(1<<a),budget-price)
                          for r,p in prior[a])-REGRET_COST*price/10
            if abs(potential-best)<1e-11:
                return a
        return None
    return decide

def planner_greedy(prior,mode:str):
    def choose(mask:int,used:int,budget:int)->int|None:
        choices=available(mask,used,budget)
        if not choices:
            return None
        if mode=="prior_greedy":
            return min(choices,key=lambda a:(
                -expected_new(mask,a,prior)/(ACTIONS[a][2]/10),a))
        if mode=="naive_greedy":
            return min(choices,key=lambda a:(
                -((ACTIONS[a][1]&~mask).bit_count())/(ACTIONS[a][2]/10),a))
        if mode=="fixed_order":
            order=[3,0,1,2,4]
            return next(a for a in order if a in choices)
        raise ValueError(mode)
    return choose

def _statement_status(case:Case, acquired:int):
    # Attestation flags in these FICTIONAL source records do not
    # cryptographically authenticate any real bank. All policies call
    # exactly the same deterministic V4 source evaluator.
    cutoff="2026-07-30T23:00:00Z"
    refs=[]
    for j,key in enumerate(CLAIMS):
        if acquired & (1<<j):
            refs.append(Reference(
                source_id=f"{SOURCE_REF}/{case.case_id}/{key}",
                source_family="synthetic-issuer-origin",
                key=key,value=case.origin[j],
                valid_from="2026-07-01T00:00:00Z",
                valid_until="2026-08-01T00:00:00Z",
                recorded_at="2026-07-29T00:00:00Z",
                ingested_at="2026-07-30T00:00:00Z",
                issuer_attested=True,completeness_attested_for_key=True,
                source_digest_sha256=hashlib.sha256((case.case_id+key).encode()).hexdigest()))
    status=verify(
        [Claim(k,case.submitted[j]) for j,k in enumerate(CLAIMS)],
        refs,effective_at="2026-07-30T12:00:00Z",
        as_of_cutoff=cutoff)["document_status"]
    return status

def run_case(case:Case, planner, budget_limit:int)->dict:
    coverage=0
    spent=0
    used=0
    seq=[]
    while coverage!=FULL:
        next_action=planner(coverage,used,budget_limit-spent)
        if next_action is None:
            break
        if next_action not in available(coverage,used,budget_limit-spent):
            raise AssertionError("Planner requested inaccessible/unaffordable source")
        name,mask,cost=ACTIONS[next_action]
        seq.append(name)
        used|=1<<next_action
        spent+=cost
        coverage|=case.source_masks[next_action]
        if spent>budget_limit:
            raise AssertionError("Exceeded shared budget")
    complete=coverage==FULL
    # Conservative study endpoint: demand field-level coverage of ALL three
    # required claims even if partial evidence already shows a difference.
    status=_statement_status(case,coverage) if complete else "ABSTAIN"
    truth=case.submitted!=case.origin
    error=(status==MATCH and truth) or (status==DIFFERENCE and not truth)
    if complete and status not in (MATCH,DIFFERENCE):
        raise AssertionError("Full synthetic source coverage failed to decide")
    if error:
        raise AssertionError("Unexpected contradiction to simulated issuer truth")
    return {"case_id":case.case_id,"profile":case.profile,
            "truth_controlled_edit":int(truth),
            "coverage_mask":coverage,"complete":int(complete),
            "status":status,"cost_units":spent/10,"queries":len(seq),
            "action_sequence":";".join(seq),
            "error_against_synthetic_source":int(error)}

def evaluate(cases,prior,budgets=BASE_BUDGETS):
    rows=[]
    methods=("fixed_order","naive_greedy","prior_greedy","adaptive_dp")
    # Reuse Bellman memoization across each profile and budget. No hidden
    # observed outcomes or ground-truth labels appear in planners.
    plans={}
    for budget in budgets:
        for p in range(PROFILES):
            plans[(p,budget)]={
                "adaptive_dp":planner_dp(prior[p],budget),
                **{mode:planner_greedy(prior[p],mode) for mode in methods if mode!="adaptive_dp"}
            }
    for budget in budgets:
        for case in cases:
            for mode in methods:
                row=run_case(case,plans[(case.profile,budget)][mode],budget)
                row.update({"budget":budget/10,"policy":mode})
                rows.append(row)
    return rows

def metrics(rows):
    by=defaultdict(list)
    for row in rows:
        by[(row["budget"],row["policy"])].append(row)
    result={}
    for (b,m),items in sorted(by.items()):
        count=len(items)
        decided=sum(x["complete"] for x in items)
        avg_cost=mean(x["cost_units"] for x in items)
        result[f"{b:.1f}:{m}"]={
            "n":count,"completed_certificates":decided,
            "certificate_coverage":decided/count,
            "mean_source_access_cost_synthetic_units":round(avg_cost,6),
            "mean_source_queries":round(mean(x["queries"] for x in items),6),
            "total_spent_synthetic_units":round(sum(x["cost_units"] for x in items),6),
            "cost_per_completed_case_synthetic_units":round(sum(x["cost_units"] for x in items)/decided,6) if decided else None,
            "false_clearances":sum(x["error_against_synthetic_source"] for x in items),
            "abstentions":count-decided,
        }
    return result

def paired_bootstrap(rows,*,budget=4.,first="adaptive_dp",second="prior_greedy",seed=20261026,n_boot=1500):
    by=defaultdict(dict)
    for r in rows:
        if r["budget"]==budget:
            by[r["case_id"]][r["policy"]]=r
    keys=sorted(k for k,v in by.items() if first in v and second in v)
    if len(keys)<30:
        raise AssertionError("Insufficient pairs")
    diffs_coverage=[by[k][first]["complete"]-by[k][second]["complete"] for k in keys]
    diffs_cost=[by[k][first]["cost_units"]-by[k][second]["cost_units"] for k in keys]
    rng=random.Random(seed)
    draws=[]
    for _ in range(n_boot):
        ids=[rng.randrange(len(keys)) for j in keys]
        draws.append((
            sum(diffs_coverage[i] for i in ids)/len(ids),
            sum(diffs_cost[i] for i in ids)/len(ids),
        ))
    a=sorted(x for x,y in draws)
    b=sorted(y for x,y in draws)
    cutoff=lambda values:(round(values[int(.025*n_boot)],6),
                          round(values[min(n_boot-1,int(.975*n_boot))],6))
    return {
        "paired_groups":len(keys),"comparison":first+" minus "+second,
        "budget_synthetic_units":budget,
        "coverage_delta":round(mean(diffs_coverage),6),
        "coverage_bootstrap_95pct":cutoff(a),
        "mean_cost_delta_units":round(mean(diffs_cost),6),
        "cost_delta_bootstrap_95pct":cutoff(b),
        "bootstrap_seed":seed,"resamples":n_boot,
        "independence_assumption":"each fictional case is a distinct generated customer group; NOT independent institution or dataset family",
        "not_real_fraud_generalization":True,
    }

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--out",default="artifacts/adaptive_v4")
    p.add_argument("--train-per-profile",type=int,default=180)
    p.add_argument("--test-per-profile",type=int,default=120)
    p.add_argument("--shift-per-profile",type=int,default=60)
    args=p.parse_args()
    if min(args.train_per_profile,args.test_per_profile,args.shift_per_profile)<30:
        raise SystemExit("At least 30 independently seeded customers/profile required")
    output=Path(args.out);output.mkdir(parents=True,exist_ok=True)
    train=generate(args.train_per_profile,TRAIN_SEED,split="train")
    test=generate(args.test_per_profile,TEST_SEED,split="test")
    shift=generate(args.shift_per_profile,SHIFT_SEED,shifted=True,split="shift")
    assert not ({x.case_id for x in train}&{x.case_id for x in test})
    assert not ({x.group for x in train}&{x.group for x in test})
    assert not ({x.case_id for x in train}&{x.case_id for x in shift})
    assert not ({x.group for x in train}&{x.group for x in shift})
    assert not ({x.case_id for x in test}&{x.case_id for x in shift})
    assert not ({x.group for x in test}&{x.group for x in shift})
    priors=estimate_probs(train)
    records={}
    full_results={}
    for name,cases in (("test",test),("shift",shift)):
        predictions=evaluate(cases,priors)
        records[name]=predictions
        full_results[name]={
            "cases":len(cases),
            "policy_metrics":metrics(predictions),
            "dp_vs_prior_greedy":paired_bootstrap(predictions),
        }
        with (output/f"{name}_predictions.csv").open("w",newline="",encoding="utf8") as f:
            writer=csv.DictWriter(f,fieldnames=list(predictions[0]))
            writer.writeheader();writer.writerows(predictions)
    protocol={
        "research_name":"V4 conditional evidence acquisition simulated falsification",
        "design_status":"pilot exploratory synthetic; NOT a claim of algorithm novelty",
        "all_planners_are_deterministic":True,
        "dp_has_access_to_hidden_realized_issuer_outcomes":False,
        "same_cost_metadata_train_distribution_and_budget":True,
        "costs_are_hypothetical_units_NOT_USD":True,
        "issuer_attestation_simulated_not_independently_authenticated":True,
        "source_document_forgeries":0,"real_bank_customers":0,
        "train_seed":TRAIN_SEED,"test_seed":TEST_SEED,"shift_seed":SHIFT_SEED,
        "profiles":PROFILES,"train_cases":len(train),"heldout_cases":len(test),"shift_cases":len(shift),
        "budget_units":[x/10 for x in BASE_BUDGETS],
        "actions":ACTIONS,
        "controller":{"utility":"1 if complete coverage, 0 if defer, minus 0.035 times synthetic source access cost",
                      "DP":"exact expected-value dynamic program under training-estimated conditional independent action outcomes",
                      "greedy":"calibrated expected newly obtained field coverage/cost",
                      "naive":"advertised potential field coverage/cost",
                      "fixed":"fixed publisher-primary bundle, then single sources, then backup"},
        "evaluation_no_label_peeking":True,
        "shift_protocol":"primary bundle reliability multiplied 0.35, singles availability multiplied 0.85 without recalibrating policies",
        "limitations":[
            "All original statements and reference issuers are synthetic",
            "Attestation is assumed via research input, no cryptography",
            "Evidence action response masks generated by same simulator used for calibration, with deliberate shift probe",
            "Dynamic program is a standard deterministic optimizer, not proven novel",
            "Strongest comparator is deterministic dynamic programming with equal metadata; there is NO LLM or GraphRAG gain claim",
            "False-clearance is zero by simulated exact original source construction; not forensic validation",
            "Source access costs are artificial cost units, not real dollar fees or latency",
            "No institution-family-disjoint empirical performance or adversarial OCR",
        ]}
    report={"protocol":protocol,"observed":full_results}
    (output/"protocol_and_results.json").write_text(json.dumps(report,indent=2)+"\n")
    print("ADAPTIVE_V4_VERIFIED_RESULT_START",flush=True)
    print(json.dumps(report,indent=2),flush=True)
    print("ADAPTIVE_V4_VERIFIED_RESULT_END",flush=True)

if __name__=="__main__":
    main()
