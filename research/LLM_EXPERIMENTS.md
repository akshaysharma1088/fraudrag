# LLM experiments: actual runs and boundaries

## Public open-weight LLM (no paid key)

The first reproducible *LLM* pilot uses the Apache-2.0 licensed
[Qwen2.5-0.5B-Instruct](https://huggingface.co/Qwen/Qwen2.5-0.5B-Instruct) model
on the **same source-URL grouped Fin-Fact held-out pool** as the classical
baselines. The trial samples **24 cases using a precommitted random seed 2026**,
runs CPU-only deterministic generation, compares on **the exact same sample**
to trained TF-IDF and majority-class baselines, and records raw answers,
abstentions, latency and model revision.

Run locally with PyTorch CPU, transformers and scikit-learn installed:

```sh
python experiments/llm_local_finfact.py --model Qwen/Qwen2.5-0.5B-Instruct --limit 24
```

See the GitHub Actions workflow `.github/workflows/research-local-llm.yml`.
**This is not a full Graph-RAG ablation or statement-forgery experiment.**
A small 0.5B model is not a substitute for commercial foundation models;
the pilot tests execution and protocol feasibility. No performance value
is claimed before the actual workflow completes.

## Hosted LLM API evaluation: optional paid work

`experiments/finfact_study.py --mode llm` supports OpenAI or Anthropic using
`OPENAI_API_KEY` or `ANTHROPIC_API_KEY` at runtime. API credentials must be
placed only in GitHub Actions encrypted secrets or the local process environment,
never in a file or message. Paid model evaluations should use precommitted
identical case IDs, explicit budget caps and recorded API model revisions;
a small 50-case run is a smoke test, not statistically sufficient proof.

## Essential before journal submission

- Obtain/construct a **document fraud** dataset with verified annotations.
- Implement and run the complete Graph-RAG pipeline on that target dataset.
- Use multiple baselines with matched data, retrieval snapshots, labels,
  prompt budgets and train/test split; prevent label and customer leakage.
- Report macro/weighted F1, fraud precision/recall, AUROC where valid,
  confidence intervals, latency, cost, and failure/abstention coverage.
- Replace historical FraudRAG 0.943 AUC and 0.883 F1 with reproducible
  experimental results. Do not cite these pilot outcomes as those results.
