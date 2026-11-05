"""LedgerShift experiment driver.

  python -m ledgershift.run build                 # write dev and test sets, tune the fuzzy threshold on dev
  python -m ledgershift.run rules                 # deterministic verifiers on test
  python -m ledgershift.run llm --shard i --nshards n --model qwen2.5:7b-instruct
                                                  # LLM-only and escalation calls for one shard of test
  python -m ledgershift.run evaluate              # merge shards and compute every table
"""
from __future__ import annotations

import argparse
import hashlib
import json
import random
from collections import Counter, defaultdict
from pathlib import Path

from . import generator_v2
from . import verify as V
from .generator import CONDITIONS, LABELS, generate, read_jsonl, write_jsonl
from .verify import apply_escalation, escalation_request, oracle_answers, run_rules

ROOT = Path(__file__).resolve().parents[1]
DATA, OUT = ROOT / "data", ROOT / "results"
DEV_SEED, TEST_SEED = 20261101, 20261102
N_DEV, N_TEST = 40, 60          # instances per condition
HI = 0.9                        # escalation confidence, fixed before any test run
BENCH = "v1"


def configure(bench):
    """v1 is the original benchmark (unchanged). v2 is larger, payee-disjoint and multi-alteration."""
    global DATA, OUT, DEV_SEED, TEST_SEED, N_DEV, N_TEST, BENCH
    BENCH = bench
    if bench == "v2":
        DATA, OUT = ROOT / "data_v2", ROOT / "results_v2"
        DEV_SEED, TEST_SEED, N_DEV, N_TEST = 20261201, 20261202, 100, 200
        V.use_catalogue_v2()


def _generate(n, seed, split):
    if BENCH == "v2":
        return generator_v2.generate(n, seed, split, split)
    return generate(n, seed, split)
T_GRID = [round(0.05 * k, 2) for k in range(20)]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def metrics(truth, pred):
    n = len(truth)
    acc = sum(t == p for t, p in zip(truth, pred)) / n
    f1s = []
    for c in LABELS:
        tp = sum(t == c and p == c for t, p in zip(truth, pred))
        fp = sum(t != c and p == c for t, p in zip(truth, pred))
        fn = sum(t == c and p != c for t, p in zip(truth, pred))
        if tp + fp + fn:
            f1s.append(0 if tp == 0 else 2 * tp / (2 * tp + fp + fn))
    not_sup = [p for t, p in zip(truth, pred) if t != "SUPPORTED"]
    sup = [p for t, p in zip(truth, pred) if t == "SUPPORTED"]
    return {"n": n, "accuracy": round(acc, 4), "macro_f1": round(sum(f1s) / len(f1s), 4),
            "false_clearance": round(sum(p == "SUPPORTED" for p in not_sup) / max(1, len(not_sup)), 4),
            "false_alarm": round(sum(p == "DIFFERENT" for p in sup) / max(1, len(sup)), 4),
            "defer_rate": round(sum(p == "DEFER" for p in pred) / n, 4)}


def build():
    DATA.mkdir(exist_ok=True); OUT.mkdir(exist_ok=True)
    dev, test = _generate(N_DEV, DEV_SEED, "dev"), _generate(N_TEST, TEST_SEED, "test")
    write_jsonl(dev, DATA / "dev.jsonl"); write_jsonl(test, DATA / "test.jsonl")
    sweep = {}
    for t in T_GRID:
        sweep[t] = metrics([r["truth"]["label"] for r in dev], [run_rules(r, "fuzzy", t)["label"] for r in dev])["macro_f1"]
    t_star = max(T_GRID, key=lambda t: (sweep[t], -t))
    alias = {t: metrics([r["truth"]["label"] for r in dev], [run_rules(r, "alias", t)["label"] for r in dev])["macro_f1"] for t in T_GRID}
    t_alias = max(T_GRID, key=lambda t: (alias[t], -t))
    info = {"dev_sha256": sha(DATA / "dev.jsonl"), "test_sha256": sha(DATA / "test.jsonl"),
            "n_dev": len(dev), "n_test": len(test), "fuzzy_dev_sweep_macro_f1": sweep, "t_fuzzy": t_star,
            "alias_dev_sweep_macro_f1": alias, "t_alias": t_alias, "escalation_hi": HI,
            "test_label_counts": Counter(r["truth"]["label"] for r in test),
            "test_manipulation_counts": Counter(str(r["truth"]["manipulation"]) for r in test),
            "test_payee_swapped_lines": sum(len(r["truth"]["payee_swapped"]) for r in test),
            "test_statements_with_swap": sum(bool(r["truth"]["payee_swapped"]) for r in test)}
    (OUT / "build.json").write_text(json.dumps(info, indent=2))
    print(json.dumps({k: info[k] for k in ("t_fuzzy", "t_alias", "n_test")}))


def rules(split="test"):
    info = json.loads((OUT / "build.json").read_text()); test = read_jsonl(DATA / f"{split}.jsonl")
    rows = []
    for r in test:
        p, l, pend = escalation_request(r, HI)
        oracle = apply_escalation(r, p, l, pend, oracle_answers(r, pend))["label"]
        rows.append({"instance_id": r["instance_id"], "condition": r["condition"], "truth": r["truth"]["label"],
                     "exact": run_rules(r, "exact")["label"], "fuzzy": run_rules(r, "fuzzy", info["t_fuzzy"])["label"],
                     "alias": run_rules(r, "alias", info["t_alias"])["label"], "escalate_oracle": oracle,
                     "escalated_lines": len(pend), "total_lines": len(r["statement"]["lines"])})
    (OUT / ("rules_predictions.json" if split == "test" else f"rules_predictions_{split}.json")).write_text(json.dumps(rows, indent=1))
    print("rules done", len(rows))


def _escalate(L, model, r, hi):
    p, l, pend = escalation_request(r, hi)
    if not pend:
        return {"answers": {}, "prompt_tokens": 0, "output_tokens": 0, "seconds": 0, "error": "", "content": "",
                "pending_lines": 0, "label": apply_escalation(r, p, l, pend, {})["label"]}
    e = L.link(model, r, pend)
    return {"answers": e["answers"], "prompt_tokens": e["prompt_tokens"], "output_tokens": e["output_tokens"],
            "seconds": e["seconds"], "error": e["error"], "content": e["content"], "pending_lines": len(pend),
            "label": apply_escalation(r, p, l, pend, e["answers"])["label"]}


def llm(shard, nshards, model, split="test", prompt="v1"):
    from . import llm as L
    L.PROMPT_VERSION = prompt
    info = json.loads((OUT / "build.json").read_text())
    test = read_jsonl(DATA / f"{split}.jsonl")
    mine = [r for k, r in enumerate(test) if k % nshards == shard]
    out = []
    for r in mine:
        rec = {"instance_id": r["instance_id"], "model": model}
        if BENCH == "v1":            # v2 runs selective escalation only (LLM-only and residual were settled on v1)
            o = L.llm_only(model, r)
            rec["llm_only"] = {k: o[k] for k in ("label", "prompt_tokens", "output_tokens", "seconds", "error", "content")}
        rec["escalation"] = _escalate(L, model, r, HI)                 # escalate everything below 0.9 similarity
        if BENCH == "v1":
            rec["escalation_residual"] = _escalate(L, model, r, info["t_fuzzy"])  # escalate only what tuned rules leave open
        out.append(rec)
        print(r["instance_id"], r["truth"]["label"], rec["escalation"]["label"], flush=True)
        d = OUT / llm_dir(split, prompt); d.mkdir(parents=True, exist_ok=True)
        (d / f"shard_{shard:02d}.partial.json").write_text(json.dumps(out, indent=1))   # survives a killed job
    d = OUT / llm_dir(split, prompt)
    d.mkdir(parents=True, exist_ok=True)
    (d / f"shard_{shard:02d}.json").write_text(json.dumps(out, indent=1))


def pair_universe():
    """Every pair an LLM payee matcher is asked about: the v2 test linker pairs and the three pair-evaluation sets."""
    from .scorers import OUT as SOUT, requested_pairs
    pairs = set(requested_pairs([ROOT / "data_v2" / "test.jsonl"]))
    for name in ("pairs_v2_test.jsonl", "pairs_v2_dev.jsonl"):
        pairs |= {(r["name"], r["descriptor"]) for r in read_jsonl(SOUT / name)}
    ext = ROOT / "external" / "foliome_pairs.jsonl"
    if ext.exists():
        pairs |= {(r["name"], r["descriptor"]) for r in read_jsonl(ext)}
    return sorted(p for p in pairs if p[0] != p[1])        # identical text needs no judgment


def pairs_llm(shard, nshards, model, batch=10):
    from . import llm as L
    from .scorers import OUT as SOUT
    mine = [p for k, p in enumerate(pair_universe()) if k % nshards == shard]
    d = SOUT / "llm_pairs" / model.replace(":", "_").replace("/", "_"); d.mkdir(parents=True, exist_ok=True)
    out = []
    for i in range(0, len(mine), batch):
        chunk = mine[i:i + batch]
        r = L.payee_batch(model, chunk)
        for k, (a, b) in enumerate(chunk):
            out.append({"name": a, "descriptor": b, "same_payee": r["answers"].get(k), "error": r["error"],
                        "seconds": r["seconds"] if k == 0 else 0})
        print(i, len(mine), r["seconds"], r["error"], flush=True)
        (d / f"shard_{shard:02d}.partial.json").write_text(json.dumps(out))
    (d / f"shard_{shard:02d}.json").write_text(json.dumps(out))


def llm_dir(split, prompt):
    return "llm" if (split, prompt) == ("test", "v1") else f"llm_{split}_{prompt}"


def boot_ci(truth, a, b, reps=5000, seed=11):
    rng = random.Random(seed); n = len(truth); diffs = []
    for _ in range(reps):
        idx = [rng.randrange(n) for _ in range(n)]
        diffs.append(sum((a[i] == truth[i]) - (b[i] == truth[i]) for i in idx) / n)
    diffs.sort()
    return [round(diffs[int(0.025 * reps)], 4), round(diffs[int(0.975 * reps)], 4)]


def evaluate(split="test", prompt="v1"):
    rp = OUT / ("rules_predictions.json" if split == "test" else f"rules_predictions_{split}.json")
    rows = {r["instance_id"]: r for r in json.loads(rp.read_text())}
    d = OUT / llm_dir(split, prompt)
    llm_files = sorted(f for f in d.glob("shard_*.json") if not f.name.endswith(".partial.json")) if d.exists() else []
    usage = defaultdict(lambda: defaultdict(float))
    for f in llm_files:
        for rec in json.loads(f.read_text()):
            row = rows[rec["instance_id"]]
            row["escalate"] = rec["escalation"]["label"]
            if "llm_only" in rec:
                row["llm_only"] = rec["llm_only"]["label"]
            if "escalation_residual" in rec:
                row["escalate_residual"] = rec["escalation_residual"]["label"]
                row["pending_residual"] = rec["escalation_residual"]["pending_lines"]
            for m in ("llm_only", "escalation", "escalation_residual"):
                if m not in rec:
                    continue
                u = rec[m]; usage[m]["calls"] += 1 if u["prompt_tokens"] else 0
                usage[m]["prompt_tokens"] += u["prompt_tokens"]; usage[m]["output_tokens"] += u["output_tokens"]
                usage[m]["seconds"] += u["seconds"]; usage[m]["errors"] += 1 if u["error"] else 0
    rows = list(rows.values())
    methods = ["exact", "fuzzy", "alias", "escalate_oracle"] + [m for m in ("llm_only", "escalate", "escalate_residual") if all(m in r for r in rows)]
    truth = [r["truth"] for r in rows]
    overall = {m: metrics(truth, [r[m] for r in rows]) for m in methods}
    by_cond = {c: {m: metrics([r["truth"] for r in rows if r["condition"] == c], [r[m] for r in rows if r["condition"] == c])
                   for m in methods} for c in CONDITIONS}
    cis = {}
    if "escalate" in methods and "llm_only" in methods:
        for mine_, other in (("escalate", "fuzzy"), ("escalate", "llm_only"), ("escalate_residual", "fuzzy"),
                             ("escalate_residual", "llm_only"), ("llm_only", "fuzzy")):
            cis[f"{mine_}_minus_{other}"] = boot_ci(truth, [r[mine_] for r in rows], [r[other] for r in rows])
    esc_lines = sum(r["escalated_lines"] for r in rows); all_lines = sum(r["total_lines"] for r in rows)
    res = {"overall": overall, "by_condition": by_cond, "paired_accuracy_ci95": cis,
           "escalated_line_share": round(esc_lines / all_lines, 4),
           "instances_with_escalation": sum(r["escalated_lines"] > 0 for r in rows),
           "llm_usage": {m: dict(v) for m, v in usage.items()},
           "confusion": {m: Counter(f"{r['truth']}->{r[m]}" for r in rows) for m in methods}}
    name = "results.json" if (split, prompt) == ("test", "v1") else f"results_{split}_{prompt}.json"
    (OUT / name).write_text(json.dumps(res, indent=2))
    for m in methods:
        print(f"{m:16s}", overall[m])


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("step", choices=["build", "rules", "llm", "evaluate", "pairs_llm"])
    ap.add_argument("--shard", type=int, default=0); ap.add_argument("--nshards", type=int, default=1)
    ap.add_argument("--model", default="qwen2.5:7b")
    ap.add_argument("--split", default="test", choices=["dev", "test"])
    ap.add_argument("--prompt", default="v1", choices=["v1", "v2", "v3"])
    ap.add_argument("--bench", default="v1", choices=["v1", "v2"])
    a = ap.parse_args()
    configure(a.bench)
    if a.step == "build":
        build()
    elif a.step == "rules":
        rules(a.split)
    elif a.step == "evaluate":
        evaluate(a.split, a.prompt)
    elif a.step == "pairs_llm":
        pairs_llm(a.shard, a.nshards, a.model)
    else:
        llm(a.shard, a.nshards, a.model, a.split, a.prompt)
