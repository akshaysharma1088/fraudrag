"""Paired GPT financial-claims pilot using the OpenAI Responses API.

This is FIN-FACT CLAIM verification, NOT the manuscript's FraudRAG document-forgery
experiment and NOT a Graph-RAG ablation. API calls require --execute, a key
provided through the runner environment, and an explicit spending cap.
"""
import argparse
import csv
import hashlib
import json
import os
import time
import urllib.error
import urllib.request
from pathlib import Path

from finfact_study import load, split, metrics, evaluate_baselines
from llm_local_finfact import select_fixed_sample, SYSTEM

PRICES_USD_PER_MILLION = {
    # Standard short-context prices, Oct 26 2026. Confirm before paid experiments.
    "gpt-6.1-sol": {"input": 1.0, "output": 5.0},
    "gpt-6-luna": {"input": 0.05, "output": 0.25},
}
MODEL_IDS = tuple(PRICES_USD_PER_MILLION)
LABELS = ("true", "false", "neutral")
MAX_OUTPUT_TOKENS = 256
PROMPT_SUFFIX = "\nAnswer with one of the three labels in the JSON schema."
SCHEMA = {
    "type": "object",
    "properties": {"label": {"type": "string", "enum": list(LABELS)}},
    "required": ["label"],
    "additionalProperties": False,
}


def parse_label(response):
    """Read validated JSON from Responses API output message (not output ordering)."""
    if response.get("status") not in (None, "completed"):
        return None
    text = ""
    for item in response.get("output") or []:
        if item.get("type") != "message":
            continue
        for content in item.get("content") or []:
            if content.get("type") == "output_text":
                text += content.get("text") or ""
    if not text.strip():
        return None
    try:
        obj = json.loads(text)
        label = obj.get("label") if isinstance(obj, dict) else None
        return label if label in LABELS else None
    except (TypeError, ValueError):
        return None


def price_usd(model, input_tokens, output_tokens):
    price = PRICES_USD_PER_MILLION[model]
    return (int(input_tokens) * price["input"] +
            int(output_tokens) * price["output"]) / 1_000_000


def make_payload(model, claim):
    return {
        "model": model,
        "store": False,
        "max_output_tokens": MAX_OUTPUT_TOKENS,
        "instructions": SYSTEM,
        "input": [{"role": "user", "content": claim[:900] + PROMPT_SUFFIX}],
        "text": {"format": {"type": "json_schema",
                            "name": "claim_verdict", "strict": True,
                            "schema": SCHEMA}},
    }


def request_gpt(api_key, payload):
    req = urllib.request.Request(
        "https://api.openai.com/v1/responses",
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        data=json.dumps(payload).encode("utf-8"), method="POST",
    )
    with urllib.request.urlopen(req, timeout=150) as result:
        return json.load(result)


def estimate_next_max_usd(model, claim):
    # Conservative per-call reservation, not a guaranteed billing ceiling.
    input_upper = max(2000, len(claim) // 2 + 1000)
    return price_usd(model, input_upper, MAX_OUTPUT_TOKENS)


def run(args):
    rows, provenance = load(Path(args.data))
    train, test = split(rows)
    sample, indices = select_fixed_sample(test, args.limit, args.seed)
    paired, _ = evaluate_baselines(train, sample)
    prices = PRICES_USD_PER_MILLION[args.model]
    planned_upper_usd = sum(estimate_next_max_usd(args.model, row["claim"])
                            for row in sample)
    summary = {"dataset": provenance,
               "experiment": "claim-only GPT study; NOT document fraud or FraudRAG-2400",
               "model": args.model, "seed": args.seed, "sample_indices": indices,
               "sample_n": len(sample), "budget_usd": args.max_estimated_usd,
               "planned_conservative_cost_estimate_usd": round(planned_upper_usd, 5),
               "unit_price_usd_per_million": prices,
               "prompt_sha256": hashlib.sha256(SYSTEM.encode()).hexdigest(),
               "max_output_tokens": MAX_OUTPUT_TOKENS, "paired_baselines": paired,
               "executed": args.execute}
    if not args.execute:
        print(json.dumps(summary, indent=2))
        return
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise SystemExit("OPENAI_API_KEY is not configured; no paid requests sent.")
    if planned_upper_usd > args.max_estimated_usd:
        raise SystemExit("Conservative planned cost exceeds allowed cap; no requests sent.")
    predictions = []
    spent_usd = 0.0
    for i, row in enumerate(sample):
        if spent_usd + estimate_next_max_usd(args.model, row["claim"]) > args.max_estimated_usd:
            print("Stopping at budget threshold before next request.", flush=True)
            break
        start = time.monotonic()
        status = "ok"
        returned_model = ""
        input_tokens = output_tokens = 0
        verdict = None
        try:
            result = request_gpt(api_key, make_payload(args.model, row["claim"]))
            returned_model = result.get("model", "")
            verdict = parse_label(result)
            if verdict is None:
                status = "abstain_or_incomplete"
            usage = result.get("usage") or {}
            input_tokens = int(usage.get("input_tokens") or 0)
            output_tokens = int(usage.get("output_tokens") or 0)
            spent_usd += price_usd(args.model, input_tokens, output_tokens)
        except urllib.error.HTTPError as exc:
            # Do not print the request, bearer token or raw error body.
            status = f"http_{exc.code}"
        except Exception as exc:
            status = type(exc).__name__
        record = {
            "test_index": indices[i], "claim": row["claim"], "truth": row["label"],
            "prediction": verdict or "ABSTAIN", "status": status,
            "actual_model": returned_model, "input_tokens": input_tokens,
            "output_tokens": output_tokens, "elapsed_seconds": round(time.monotonic()-start, 4),
        }
        predictions.append(record)
        print(f"GPT case {i+1}/{len(sample)}: {status}; total recorded tokens billed={spent_usd:.5f} USD",
              flush=True)
        if status.startswith("http_"):
            print("HTTP failure: stopping instead of incurring retries/costs.", flush=True)
            break
    valid = [r for r in predictions if r["prediction"] in LABELS]
    summary.update({
        "attempted": len(predictions), "coverage": len(valid) / len(sample),
        "actual_usage_estimated_cost_usd": round(spent_usd, 6),
        "billed_usage_note": "Computed using recorded API tokens at stated standard prices; final invoice may differ",
        "metrics_including_abstentions_as_errors": (
            metrics([r["truth"] for r in predictions],
                    [r["prediction"] for r in predictions]) if predictions else None),
        "metrics_conditional_on_valid": (
            metrics([r["truth"] for r in valid],
                    [r["prediction"] for r in valid]) if valid else None),
        "original_fraudrag_auc_not_reproduced": True
    })
    out = Path(args.output)
    out.mkdir(parents=True, exist_ok=True)
    with (out / "predictions.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(predictions[0]) if predictions else [
            "test_index", "claim", "truth", "prediction", "status", "actual_model",
            "input_tokens", "output_tokens", "elapsed_seconds"])
        writer.writeheader()
        writer.writerows(predictions)
    (out / "metrics.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2), flush=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", choices=MODEL_IDS, default="gpt-6.1-sol")
    parser.add_argument("--data", default="data/external/finfact.json")
    parser.add_argument("--output", default="artifacts/finfact_gpt")
    parser.add_argument("--limit", type=int, default=24)
    parser.add_argument("--seed", type=int, default=2026)
    parser.add_argument("--max-estimated-usd", type=float, default=2.00)
    parser.add_argument("--execute", action="store_true", help="Explicit opt-in to paid API requests")
    args = parser.parse_args()
    if not 1 <= args.limit <= 867:
        parser.error("--limit must be between 1 and 867")
    if not 0 < args.max_estimated_usd <= 100:
        parser.error("--max-estimated-usd must be between 0 and 100")
    run(args)


if __name__ == "__main__":
    main()
