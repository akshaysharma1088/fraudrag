"""FraudRAG-V5 external financial QA evidence-witness stress evaluation.

TAT-QA has human-authored questions over excerpts from authentic published
financial reports. We evaluate conditional VERIFICATION of a supplied answer
candidate, not generation of answers, bank-statement forgery or fraud.
Candidate strings come from human gold labels solely to construct an
answer-evidence challenge. No method is trained on or allowed to infer bank
authenticity from TAT-QA. Synthetic source deletion, spoofing, late arrival,
conflicts and candidate edits are explicitly labeled interventions.

All comparators inspect the SAME textual sources and metadata.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
import random
import re
import unicodedata
import urllib.request
from collections import Counter, defaultdict
from pathlib import Path

UPSTREAM_COMMIT = "870accc41953dcde885aabeb963d94aabdc0fbc3"
DEV_BLOB_SHA1 = "48075c812af3fe6698b1d5cb50d9dbf358d52784"
DEV_URL = (f"https://raw.githubusercontent.com/NExTplusplus/TAT-QA/"
           f"{UPSTREAM_COMMIT}/dataset_raw/tatqa_dataset_dev.json")
METHODS = ("raw_literal", "source_integrity", "temporal_integrity", "conflict_aware")
SCENARIOS = ("intact", "removed_witness", "untrusted_replay", "late_record", "constructed_conflict", "wrong_candidate")
SEED = 20261026


def git_blob_hash(raw: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(raw)).encode() + bytes([0]) + raw).hexdigest()


def load_external_data(cache: Path, *, allow_network: bool = True):
    cache.parent.mkdir(parents=True, exist_ok=True)
    if cache.exists():
        raw = cache.read_bytes()
    elif allow_network:
        with urllib.request.urlopen(DEV_URL, timeout=60) as response:
            raw = response.read()
        cache.write_bytes(raw)
    else:
        raise FileNotFoundError(cache)
    observed = git_blob_hash(raw)
    if observed != DEV_BLOB_SHA1:
        raise RuntimeError(f"Pinned TAT-QA content mismatch: {observed} != {DEV_BLOB_SHA1}")
    items = json.loads(raw)
    if not isinstance(items, list) or len(items) < 100:
        raise ValueError("Unexpected upstream dataset structure")
    return items, hashlib.sha256(raw).hexdigest()


def normalize(text: str) -> str:
    return " ".join(unicodedata.normalize("NFKC", str(text)).casefold().split())


def matches(text: str, candidate: str) -> bool:
    corpus, value = normalize(text), normalize(candidate)
    if not value:
        return False
    return re.search(r"(?<!\w)" + re.escape(value) + r"(?!\w)", corpus) is not None


def build_cases(data):
    cases = []
    discarded = Counter()
    for context in data:
        table_id = str(context.get("table", {}).get("uid", "")).strip()
        paragraphs = context.get("paragraphs", [])
        if not table_id or not isinstance(paragraphs, list):
            discarded["context_missing_id_or_paragraphs"] += 1
            continue
        sources = [{"source_id": str(p.get("uid", "")), "text": str(p.get("text", "")),
                    "released_dataset_source": True, "observed_after_cutoff": False,
                    "hypothetical_authoritative_conflict": False}
                   for p in paragraphs if p.get("uid") and p.get("text")]
        for q in context.get("questions", []):
            if q.get("answer_type") != "span" or q.get("answer_from") != "text":
                discarded["not_single_text_span"] += 1
                continue
            answer = q.get("answer")
            if not isinstance(answer, list) or len(answer) != 1:
                discarded["not_single_gold_answer"] += 1
                continue
            candidate = str(answer[0]).strip()
            if len(normalize(candidate)) < 5:
                discarded["too_short"] += 1
                continue
            witnesses = [s["source_id"] for s in sources if matches(s["text"], candidate)]
            if not witnesses:
                discarded["no_literal_witness"] += 1
                continue
            cases.append({"case_id": q["uid"], "source_group": table_id,
                          "gold_candidate": candidate, "source_texts": sources,
                          "witnesses": witnesses})
    if len({x["case_id"] for x in cases}) != len(cases):
        raise ValueError("Duplicate external question identifiers")
    if len(cases) < 50 or len({x["source_group"] for x in cases}) < 25:
        raise ValueError("Insufficient anchored gold text spans in external benchmark")
    return cases, dict(discarded)


def scenario_sources(case, scenario: str):
    # Publication excerpts are integrity-checked against the pinned dataset,
    # but are NOT independently issuer-signed bank statements.
    originals = [dict(x) for x in case["source_texts"]]
    witnesses = set(case["witnesses"])
    remaining = [x for x in originals if x["source_id"] not in witnesses]
    if scenario in ("intact", "wrong_candidate"):
        return originals
    if scenario == "removed_witness":
        return remaining
    if scenario == "untrusted_replay":
        return remaining + [{
            **next(x for x in originals if x["source_id"] in witnesses),
            "source_id": "untrusted-user-replay:" + case["case_id"],
            "released_dataset_source": False,
        }]
    if scenario == "late_record":
        return remaining + [{
            **next(x for x in originals if x["source_id"] in witnesses),
            "source_id": "hypothetical-late:" + case["case_id"],
            "observed_after_cutoff": True,
        }]
    if scenario == "constructed_conflict":
        return originals + [{
            "source_id": "synthetic-conflicting-assertion:" + case["case_id"],
            "text": "Counterfactual contradiction constructed by the evaluators.",
            "released_dataset_source": True,
            "observed_after_cutoff": False,
            "hypothetical_authoritative_conflict": True,
        }]
    raise ValueError(scenario)


def decision(method: str, candidate: str, sources):
    valid = [s for s in sources if matches(s["text"], candidate)]
    if method == "raw_literal":
        return bool(valid)
    valid = [s for s in valid if s["released_dataset_source"]]
    if method == "source_integrity":
        return bool(valid)
    valid = [s for s in valid if not s["observed_after_cutoff"]]
    if method == "temporal_integrity":
        return bool(valid)
    if method == "conflict_aware":
        return bool(valid) and not any(
            s["hypothetical_authoritative_conflict"] and s["released_dataset_source"]
            and not s["observed_after_cutoff"] for s in sources)
    raise ValueError(method)


def evaluate(cases):
    rows = []
    for case in cases:
        for scenario in SCENARIOS:
            sources = scenario_sources(case, scenario)
            candidate = (case["gold_candidate"] + " [fabricated-extra]")
            if scenario != "wrong_candidate":
                candidate = case["gold_candidate"]
            for method in METHODS:
                supported = decision(method, candidate, sources)
                rows.append({
                    "case_id": case["case_id"], "source_group": case["source_group"],
                    "scenario": scenario, "method": method,
                    "supported": int(supported),
                    # This controlled task's expected binary SUPPORT status
                    # is defined by intervention, not independently adjudicated QA.
                    "expected_supported": int(scenario == "intact"),
                    "source_count": len(sources),
                })
    return rows


def metrics(rows):
    by = defaultdict(list)
    for row in rows:
        by[(row["scenario"], row["method"])].append(row)
    summary = {}
    for (scenario, method), items in sorted(by.items()):
        n = len(items)
        support = sum(x["supported"] for x in items)
        expected = int(scenario == "intact")
        errors = n - support if expected else support
        summary[f"{scenario}:{method}"] = {
            "cases": n, "supported": support, "support_rate": round(support / n, 6),
            "unsupported_acceptances_or_false_deferrals": errors,
            "error_rate": round(errors / n, 6)}
    return summary


def group_bootstrap(rows, *, method_a="conflict_aware", method_b="raw_literal",
                    scenario="untrusted_replay", resamples=2000, seed=SEED):
    pairs = defaultdict(dict)
    for row in rows:
        if row["scenario"] == scenario and row["method"] in (method_a, method_b):
            pairs[row["case_id"]][row["method"]] = row
    groups = defaultdict(list)
    for pair in pairs.values():
        if set(pair) != {method_a, method_b}:
            raise RuntimeError("Unpaired source intervention")
        a, b = pair[method_a], pair[method_b]
        if a["source_group"] != b["source_group"]:
            raise RuntimeError("Mismatched source context group")
        groups[a["source_group"]].append(a["supported"] - b["supported"])
    keys = sorted(groups)
    diffs = [x for g in keys for x in groups[g]]
    rng = random.Random(seed)
    boot = []
    for _ in range(resamples):
        chosen = [groups[keys[rng.randrange(len(keys))]] for j in keys]
        boot.append(sum(sum(g) for g in chosen) / sum(len(g) for g in chosen))
    boot.sort()
    return {
        "contrast": method_a + " minus " + method_b, "scenario": scenario,
        "source_group_kind": "table_context_not_independent_institution",
        "group_count": len(keys), "question_count": len(diffs),
        "support_rate_difference": round(sum(diffs) / len(diffs), 6),
        "cluster_bootstrap_95pct": [
            round(boot[int(.025 * resamples)], 6),
            round(boot[min(resamples-1, int(.975 * resamples))], 6)
        ], "bootstrap_resamples": resamples,
        "warning": "Gold-answer-conditioned candidate verification; entirely controlled interventions. Not end-to-end QA, document forgery or bank fraud."
    }


def run(dataset: Path, out: Path, allow_network=True):
    records, data_sha = load_external_data(dataset, allow_network=allow_network)
    cases, excluded = build_cases(records)
    rows = evaluate(cases)
    out.mkdir(parents=True, exist_ok=True)
    with (out / "predictions.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    report = {
        "study": "External financial text answer-candidate evidence sufficiency stress study",
        "external_data": "TAT-QA development split over real published financial reports",
        "upstream_commit": UPSTREAM_COMMIT, "upstream_blob_sha1": DEV_BLOB_SHA1,
        "download_sha256": data_sha, "dataset_url": DEV_URL,
        "license": "CC BY 4.0 for dataset; cite Zhu et al. ACL 2021",
        "original_contexts": len(records),
        "eligible_gold_span_questions": len(cases),
        "unique_context_groups": len({c["source_group"] for c in cases}),
        "excluded_questions_by_reason": excluded,
        "methods": METHODS, "scenarios": SCENARIOS, "results": metrics(rows),
        "bootstrap_untrusted_replay": group_bootstrap(rows),
        "bootstrap_late_record": group_bootstrap(rows, scenario="late_record"),
        "benchmark_uses_gold_candidate": True,
        "independently_adjudicated_bank_fraud": False,
        "issuer_signature_authenticated": False,
        "synthetic_evidence_interventions": True,
        "LLM_evaluated_in_this_study": False,
        "graph_or_vector_retrieval_evaluated_in_this_study": False,
        "scientific_novelty_or_real_fraud_advantage_proven": False,
        "scope_warning": "This is deterministic provenance-condition stress testing on REAL financial-report excerpts with GOLD answer candidates and SYNTHETIC evidence disruptions. It is not an independent end-to-end answer generation test. Simulated source trust/time/conflict flags are not attested by issuers."
    }
    (out / "metrics.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf8")
    print(json.dumps({
        "eligible_questions": len(cases),
        "context_groups": report["unique_context_groups"],
        "untrusted_replay": {m: report["results"][f"untrusted_replay:{m}"]["support_rate"] for m in METHODS},
        "late_record": {m: report["results"][f"late_record:{m}"]["support_rate"] for m in METHODS},
        "out": str(out)
    }, indent=2))
    return report


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--dataset", type=Path, default=Path("artifacts/tatqa/tatqa_dataset_dev.json"))
    p.add_argument("--out", type=Path, default=Path("artifacts/tatqa_v5"))
    p.add_argument("--offline", action="store_true")
    args = p.parse_args()
    run(args.dataset, args.out, allow_network=not args.offline)


if __name__ == "__main__":
    main()
