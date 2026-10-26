# Evidence-Grounded Financial-Statement Consistency Checking with GPT and Time-Filtered Bank-Side References

**Research working draft — NOT APPROVED FOR JOURNAL SUBMISSION**  
**Author:** Akshay Sharma  
**Date:** October 26, 2026  
**Evidence policy:** Every numerical result here is derived from a recorded workflow. Model-assisted results remain pending until actual execution and source validation.

## Abstract

This working paper investigates whether retrieved bank-side and historical account evidence improves the detection of **controlled synthetic modifications** to machine-readable financial statements. The goal is document *consistency checking* against separately held records, not a demonstrated solution to real-world financial crime. The research implementation includes a domain-structured ingestion and Graph-RAG software prototype and a newly generated controlled dataset, FraudRAG-v2, containing 840 synthetically generated statement cases grouped into 120 fictional customers. The evaluation preserves customers as disjoint units and uses a precommitted 28-case held-out subset with four cases from each of seven manipulation/legitimate categories. A basic arithmetic/date baseline achieved an F1 of 0.571 (precision 1.000, recall 0.400) on this subset. A separate deterministic baseline comparing each submitted statement against an **authoritative same-period synthetic bank-side ledger** achieved F1 1.000. These outcomes underscore the critical role, and unrealistic completeness, of the trusted ledger supplied in this synthetic study. We also specify a paired GPT study with statement-only, historical-text retrieval, serialized bank reference, and combined evidence configurations; these runs must be completed and audited before reporting any corresponding results. No current result substantiates claims about real-bank forgery detection, production scalability, novelty priority, or superiority to classical reference matching.

## 1. Scope, Motivation and Research Questions

Financial statement manipulation presents several independent tasks: verifying accounting arithmetic, identifying modifications to authentic records, comparing a submitted statement with a bank-side ledger, and investigating real-world fraud intentions. These tasks are not interchangeable. The present experiment considers a narrow, programmatically labeled **synthetic document consistency** task. A positive label means the generator intentionally modified a source statement; it does not constitute an adjudication of fraud by any institution.

The specific research question is whether the same GPT model, given different verifiable evidence contexts, distinguishes controlled edits better than document-only GPT and elementary arithmetic/date rules, **and whether it adds value over a deterministic ledger comparison when exact authoritative records exist**. This last comparator is mandatory: retrieval of nearly complete ground truth may make the LLM unnecessary.

## 2. Existing Literature and Positioning

Barry et al. (2025), *GraphRAG: Leveraging Graph-Based Efficiency to Minimize Hallucinations in LLM-Driven RAG for Finance Data*, describe graph and hybrid retrieval for financial and regulatory document reasoning (ACL Anthology: https://aclanthology.org/2025.genaik-1.6/). Li et al. (2025), *FinGEAR: Financial Mapping-Guided Enhanced Answer Retrieval*, develop structured retrieval for financial reports (https://aclanthology.org/2025.findings-emnlp.382/). Ma (2026), *Detection of false financial statements in enterprises based on dual-layer knowledge graph and graph-driven approach*, studies knowledge-graph-based false statement detection (https://doi.org/10.1007/s44163-026-00977-y). Related work on supply-chain knowledge graphs and financial fraud appeared in 2025 (https://doi.org/10.3390/jtaer20010026).

These established precedents preclude broad claims that combining graph retrieval and financial fraud detection is unprecedented. The present manuscript proposes a **time-valid, evidence-cited operational consistency-checking evaluation protocol**. Its originality, superiority and generalization remain hypotheses, not established contributions.

## 3. Implementation and Data Provenance

### 3.1 FraudRAG prototype

The open-source repository https://github.com/akshaysharma1088/fraudrag contains a Python FastAPI prototype, a Bronze/Silver/Gold normalization pipeline, Neo4j graph helpers, ChromaDB retrieval support, and an LLM analysis service. Software implementation is not a clinical or forensic performance validation. The original paper described Claude 3.5 and Anthropic embeddings, which are not the verified model configurations for the current GPT study; those historical descriptions are excluded from this research report.

### 3.2 FraudRAG-v2 replacement corpus

The program `benchmark/fraudrag_v2.py` generates **840 cases** for **120 fictional customer groups**, 7 variations for each customer: unchanged legitimate, format-only hard negative, balance manipulation, arithmetically balanced amount alteration, out-of-range date, account identity substitution, and fabricated transaction with a corrected reported closing balance. Labels are generated deterministically from synthetic edits, not from independent investigators. Each bank-side reference is dated before its customer's document submission and includes a source identifier, institution, account and trusted statement ledger entries. These synthetic 'bank-side facts' are created by the generator and are not independently acquired bank documents.

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

**GPT results:** [BLOCKED — DO NOT SUBMIT] To be inserted only after the paired inference completes, archived raw predictions are audited and all comparison conditions are verified.

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
