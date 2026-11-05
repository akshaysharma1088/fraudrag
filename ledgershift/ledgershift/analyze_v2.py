"""Evaluation for the revised study: learned matchers, LLM payee matching and LedgerShift v2.

  python -m ledgershift.analyze_v2 [--scores DIR] [--llm-pairs DIR] [--escalation DIR]

Reads the score caches written by scorers.py and the LLM outputs published by the
workflow, plugs every matcher into the same deterministic linker and contract,
tunes every threshold on dev only, and writes results_v2/analysis.json.
"""
from __future__ import annotations

import argparse
import json
import random
from collections import Counter
from pathlib import Path

from . import run as R
from . import verify as V
from .generator import read_jsonl
from .scorers import OUT as SOUT, load_scores

LEARNED = ["embed_minilm", "embed_bge", "ditto"]


# ---------------- pair-level ----------------
def auc(labels, scores):
    pos = [s for l, s in zip(labels, scores) if l == 1]; neg = [s for l, s in zip(labels, scores) if l == 0]
    if not pos or not neg:
        return None
    wins = sum((p > n) + 0.5 * (p == n) for p in pos for n in neg)
    return round(wins / (len(pos) * len(neg)), 4)


def binary(labels, preds):
    tp = sum(l and p for l, p in zip(labels, preds)); fp = sum((not l) and p for l, p in zip(labels, preds))
    fn = sum(l and not p for l, p in zip(labels, preds)); tn = len(labels) - tp - fp - fn
    prec = tp / (tp + fp) if tp + fp else 0.0; rec = tp / (tp + fn) if tp + fn else 0.0
    return {"n": len(labels), "accuracy": round((tp + tn) / len(labels), 4), "precision": round(prec, 4),
            "recall": round(rec, 4), "f1": round(2 * prec * rec / (prec + rec), 4) if prec + rec else 0.0}


def best_threshold(rows, f):
    grid = [round(0.02 * k, 2) for k in range(51)]
    lab = [r["label"] for r in rows]; sc = [f(r["name"], r["descriptor"]) for r in rows]
    return max(grid, key=lambda t: (binary(lab, [s >= t for s in sc])["f1"], -t))


def pair_eval(matchers, llm):
    sets = {"v2_test": read_jsonl(SOUT / "pairs_v2_test.jsonl")}
    ext = R.ROOT / "external" / "foliome_pairs.jsonl"
    if ext.exists():
        sets["foliome"] = read_jsonl(ext)
    dev = read_jsonl(SOUT / "pairs_v2_dev.jsonl")
    out = {}
    for sname, rows in sets.items():
        lab = [r["label"] for r in rows]
        res = {}
        for m, f in matchers.items():
            t = best_threshold(dev, f)
            sc = [f(r["name"], r["descriptor"]) for r in rows]
            pred = [s >= t for s in sc]
            res[m] = {"threshold_from_dev": t, "auc": auc(lab, sc), **binary(lab, pred),
                      "by_kind": {k: round(sum(p == bool(l) for p, l, r in zip(pred, lab, rows) if r["kind"] == k)
                                           / max(1, sum(r["kind"] == k for r in rows)), 4) for k in sorted({r["kind"] for r in rows})}}
        for m, cache in llm.items():
            got = [(r, cache.get((r["name"], r["descriptor"]))) for r in rows]
            got = [(r, True if r["name"] == r["descriptor"] else v) for r, v in got]
            answered = [(r, v) for r, v in got if v is not None]
            pred = [bool(v) for _, v in answered]; lab2 = [r["label"] for r, _ in answered]
            res[m] = {"answered": len(answered), **binary(lab2, pred),
                      "by_kind": {k: round(sum(p == bool(r["label"]) for (r, _), p in zip(answered, pred) if r["kind"] == k)
                                           / max(1, sum(r["kind"] == k for r, _ in answered)), 4) for k in sorted({r["kind"] for r in rows})}}
        out[sname] = {"n": len(rows), "n_pos": sum(lab), "methods": res}
    return out


# ---------------- statement- and line-level ----------------
def line_metrics(insts, results):
    """Swap detection: share of payee-swapped lines (with evidence present) marked different.
    Genuine-line false difference: share of truly supported lines marked different."""
    sw_hit = sw_n = gen_bad = gen_n = 0
    for inst, res in zip(insts, results):
        st = inst["truth"]["line_status"]
        for lid in inst["truth"]["payee_swapped"]:
            if st.get(lid) == "different":
                sw_n += 1; sw_hit += res["line_status"].get(lid) == "different"
        for lid, s in st.items():
            if s == "supported":
                gen_n += 1; gen_bad += res["line_status"].get(lid) == "different"
    return {"swap_lines": sw_n, "swap_detected": round(sw_hit / max(1, sw_n), 4),
            "genuine_lines": gen_n, "genuine_flagged": round(gen_bad / max(1, gen_n), 4)}


def tune(dev, mode):
    sweep = {t: R.metrics([r["truth"]["label"] for r in dev], [V.run_rules(r, mode, t)["label"] for r in dev])["macro_f1"]
             for t in R.T_GRID}
    return max(R.T_GRID, key=lambda t: (sweep[t], -t)), sweep


def veto(base, other):
    return ["DIFFERENT" if b == "SUPPORTED" and o == "DIFFERENT" else b for b, o in zip(base, other)]


def statement_eval(bench, matchers, llm, escalation_dir=None):
    R.configure(bench)
    dev, test = read_jsonl(R.DATA / "dev.jsonl"), read_jsonl(R.DATA / "test.jsonl")
    info = json.loads((R.OUT / "build.json").read_text())
    truth = [r["truth"]["label"] for r in test]
    preds, lines, thresholds = {}, {}, {}

    def add(name, results):
        preds[name] = [x["label"] for x in results]; lines[name] = line_metrics(test, results)

    add("exact", [V.run_rules(r, "exact") for r in test])
    add("fuzzy", [V.run_rules(r, "fuzzy", info["t_fuzzy"]) for r in test]); thresholds["fuzzy"] = info["t_fuzzy"]
    if bench == "v2":
        add("fuzzy_t0.25", [V.run_rules(r, "fuzzy", 0.25) for r in test])
    add("alias", [V.run_rules(r, "alias", info["t_alias"]) for r in test]); thresholds["alias"] = info["t_alias"]
    for m, f in matchers.items():
        V.EXTERNAL_SIM[m] = f
        t, _ = tune(dev, m); thresholds[m] = t
        add(m, [V.run_rules(r, m, t) for r in test])
    for m, cache in (llm.items() if bench == "v2" else []):
        V.EXTERNAL_SIM[m] = lambda a, b, c=cache: 1.0 if a == b else (1.0 if c.get((a, b)) else 0.0)
        add(m, [V.run_rules(r, m, 0.5) for r in test]); thresholds[m] = 0.5
    oracle = []
    for r in test:
        p, l, pend = V.escalation_request(r, R.HI)
        oracle.append(V.apply_escalation(r, p, l, pend, V.oracle_answers(r, pend)))
    add("escalate_oracle", oracle)
    if escalation_dir:
        by_id = {}
        for f in sorted(Path(escalation_dir).glob("shard_*.json")):
            if not f.name.endswith(".partial.json"):
                by_id.update({x["instance_id"]: x for x in json.loads(f.read_text())})
        if len(by_id) == len(test):
            res = []
            for r in test:
                p, l, pend = V.escalation_request(r, R.HI)
                res.append(V.apply_escalation(r, p, l, pend, by_id[r["instance_id"]]["escalation"]["answers"]))
            add("escalate_llm", res)
    for m in [k for k in list(preds) if k not in ("exact", "fuzzy", "fuzzy_t0.25", "escalate_oracle")]:
        if m != "alias":
            preds[f"veto_{m}"] = veto(preds["fuzzy"], preds[m])
    overall = {m: R.metrics(truth, p) for m, p in preds.items()}
    for m in overall:
        if m in lines:
            overall[m].update(lines[m])
    # paired bootstrap against fuzzy, and break-even cost ratios (missed alterations vs extra alarms)
    cis = {m: R.boot_ci(truth, preds[m], preds["fuzzy"]) for m in preds if m != "fuzzy"}
    breakeven = {}
    for m, p in preds.items():
        removed = sum(t != "SUPPORTED" and f == "SUPPORTED" and q != "SUPPORTED" for t, f, q in zip(truth, preds["fuzzy"], p))
        added_clear = sum(t != "SUPPORTED" and f != "SUPPORTED" and q == "SUPPORTED" for t, f, q in zip(truth, preds["fuzzy"], p))
        added_alarm = sum(t == "SUPPORTED" and f != "DIFFERENT" and q == "DIFFERENT" for t, f, q in zip(truth, preds["fuzzy"], p))
        net = removed - added_clear
        breakeven[m] = {"clearances_removed": removed, "clearances_added": added_clear, "alarms_added": added_alarm,
                        "ratio": round(added_alarm / net, 2) if net > 0 else None}
    payee_only = [i for i, r in enumerate(test) if r["truth"]["manipulations"] and set(r["truth"]["manipulations"]) == {"payee"}] \
        if bench == "v2" else [i for i, r in enumerate(test) if r["truth"]["manipulation"] == "payee"]
    cleared_payee_only = {m: sum(p[i] == "SUPPORTED" for i in payee_only) for m, p in preds.items()}
    by_cond = {c: {m: R.metrics([truth[i] for i, r in enumerate(test) if r["condition"] == c],
                                [p[i] for i, r in enumerate(test) if r["condition"] == c])["accuracy"] for m, p in preds.items()}
               for c in R.CONDITIONS}
    return {"bench": bench, "n_test": len(test), "label_counts": Counter(truth), "thresholds": thresholds,
            "overall": overall, "paired_accuracy_ci95_vs_fuzzy": cis, "breakeven_vs_fuzzy": breakeven,
            "payee_only_statements": len(payee_only), "cleared_payee_only": cleared_payee_only,
            "accuracy_by_condition": by_cond}


def load_llm_pairs(folder):
    out = {}
    for d in sorted(Path(folder).glob("*")) if Path(folder).exists() else []:
        cache = {}
        files = sorted(f for f in d.glob("shard_*.json") if not f.name.endswith(".partial.json"))
        for f in files:
            for x in json.loads(f.read_text()):
                if x["same_payee"] is not None:
                    cache[(x["name"], x["descriptor"])] = x["same_payee"]
        if cache:
            out["llm_" + d.name] = cache
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--scores", default=str(SOUT)); ap.add_argument("--llm-pairs", default=str(SOUT / "llm_pairs"))
    ap.add_argument("--escalation", default=None)
    a = ap.parse_args()
    matchers = {m: load_scores(m, a.scores) for m in LEARNED if (Path(a.scores) / f"scores_{m}.json.gz").exists()}
    llm = load_llm_pairs(a.llm_pairs)
    res = {"pairs": pair_eval(matchers, llm),
           "v1": statement_eval("v1", matchers, {}),
           "v2": statement_eval("v2", matchers, llm, a.escalation)}
    R.configure("v2")
    (R.OUT / "analysis.json").write_text(json.dumps(res, indent=2))
    for b in ("v1", "v2"):
        print("==", b)
        for m, v in res[b]["overall"].items():
            print(f"  {m:22s} acc {v['accuracy']:.3f} f1 {v['macro_f1']:.3f} clear {v['false_clearance']:.3f} alarm {v['false_alarm']:.3f}"
                  + (f" swapdet {v['swap_detected']:.3f} genflag {v['genuine_flagged']:.3f}" if "swap_detected" in v else ""))


if __name__ == "__main__":
    random.seed(0)
    main()
