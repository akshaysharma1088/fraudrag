# FraudRAG — Evidence-Grounded Financial Statement Consistency Research

[![CI](https://github.com/akshaysharma1088/fraudrag/actions/workflows/ci-cd.yml/badge.svg)](https://github.com/akshaysharma1088/fraudrag/actions)
[MIT license](LICENSE) · [Research paper **WORKING DRAFT**](docs/FraudRAG_VERIFIED_WORKING_DRAFT.md) · [Scientific verification register](research/CLAIM_VERIFICATION_REGISTER.md) · [Publication-readiness checklist](research/PUBLICATION_READINESS_CHECKLIST.md)

**Status: Experimental research prototype. No validated production financial-fraud system or accepted peer-reviewed FraudRAG journal article is claimed.**

FraudRAG explores whether a financial statement's arithmetic and contents can be checked against **independently held, dated evidence** using deterministic rules, bank-ledger reconciliation, graph retrieval, historical-text retrieval and GPT. The repository contains two distinct implementations:

1. **Application prototype:** `backend/`, frontend, Bronze/Silver/Gold pipeline, Neo4j graph utilities, Chroma support and risk-scoring services. Existence of code does **not** demonstrate field accuracy.
2. **Controlled research studies:** `benchmark/`, `experiments/`, `tests/` and `research/`. These include measured experiments with *fictional* statements and a **separate** publicly released SEC enforcement-linked accounting misstatement baseline.

## NEW: Evidence Acquisition Controller (FraudRAG-EAC)

**Implemented in the research branch:** a gated, interactive, **fictional-only**
evidence request and verification application, separate from the legacy
fraud-scoring dashboard. The UI has an **Evidence Acquisition** tab,
adaptive dynamic-programming source requests, prior-aware greedy/fixed
baselines, deterministic source response traces and replayable field-level
conditional certificates. It handles matching, deliberate controlled edits,
incomplete references, source conflicts and future-dated records.

- [Implementation and opt-in demo instructions](docs/FRAUDRAG_EAC_SANDBOX.md)
- Backend: `backend/services/eac_service.py`,
  `backend/services/eac_certificate.py`, `backend/api/routes/eac.py`
- Frontend: `frontend/src/pages/EvidenceAcquisition.jsx`
- Tests: `tests/test_eac_service.py`, `tests/test_eac_api.py`
- Docker Compose: `EAC_DEMO_ENABLED=false` by default. For a
  **controlled local demo only**, set `EAC_DEMO_ENABLED=true` before
  running Compose. Open `http://localhost:3000/evidence` after starting
  the stack, or use `POST /api/v1/eac/demo/run`.

**Optional genuine-source adapter code is now implemented, OFF by default:** (1)
[Plaid Statements](docs/EAC_ISSUER_PROVIDER_INTEGRATIONS.md) for retrieving a
bank-provided original PDF and checking Plaid's SHA-256 response integrity,
and (2) a proposed **custom Ed25519-signed issuer-field receipt format**
with server-pinned issuer trust roots and scope validation. **No live bank,
Plaid Item, user-consented account, approved partner signing key or external
financial document has actually been connected.** Plaid's content checksum is
NOT a bank cryptographic signature; custom signed receipts are NOT a
standard supported bank protocol unless a partner agrees to implement it.
There is deliberately no public API to query live bank sources before
customer authentication and consent vaults exist. Historical verified
synthetic results and the SSRN-cited FraudRAG project are preserved.

## Research result provenance — October 26, 2026

The **original historical FraudRAG-2400 dataset and raw predictions are unavailable**. Historical performance claims (including AUC 0.943/F1 0.883, petabyte scale, specific latency and multi-hop retrieval gains) are **not validated** and must **not** be copied into journal submissions. Historical draft figures and DOCX files remain archival material only.

### Verified synthetic document consistency study (28 cases)

The new `FraudRAG-v2` dataset consists of **840 synthetic cases generated from 120 fictional customer groups**, with a 28-case customer-disjoint exploratory test set. A real GPT-6.1 Sol run produced 112 API responses over four conditions (same case IDs in each). All outputs were archived and independently recomputed.

| Configuration | Accuracy | F1 | Abstentions |
|---|---:|---:|---:|
| Basic arithmetic/date rules, no GPT | 0.571 | 0.571 | 0 |
| GPT without retrieved external evidence | 0.571 | 0.571 | 1 |
| GPT + prior-period TF-IDF text | 0.679 | 0.710 | 4 |
| GPT + serialized authoritative bank ledger | 1.000 | 1.000 | 0 |
| GPT + both serialized bank ledger and prior text | 1.000 | 1.000 | 0 |
| **Exact deterministic comparison to the same bank ledger; NO GPT** | **1.000** | **1.000** | **0** |

**These scores describe a small synthetic reconciliation task with an almost complete bank-side oracle and 71.4% artificially manipulated examples.** The complete ledger makes exact matching trivial. The study does **not** demonstrate that GPT beats deterministic ledger comparison or detects real bank-statement forgery. The serialized-ledger GPT run **did not make live Neo4j or Chroma retrieval queries**; those services have separate integration tests, plus the follow-on actual integrated study in `experiments/fraudrag_v2_integrated.py`.

Evidence: [Original 112-call experiment](https://github.com/akshaysharma1088/fraudrag/actions/runs/40363144409) and [per-case permanent verified archive](research/verified_runs/fraudrag_v2_20261026/independent_post_run_audit.json). **Five GPT-only outputs contained unsupported source citations** and are retained as observed errors.

#### Actually integrated database-backed GPT (same 28 synthetic cases)

A *second* 112-call GPT study built prompts using **actual Neo4j as-of-time queries and ChromaDB indexed-history retrieval**, rather than serialized research fixture paths. All cases and predictions were independently audited and archived. The F1 results were: GPT document-only **0.571**, Chroma-only **0.563** (8 abstentions), Neo4j-only **1.000**, and combined **1.000**. A deterministic exact comparison to the same authoritative bank ledger again scored **1.000**. Two unsupported GPT-only evidence citations were recorded. Model token-cost estimate was **$0.283302**.

**The integrated retrieval adds no measured predictive advantage over exact non-LLM ledger matching in the controlled synthetic set.** The graph has a full synthetic ledger oracle; these are not customer bank records, realistic fraud prevalence or new adjudications. See [the executed real-database run](https://github.com/akshaysharma1088/fraudrag/actions/runs/40366638447), [per-case archive](research/verified_runs/fraudrag_v2_integrated_20261026/) and [research manuscript](docs/FraudRAG_VERIFIED_WORKING_DRAFT.md).

### Benchmark v3: third-party PDF source verification

Five publicly released **fictional synthetic bank-statement PDFs** from the Bankstatemently Open Benchmark were pinned to upstream Git commit `2d8d31d68dcedbf9028b87f6c7df286f53a6c7de`. Their real PDF SHA-256 hashes matched publisher records; all **17 pages** yielded selectable extracted text. Twenty experimental cases comprised five originals, five harmless spacing edits, and ten controlled monetary edits to **extracted text only**. A complete original-text reference matched all edits (an explicit source oracle); the normalized 30-token partial reference and no-reference variants abstained on all cases. **Not a fraud dataset or a forged PDF image benchmark.** [Executed verification](https://github.com/akshaysharma1088/fraudrag/actions/runs/40371198225) · [Hashed v3 result](research/RESULTS_V3_EXTERNAL_PDF_2026-10-26.json) · [Source methodology](research/BENCHMARK_V3_PROTOCOL.md)

### Independently audited GPT follow-up on the same v3 synthetic PDFs

A separate actual GPT-6.1 Sol experiment scored the same 20 controlled extracted-text cases under three evidence conditions (**60 completed calls**). With no original text or only a 30-token excerpt, GPT abstained on **all 20** in each condition. Given the **complete original extracted text**, it distinguished all ten scripted monetary edits from ten unchanged/benign cases. This is an **exact-source textual comparison oracle**, not a tested bank fraud detector. All evidence-ID citations passed source validation. Estimated token cost was **$0.349444**.

[Executed GPT study](https://github.com/akshaysharma1088/fraudrag/actions/runs/40372143670) · [Independent audit](https://github.com/akshaysharma1088/fraudrag/actions/runs/40372704350) · [Permanent record](research/verified_runs/fraudrag_v3_external_20261026/).

## Larger synthetic evaluation

`benchmark/robustness_multiseed_v2.py` generated **4,900 fictional cases from 700 fictional customers**, then executed **three held-out customer-disjoint splits of 175 examples each**. As designed, complete authoritative-ledger reconciliation scored F1 1.000 in all three; arithmetic/date rules scored F1 0.571 in all three. When the ledger is incomplete, the checker abstains frequently instead of assuming authenticity. **These are not real-world external replications.**

Evidence: [Executed three-seed workflow](https://github.com/akshaysharma1088/fraudrag/actions/runs/40366478963), [machine-readable aggregate](research/RESULTS_MULTISEED_SYNTHETIC_2026-10-26.json).

### Separate real accounting-fraud task — do not conflate with forgery

A reproducible, non-GPT logistic-regression benchmark uses **146,045 published firm-year records**, with AAER-linked accounting misstatement labels from Bao et al. (2020). The temporal test produced **PR-AUC 0.00614**, and company-isolated test **PR-AUC 0.01352**, at extremely low positive prevalence. It is a distinct **issuer accounting fraud** task, **not** financial document tampering; no bank-document, GPT or Graph-RAG accuracy conclusion follows.

Evidence: [Executed AAER evaluation](https://github.com/akshaysharma1088/fraudrag/actions/runs/40366949592), [source-hashed metrics](research/RESULTS_REAL_AAER_2026-10-26.json). Raw third-party data are downloaded at runtime and **not committed or redistributed**.

## Verified component integration tests

| Component | Actual tested observation | Evidence |
|---|---|---|
| Neo4j 5 temporal query | 12 fictional bank-ledger snapshots; future facts excluded | [Completed integration run](https://github.com/akshaysharma1088/fraudrag/actions/runs/40363346100) |
| Chroma vector database | 16 historical synthetic accounts, 40 source/time-filtered searches using **local 256-dimensional hashing**, not OpenAI embeddings | [Completed integration run](https://github.com/akshaysharma1088/fraudrag/actions/runs/40363998267) |
| Digital PDF parsing | 28 generated **text-native fictional PDFs** rendered and extracted; no scanned/real-bank accuracy inference | [Completed PDF experiment](https://github.com/akshaysharma1088/fraudrag/actions/runs/40364130518) |
| Actual Neo4j + Chroma + GPT | Four-mode, 112 actual calls and full provenance audit on 28 synthetic statements; Neo4j-only/hybrid both match the perfect deterministic ledger oracle | [Execution](https://github.com/akshaysharma1088/fraudrag/actions/runs/40366638447) · [Independently audited records](research/verified_runs/fraudrag_v2_integrated_20261026/integrated_independent_audit.json) |

### Proposed v4 selective verification research (prototype ONLY)

The next candidate paper shifts from unsubstantiated real fraud classification
to **source-conditional evidence contracts**, explicit completeness,
bitemporal cutoff, conflict witnesses and auditable abstention. The
machine-replayable research prototype at
`benchmark/provenance_certificate_v4.py` and tests
`tests/test_provenance_certificate_v4.py`
**do not authenticate bank issuers, establish a new algorithm, or demonstrate
any improvement over strong deterministic comparators**. Results must be
generated by new fair studies; no new GPT costs or real documents are used.
[Research hypotheses and experimental design](research/OJCS_RESEARCH_PIVOT_V4_BLUEPRINT_2026-10-26.md) ·
[Verified prototype test run](https://github.com/akshaysharma1088/fraudrag/actions/runs/40393206867).

**Earlier public SSRN preprint correction pending:** a May 2026 FraudRAG
abstract currently contains unsupported old novelty/performance statements;
the preprint must be accurately revised and prior overlap disclosed to any
journal. [Revision plan](research/SSRN_CORRECTION_DRAFT.md).


### V4 Evidence Acquisition Controller — audited simulated adaptive-vs-deterministic study

The exploratory **FraudRAG-EAC** research module compares **four deterministic retrieval policies**, including a prior-aware cost/coverage greedy baseline and classical finite-horizon dynamic programming, under exactly the same fictional source outcomes, learned priors and budgets. It used **1,080 calibration**, **720 held-out**, and **360 synthetic shifted** case groups. Independent post-run audit reproduced all **12,960 policy/budget paths** and source costs.

At the **4-unit fictional access budget**, DP obtained complete field-coverage certificates for **509/720 (70.69%)** test statements at mean synthetic cost **2.593**, versus prior-aware greedy **495/720 (68.75%)** at **2.794** units. Paired coverage difference **+1.94 percentage points, 95% bootstrap interval [−0.14,+4.03]**, not conclusive. Under source availability shift, DP coverage **35.00%** versus greedy **35.56%**. The costs are made-up simulator units, and the source issuer is **not externally authenticated**. **The DP itself is deterministic standard optimization, not established research novelty, and this experiment contains no GPT/GraphRAG or actual financial-fraud test.**

[Actual V4 workflow](https://github.com/akshaysharma1088/fraudrag/actions/runs/40395485609) · [Permanent reproducible source/decision audit](research/verified_runs/fraudrag_v4_adaptive_20261026/) · [Detailed findings and limitations](research/ADAPTIVE_V4_PRELIMINARY_FINDINGS.md).

## Reproduce the **synthetic** baselines

Python 3.11+:

```bash
python -m pip install pytest scikit-learn
python benchmark/evaluate_v2.py
python -m pytest tests/test_fraudrag_v2.py -q
python benchmark/robustness_multiseed_v2.py
python benchmark/incomplete_evidence_v2.py
```

`benchmark/fraudrag_v2.py` uses explicit seeds and yields SHA-256-manifested CSVs. **These are fictional records**; no actual bank customer or private account is used. Dataset labels arise from controlled edits, not adjudicated fraud investigations.

For live Neo4j/Chroma tests, use dedicated CI workflows with isolated Neo4j 5 and in-memory Chroma installations. For an authorized GPT account, `experiments/fraudrag_v2_integrated.py` supports a dry run without an API key; `--execute` explicitly initiates paid requests and must be cost-limited and accompanied by a configured `OPENAI_API_KEY` secret. **Never add credentials to GitHub files, chat messages or published datasets.**

## Application source and boundaries

- `backend/api/` — REST routes for statements, customers, graph and analyses.
- `backend/pipelines/medallion.py` — Bronze source handling, Silver extraction and conditional arithmetic checks, Gold features.
- `backend/graph/neo4j_client.py` — application graph functionality, distinct from the independently tested `benchmark/neo4j_snapshot.py`.
- `backend/services/graph_rag_service.py` — prototype LLM scoring, distinct from the research model runner and its measured source list.
- `benchmark/chroma_historical_v2.py` — independently tested historical retrieval with source/time constraints; 256d deterministic hash features are **not** OpenAI embeddings.
- `research/CLAIM_VERIFICATION_REGISTER.md` — science-claim and citation clearance register.
- `docs/FraudRAG_VERIFIED_WORKING_DRAFT.md` — conservative research manuscript under development.

The old diagrams and manuscripts are **not evidence that all depicted infrastructure works end-to-end**. This repository is not cleared for automated credit, banking, or fraud enforcement decisions. Human expert review, independent data rights, privacy controls, missing-reference handling, fairness evaluation, security and external adjudicated testing would be required before discussing deployment.

## Originality and publication status

Published Graph-RAG, knowledge-graph financial analysis and LLM-based accounting-fraud research precedes this work. **No “first”, “novel”, “state of the art”, or real-world superiority claim is established**. See the [primary-source prior-work review](research/LITERATURE_NOVELTY_AUDIT.md).

The research draft is not approved for submission until: complete source-by-source bibliography validation, independent real document ground truth, realistic missing-ledger evaluation, bigger leakage-controlled GPT studies, reproducible end-to-end model comparisons, and review of the final authored manuscript. All prior unverified numbers remain excluded from the current results tables.

## Author

Akshay Sharma, IEEE Senior Member — see current manuscript for author-approved affiliations and corresponding author information.
