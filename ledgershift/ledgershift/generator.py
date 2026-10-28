"""LedgerShift benchmark generator.

Each instance is a submitted bank statement (what a customer or applicant
hands in) plus reference evidence from the institution (posted ledger
records). The task is to decide, for the whole statement, one of four states:

  SUPPORTED    every line is matched by admissible evidence and nothing is omitted
  DIFFERENT    admissible evidence contradicts at least one line, or shows an omitted posting
  CONFLICTING  admissible reference sources disagree on a record the statement relies on
  DEFER        the evidence is insufficient to decide

Six evidence conditions vary how hard it is to line up the statement with the
evidence while the underlying facts stay the same:

  clean      identical wording, dates and formats
  format     bank descriptors, posting lag of 0 to 2 days
  ocr        format shift plus OCR character noise in the submitted statement
  split      format shift plus postings that merge or split statement lines
  partial    format shift plus an incomplete ledger extract (coverage flag false)
  conflict   format shift plus a second source disagreeing on one record

Half of the instances carry exactly one manipulation that keeps the
statement's own arithmetic consistent (running balances are recomputed).
Ground truth comes from the generator's knowledge of which ledger records
belong to which lines; no model or heuristic is involved.
"""
from __future__ import annotations

import datetime as dt
import json
import random

CONDITIONS = ("clean", "format", "ocr", "split", "partial", "conflict")
MANIPULATIONS = ("amount", "date", "payee", "insert", "delete")
LABELS = ("SUPPORTED", "DIFFERENT", "CONFLICTING", "DEFER")

# (statement display name, bank descriptor template, kind, family)
# Descriptor templates use {n} for a store number and {a} for a reference code.
# Three kinds of difficulty are mixed on purpose:
#   string-recoverable   COSTCO WHSE #1234 for Costco
#   knowledge-dependent  WM SUPERCENTER for Walmart, SBUX for Starbucks, VZWRLSS for Verizon
#   sibling confusables  UBER *TRIP vs UBER *EATS, GOOGLE *YOUTUBE vs GOOGLE *GOOGLE ONE
MERCHANTS = [
    ("Costco", "COSTCO WHSE #{n}", "grocery", "costco"),
    ("Target", "TARGET T-{n}", "shop", "target"),
    ("Home Depot", "THE HOME DEPOT #{n}", "shop", "homedepot"),
    ("Kroger", "KROGER #{n}", "grocery", "kroger"),
    ("CVS Pharmacy", "CVS/PHARMACY #{n}", "health", "cvs"),
    ("Chevron", "CHEVRON {n}", "fuel", "chevron"),
    ("Spotify", "SPOTIFY USA {a}", "sub", "spotify"),
    ("Walmart", "WM SUPERCENTER #{n}", "grocery", "walmart"),
    ("Walmart+", "WMT PLUS {a}", "sub", "walmart"),
    ("Starbucks", "SBUX {n}", "food", "starbucks"),
    ("Verizon Wireless", "VZWRLSS*APOCC VISB", "bill", "verizon"),
    ("Whole Foods", "WFM #{n} AUSTIN", "grocery", "amazon"),
    ("Amazon", "AMZN MKTP US*{a}", "shop", "amazon"),
    ("Amazon Prime", "AMZN PRIME*{a}", "sub", "amazon"),
    ("Prime Video", "PRIME VIDEO*{a}", "sub", "amazon"),
    ("Uber", "UBER *TRIP {a}", "travel", "uber"),
    ("Uber Eats", "UBER *EATS {a}", "food", "uber"),
    ("Google One", "GOOGLE *GOOGLE ONE", "sub", "google"),
    ("YouTube Premium", "GOOGLE *YOUTUBEPREMIUM", "sub", "google"),
    ("Apple Music", "APPLE.COM/BILL", "sub", "apple"),
    ("Apple Store", "APPLE STORE #R{n}", "shop", "apple"),
    ("McDonald's", "MCDONALD'S F{n}", "food", "mcdonalds"),
    ("Dunkin'", "DD/BR #{n} Q35", "food", "dunkin"),
    ("DoorDash", "DD *DOORDASH {a}", "food", "doordash"),
    ("Southwest Airlines", "SOUTHWES {n}", "travel", "southwest"),
    ("Comcast Xfinity", "COMCAST CABLE COMM", "bill", "comcast"),
    ("Duke Energy", "DUKE-ENERGY PAYMENT", "bill", "duke"),
    ("Planet Fitness", "PLANET FIT CLUB FEES", "sub", "planetfitness"),
    ("Payroll Acme Corp", "ACME CORP DIR DEP PPD", "income", "acme"),
    ("Venmo", "VENMO PAYMENT {a}", "transfer", "venmo"),
    ("Zelle", "ZELLE TO {a}", "transfer", "zelle"),
    ("Cash App", "SQ *CASH APP {a}", "transfer", "cashapp"),
    ("ATM Withdrawal", "ATM WITHDRAWAL {n}", "transfer", "atm"),
    ("Rent Payment", "ONLINE PMT RENT LLC", "bill", "rent"),
]
SUB_PRICES = [299, 999, 1099, 1199, 1399, 1499, 1549, 1799]
ROUND = [2000, 2500, 4000, 5000, 6000, 10000, 15000, 20000, 25000, 30000]

OCR_DIGIT = {"0": "O", "1": "l", "5": "S", "8": "B", "6": "b", "2": "Z"}
OCR_ALPHA = {"o": "0", "l": "1", "i": "1", "e": "c", "m": "rn", "a": "o", "s": "5"}


def _money(c):
    s = f"{abs(c) / 100:,.2f}"
    return ("-" if c < 0 else "") + s


def _descriptor(rng, template):
    return template.format(n=rng.randint(100, 9999), a="".join(rng.choice("ABCDEFGHJKLMNPQRSTUVWXYZ23456789") for _ in range(6)))


def _amount(rng, kind):
    if kind == "sub":
        return rng.choice(SUB_PRICES)
    if kind == "transfer":
        return rng.choice(ROUND)
    lo, hi = {"income": (180000, 420000), "bill": (4000, 25000), "travel": (1200, 45000),
              "fuel": (2500, 9000), "food": (450, 4500), "grocery": (2500, 22000), "health": (800, 9000),
              "shop": (1500, 40000)}[kind]
    return rng.randint(lo, hi)


def _ocr(rng, text, rate):
    out = []
    for ch in text:
        low = ch.lower()
        if rng.random() < rate and (ch in OCR_DIGIT or low in OCR_ALPHA):
            out.append(OCR_DIGIT.get(ch) or OCR_ALPHA[low])
        else:
            out.append(ch)
    return "".join(out)


def make_instance(rng: random.Random, iid: str, condition: str, manipulated: bool):
    start = dt.date(2026, rng.randint(1, 9), 1)
    n_lines = rng.randint(10, 16)
    opening = rng.randint(80000, 900000)
    mids = rng.sample(range(len(MERCHANTS)), k=min(n_lines, len(MERCHANTS)))
    lines = []
    for k in range(n_lines):
        name, tmpl, kind, _fam = MERCHANTS[mids[k % len(mids)]]
        amt = _amount(rng, kind)
        sign = 1 if kind == "income" else -1
        day = start + dt.timedelta(days=rng.randint(0, 27))
        lines.append({"merchant": name, "template": tmpl, "kind": kind, "date": day, "amount": sign * amt})
    lines.sort(key=lambda x: x["date"])

    # ---- ledger (truth) ----
    shifted = condition != "clean"
    ledger, line_to_recs = [], {}
    rid = 0
    for li, ln in enumerate(lines):
        lag = rng.randint(0, 2) if shifted else 0
        desc = _descriptor(rng, ln["template"]) if shifted else ln["merchant"]
        ledger.append({"record_id": f"R{rid:03d}", "posted": ln["date"] + dt.timedelta(days=lag),
                       "description": desc, "amount": ln["amount"], "sources": None})
        line_to_recs[li] = [f"R{rid:03d}"]
        rid += 1

    # split condition: one line posted as two records, and two same-merchant lines merged into one record
    split_info = None
    if condition == "split":
        li = rng.randrange(len(lines))
        rec = next(r for r in ledger if r["record_id"] == line_to_recs[li][0])
        part = int(rec["amount"] * rng.uniform(0.3, 0.7))
        rec2 = dict(rec, record_id=f"R{rid:03d}", amount=rec["amount"] - part,
                    posted=rec["posted"] + dt.timedelta(days=rng.randint(0, 1)))
        rec["amount"] = part
        ledger.append(rec2); line_to_recs[li] = [rec["record_id"], rec2["record_id"]]; rid += 1
        # duplicate-merchant pair merged into one posting
        base = lines[rng.randrange(len(lines))]
        if base["kind"] not in ("income",):
            extra = {"merchant": base["merchant"], "template": base["template"], "kind": base["kind"],
                     "date": base["date"], "amount": -_amount(rng, base["kind"])}
            lines.append(extra)
            j = lines.index(base); k = len(lines) - 1
            rb = next(r for r in ledger if r["record_id"] == line_to_recs[j][0])
            if len(line_to_recs[j]) == 1:
                rb["amount"] += extra["amount"]
                line_to_recs[k] = list(line_to_recs[j])
            else:
                ledger.append({"record_id": f"R{rid:03d}", "posted": extra["date"], "description": _descriptor(rng, extra["template"]),
                               "amount": extra["amount"], "sources": None}); line_to_recs[k] = [f"R{rid:03d}"]; rid += 1
        split_info = True

    # ---- manipulation on the submitted statement (arithmetic stays consistent) ----
    manip, manip_line, deleted_recs = None, None, []
    stmt = [dict(ln, line_id=None) for ln in lines]
    if manipulated:
        manip = rng.choice(MANIPULATIONS)
        candidates = [i for i in range(len(stmt)) if len(line_to_recs[i]) == 1 and sum(line_to_recs[i] == line_to_recs[j] for j in line_to_recs) == 1]
        i = rng.choice(candidates)
        manip_line = i
        if manip == "amount":
            f = rng.choice([10, 0.1, None])
            stmt[i]["amount"] = int(stmt[i]["amount"] * f) if f else stmt[i]["amount"] + rng.choice([-1, 1]) * rng.randint(500, 9000)
        elif manip == "date":
            stmt[i]["date"] = stmt[i]["date"] + dt.timedelta(days=rng.choice([-1, 1]) * rng.randint(9, 20))
        elif manip == "payee":
            fam = next(m[3] for m in MERCHANTS if m[0] == stmt[i]["merchant"])
            siblings = [m for m in MERCHANTS if m[0] != stmt[i]["merchant"] and m[3] == fam]
            same_kind = [m for m in MERCHANTS if m[0] != stmt[i]["merchant"] and m[2] == stmt[i]["kind"]]
            pool = siblings if siblings and rng.random() < 0.6 else (same_kind or [m for m in MERCHANTS if m[0] != stmt[i]["merchant"]])
            stmt[i]["merchant"] = rng.choice(pool)[0]
        elif manip == "insert":
            name, tmpl, kind, _fam = rng.choice(MERCHANTS)
            stmt.append({"merchant": name, "template": tmpl, "kind": kind, "amount": (1 if kind == "income" else -1) * _amount(rng, kind),
                         "date": start + dt.timedelta(days=rng.randint(0, 27)), "inserted": True})
            manip_line = len(stmt) - 1
        elif manip == "delete":
            deleted_recs = list(line_to_recs[i])
            stmt[i]["deleted"] = True
    order = sorted([k for k in range(len(stmt)) if not stmt[k].get("deleted")], key=lambda k: stmt[k]["date"])
    bal = opening; out_lines = []
    orig_to_new = {}
    for n_, k in enumerate(order):
        bal += stmt[k]["amount"]
        orig_to_new[k] = f"L{n_:02d}"
        out_lines.append({"line_id": f"L{n_:02d}", "date": stmt[k]["date"].isoformat(), "description": stmt[k]["merchant"],
                          "amount": _money(stmt[k]["amount"]), "balance": _money(bal)})
    closing = bal

    # ---- evidence availability ----
    coverage_complete = True
    missing = set()
    if condition == "partial":
        coverage_complete = False
        k = max(2, int(len(ledger) * rng.uniform(0.2, 0.4)))
        missing = set(r["record_id"] for r in rng.sample(ledger, k))
    conflict_rec = None
    if condition == "conflict":
        pool = [r for r in ledger if r["record_id"] not in deleted_recs and
                (manip_line is None or r["record_id"] not in line_to_recs.get(manip_line, []))]
        conflict_rec = rng.choice(pool)["record_id"]

    evid = []
    for r in ledger:
        if r["record_id"] in missing:
            continue
        e = {"record_id": r["record_id"], "posted": r["posted"].isoformat(), "description": r["description"],
             "amount": _money(r["amount"]), "source": "core_ledger"}
        if r["record_id"] == conflict_rec:
            alt = r["amount"] + rng.choice([-1, 1]) * rng.randint(1000, 8000)
            e["alternate_source"] = {"source": "card_processor_feed", "amount": _money(alt)}
        evid.append(e)
    rng.shuffle(evid)

    # ---- OCR rendering of the submitted statement ----
    if condition == "ocr":
        for ln in out_lines:
            ln["description"] = _ocr(rng, ln["description"], 0.12)
            ln["amount"] = _ocr(rng, ln["amount"], 0.15)
            ln["balance"] = _ocr(rng, ln["balance"], 0.10)

    # ---- ground-truth oracle ----
    status = {}
    for k in order:
        lid = orig_to_new[k]
        if stmt[k].get("inserted"):
            status[lid] = "different" if coverage_complete else "unknown"
            continue
        recs = line_to_recs[k]
        if k == manip_line and manip in ("amount", "date", "payee"):
            status[lid] = "different" if all(r not in missing for r in recs) else "unknown"
            continue
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
    payee_swapped = [orig_to_new[manip_line]] if manip == "payee" else []
    return {
        "instance_id": iid, "condition": condition,
        "statement": {"period_start": start.isoformat(), "period_end": (start + dt.timedelta(days=27)).isoformat(),
                      "opening_balance": _money(opening), "closing_balance": _money(closing), "lines": out_lines},
        "evidence": {"coverage_complete": coverage_complete, "records": evid},
        "truth": {"label": label, "manipulation": manip, "line_status": status, "omitted_records": omitted,
                  "links": truth_links, "payee_swapped": payee_swapped},
    }


def generate(n_per_condition: int, seed: int, prefix: str):
    rng = random.Random(seed)
    out = []
    for c in CONDITIONS:
        for i in range(n_per_condition):
            out.append(make_instance(rng, f"{prefix}-{c}-{i:03d}", c, manipulated=(i % 2 == 1)))
    return out


def write_jsonl(rows, path):
    with open(path, "w") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")


def read_jsonl(path):
    with open(path) as f:
        return [json.loads(x) for x in f]
