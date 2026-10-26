# Evidence-Grounded Financial-Statement Consistency Checking with GPT and Time-Filtered Bank-Side References

**Research working draft — NOT APPROVED FOR JOURNAL SUBMISSION**  
**Author:** Akshay Sharma  
**Date:** October 26, 2026  
**Evidence policy:** Every numerical result here is derived from a recorded workflow. Numbers are reported only for completed and audited runs. External validity and manuscript submission clearance remain pending.

## Abstract

This working paper investigates whether retrieved bank-side and historical account evidence improves the detection of **controlled synthetic modifications** to machine-readable financial statements. The goal is document *consistency checking* against separately held records, not a demonstrated solution to real-world financial crime. The research implementation includes a domain-structured ingestion and Graph-RAG software prototype and a newly generated controlled dataset, FraudRAG-v2, containing 840 synthetically generated statement cases grouped into 120 fictional customers. The evaluation preserves customers as disjoint units and uses a precommitted 28-case held-out subset with four cases from each of seven manipulation/legitimate categories. A basic arithmetic/date baseline achieved an F1 of 0.571 (precision 1.000, recall 0.400) on this subset. A separate deterministic baseline comparing each submitted statement against an **authoritative same-period synthetic bank-side ledger** achieved F1 1.000. These outcomes underscore the critical role, and unrealistic completeness, of the trusted ledger supplied in this synthetic study. A paired GPT experiment was subsequently executed using 112 API calls across statement-only, historical-text retrieval, serialized synthetic bank reference, and combined evidence conditions. Independent archival checks confirmed the source-level confusion counts. Both evidence-rich GPT conditions matched the deterministic full-ledger comparator on this 28-case sample, providing no evidence of incremental predictive value from GPT when the exact complete ledger was already available. A follow-on real-database experiment reproduced this equality using actual Neo4j and Chroma queries feeding GPT, with the same decisive dependence on a complete synthetic ledger. No current result substantiates claims about real-bank forgery detection, production scalability, novelty priority, or superiority to classical reference matching.

## 1. Scope, Motivation and Research Questions

Financial statement manipulation presents several independent tasks: verifying accounting arithmetic, identifying modifications to authentic records, comparing a submitted statement with a bank-side ledger, and investigating real-world fraud intentions. These tasks are not interchangeable. The present experiment considers a narrow, programmatically labeled **synthetic document consistency** task. A positive label means the generator intentionally modified a source statement; it does not constitute an adjudication of fraud by any institution.

The specific research question is whether the same GPT model, given different verifiable evidence contexts, distinguishes controlled edits better than document-only GPT and elementary arithmetic/date rules, **and whether it adds value over a deterministic ledger comparison when exact authoritative records exist**. This last comparator is mandatory: retrieval of nearly complete ground truth may make the LLM unnecessary.

## 2. Existing Literature and Positioning

Barry et al. (2025), *GraphRAG: Leveraging Graph-Based Efficiency to Minimize Hallucinations in LLM-Driven RAG for Finance Data*, describe graph and hybrid retrieval for financial and regulatory document reasoning (ACL Anthology: https://aclanthology.org/2025.genaik-1.6/). Li et al. (2025), *FinGEAR: Financial Mapping-Guided Enhanced Answer Retrieval*, develop structured retrieval for financial reports (https://aclanthology.org/2025.findings-emnlp.382/). Ma (2026), *Detection of false financial statements in enterprises based on dual-layer knowledge graph and graph-driven approach*, studies knowledge-graph-based false statement detection (https://doi.org/10.1007/s44163-026-00977-y). Related work on supply-chain knowledge graphs and financial fraud appeared in 2025 (https://doi.org/10.3390/jtaer20010026).



Additional verified contextual prior work includes Yu et al. (2026), *Improving Financial Statement Fraud Detection: A Large Language Model Processing Approach*, *ACM Transactions on Internet Technology*, DOI https://doi.org/10.1145/3796514 ; Yue et al. (2026), *FraudDebate-Agent*, *Mathematics*, DOI https://doi.org/10.3390/math14152695 ; and Dai et al. (2026), *FSFDLLM*, *Intelligent Computing*, DOI https://doi.org/10.34133/icomputing.0274 . These studies address issuer-level statements and narrative accounting fraud; they do not establish consumer bank-statement forgery detection, but preclude novelty claims founded merely on financial fraud plus LLM interpretation.

These established precedents preclude broad claims that combining graph retrieval and financial fraud detection is unprecedented. The present manuscript proposes a **time-valid, evidence-cited operational consistency-checking evaluation protocol**. Its originality, superiority and generalization remain hypotheses, not established contributions.

## 3. Implementation and Data Provenance

### 3.1 FraudRAG prototype

The open-source repository https://github.com/akshaysharma1088/fraudrag contains a Python FastAPI prototype, a Bronze/Silver/Gold normalization pipeline, Neo4j graph helpers, ChromaDB retrieval support, and an LLM analysis service. Software implementation is not a clinical or forensic performance validation. The model and embedding descriptions in the original unverified draft do not match all of the actual implementations. This study instead specifies the exact model and embedding implementation used by each executed experiment.

### 3.2 FraudRAG-v2 replacement corpus

The program `benchmark/fraudrag_v2.py` generates **840 cases** for **120 fictional customer groups**, 7 variations for each customer: unchanged legitimate, benign description-change negative (not yet demonstrated difficult), balance manipulation, arithmetically balanced amount alteration, out-of-range date, account identity substitution, and fabricated transaction with a corrected reported closing balance. Labels are generated deterministically from synthetic edits, not from independent investigators. Each bank-side reference is dated before its customer's document submission and includes a source identifier, institution, account and trusted statement ledger entries. These synthetic 'bank-side facts' are created by the generator and are not independently acquired bank documents.

Generation seed: `20261026`. Full synthetic CSV SHA-256 in the GitHub Actions recorded manifest:
`1ab25182cd7607f4090dc87695e1f668940a74b1d67fd620f418278f018878b7`.
The test uses exactly **28 cases** drawn from distinct customer groups (four per case type) under split seed `57`; no customer's generated statement enters both training and held-out sets. The source-level labels and edit type do not enter the GPT prompts.

### 3.3 Trusted data assumption and its limitation

The graph-evidence configuration in this first pilot includes a nearly complete **same-period authoritative synthetic bank ledger**, making exact document reconciliation possible. Real organizations may lack bank-provided authoritative ledger copies, and available records may be delayed, redacted, inconsistent, or incomplete. The experiment therefore cannot establish that graph retrieval is sufficient, that LLM reasoning is required, or that its expected gains transfer outside this controlled environment.

The historical-vector context is a TF-IDF retrieval of earlier synthetic account relationships. **The paired pilot is not an execution of Neo4j and ChromaDB in the inference path**; the graph context is serialized from programmatically produced trusted references. A separate Neo4j as-of-time retrieval integration test is being validated. Distinguishing these paths is essential to avoid misreporting the implemented experiment.

## 4. Experimental Protocol

All methods are evaluated on identical, precommitted held-out cases:

- **Arithmetic/date rules:** read the submitted document, check the opening-plus-transactions identity and statement-date consistency.
- **Exact trusted-ledger comparison:** compare the submitted fields/transaction IDs to the synthetic bank-side ledger. This is a strong non-LLM baseline with the same reference facts supplied to GPT graph-enabled modes.
- **GPT only:** the submitted statement, without retrieval.
- **GPT + historical vector context:** previous-period synthetic history retrieved through TF-IDF, without graph reference.
- **GPT + graph-style reference:** the independently constructed synthetic bank-side reference encoded as an evidence context.
- **GPT + both reference types:** historical TF-IDF passages and synthetic ledger evidence.

All GPT configurations use the same API model and output schema. Prompts prohibit unsupported evidence IDs and contain neither source labels nor manipulation categories. Invalid, ambiguous, incomplete or absent model outputs must be counted as errors or abstentions, **not silently converted into legitimate judgments**. The pilot preserves per-case predictions, evidence IDs, latency, API usage and corresponding documentation. It is explicitly a small synthetic feasibility study, not a confirmatory trial.

## 5. Results: Verified Deterministic Components

A GitHub Actions experiment on October 26, 2026 executed the dataset generator, six reproducibility/leakage tests, and both non-LLM baseline scorers: https://github.com/akshaysharma1088/fraudrag/actions/runs/40362679991 .

| Configuration | n | TP | TN | FP | FN | Precision | Recall | F1 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Arithmetic/date rules | 28 | 8 | 8 | 0 | 12 | 1.000 | 0.400 | 0.571 |
| Exact authoritative ledger match | 28 | 20 | 8 | 0 | 0 | 1.000 | 1.000 | 1.000 |

This is a **descriptive result on a very small, deliberately balanced-by-category synthetic test set with 71.4% positive labels**, not a calibrated real-world performance estimate. Exact ledger matching is perfect because the task generator supplies a complete independent synthetic bank reference against which its own alterations can be compared. That fact materially limits any plausible superiority claim for an LLM over exact checking.

**Paired GPT results: observed and independently audited on synthetic cases.** On October 26, 2026, a single actual GPT-6.1 Sol run completed **112 API calls** over four precommitted conditions and 28 unique held-out synthetic statements. Raw per-case predictions, source labels, retrieved evidence IDs, usage and timing are archived in `research/verified_runs/fraudrag_v2_20261026/`. Independent audit: `independent_post_run_audit.json` in that folder, produced after the original run and checked against the recorded original confusion counts.

| Configuration | Accuracy | Precision | Recall | F1 | Abstentions |
| --- | ---: | ---: | ---: | ---: | ---: |
| Statement-only rules | 0.571 | 1.000 | 0.400 | 0.571 | 0 |
| GPT only, no retrieved evidence | 0.571 | 1.000 | 0.400 | 0.571 | 1 |
| GPT + historical TF-IDF passages | 0.679 | 1.000 | 0.550 | 0.710 | 4 |
| GPT + serialized trusted graph-style bank reference | 1.000 | 1.000 | 1.000 | 1.000 | 0 |
| GPT + both evidence types | 1.000 | 1.000 | 1.000 | 1.000 | 0 |
| Exact authoritative-ledger comparison, no GPT | 1.000 | 1.000 | 1.000 | 1.000 | 0 |

**Results interpretation:** The same complete synthetic bank-side ledger enables perfect matching with and without GPT. Therefore the experiment offers **no evidence that GPT or hybrid Graph-RAG improves upon the strongest deterministic comparator**. The historical vector-only condition used TF-IDF over previous-period synthetic textual summaries, not ChromaDB; the graph-style condition used serialized bank records, not executed Neo4j Cypher queries. F1 and precision count any abstained positive case as a false negative and any abstained negative case as a false positive for the reporting denominator; abstention counts are reported separately to avoid hiding failures.

**Observed citation integrity issue:** Five GPT-only responses contained unsupported evidence IDs, although the prompt supplied no evidence IDs. This is a measured response-grounding limitation and must not be omitted.

**Model usage and timing:** Recorded token usage gives approximately **$0.285052** under stated standard API list rates; actual billing may differ. P50/P95 recorded model-call latencies were respectively: GPT only **4.333/24.757 seconds**; vector **4.197/25.971 seconds**; graph-style **3.633/9.024 seconds**; hybrid **4.452/23.905 seconds**. These are experimental API-call timings, **not** measured end-to-end PDF ingestion/Neo4j/Chroma/LLM latencies.

**Exploratory paired uncertainty:** Resampling the 28 independent customer cases 2,000 times (seed 42) produced a **hybrid minus GPT-only accuracy difference of 0.429** and percentile bootstrap interval **[0.250, 0.607]**. This describes the *constructed* dataset only, and must not be presented as real-world generalization or a confirmatory finding.

Original run: https://github.com/akshaysharma1088/fraudrag/actions/runs/40363144409 . Post-run verification archive: `research/verified_runs/fraudrag_v2_20261026/independent_post_run_audit.json`.

**Neo4j temporal integration, observed separately:** A GitHub Actions job
(https://github.com/akshaysharma1088/fraudrag/actions/runs/40363346100)
executed actual Neo4j 5.20 queries against twelve synthetic customer references.
Tests retrieved correctly dated snapshots and withheld seeded future evidence.
This shows that temporal querying works in the isolated test; it **does not**
mean the GPT ablation itself retrieved evidence through Neo4j.

**Chroma historical retrieval, observed separately:** A GitHub Actions job
(https://github.com/akshaysharma1088/fraudrag/actions/runs/40363998267)
completed real Chroma collection insert/retrieval using deterministic hashed
text features on synthetic *historical* records, filtering future-dated matches.
It is **not** a measured Chroma-backed GPT result.

**Digital-PDF extraction, observed separately:** A GitHub Actions job
(https://github.com/akshaysharma1088/fraudrag/actions/runs/40364130518)
produced and extracted 28 fictional vector-text PDFs while validating expected
structured fields. Scanned PDFs, image forgeries, OCR mistakes and real bank
templates were not tested.

## 5A. Multi-Seed Synthetic Robustness Evaluation

A separate run generated 4,900 text-native cases for 700 fictional customer groups and evaluated three customer-disjoint test splits with 175 held-out cases in each (25 per case category; split seeds 57, 61, and 83). The generator, raw prediction log, versioned evaluation procedure and results are recorded in `benchmark/robustness_multiseed_v2.py` and `research/RESULTS_MULTISEED_SYNTHETIC_2026-10-26.json`; actual execution: https://github.com/akshaysharma1088/fraudrag/actions/runs/40366478963 .

Across the three synthetic splits, arithmetic/date rules attained a mean F1 of **0.5714**. Complete synthetic bank-ledger comparison attained mean F1 **1.0000**, as expected because the constructed reference is a complete reconciliation oracle. When access was limited to two out of four bank ledger transactions, the deterministic comparator's mean F1 fell to **0.4350** and it abstained on **379 of the 525** evaluated cases. With only bank/account identity, mean F1 was **0.2500**, with **450 of 525 abstentions**. With no bank-side record, the checker abstained on all **525** cases. These measures intentionally penalize abstention as an unsuccessful classification; abstention itself does **not** imply that the document is fraudulent or legitimate.

The three splits share the same underlying 700 fictional customers and generator templates. Consequently, the outcomes are not independent real-world replications. Nor do the enlarged synthetic experiments validate GPT or production document parsing. The major observed limitation is that complete independent ground truth in the graph makes reconciliation easy; realistic missing-record distributions still need evaluation.

## 5B. Independent SEC Enforcement-Linked Fraud Study — Different Task

To examine whether a real, highly imbalanced fraud-label dataset changes the research outlook, we evaluated the published Bao et al. (2020) processed firm-year accounting panel (https://doi.org/10.1111/1475-679X.12292), using 146,045 SEC enforcement-linked labeled observations and 28 documented raw accounting variables. Data were downloaded from a pinned GitHub revision and hashed; the original data were not redistributed. Observed experiment: https://github.com/akshaysharma1088/fraudrag/actions/runs/40366949592 . Machine-readable audit: `research/RESULTS_REAL_AAER_2026-10-26.json`.

A median-imputed, standardized, class-balanced logistic-regression baseline achieved average precision (PR-AUC) **0.00614** and ROC-AUC **0.6501** on a time-ordered 2009–2014 test set of 33,064 firm-years containing only 112 labeled positives (0.339%). Under company-isolated evaluation, PR-AUC was **0.01352** and ROC-AUC **0.6530** on 28,579 held-out firm-years with 154 labeled positives (0.539%). Threshold selection occurred on separate validation partitions. Such low positive prevalence makes precision-recall evaluation indispensable; neither a high majority-class accuracy nor these baselines demonstrates competent detection in deployment.

**Crucial task separation:** These real observations concern public-company *accounting misstatements* linked to enforcement actions, not forged consumer bank statements. The experiment used neither GPT nor Neo4j nor ChromaDB. Its low baseline scores **cannot** be presented as a benchmark result for FraudRAG or as evidence that the prototype detects real forged financial documents.

## 5C. Actually Integrated Neo4j + ChromaDB + GPT Experiment

After the separately reported serialized-context pilot, a second **genuinely integrated** experiment ran real temporal Cypher lookups on an isolated Neo4j 5 database and real queries against an in-memory ChromaDB collection to construct each GPT prompt. It used the same 28 precommitted, customer-disjoint synthetic submissions and four paired conditions. Each condition had **28 actual model responses** (112 calls total). The graph contained fictional, complete same-period bank-ledger facts with source provenance. The Chroma historical corpus used **locally hashed 256-dimensional text features**, not OpenAI embeddings. Neither retrieval mechanism accessed target fraud labels in the prompts. Original execution: https://github.com/akshaysharma1088/fraudrag/actions/runs/40366638447 . Independently audited, permanently stored records: `research/verified_runs/fraudrag_v2_integrated_20261026/`.

| Actually executed configuration | TP | TN | FP | FN | Accuracy | F1 | Abstentions |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| GPT, statement alone | 8 | 8 | 0 | 12 | 0.571 | 0.571 | 0 |
| GPT + real Chroma historical retrieval | 9 | 5 | 3 | 11 | 0.500 | 0.563 | 8 |
| GPT + real Neo4j bank-side ledger retrieval | 20 | 8 | 0 | 0 | 1.000 | 1.000 | 0 |
| GPT + both actual database retrieval mechanisms | 20 | 8 | 0 | 0 | 1.000 | 1.000 | 0 |
| Same exact ledger, deterministic comparison, **no LLM** | 20 | 8 | 0 | 0 | 1.000 | 1.000 | 0 |

The independent auditor confirmed 112 unique case/mode outcomes, complete coverage, correctly filtered dated source records, and exact agreement with original logged confusion counts. **Two GPT-only responses supplied source IDs absent from the prompt**, demonstrating a residual evidence-grounding failure. The complete-bank-ledger comparator again matches both Graph-assisted GPT modes. Accordingly, **these results do not demonstrate that hybrid Graph-RAG adds predictive accuracy beyond a simple non-LLM authoritative match**. Moreover, adding Chroma-only historical text reduced synthetic F1 versus no-retrieval GPT (0.563 versus 0.571) in this sample; the study does not establish that retrieval reliably improves performance.

The independently recomputed exploratory paired difference between integrated and document-only GPT accuracy was **0.4286**, with a 2,000-resample customer-level percentile bootstrap 95% interval **[0.250, 0.607]**; this interval describes only the constructed evaluation population and is not an external-generalization claim.

API call p50/p95 durations, in seconds, were: document-only **4.189 / 14.951**, Chroma-only **5.039 / 25.589**, Neo4j-only **3.934 / 15.755**, integrated **3.462 / 6.122**. These are model-call timings, not whole-system PDF/OCR/retrieval throughput. Total recorded token usage corresponded to approximately **$0.283302** in estimated API token charges under the recorded standard rates; final billing could differ. The experiment makes no production-scale or bank-fraud accuracy claim.

**Primary limitations:** All graph records and their authoritative same-period ledger contents were generated programmatically as a near-perfect oracle; only 28 synthetic submissions were scored. The graph inference traversed bank/account ledger relationships; no fraud-ring labels or k-hop superiority hypothesis was tested. The vector embeddings were simple deterministic hash features, not semantic embedding model output. Thus this is a transparent *software-integration feasibility and comparison study*, not evidence of a superior real-world financial-fraud detector.

## 5D. External synthetic-bank-PDF source experiment (Benchmark v3)

Five openly licensed, third-party **synthetic** bank-statement PDFs were fetched at pinned commit `2d8d31d68dcedbf9028b87f6c7df286f53a6c7de` from Bankstatemently's benchmark. All five actual PDF SHA-256 hashes matched the publisher's reissued source records, and text extraction yielded selectable text on **17/17 pages**. The underlying transaction-level answer keys are not included in the public release, so no field-extraction accuracy claim is supportable. All source accounts are fictional and **none is an independently adjudicated bank fraud case**.

We applied controlled perturbations to the **extracted text**: one unchanged case, one harmless whitespace-only variant and two single-monetary-number edits for each of the five source PDFs, giving **20 related examples** with ten deliberate edits. Comparing against the complete extracted original correctly distinguished all cases by construction because it had an exact textual oracle. Both a normalized first-30-token partial reference and no-reference comparison returned abstentions for all 20. These decisions represent inability to verify, not findings of authenticity or wrongdoing.

The experiment was executed at https://github.com/akshaysharma1088/fraudrag/actions/runs/40371198225 . The source checksums, corpus design, precommitted comparisons and exclusions are stored in `research/RESULTS_V3_EXTERNAL_PDF_2026-10-26.json`. The first partial-reference implementation sliced by character count and produced false detections due to harmless whitespace changes. This flaw was corrected to lexical-token normalization and documented; the earlier run is explicitly superseded. The PDF source files are not redistributed by this repository.

**Inference boundary:** these results verify ingestion and controlled text-edit comparison on only five externally sourced fictional PDFs. They do not validate scanned image forgery, independently annotated genuine bank fraud, transaction-level parsing accuracy, novel Graph-RAG advantages or cross-institution generalization. GPT results from a later v3 study may be cited only after their separate raw inference records have passed independent auditing.

## 6. Limitations, Ethics and Threats to Validity

All data are fictional; no private bank statements or customer records are used. The examples have text-native, regularized formatting and no OCR corruption, image-level tampering, financial institution branding, third-party adjudication, or real-world fraud labels. Every manipulation is produced from a small, known transformation family. Customer-disjoint splits reduce direct identity leakage but do not make institution or generator distributions independent. The authoritative ledger is more complete than most externally accessible financial records. Thus perfect synthetic matching is not evidence of deployable accuracy.

A trustworthy deployment must also address unjustified graph-based guilt by association, user rights, human analyst review, model errors, sensitive financial information processing, retention restrictions, account-access authorization, temporal inconsistencies, and adversarial prompts embedded in uploaded statement text.

## 7. Conclusion and Status

The new dataset, evaluation scripts, provenance and deterministic baseline measurements establish a reproducible starting point for evaluating financial-document consistency checking, but **do not validate the legacy FraudRAG-2400 manuscript**. The early finding that an exact ledger comparison solves the synthetic task prevents an unsupported claim of Graph-RAG superiority. The research contribution will have to be more carefully defined and independently substantiated through graph/embedding integration, incomplete-evidence cases, independent real-world evaluation and a much more robust test design.

**SUBMISSION GATE: NOT CLEARED.** The full GPT results, exact implementation verification, larger held-out and hard-negative evaluations, statistical uncertainty, end-to-end latency, bibliography audit and journal-fit review remain necessary.

## Source and evidence record

- Generator: `benchmark/fraudrag_v2.py`.
- Deterministic scorer: `benchmark/evaluate_v2.py`.
- Model protocol: `experiments/fraudrag_v2_gpt.py`.
- GitHub Actions baseline: https://github.com/akshaysharma1088/fraudrag/actions/runs/40362679991 .
- Claim-level exclusions: `research/CLAIM_VERIFICATION_REGISTER.md`.
- Targeted literature: `research/LITERATURE_NOVELTY_AUDIT.md`.
