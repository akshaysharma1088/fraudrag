# FraudRAG manuscript: claim-by-claim verification register
**Review date:** October 26, 2026  
**Status:** **NOT CLEARED FOR PEER-REVIEWED JOURNAL SUBMISSION**

This audit compares the submitted-style `FraudRAG_Manuscript.docx` (14 pages,
previously provided by author), the GitHub repository, publicly accessible
primary sources, and **actually executed GitHub Actions logs**. It does not
assert that a historical result is false merely because its source is missing.
Until it can be reproduced, it is **not a publishable verified observation**.

## Rules of evidence

- **V1 — Directly inspected implementation:** code exists at pinned commit;
  describe it as implementation/design only, never proof of effectiveness.
- **V2 — Observed in actual experiment:** code, immutable dataset revision/hash,
  config, per-sample predictions, and workflow logs exist; can be reported
  *only with their exact task, sample size and limitations*. A single run does
  not establish generalization or novel scientific contribution.
- **V3 — Independently corroborated external fact:** primary publication,
  standard, vendor documentation, dated edition, or verified DOI supports
  precisely the stated claim.
- **UNVERIFIED:** lacking reproducible evidence; **exclude** from submission
  draft, including its tables/plots/abstract and conclusions.
- **FUTURE WORK:** explicitly proposed, not written as a demonstrated result.
- **Contradicted by inspected sources:** correct/retract; do not retain.

No “verified” label is conferred merely by the presence of an API response,
software test, a markdown table, an AI-generated sentence, or a citation.

## High-impact manuscript claim audit

| ID | Manuscript assertion | Current evidence and source | Status | Permissible treatment |
|---|---|---|---|---|
| F01 | FraudRAG-2400, 2,400 statements; 1,600 legitimate and 800 fraudulent; six document types | Original labeled records, generator and raw predictions are **not present** in repository. New `benchmark/generate_synthetic.py` is a **different** arithmetic-only fixture. | **UNVERIFIED** | Remove all historical dataset metrics; plan and create a **new, versioned** research dataset. |
| F02 | FraudRAG AUC=0.943, Precision=0.891, Recall=0.876, F1=0.883 | No original prediction files or actual evaluation scripts; values are typed into `scripts/generate_ieee_paper.js`, `scripts/generate_figures.js` and README. | **UNVERIFIED** | Exclude from title/abstract/results/conclusion/figures until reproduced on an authenticated dataset. |
| F03 | Four comparative baselines and 5-fold cross-validation | No fold manifests, exact baseline runs, metric provenance or train/test leakage audit. | **UNVERIFIED** | Build the same-sample experiments and archive splits and predictions. |
| F04 | Ablations, ring-subset gains, sensitivity plots, per-type F1 | Figures and manuscript contain fixed numbers rather than machine-generated evaluation artifacts. | **UNVERIFIED** | Remove current ablations and sensitivity graphs; generate from actual controlled experiments. |
| F05 | 2.8 seconds end-to-end, <1ms validator, 500 repetitions, stage p95 latencies | No latency traces/hardware or request distributions. | **UNVERIFIED** | Benchmark complete workflow; report p50/p95, sample size, runtime, API model versions. |
| F06 | Petabyte-scale performance, Spark/EMR and millions of documents/day | No production scaling results; code/design references are not a stress test. | **UNVERIFIED** | State intended architecture only, explicitly not evaluated; remove achieved scalability claims. |
| F07 | “First” Graph-RAG financial document fraud system; “first” Medallion document fraud system; “state of the art” | No systematic review establishing precedence over all prior literature. GraphRAG is itself existing work. | **UNVERIFIED** | Drop priority/superiority words until dated systematic search supports them. |
| F08 | Anthropic-native text embedding used with Claude 3.5 | `backend/services/graph_rag_service.py` uses OpenAIEmbeddings or HuggingFace fallback. Official Anthropic docs explicitly state Anthropic lacks its own embedding model: https://platform.claude.com/docs/en/build-with-claude/embeddings | **CONTRADICTED** | Describe actually configured embedding/model in each experimental run, including exact version. |
| F09 | Graph context always performs Neo4j depth-two traversal | `backend/graph/neo4j_client.py:get_graph_context_for_rag` retrieves direct customer statements/patterns; separate graph-neighborhood method does not prove it is used by scorer. | **OVERSTATED** | Describe actual Cypher query and verify runtime edges/hops with integration tests. |
| F10 | Silver check emits high-confidence fraud indicators *before* LLM | Parser did not infer debit/credit direction; hardening branch abstains on unknown direction; the model still requires complete integration tests. | **NOT VALIDATED** | Describe detection as a conditionally executed validation check; do not assert sensitivity or precision until tested. |
| F11 | LLM fraud score is posterior probability | A generative model's uncalibrated numeric answer is not a measured posterior. | **UNVERIFIED** | Call it a heuristic risk score until independent calibration and reliability analysis. |
| F12 | High-risk graph propagation “detects fraud rings” | Neo4j has risk-update code, but no labeled fraud-ring benchmark and no documented bias/false-positive assessment. | **NOT VALIDATED** | Describe as a risk propagation design, not proven detection or causal guilt. |
| F13 | Privacy: outgoing LLM receives only masked identifiers, Bronze raw text expires, SSNs hashed | `backend/api/routes/statements.py` forwards raw extracted text to RAG; Bronze persists `raw_text`; no demonstrated TTL or SSN hashing. | **CONTRADICTED** | Remove those guarantees; run privacy test and implement protections before any real PII use. |
| F14 | “Production-grade / production-ready” | Tests predominantly mock Neo4j/LLM; no deployment security, integration, or incident evidence offered. | **UNVERIFIED** | Call the repository a *research prototype*. |
| F15 | “Six fraud types” in original dataset | Manuscript Table I lists **five** fraud manipulation categories. | **INTERNALLY INCONSISTENT** | Correct category terminology only after dataset definition is verified. |
| F16 | ACFE estimated "$5.38 trillion annually on global financial institutions"; "document forgery 21% of all cases" | ACFE 2024 original states estimated 5% annual occupational-fraud loss; projected **more than $5 trillion globally**, not an exact $5.38 trillion loss exclusively for financial institutions. Primary: https://www.acfe.com/about-the-acfe/newsroom-for-media/press-releases/press-release-detail?s=2024-Report-to-the-Nations ; see current 2026 edition before choosing statistics. The 21% figure is not verified here. | **MISATTRIBUTED / PENDING** | Use a precise, edition-dated occupational-fraud statement *only* with primary support, or omit. |
| F17 | LSTM fraud paper cited by reference [9] | Manuscript [9] is a UbiComp paper on social relationships, not LSTM transaction fraud. | **CITATION MISMATCH** | Remove/replace only after independently checking a correct source and its DOI. |
| F18 | Other 29 bibliography entries and causal related-work comparisons | Not yet source-by-source audited in this review. | **PENDING** | Verify each title, author, venue, date, DOI and whether it supports the exact sentence. |
| F19 | “Manuscript submitted April 2025,” journal-accepted/professional affiliations | Manuscript has outdated submission date; multiple draft versions have differing affiliations, publication headers and submission badges. | **PENDING AUTHOR DOCUMENTATION** | Use correct, current, author-approved affiliation and editorial status; do not imply acceptance. |
| F20 | Open-source prototype includes Bronze/Silver/Gold orchestration and Neo4j + Chroma integrations | The listed modules, routes and configurations exist in the public repo. | **V1 CODE VERIFIED** | Describe structure and explicit limitations, not fraud-detection quality. |
| F21 | External Fin-Fact classical pilot: 3,369 mapped records, 2,502 train, 867 test, macro-F1 0.5067 for TF-IDF | Actual run: https://github.com/akshaysharma1088/fraudrag/actions/runs/40355375818 ; dataset hash and results: `research/RESULTS_FINFACT_2026-10-26.json`. | **V2 OBSERVED ONLY** | May report in a separate *financial-claim verification pilot*, not as document fraud. |
| F22 | GPT-6.1 Sol fact-check pilot: 24 claims, 8.33% accuracy, macro-F1 0.0722, 23 neutral responses, estimated token cost $0.01024 | Actual run: https://github.com/akshaysharma1088/fraudrag/actions/runs/40359651993 ; `research/RESULTS_GPT_2026-10-26.json`. | **V2 OBSERVED ONLY** | If used, explicitly say GPT saw no retrieved verification evidence and sample n=24. Do not infer model quality or Graph-RAG performance. |
| F23 | “18–24 percentage points over all baselines” | Even taking legacy table as written, graph-only AUC 0.893 to full 0.943 is **5.0 percentage points**; comparison claim is inconsistent. | **CONTRADICTED / HISTORICAL UNVERIFIED** | Remove; if eventual claim, show correct metric-specific comparison and uncertainty. |

## Required approval for any paper sentence

Before inclusion, record in this register: sentence/paragraph, exact source
(including revision/DOI/run/row), verification class, analysis script, reviewer
and date. **A citation does not replace checking that the cited source says it.**
Conclusions and abstract must not contain stronger claims than results support.

**Important:** The automated `research/check_manuscript.py` screens only known
unsafe phrases and is an extra *negative* check. Passing it is **not** evidence
of correctness, completeness, novelty, or publication readiness. The historical
draft DOCX files in `docs/` remain archival/unapproved.


## FraudRAG-v2 replacement study — new verified evidence (October 26, 2026)

**G01 — Synthetic corpus and deterministic baselines: V2 observed, synthetic only.**
Run https://github.com/akshaysharma1088/fraudrag/actions/runs/40362679991 .
Generator `benchmark/fraudrag_v2.py`, scorer `benchmark/evaluate_v2.py`.
120 fictional customers, 840 machine-readable statement scenarios, dataset SHA-256
`1ab25182cd7607f4090dc87695e1f668940a74b1d67fd620f418278f018878b7`.
Twenty-eight test cases belong to twenty-eight independent customers.
Statement-only arithmetic/date rules: TP8, TN8, FP0, FN12, precision1.000,
recall0.400, F1 0.5714. Exact matching of complete authoritative bank-side
synthetic ledger: TP20, TN8, FP0, FN0, F1 1.000.
**Critical**: The ledger is an unusually strong constructed oracle;
perfect results are by experimental design and cannot establish real-world
fraud performance.

**G02 — Neo4j temporal graph retrieval: V2 integration observed.**
Run https://github.com/akshaysharma1088/fraudrag/actions/runs/40363346100 .
Containerized Neo4j 5.20 driver queries retrieved 12 synthetic source-provenance
snapshots, verified all prior-to-submission records and excluded a seeded
future-dated record. Not yet evidence of accuracy benefit or Neo4j-backed
GPT inference.

**G03 — GPT document pilot: pending independent result audit.**
Experiment runner `experiments/fraudrag_v2_gpt.py` precommits 28 cases,
four GPT conditions, a complete deterministic-ledger comparator, and a $2
budget reservation cap. Until artifact audit completes, **no GPT performance
values may be quoted** in a manuscript.

**G04 — Financial Graph-RAG novelty: unverified, explicitly constrained.**
Prior art verified in `research/LITERATURE_NOVELTY_AUDIT.md`, including
Barry et al. (2025) financial GraphRAG and Ma (2026) false financial
statement knowledge graphs. 'First application' and superiority claims
are blocked.

**G05 — Revised manuscript: research draft only.**
`docs/FraudRAG_VERIFIED_WORKING_DRAFT.md` is a provisional, disclosure-heavy
working manuscript, not a journal-ready article. All historical DOCX metrics
remain blocked; they must not be restored without experiments.


## G06 — Paired GPT synthetic-statement experiment VERIFIED WITH LIMITS

Actual 112-call GPT run: https://github.com/akshaysharma1088/fraudrag/actions/runs/40363144409

Permanently archived original test corpus, 28 held-out case IDs, all 112 raw
predictions, ledger evidence, prompt protocol, observed API token usage,
and independently recomputed audit (including 2,000 customer-level paired
bootstrap replicates):
`research/verified_runs/fraudrag_v2_20261026/`.

**V2 OBSERVED on synthetic case set only:** GPT-only F1=0.5714,
vector/TFiDF F1=0.7097 (with 4 abstentions), serialized bank-ledger
graph-style GPT F1=1.000, hybrid GPT F1=1.000, and exact
**non-LLM** bank-ledger matching F1=1.000. All are n=28 with 71.4%
tampered label prevalence. Six software/retrieval demonstrations should not
be merged into claims that the *GPT experimental inference* ran Neo4j or Chroma;
the actual GPT protocol uses graph-like JSON and TF-IDF text retrieval.

**V2 OBSERVED limitation:** 5 GPT-only outputs cite nonexistent evidence IDs;
do not suppress these. API token-cost estimate $0.285052. Paired accuracy
improvement hybrid vs no-retrieval GPT 0.4286, bootstrap 95% percentile interval
[0.25, 0.6071] **conditional on these 28 constructed customer cases**.

**Publication interpretation:** GPT does **not** beat the equally informed
deterministic authoritative-ledger comparator. No support for superior
financial-fraud detection, real-world generalization, calibrated scores,
first-of-kind novelty, or performance at petabyte scale.

## G07 — Missing reference robustness VERIFIED WITH LIMITS

Run https://github.com/akshaysharma1088/fraudrag/actions/runs/40365030542 .
With exact same 28 synthetic cases, deterministic reference comparison
was correct on 28/28 given the full ledger; on 9/28 with a partial ledger
(19 abstentions); on 4/28 with account/institution identity only
(24 abstentions); and on 0/28 when no bank-side evidence exists
(28 abstentions). Those are **synthetic and highly simplified availability
assumptions**, not observed real-world coverage or external validity.


## G08 — Actual Neo4j + Chroma + GPT study: VERIFIED ON FICTIONAL CASES ONLY

Original executed 112-call GPT job:
https://github.com/akshaysharma1088/fraudrag/actions/runs/40366638447

Independent source/provenance and metric re-computation:
https://github.com/akshaysharma1088/fraudrag/actions/runs/40368862175

Permanent source-dataset SHA256, raw test cases, 112 model predictions,
retrieved IDs, run settings, token usage, and paired bootstrap findings:
`research/verified_runs/fraudrag_v2_integrated_20261026/`.

**Verified synthetic-only n=28:** actual Neo4j bank-ledger GPT F1=1.000,
actual Neo4j+Chroma GPT F1=1.000, exact non-LLM matching the same bank
reference F1=1.000. Actual Chroma-only GPT F1=0.5625, lower than GPT
document-only F1=0.5714. Chroma-only had 8 abstentions. 2 document-only
model responses asserted nonexistent evidence citations. All four mode
predictions and their source records were audited.

**Observed comparative limitation:** no added predictive value for the
LLM or Chroma retrieval over simple complete-ledger reconciliation in
the synthetic protocol. The artificially comprehensive synthetic reference
is an oracle; this is not bank fraud adjudication or external generalization.

The retrieval uses *actual database queries*, but knowledge graph content
is a simple fictional bank-account/ledger snapshot, not trained ring
reasoning. Chroma uses deterministic local 256d hashing, not OpenAI
embedding vectors. The study includes no scanned/OCR tampering, real
institution labeling, or validated k-hop risk propagation improvements.

**Cost/time caveat:** API token-usage cost estimate $0.283302; p50/p95
times include model API calls only, not end-to-end document ingestion.
A 2,000-resample customer-paired exploratory bootstrap gives integrated
minus document-only accuracy difference 0.4286, percentile interval
[0.25, 0.6071] **within the constructed experimental population**.

**Article readiness unchanged: NOT CLEARED.** The verified paper should
report real matched controls and all negative results, and cannot
claim superiority or significant fraud detection in production.

## G09 — Third-party synthetic PDF v3 study: VERIFIED WITH LIMITS

GitHub Actions https://github.com/akshaysharma1088/fraudrag/actions/runs/40371198225 successfully checked five released Bankstatemently **fictional** PDF SHA-256 records and text-extracted all 17 pages. A reproducible 20-case benchmark used ten extracted-text monetary edits and ten unchanged/harmless-space controls. Complete extracted originals gave oracle matching, and short/no reference yielded 20 abstentions. These are *text modifications*, not forged PDF images, real bank misconduct labels, or a non-oracle fraud classifier.

The previous first-250-character partial reference run https://github.com/akshaysharma1088/fraudrag/actions/runs/40370987339 yielded false positive whitespace differences and is **superseded** by the corrected first-30-normalized-token method. Full hash and outcome provenance in `research/RESULTS_V3_EXTERNAL_PDF_2026-10-26.json`. No GPT v3 results are approved until actual execution and independent audit.

## G10 — V3 licensed SYNTHETIC-PDF GPT text comparison: V2 OBSERVED WITH LIMITS

60/60 GPT-6.1 Sol calls executed at https://github.com/akshaysharma1088/fraudrag/actions/runs/40372143670 . Independent case IDs, provenance, source claims and scoring recomputed successfully at https://github.com/akshaysharma1088/fraudrag/actions/runs/40372704350 . Full predictions and protocol at `research/verified_runs/fraudrag_v3_external_20261026/`. Five third-party **synthetic** original PDFs each contribute four related derived text cases (20 total). GPT without an original and with only 30 original tokens abstained on all 20; GPT supplied **the complete original extracted text** classified all 20 scripted edits/unchanged controls correctly. Token estimate $0.349444, unsupported citations zero.

**This is an artificial exact-original textual oracle** with no independently adjudicated real fraud, no falsified PDF images, no broad institution split and no separate bank ledger. It cannot establish publication-ready novelty or real-world financial fraud accuracy.
