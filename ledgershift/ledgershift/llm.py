"""Open-weights LLM calls through a local Ollama server (no paid API).

Two uses:
  link(...)      selective escalation: propose which record each unresolved line refers to
  llm_only(...)  give the model the whole instance and ask for the final state
"""
from __future__ import annotations

import json
import time
import urllib.request

OLLAMA = "http://localhost:11434/api/chat"
OPTIONS = {"temperature": 0, "seed": 7, "num_ctx": 8192}

POLICY = (
    "Decision policy. A statement line is supported when an admissible reference record (or two records "
    "whose amounts sum to it, or one record covering it together with another same-day line) shows the same "
    "payee, the same amount and a posting date 0 to 3 days after the line date. A line is different when the "
    "evidence shows the same transaction with another amount, date or payee, or when no record supports it and "
    "the extract is complete. A record inside the statement period that no line accounts for is an omitted "
    "posting, which also makes the statement different. A line is conflicting when its record has an alternate "
    "source that disagrees on the amount. When the extract is incomplete (coverage_complete is false), an "
    "unsupported line is unknown. Overall: DIFFERENT if any line is different or a posting is omitted; else "
    "CONFLICTING if any line is conflicting; else DEFER if any line is unknown or coverage is incomplete; else SUPPORTED."
)

LINK_INSTRUCTIONS = (
    "You link lines from a customer's submitted bank statement to the bank's own ledger records. Ledger "
    "descriptions are raw bank descriptors with abbreviations, store numbers and processor prefixes such as "
    "SQ *, TST*, PAYPAL * or DD *. Statement text may contain OCR errors such as O for 0, l for 1, S for 5. "
    "For each statement line, choose the option that records the same real-world transaction, or 'none' if no "
    "option does. The amount or date may differ if the statement was altered; still choose the option if it is "
    "clearly the same purchase or payment. Options with shared_with cover this line together with another "
    "statement line. Also say whether the record's payee is the same business or person as the statement "
    "description (same_payee). Answer for every line, in JSON only."
)

LINK_SCHEMA = {"type": "object", "properties": {"links": {"type": "array", "items": {"type": "object", "properties": {
    "line_id": {"type": "string"}, "option": {"type": "string"}, "same_payee": {"type": "boolean"}},
    "required": ["line_id", "option", "same_payee"]}}}, "required": ["links"]}

ONLY_SCHEMA = {"type": "object", "properties": {
    "label": {"type": "string", "enum": ["SUPPORTED", "DIFFERENT", "CONFLICTING", "DEFER"]},
    "line_ids": {"type": "array", "items": {"type": "string"}}, "reason": {"type": "string"}},
    "required": ["label", "line_ids", "reason"]}


def _chat(model, system, user, schema, timeout=900):
    body = {"model": model, "stream": False, "format": schema, "options": OPTIONS,
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}]}
    req = urllib.request.Request(OLLAMA, data=json.dumps(body).encode(), headers={"Content-Type": "application/json"})
    t = time.monotonic()
    with urllib.request.urlopen(req, timeout=timeout) as f:
        raw = json.load(f)
    return {"content": raw["message"]["content"], "prompt_tokens": raw.get("prompt_eval_count", 0),
            "output_tokens": raw.get("eval_count", 0), "seconds": round(time.monotonic() - t, 2)}


def link_payload(inst, pending):
    rec_by = {r["record_id"]: r for r in inst["evidence"]["records"]}
    items = []
    for p in pending:
        opts = []
        for o in p["options"]:
            rs = [{k: rec_by[i][k] for k in ("record_id", "posted", "description", "amount")} for i in o["record_ids"]]
            d = {"option": o["option_id"], "records": rs}
            if "shared_with" in o:
                d["shared_with"] = o["shared_with"]
            opts.append(d)
        items.append({"line_id": p["line_id"], "date": p["date"], "description": p["description"], "amount": p["amount"], "options": opts})
    return json.dumps({"statement_lines": items}, ensure_ascii=False)


def _safe_chat(*args):
    try:
        return _chat(*args)
    except Exception as e:  # timeouts and server errors are recorded, not fatal
        return {"content": "", "prompt_tokens": 0, "output_tokens": 0, "seconds": 0, "call_error": f"{type(e).__name__}:{str(e)[:80]}"}


def link(model, inst, pending):
    out = _safe_chat(model, LINK_INSTRUCTIONS, link_payload(inst, pending), LINK_SCHEMA)
    try:
        parsed = json.loads(out["content"])
        answers = {x["line_id"]: {"option": x["option"], "same_payee": bool(x["same_payee"])} for x in parsed["links"]}
        out["error"] = ""
    except Exception as e:  # malformed output counts as no links
        answers, out["error"] = {}, out.get("call_error") or f"parse:{type(e).__name__}"
    out["answers"] = answers
    return out


def only_payload(inst):
    return json.dumps({"statement": inst["statement"], "evidence": inst["evidence"]}, ensure_ascii=False)


def llm_only(model, inst):
    system = ("You verify a customer's submitted bank statement against the bank's reference evidence. "
              + POLICY + " Ledger descriptions are raw bank descriptors; statement text may contain OCR errors. "
              "Return the overall state, the line ids that drive it, and a one-sentence reason, in JSON only.")
    out = _safe_chat(model, system, only_payload(inst), ONLY_SCHEMA)
    try:
        parsed = json.loads(out["content"]); out["label"] = parsed["label"]; out["error"] = ""
    except Exception as e:
        out["label"], out["error"] = "DEFER", out.get("call_error") or f"parse:{type(e).__name__}"
    return out
