# FraudRAG: reproducibility evidence and submission gates (October 26, 2026)

**Publication readiness:** **NOT CLEARED**. This is an execution checklist, not a promise of acceptance. The old FraudRAG-2400 results are unsupported and remain barred from peer-reviewed manuscripts.

## Verified new experimental foundation

| Work | Evidence / file | Result / scope |
| --- | --- | --- |
| New dataset generation | `benchmark/fraudrag_v2.py`; https://github.com/akshaysharma1088/fraudrag/actions/runs/40362679991 | Reproduced 840 **synthetic** cases from 120 fictional customers. Machine-readable text and predetermined manipulation types. |
| Customer-disjoint 28-case subset | `benchmark/evaluate_v2.py`, split seed 57 | 4 cases per category, no repeated test customer, artificially high 71.4% positive rate. |
| Rules-only and complete-ledger baselines | https://github.com/akshaysharma1088/fraudrag/actions/runs/40362679991 | Rules F1=0.5714; exact bank-ledger match F1=1.000. The latter is a **synthetic reference oracle**, not a deployable result. |
| Real Neo4j as-of-time graph test | https://github.com/akshaysharma1088/fraudrag/actions/runs/40363346100 | 12 bank-side synthetic source snapshots; a future-dated graph fact was excluded. |
| Real Chroma vector index integration | https://github.com/akshaysharma1088/fraudrag/actions/runs/40363998267 | 16 synthetic past-evidence records and 40 searches with provenance/date restrictions; deterministic hashed features, not an OpenAI embedding benchmark. |
| Digital PDF statement roundtrip | https://github.com/akshaysharma1088/fraudrag/actions/runs/40364130518 | 28 entirely synthetic vector-text PDFs generated and extracted; not scans, fraud-forgery image localization or real-world OCR performance. |
| Paired GPT study | `experiments/fraudrag_v2_gpt.py`; https://github.com/akshaysharma1088/fraudrag/actions/runs/40363144409 | 112 precommitted calls over 28 fixed cases (4 GPT context conditions); final metrics **cannot be cited until the run and artifacts pass independent audit**. No claim that the paid pilot itself calls Neo4j or Chroma. |
| Pre-existing financial *claim* pilots | `research/RESULTS_FINFACT_2026-10-26.json`, `research/RESULTS_GPT_2026-10-26.json` | Separate task: fact-checking claims, **not** bank-statement forgery. |

## Mandatory remaining gates (all must be satisfied)

1. **GPT output integrity:** Confirm the entire fixed schedule completes; archive source case IDs, prompts and schema versions, model identifier and version, per-case predictions, response statuses, evidence IDs, token usage, API charges, and timed retries/failures. Run `benchmark/audit_gpt_v2.py`; add paired 95% uncertainty interval without editing predictions.
2. **Correct end-to-end integration:** Connect GPT scoring directly to Neo4j as-of-time retrieval *and* a Chroma index built only from historical trusted records, with real deployment tests. The first GPT pilot only consumes serialized graph references and TF-IDF historical passages. **Do not relabel that run as Neo4j/Chroma Graph-RAG.**
3. **Non-oracle robustness:** Re-run with genuinely **missing, incomplete, conflicting and delayed authoritative bank-side data**, including cases whose valid statements have unusual large transfers and misleading relationships. A 100% exact matching result with a complete synthetic ledger is a ceiling, not a persuasive novelty result.
4. **Statistical design:** Increase independent customer groups, pre-register multiple seeds, hold out institutions/styles, evaluate case-level and customer-group-level errors, confidence intervals, retrieval leakage, calibration and adverse/abstain rates. Report a realistic prevalence sensitivity analysis.
5. **External ground truth:** Use appropriately licensed real or independently adjudicated examples. Public parser PDFs lacking forgery labels do not become positive/negative fraud observations. Access, authorization, privacy and ethics review may be necessary.
6. **Actual performance and cost:** Measure digital/scanned PDF processing, OCR failures, graph and vector latency, GPT inference p50/p95, model revisions and costs from run logs. No petabyte-scale/production claims without stress tests.
7. **Bibliography and novelty:** Verify the **entire** bibliography, not only the several prior studies already checked in `research/LITERATURE_NOVELTY_AUDIT.md`. No 'first' or 'better than all methods' language without a complete primary-source comparison.
8. **Manuscript reconciliation:** Regenerate tables and figures programmatically from immutable artifacts; remove all historical AUC=0.943/F1=0.883 and fictional five-fold/latency claims. Prepare a new submission document and re-run manuscript preflight; manually validate every sentence.
9. **Author review and ethics:** Verify author affiliation, preprint and previous submission disclosures, anonymization, data-use permissions and selected journal's policies. No actual journal submission without user authorization.

## Mandatory editorial principle

If GPT underperforms a simple, deterministic verification rule with the same trusted bank-side evidence, **publish that negative/comparative result honestly** or redefine the research question. Do not remove the stronger baseline, fabricate favorable splits, copy hard-coded charts, conceal abstentions, or change the hypothesis after seeing results without disclosure.

**Main branch is unchanged by the research draft pull request.** All scientific claims in the provisional manuscript remain subject to the versioned claim-verification register.
