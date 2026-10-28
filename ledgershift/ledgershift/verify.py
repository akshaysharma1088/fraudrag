"""Verifiers for LedgerShift.

All verifiers share one admissibility contract (``decide``). They differ only
in how statement lines are linked to evidence records:

  exact      exact amount, same date, identical normalized description
  fuzzy      OCR-repaired amounts, posting window, string similarity >= t
  alias      fuzzy plus an oracle merchant alias table (upper bound for curated rules)
  escalate   fuzzy for near-certain links (similarity >= hi); every other line is
             linked by an LLM that sees the line and candidate records. The LLM
             only proposes *which record* (if any) is the same transaction; the
             deterministic contract then compares amounts and dates and decides.

``llm_only`` (in llm.py) gives the LLM the whole statement and evidence and
asks it for the final state directly.
"""
from __future__ import annotations

import datetime as dt
import re
from difflib import SequenceMatcher

from .generator import MERCHANTS

WINDOW = 3            # posting-lag window in days
LINK_WINDOW = 25      # how far apart a candidate may be when proposing links to the LLM
REPAIR = str.maketrans({"O": "0", "o": "0", "l": "1", "I": "1", "i": "1", "S": "5", "s": "5", "B": "8", "b": "6", "Z": "2", "z": "2"})
NOISE = {"pos", "debit", "pmt", "payment", "online", "store", "inc", "llc", "com", "usa", "us", "the", "co"}


# ---------------- parsing ----------------
def parse_amount(text, repair):
    t = text.replace(",", "").strip()
    if repair:
        t = t.translate(REPAIR)
    try:
        return round(float(t) * 100)
    except ValueError:
        return None


def norm(text):
    t = re.sub(r"[^a-z ]", " ", text.lower())
    return " ".join(w for w in t.split() if w not in NOISE and len(w) > 1)


def sim(a, b):
    a, b = norm(a), norm(b)
    if not a or not b:
        return 0.0
    whole = SequenceMatcher(None, a, b).ratio()
    ta, tb = a.split(), b.split()
    token = sum(max(SequenceMatcher(None, x, y).ratio() for y in tb) for x in ta) / len(ta)
    return max(whole, token)


ALIAS = {}
for name, tmpl, _k, _f in MERCHANTS:
    key = norm(tmpl.split("{")[0])
    ALIAS[norm(name)] = key


def alias_sim(line_desc, rec_desc):
    s = sim(line_desc, rec_desc)
    a = ALIAS.get(norm(line_desc))
    if a and norm(rec_desc).startswith(a):
        s = max(s, 1.0)
    return s


def _date(s):
    return dt.date.fromisoformat(s)


# ---------------- linking ----------------
def candidate_options(line, records, amount_of, used=()):
    """Options a line could be linked to: single records and record pairs whose
    amounts sum to the line, within the posting window. Returns (ids, amount, posted)."""
    d = _date(line["date"])
    near = [r for r in records if r["record_id"] not in used and abs((_date(r["posted"]) - d).days) <= LINK_WINDOW]
    opts = [([r["record_id"]], amount_of[r["record_id"]], _date(r["posted"])) for r in near]
    win = [r for r in near if 0 <= (_date(r["posted"]) - d).days <= WINDOW]
    for i in range(len(win)):
        for j in range(i + 1, len(win)):
            a, b = win[i], win[j]
            if amount_of[a["record_id"]] is not None and amount_of[b["record_id"]] is not None:
                opts.append(([a["record_id"], b["record_id"]], amount_of[a["record_id"]] + amount_of[b["record_id"]],
                             min(_date(a["posted"]), _date(b["posted"]))))
    return opts


def deterministic_links(inst, mode, t=None, repair=True):
    """Returns parsed lines, links {line_id: [record ids]}, and per-line best similarity."""
    lines = inst["statement"]["lines"]; recs = inst["evidence"]["records"]
    rec_by = {r["record_id"]: r for r in recs}
    amt = {r["record_id"]: parse_amount(r["amount"], True) for r in recs}
    parsed = {ln["line_id"]: parse_amount(ln["amount"], repair) for ln in lines}
    simf = alias_sim if mode == "alias" else sim
    edges = []
    for ln in lines:
        a = parsed[ln["line_id"]]
        if a is None:
            continue
        d = _date(ln["date"])
        for ids, total, posted in candidate_options(ln, recs, amt):
            lag = (posted - d).days
            if total != a:
                continue
            if mode == "exact":
                if lag != 0 or len(ids) > 1 or norm(rec_by[ids[0]]["description"]) != norm(ln["description"]):
                    continue
                s = 1.0
            else:
                if not 0 <= lag <= WINDOW:
                    continue
                s = max(simf(ln["description"], rec_by[i]["description"]) for i in ids)
            edges.append((s, len(ids), ln["line_id"], ids))
    # merged postings: two lines summing to one record (fuzzy modes only)
    if mode != "exact":
        for r in recs:
            ra = amt[r["record_id"]]
            for i in range(len(lines)):
                for j in range(i + 1, len(lines)):
                    a, b = parsed[lines[i]["line_id"]], parsed[lines[j]["line_id"]]
                    if a is None or b is None or a + b != ra:
                        continue
                    if lines[i]["date"] != lines[j]["date"] or not 0 <= (_date(r["posted"]) - _date(lines[i]["date"])).days <= WINDOW:
                        continue
                    s = min(simf(lines[i]["description"], r["description"]), simf(lines[j]["description"], r["description"]))
                    edges.append((s, 0, (lines[i]["line_id"], lines[j]["line_id"]), [r["record_id"]]))
    edges.sort(key=lambda e: (-e[0], e[1]))
    links, best, used = {}, {}, set()
    for s, _, lid, ids in edges:
        lids = lid if isinstance(lid, tuple) else (lid,)
        for x in lids:
            best[x] = max(best.get(x, 0.0), s)
        thr = 1.0 if mode == "exact" else t
        if s < thr or any(x in links for x in lids) or (any(i in used for i in ids) and not isinstance(lid, tuple)):
            continue
        if isinstance(lid, tuple) and any(i in used for i in ids):
            continue
        for x in lids:
            links[x] = list(ids)
        used.update(ids)
    return parsed, links, best


# ---------------- admissibility contract ----------------
def decide(inst, parsed, links, rejected=(), repair=True):
    """Shared decision contract. ``links`` maps line ids to linked record ids.
    ``rejected`` lists lines for which an identity link exists but disagrees
    (used by escalation when the LLM links a line to a record whose amount or date differ)."""
    lines = inst["statement"]["lines"]; recs = inst["evidence"]["records"]
    complete = inst["evidence"]["coverage_complete"]
    rec_by = {r["record_id"]: r for r in recs}
    amt = {r["record_id"]: parse_amount(r["amount"], True) for r in recs}
    used = {i for ids in links.values() for i in ids}
    status = {}
    for ln in lines:
        lid = ln["line_id"]
        if lid in rejected:
            status[lid] = "different"; continue
        if lid in links:
            alt = [rec_by[i].get("alternate_source") for i in links[lid]]
            conflict = any(a and parse_amount(a["amount"], True) != amt[i] for a, i in zip(alt, links[lid]))
            status[lid] = "conflicting" if conflict else "supported"
            continue
        status[lid] = "different" if complete else "unknown"
    # postings the statement omits: present records nobody links to
    lo = _date(inst["statement"]["period_start"])
    hi = _date(inst["statement"]["period_end"]) + dt.timedelta(days=WINDOW)
    omitted = [r["record_id"] for r in recs if r["record_id"] not in used and lo <= _date(r["posted"]) <= hi]
    vals = set(status.values())
    if "different" in vals or omitted:
        label = "DIFFERENT"
    elif "conflicting" in vals:
        label = "CONFLICTING"
    elif "unknown" in vals or not complete:
        label = "DEFER"
    else:
        label = "SUPPORTED"
    return {"label": label, "line_status": status, "omitted": omitted}


def run_rules(inst, mode, t=0.6):
    repair = mode != "exact"
    parsed, links, _ = deterministic_links(inst, mode, t=t, repair=repair)
    return decide(inst, parsed, links, repair=repair)


# ---------------- selective escalation ----------------
def escalation_request(inst, hi):
    """Lines that deterministic linking cannot resolve at confidence ``hi``, with
    candidate options for the LLM. Returns (parsed, confident_links, request)."""
    parsed, links, best = deterministic_links(inst, "fuzzy", t=hi, repair=True)
    recs = inst["evidence"]["records"]
    amt = {r["record_id"]: parse_amount(r["amount"], True) for r in recs}
    used = {i for ids in links.values() for i in ids}
    pending = []
    unresolved = [ln for ln in inst["statement"]["lines"] if ln["line_id"] not in links]
    for ln in inst["statement"]["lines"]:
        if ln["line_id"] in links:
            continue
        opts = candidate_options(ln, recs, amt, used=used)
        d = _date(ln["date"])
        a = parsed[ln["line_id"]]

        def rank(o):
            ids, total, posted = o
            close_amt = 0 if a is None or total is None else min(1.0, abs(total - a) / max(1, abs(a)))
            return (close_amt, abs((posted - d).days), len(ids))
        opts = sorted(opts, key=rank)[:6]
        shared = []
        if a is not None:
            for other in unresolved:
                b_ = parsed[other["line_id"]]
                if other is ln or b_ is None or other["date"] != ln["date"]:
                    continue
                for r in recs:
                    if r["record_id"] not in used and amt[r["record_id"]] == a + b_ and 0 <= (_date(r["posted"]) - d).days <= WINDOW:
                        shared.append(([r["record_id"]], other["line_id"]))
        if not opts and not shared:
            continue
        options = [{"option_id": f"O{k}", "record_ids": ids} for k, (ids, _, _) in enumerate(opts)]
        options += [{"option_id": f"S{k}", "record_ids": ids, "shared_with": other} for k, (ids, other) in enumerate(shared)]
        pending.append({"line_id": ln["line_id"], "date": ln["date"], "description": ln["description"], "amount": ln["amount"],
                        "options": options})
    return parsed, links, pending


def apply_escalation(inst, parsed, links, pending, answers):
    """Merge LLM link proposals into the deterministic links and decide.
    answers: {line_id: option_id or 'none'}. A proposed link is accepted only if the
    records are still unused; the contract then checks amount and date."""
    recs = inst["evidence"]["records"]
    rec_by = {r["record_id"]: r for r in recs}
    amt = {r["record_id"]: parse_amount(r["amount"], True) for r in recs}
    links = dict(links); used = {i for ids in links.values() for i in ids}
    rejected = set()
    # shared postings first: both lines must point at the same record
    by_line = {p["line_id"]: p for p in pending}
    for p in pending:
        ans = answers.get(p["line_id"], {})
        opt = next((o for o in p["options"] if o["option_id"] == ans.get("option")), None)
        if not opt or "shared_with" not in opt or p["line_id"] in links:
            continue
        q = by_line.get(opt["shared_with"]); qa = answers.get(opt["shared_with"], {})
        qopt = next((o for o in (q or {}).get("options", []) if o["option_id"] == qa.get("option")), None)
        if qopt and qopt.get("shared_with") == p["line_id"] and qopt["record_ids"] == opt["record_ids"] \
                and not any(i in used for i in opt["record_ids"]) and ans.get("same_payee", True) and qa.get("same_payee", True):
            links[p["line_id"]] = list(opt["record_ids"]); links[q["line_id"]] = list(opt["record_ids"])
            used.update(opt["record_ids"])
    for p in pending:
        if p["line_id"] in links:
            continue
        ans = answers.get(p["line_id"], {"option": "none", "same_payee": True})
        choice = ans.get("option", "none")
        opt = next((o for o in p["options"] if o["option_id"] == choice), None)
        if opt is None or "shared_with" in opt or any(i in used for i in opt["record_ids"]):
            continue
        a = parsed[p["line_id"]]
        total = sum(amt[i] for i in opt["record_ids"])
        lag = min((_date(rec_by[i]["posted"]) - _date(p["date"])).days for i in opt["record_ids"])
        used.update(opt["record_ids"])
        if a is not None and a == total and 0 <= lag <= WINDOW and ans.get("same_payee", True):
            links[p["line_id"]] = list(opt["record_ids"])
        else:
            rejected.add(p["line_id"])              # same transaction, but amount or date disagree
            links_hidden = opt["record_ids"]        # the record is explained by this line
            links.setdefault("__consumed__" + p["line_id"], list(links_hidden))
    clean_links = {k: v for k, v in links.items() if not k.startswith("__consumed__")}
    consumed = {i for k, v in links.items() for i in v}
    res = decide(inst, parsed, clean_links, rejected=rejected)
    # records consumed by rejected links are not omissions
    res["omitted"] = [r for r in res["omitted"] if r not in consumed]
    if not res["omitted"] and res["label"] == "DIFFERENT" and "different" not in res["line_status"].values():
        vals = set(res["line_status"].values())
        res["label"] = "CONFLICTING" if "conflicting" in vals else ("DEFER" if "unknown" in vals or not inst["evidence"]["coverage_complete"] else "SUPPORTED")
    return res


def oracle_answers(inst, pending):
    """Answers a perfect linker would give (uses ground truth). For testing and as an upper bound."""
    truth = inst["truth"]["links"]
    out = {}
    swapped = set(inst["truth"].get("payee_swapped", []))
    for p in pending:
        want = sorted(truth.get(p["line_id"], []))
        shared = [k for k, v in truth.items() if k != p["line_id"] and sorted(v) == want]
        opt = next((o["option_id"] for o in p["options"] if sorted(o["record_ids"]) == want
                    and (o.get("shared_with") in shared if shared else "shared_with" not in o)), "none")
        out[p["line_id"]] = {"option": opt, "same_payee": p["line_id"] not in swapped}
    return out
