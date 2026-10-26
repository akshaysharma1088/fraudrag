# Real-data experiment roadmap

The original 2,400-document FraudRAG study dataset is missing. No historical AUC/F1 value can be reproduced from existing repository files.

## External datasets and separate research questions

- **Fin-Fact**: https://github.com/IIT-DM/Fin-Fact (MIT, archived). Financial fact-checking truth labels and supporting evidence. Our first baseline studies **claim-only** classification, not statement forgery. Pinned to commit `b30387813734d4b461e6fcdd576feb819cc0bcbd`.
- **Bankstatemently benchmark**: https://github.com/bankstatemently/bank-statement-parsing-benchmark. Public synthetic statement PDFs for OCR/extraction and normalization, NOT fraud classification; small publicly released set.
- **PaySim**: https://www.kaggle.com/datasets/ealaxi/paysim1. Synthetic transaction fraud useful for graph stress testing; NOT document fraud.
- **FinQA**: https://github.com/czyssrs/FinQA. Financial numerical reasoning, not fraud detection.
- **DocTamper**: https://github.com/ubbagg/DocTamper. Image-tampering evaluation; check licensing, access and permitted academic use first.

## Run public-data feasibility experiment

```bash
python -m pip install scikit-learn
python experiments/finfact_study.py --mode baseline
```

This downloads the version-pinned real dataset and saves SHA-256, grouped holdout configuration, predictions and macro-F1. It uses majority and TF-IDF/logistic regression baselines. Fin-Fact labels may be influenced by how statements were selected by fact-checkers. Source URL grouping is a precaution, not a comprehensive temporal contamination audit.

An LLM *claim-only* trial is supported only if the runner has a separate API account/key:

```bash
export OPENAI_API_KEY=... # Never commit credentials
python experiments/finfact_study.py --mode llm --provider openai --model gpt-4o-mini --limit 50
```

No paid inference is performed by the benchmark workflow. In the manuscript, model outputs, costs, sampling choices, prompt versions, refusals/abstentions and errors must be reported. Comparing small LLM subsets with larger classical evaluations is only exploratory.

## Next research contribution: temporal, evidence-grounded Graph-RAG

1. Build fresh versioned statement data with consent/licensed real examples where possible and explicit synthetic perturbations for balance, entity, date, and account inconsistencies.
2. Implement graph snapshots of information available **before** the claimed document date; split by institution, document and entity, not only random row.
3. Compare rule-only, LLM-only, vector-RAG, graph-RAG, and hybrid with *identical test cases* and fixed annotation protocols; evaluate precision/recall/AUC, calibration, uncertainty, refusal coverage, p50/p95 latency and cost.
4. Add source provenance/citations to every graph-supported indicator and bounded risk propagation to avoid guilt by association.
5. Run and publish independent evaluation scripts producing machine-readable predictions, uncertainty intervals, failure analysis and generated figures from real output.
6. Treat novel methodology as a hypothesis until both literature comparison and independent experimental improvements support it.

**No claim of reproduced FraudRAG-2400 findings should be made.** This pilot cannot validate the prior manuscript or replace its study without transparent reframing.
