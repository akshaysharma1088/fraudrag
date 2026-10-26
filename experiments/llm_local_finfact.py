"""Small, honest CPU LLM pilot on held-out Fin-Fact financial claims.

This does NOT test bank-statement fraud detection, RAG, or manuscript AUC claims.
Produces paired small-sample baselines plus model labels, abstentions and timing.
"""
import argparse
import csv
import json
import random
import re
import time
from pathlib import Path

from finfact_study import load, split, metrics, evaluate_baselines

SYSTEM = (
    "You are evaluating financial fact-checking claims without access to external "
    "verification documents. Return exactly one label: true, false, or neutral. "
    "Use neutral if the claim cannot be verified from available information; "
    "do not invent corroborating sources."
)


def select_fixed_sample(test, limit, seed):
    """Precommitted random sample, no selection based on model predictions."""
    rng = random.Random(seed)
    idx = sorted(rng.sample(range(len(test)), min(limit, len(test))))
    return [test[i] for i in idx], idx


def evaluate_local_model(rows, model_id):
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer
    torch.set_num_threads(2)
    tokenizer = AutoTokenizer.from_pretrained(model_id, trust_remote_code=False)
    model = AutoModelForCausalLM.from_pretrained(
        model_id, torch_dtype=torch.float32, trust_remote_code=False
    ).to("cpu").eval()
    model_revision = getattr(model.config, "_commit_hash", None)
    outputs = []
    with torch.inference_mode():
        for i, row in enumerate(rows):
            messages = [
                {"role": "system", "content": SYSTEM},
                {"role": "user", "content": "Financial claim:\n" + row["claim"][:900] +
                    "\nReturn just the label."},
            ]
            start = time.monotonic()
            try:
                input_ids = tokenizer.apply_chat_template(
                    messages, tokenize=True, add_generation_prompt=True,
                    return_tensors="pt"
                )
                generated = model.generate(
                    input_ids, max_new_tokens=12, do_sample=False,
                    pad_token_id=tokenizer.eos_token_id,
                )
                response = tokenizer.decode(
                    generated[0][input_ids.shape[-1]:], skip_special_tokens=True
                ).strip()
                match = re.search(r"\b(true|false|neutral)\b", response.lower())
                label = match.group(1) if match else None
                error = None
            except Exception as exc:
                response, label, error = "", None, type(exc).__name__
            seconds = round(time.monotonic() - start, 4)
            outputs.append({
                "claim": row["claim"], "truth": row["label"],
                "prediction": label or "ABSTAIN", "raw_response": response,
                "elapsed_seconds": seconds, "error": error or ""
            })
            print(f"case={i+1}/{len(rows)} predicted={label or 'ABSTAIN'} sec={seconds}", flush=True)
    return outputs, model_revision


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="Qwen/Qwen2.5-0.5B-Instruct")
    parser.add_argument("--limit", type=int, default=24)
    parser.add_argument("--seed", type=int, default=2026)
    parser.add_argument("--data", default="data/external/finfact.json")
    parser.add_argument("--out", default="artifacts/finfact_local_llm")
    args = parser.parse_args()
    if args.limit <= 0 or args.limit > 250:
        raise SystemExit("limit must be 1..250; start with a small feasibility sample")
    rows, provenance = load(Path(args.data))
    train, test = split(rows)
    sample, indices = select_fixed_sample(test, args.limit, args.seed)
    baselines, _ = evaluate_baselines(train, sample)
    outcomes, revision = evaluate_local_model(sample, args.model)
    truth = [row["truth"] for row in outcomes]
    pred = [row["prediction"] for row in outcomes]
    valid = [i for i, p in enumerate(pred) if p != "ABSTAIN"]
    result = {
        "study": "CPU-only financial claim verification pilot, NOT FraudRAG-2400",
        "dataset": provenance, "split": "source-URL group holdout, seed 42",
        "sample_indices": indices, "sample_seed": args.seed,
        "sample_n": len(sample), "sampling": "uniform random sample of test cases",
        "model": args.model, "model_commit": revision,
        "generation": {"temperature": 0, "do_sample": False, "max_new_tokens": 12,
                       "system_prompt": SYSTEM},
        "llm_including_abstentions_as_errors": metrics(truth, pred),
        "llm_coverage": len(valid) / len(sample),
        "llm_conditional_on_valid": (metrics([truth[i] for i in valid],
                                              [pred[i] for i in valid]) if valid else None),
        "paired_same_sample_baselines": baselines,
        "latency_seconds": {
            "sum": sum(r["elapsed_seconds"] for r in outcomes),
            "median": sorted(r["elapsed_seconds"] for r in outcomes)[len(outcomes)//2],
        },
        "exploratory_only": True,
        "not_document_fraud": True,
        "not_paper_results": True,
    }
    dest = Path(args.out)
    dest.mkdir(parents=True, exist_ok=True)
    with (dest / "predictions.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(outcomes[0]))
        writer.writeheader()
        writer.writerows(outcomes)
    (dest / "metrics.json").write_text(json.dumps(result, indent=2) + "\n")
    print("EXPERIMENT_RESULT_JSON_START", flush=True)
    print(json.dumps(result, indent=2), flush=True)
    print("EXPERIMENT_RESULT_JSON_END", flush=True)


if __name__ == "__main__":
    main()
