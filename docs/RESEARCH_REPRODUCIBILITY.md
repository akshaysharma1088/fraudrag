# FraudRAG Research Reproducibility and Submission Checklist

## Evidence status (2026-10-26)

The application implementation is open source. **The public repository does not contain
the experiment provenance needed to independently verify the manuscript's reported
FraudRAG-2400 AUC 0.943 / F1 0.883 or its latency and scalability estimates.**
Those values should be treated as *reported, unverified historical results* and not as
results established by the scripts added in this change.

### What is included

- `benchmark/generate_synthetic.py`: seeded balance-manipulation **smoke data**
  (not the manuscript's multi-document FraudRAG-2400 corpus).
- `benchmark/evaluate_balance.py`: reproducible arithmetic baseline and metrics.
- `tests/test_research_baseline.py`: determinism, expected detection, and metric checks.

To run with Python 3.10+:

```bash
python benchmark/generate_synthetic.py --n 2400 --seed 2026
python benchmark/evaluate_balance.py
python -m pytest tests/test_research_baseline.py -q
```

These tests cannot establish Graph-RAG uplift, model-calibration, production performance,
or generalization to authentic financial documents.

## Requirements before a peer-reviewed research submission

1. Locate original dataset generator and inputs, raw labels, annotation policy,
   ground truth provenance, negative-control cases, and license/ethics statement.
2. Archive source version, package lock, prompt templates, API/model versions,
   embedding model, inference parameters, seeds, run dates, and compute hardware.
3. Implement **five** baselines using identical documents and time-aware,
   entity-disjoint train/retrieval/test splits: rules, LLM-only, vector-only,
   graph-only, and full Graph-RAG. Fit thresholds only on training/validation data.
4. Prevent leakage from historical labels: exclude test documents, customers,
   related entities, and future events from retrieval indexes at scoring time.
5. Save per-document prediction records, run logs, confusion matrices, ROC curves,
   confidence intervals across independent seeds, and cost/latency percentiles.
6. Run ablations for retrieval type, depth, top-k, accounting validator, and risk
   propagation; compare to credible recent baselines, including graph-only
   systems, and report false-positive rates for unrelated graph neighbors.
7. Verify model output types and calibration: raw LLM scores are not automatically
   posterior probabilities; investigate calibration and uncertainty.
8. Provide a threat model: false allegations due to risk propagation, sensitive
   financial information retention, third-party LLM processing, and human review.
9. Match every numerical manuscript claim to a committed machine-readable
   experiment result. Generate figures and tables from these results, never from
   hand-entered publication values.
10. Audit every reference and novelty claim against current literature; avoid
    claims of being 'first' or 'production-grade' without appropriate evidence.
11. Disclose synthetic-only results and inability to infer generalization; maintain
    a transparent limitations and reproducibility section.
12. Check prior publication/preprint policies of the target journal; disclose any
    preprint and prior submissions truthfully. Do not submit to two journals at once.

## Potential contributions, requiring experimental validation

- **Evidence-grounded dual retrieval:** graph paths plus vector passages with
  provenance and citation validation for every fraud indicator.
- **Temporal / leakage-resistant graph reasoning:** as-of-time graph snapshots
  and entity-disjoint, time-ordered evaluation.
- **Safe risk propagation:** bounded influence, relationship-type weighting,
  decay, explainability, and false-positive fairness assessment.
- **Governance-aware fallback:** clear abstention when LLM, OCR, graph, or vector
  retrieval fails; separate deterministic rule flags from model judgments.

These are research directions, **not established novel contributions** at present.

## EB-1A evidence stewardship

Keep dated code releases, independent review decisions, manuscript versions, DOI,
citation counts by date, and evidence of external use. Publication alone does not
establish major significance or guarantee any immigration outcome.
