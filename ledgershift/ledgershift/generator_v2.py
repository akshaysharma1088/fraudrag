"""LedgerShift v2: a larger and harder version of the benchmark.

Differences from v1 (generator.py, which is unchanged and hash-checked):

  * 184 payees in 134 families (v1: 34 payees), with several descriptor
    templates per payee (store, online, processor and fuel variants).
  * Payee-disjoint splits. Families are split between dev and test, stratified
    by kind, so nothing tuned or trained on dev has seen a test payee or any of
    its siblings.
  * One to three alterations per altered statement (v1: exactly one), drawn
    from the same five types, on distinct lines.
  * More statements: 100 per condition for dev and 200 per condition for test.

Everything else (conditions, the four states, the ground-truth precedence and
the instance schema) is the same as v1, so every verifier runs unchanged.
"""
from __future__ import annotations

import datetime as dt
import random
import re

from .catalogue_v2 import CITIES, MERCHANTS_V2
from .generator import CONDITIONS, MANIPULATIONS, _amount, _money, _ocr

SPLIT_SEED = 20261104
DEV_SHARE = 0.4


def split_families(merchants=MERCHANTS_V2, seed=SPLIT_SEED, dev_share=DEV_SHARE):
    """Assign each family to dev or test, stratified by the kind of its first payee."""
    first_kind = {}
    for _n, _t, kind, fam in merchants:
        first_kind.setdefault(fam, kind)
    rng = random.Random(seed)
    dev, test = set(), set()
    for kind in sorted(set(first_kind.values())):
        fams = sorted(f for f, k in first_kind.items() if k == kind)
        rng.shuffle(fams)
        k = max(1, round(len(fams) * dev_share)) if len(fams) > 1 else 0
        dev.update(fams[:k]); test.update(fams[k:])
    return dev, test


def catalogue(split):
    dev, test = split_families()
    fams = dev if split == "dev" else test
    return [m for m in MERCHANTS_V2 if m[3] in fams]


def _descriptor(rng, templates):
    t = rng.choice(templates)
    return t.format(n=rng.randint(100, 9999), c=rng.choice(CITIES),
                    a="".join(rng.choice("ABCDEFGHJKLMNPQRSTUVWXYZ23456789") for _ in range(6)))


def template_regex(t):
    """Regex matching every descriptor a template can produce (used by the curated alias table)."""
    parts = re.split(r"(\{[nca]\})", t)
    out = []
    for p in parts:
        out.append({"{n}": r"\d{3,4}", "{a}": r"[A-Z0-9]{6}", "{c}": "(?:" + "|".join(map(re.escape, CITIES)) + ")"}.get(p, re.escape(p)))
    return re.compile("^" + "".join(out) + "$")


def make_instance(rng: random.Random, iid: str, condition: str, manipulated: bool, merchants):
    by_name = {m[0]: m for m in merchants}
    start = dt.date(2026, rng.randint(1, 9), 1)
    n_lines = rng.randint(10, 16)
    opening = rng.randint(80000, 900000)
    mids = rng.sample(range(len(merchants)), k=min(n_lines, len(merchants)))
    lines = []
    for k in range(n_lines):
        name, tmpls, kind, _fam = merchants[mids[k % len(mids)]]
        amt = _amount(rng, kind)
        sign = 1 if kind == "income" else -1
        day = start + dt.timedelta(days=rng.randint(0, 27))
        lines.append({"merchant": name, "templates": tmpls, "kind": kind, "date": day, "amount": sign * amt})
    lines.sort(key=lambda x: x["date"])

    shifted = condition != "clean"
    ledger, line_to_recs, rid = [], {}, 0
    for li, ln in enumerate(lines):
        lag = rng.randint(0, 2) if shifted else 0
        desc = _descriptor(rng, ln["templates"]) if shifted else ln["merchant"]
        ledger.append({"record_id": f"R{rid:03d}", "posted": ln["date"] + dt.timedelta(days=lag),
                       "description": desc, "amount": ln["amount"]})
        line_to_recs[li] = [f"R{rid:03d}"]; rid += 1

    if condition == "split":
        li = rng.randrange(len(lines))
        rec = next(r for r in ledger if r["record_id"] == line_to_recs[li][0])
        part = int(rec["amount"] * rng.uniform(0.3, 0.7))
        rec2 = dict(rec, record_id=f"R{rid:03d}", amount=rec["amount"] - part,
                    posted=rec["posted"] + dt.timedelta(days=rng.randint(0, 1)))
        rec["amount"] = part
        ledger.append(rec2); line_to_recs[li] = [rec["record_id"], rec2["record_id"]]; rid += 1
        base = lines[rng.randrange(len(lines))]
        if base["kind"] != "income":
            extra = dict(base, amount=-_amount(rng, base["kind"]))
            lines.append(extra)
            j = lines.index(base); k = len(lines) - 1
            rb = next(r for r in ledger if r["record_id"] == line_to_recs[j][0])
            if len(line_to_recs[j]) == 1:
                rb["amount"] += extra["amount"]; line_to_recs[k] = list(line_to_recs[j])
            else:
                ledger.append({"record_id": f"R{rid:03d}", "posted": extra["date"],
                               "description": _descriptor(rng, extra["templates"]) if shifted else extra["merchant"],
                               "amount": extra["amount"]})
                line_to_recs[k] = [f"R{rid:03d}"]; rid += 1

    # ---- one to three alterations on distinct lines ----
    stmt = [dict(ln) for ln in lines]
    manips, manip_lines, deleted_recs, swapped = [], {}, [], []
    if manipulated:
        n_alter = rng.choice([1, 2, 3])
        singles = [i for i in range(len(stmt)) if len(line_to_recs[i]) == 1
                   and sum(line_to_recs[i] == line_to_recs[j] for j in line_to_recs) == 1]
        targets = rng.sample(singles, k=min(n_alter, len(singles)))
        for i in targets:
            m = rng.choice(MANIPULATIONS)
            manips.append(m)
            if m == "amount":
                f = rng.choice([10, 0.1, None])
                stmt[i]["amount"] = int(stmt[i]["amount"] * f) if f else stmt[i]["amount"] + rng.choice([-1, 1]) * rng.randint(500, 9000)
                manip_lines[i] = m
            elif m == "date":
                stmt[i]["date"] = stmt[i]["date"] + dt.timedelta(days=rng.choice([-1, 1]) * rng.randint(9, 20))
                manip_lines[i] = m
            elif m == "payee":
                fam = by_name[stmt[i]["merchant"]][3]
                siblings = [x for x in merchants if x[0] != stmt[i]["merchant"] and x[3] == fam]
                same_kind = [x for x in merchants if x[0] != stmt[i]["merchant"] and x[2] == stmt[i]["kind"]]
                pool = siblings if siblings and rng.random() < 0.6 else (same_kind or [x for x in merchants if x[0] != stmt[i]["merchant"]])
                stmt[i]["merchant"] = rng.choice(pool)[0]
                manip_lines[i] = m
            elif m == "insert":
                name, tmpls, kind, _f = rng.choice(merchants)
                stmt.append({"merchant": name, "templates": tmpls, "kind": kind,
                             "amount": (1 if kind == "income" else -1) * _amount(rng, kind),
                             "date": start + dt.timedelta(days=rng.randint(0, 27)), "inserted": True})
                manip_lines[len(stmt) - 1] = m
            elif m == "delete":
                deleted_recs += list(line_to_recs[i]); stmt[i]["deleted"] = True
    order = sorted([k for k in range(len(stmt)) if not stmt[k].get("deleted")], key=lambda k: stmt[k]["date"])
    bal = opening; out_lines = []; orig_to_new = {}
    for n_, k in enumerate(order):
        bal += stmt[k]["amount"]; orig_to_new[k] = f"L{n_:02d}"
        out_lines.append({"line_id": f"L{n_:02d}", "date": stmt[k]["date"].isoformat(), "description": stmt[k]["merchant"],
                          "amount": _money(stmt[k]["amount"]), "balance": _money(bal)})

    coverage_complete, missing = True, set()
    if condition == "partial":
        coverage_complete = False
        k = max(2, int(len(ledger) * rng.uniform(0.2, 0.4)))
        missing = set(r["record_id"] for r in rng.sample(ledger, k))
    conflict_rec = None
    if condition == "conflict":
        touched = set(deleted_recs) | {r for i in manip_lines for r in line_to_recs.get(i, [])}
        pool = [r for r in ledger if r["record_id"] not in touched]
        conflict_rec = rng.choice(pool)["record_id"]

    evid = []
    for r in ledger:
        if r["record_id"] in missing:
            continue
        e = {"record_id": r["record_id"], "posted": r["posted"].isoformat(), "description": r["description"],
             "amount": _money(r["amount"]), "source": "core_ledger"}
        if r["record_id"] == conflict_rec:
            e["alternate_source"] = {"source": "card_processor_feed",
                                     "amount": _money(r["amount"] + rng.choice([-1, 1]) * rng.randint(1000, 8000))}
        evid.append(e)
    rng.shuffle(evid)

    if condition == "ocr":
        for ln in out_lines:
            ln["description"] = _ocr(rng, ln["description"], 0.12)
            ln["amount"] = _ocr(rng, ln["amount"], 0.15)
            ln["balance"] = _ocr(rng, ln["balance"], 0.10)

    status = {}
    for k in order:
        lid = orig_to_new[k]
        if stmt[k].get("inserted"):
            status[lid] = "different" if coverage_complete else "unknown"; continue
        recs = line_to_recs[k]
        if manip_lines.get(k) in ("amount", "date", "payee"):
            status[lid] = "different" if all(r not in missing for r in recs) else "unknown"; continue
        if any(r in missing for r in recs):
            status[lid] = "unknown"
        elif conflict_rec in recs:
            status[lid] = "conflicting"
        else:
            status[lid] = "supported"
    omitted = [r for r in deleted_recs if r not in missing]
    if "different" in status.values() or omitted:
        label = "DIFFERENT"
    elif "conflicting" in status.values():
        label = "CONFLICTING"
    elif "unknown" in status.values() or not coverage_complete:
        label = "DEFER"
    else:
        label = "SUPPORTED"
    truth_links = {orig_to_new[k]: line_to_recs[k] for k in order if not stmt[k].get("inserted")}
    swapped = [orig_to_new[i] for i, m in manip_lines.items() if m == "payee"]
    return {
        "instance_id": iid, "condition": condition,
        "statement": {"period_start": start.isoformat(), "period_end": (start + dt.timedelta(days=27)).isoformat(),
                      "opening_balance": _money(opening), "closing_balance": _money(bal), "lines": out_lines},
        "evidence": {"coverage_complete": coverage_complete, "records": evid},
        "truth": {"label": label, "manipulation": "+".join(manips) if manips else None, "manipulations": manips,
                  "line_status": status, "omitted_records": omitted, "links": truth_links, "payee_swapped": swapped},
    }


def generate(n_per_condition: int, seed: int, prefix: str, split: str):
    rng = random.Random(seed)
    merchants = catalogue(split)
    out = []
    for c in CONDITIONS:
        for i in range(n_per_condition):
            out.append(make_instance(rng, f"{prefix}-{c}-{i:03d}", c, manipulated=(i % 2 == 1), merchants=merchants))
    return out
