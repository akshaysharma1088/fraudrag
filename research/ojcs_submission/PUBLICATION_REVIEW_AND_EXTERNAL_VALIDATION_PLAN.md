# OJ-CS journal submission project — evidence-grounded manuscript v0.1

**Date:** 2026-10-26  
**Manuscript working title:** *Evidence Sufficiency and Acquisition Cost in Financial-Document Verification: An Audited Graph-Retrieval and Deterministic Baseline Study*  
**Status:** **REVIEW DRAFT; DO NOT SUBMIT**. A four-page compiled IEEEtran provisional two-column PDF and editable LaTeX source were generated and supplied directly to the author in the ChatGPT conversation on October 26, 2026. The formatted paper source is NOT YET mirrored into this GitHub directory. Do not pretend a PDF exists at a GitHub location without an actual verified upload.

## Immediate editorial decision

Prioritize a precise, defensible methodological paper, NOT the old claim of a novel bank-fraud detector. The strongest prior results show why:

1. **LLM retrieval test:** genuinely integrated Neo4j + Chroma + GPT on 28 fictional held-out statements: GPT-only F1 0.571, Chroma-history F1 0.563, graph-ledger GPT F1 1.000, graph+Chroma GPT F1 1.000. **The equally informed deterministic exact-ledger comparator also achieves F1 1.000.** There is no measured incremental predictive value over that strongest baseline. Actual execution and independent audit: https://github.com/akshaysharma1088/fraudrag/actions/runs/40366638447 and https://github.com/akshaysharma1088/fraudrag/actions/runs/40368862175 .
2. **External layout test:** five externally published but *synthetic* bank-statement PDF origins (17 pages), 20 controlled text cases and 60 paid GPT evaluations. Full exact original gives 20/20 decisions; missing/short source leads to 20/20 abstentions. No actual forged/scanned bank-document ground truth. https://github.com/akshaysharma1088/fraudrag/actions/runs/40372704350 .
3. **Source-acquisition study:** 1,080 fictional calibration, 720 held-out and 360 shifted fictional groups, four **deterministic** source-selection policies. At budget 4 invented units, standard DP completes 509/720 (70.69%) at mean 2.593 cost versus prior-aware greedy 495/720 (68.75%) at 2.794. Difference in paired completion coverage +1.94 percentage points, 95% CI [−0.14,+4.03], which contains zero. Shifted DP coverage 35.00% versus prior-aware greedy 35.56%, an inconclusive slightly worse coverage. No real source availability or cost, no novel DP algorithm. Full audit: https://github.com/akshaysharma1088/fraudrag/tree/research/reproducibility-hardening-2026-10/research/verified_runs/fraudrag_v4_adaptive_20261026 .

## Official OJ-CS requirements checked

- Journal CFP and author instructions: https://www.computer.org/digital-library/journals/oj/cfp-open-journal
- **Actual IEEE Open Journals Word/LaTeX article template is required**, not merely generic IEEEtran; the review PDF provided in chat is PROVISIONAL.
- **Maximum 12 double-column pages**, figures uploaded individually.
- Regular/special issue abstracts **100–200 words**. The current provisional paper's abstract is 151 words.
- OJ-CS rapid-review has **no revision option**: https://www.computer.org/publications/peer-review-schedules .
- IEEE AI-generated-content policy requires acknowledgment naming tool, affected sections and level of assistance: https://open.ieee.org/author-guidelines-for-artificial-intelligence-ai-generated-text/ .

## Priority: next independent external test WITHOUT PLAID

A stronger paper must move beyond fictional issuer statements and evaluation policies trained/tested on identical simulator families.

**Recommended external evidence benchmark:** NExT++ TAT-QA, 16,552 human-authored questions over hybrid table+text contexts from real published financial reports, with official public dev/test data, source-related paragraph annotations and **CC BY 4.0 dataset license**. Official repo: https://github.com/NExTplusplus/TAT-QA ; paper DOI 10.18653/v1/2021.acl-long.254 . This is **financial-report question answering**, NOT bank-statement forgery or adjudicated fraud. Use to test evidence sufficiency, witness deletion and response abstention, never label it a real document-fraud benchmark.

Second candidate **FinMRAGBench** (ACL Findings 2026): 887 expert-verified QA pairs over real annual reports, code/data https://github.com/sqyangit/FinMRAGBench , paper https://aclanthology.org/2026.findings-acl.187/ . Inspect its exact dataset license/access and model evaluation instructions before caching/repackaging any source content.

### Preregistered external protocol v5 (NOT YET RUN)

1. Fix and hash a specific upstream release/commit. Preserve original source IDs; do not alter gold-answer strings and then claim independent adjudication.
2. Separate training/development and sealed test by **source document/group**. Establish that reports or evidence contexts do not leak across splits; mark any existing benchmark test use by the model as a contamination limitation.
3. Study evidence availability states **induced from documented gold supporting evidence**: complete, partial, missing, irrelevant, and conflicting. Clearly label conflict construction as synthetic even though base report contexts are real.
4. Compare GPT without source; GPT with source, explicit abstention prompt; exact deterministic source-span baseline when well defined; full evidence-contract gate; graph/vector retrieval with identical document access. **Fair same-information source conditions** for all methods.
5. Primary outcomes: incorrect supported-answer rate **at matched non-abstention coverage**, source citation validity, group-level abstention/errors, retrieval cost measured in actual calls/tokens and separately time. Log end-to-end system latency; avoid invented bank prices. Report required source-answer extraction limits and natural financial QA scoring.
6. Cluster uncertainty by document/report group (not dozens of dependent questions from the same report). Precommit a primary contrast and error analysis before touching the sealed test.
7. Test the `NO REAL DOCUMENT FORGERY CLAIM` gate: this study can validate financial *evidence sufficiency in QA* but cannot validate independent bank-statement authenticity or fraud detection.
8. Retain rights and attribution, original upstream link and SHA, raw predictions, source captures, costs and reproducible scripts. Author reviews study design before any paid GPT use.

### Prospective reviewer kill criteria

- **Novelty:** evidence-sufficiency/abstention, graph-RAG, temporal sources and DP acquisition all predate us. The combination is not automatically novel. Need a genuinely new, tested source-contract method or useful external benchmark with a clearly demonstrated result, or reposition to a more suitable venue.
- **Fairness:** equal-information deterministic baseline must remain in all tables.
- **External validity:** no claim about actual bank forgery accuracy from real public company-report QA.
- **Statistical strength:** true source-document groups, confidence intervals, and equal coverage/cost comparisons are mandatory; simulated beta distributions are not bank operations.
- **Authorship and overlap:** correct, not delete, the May 2026 SSRN preprint DOI 10.2139/ssrn.6714178, whose public abstract contains unsupported historical results; explain the actual prior overlap to OJ-CS.
- **AI disclosure, rights and editor approval:** no journal submission until author verification and appropriate permissions.

## Initial submission package (in chat)

The four-page review PDF includes:
- 151-word abstract and appropriately bounded contribution statement
- Definition of reference admissibility, distinct effective-time and recorded-time checks, source deduplication and explicit deferral states
- Conceptual source-trust diagram
- Real Neo4j/Chroma/GPT results against exact ledger
- Acquisition table and actual coverage-vs-budget plot from archived V4 data
- Null coverage confidence interval, shifted experiment, validity threats, disclosure, and seven verifiable primary research references
- Explicit note distinguishing the earlier cited SSRN FraudRAG paper

It has been compiled and rendered to images for visual inspection but has **not** yet received human author or expert methodologist signoff. The seven references are not necessarily sufficient for final submission; expand related work through verified sources only. Current provisional page count 4 is under OJ-CS's 12-page maximum but is not a completeness judgment.

**Next manuscript revision should incorporate measured new externally grouped evidence-QA outcomes and the author-approved SSRN correction; do not invent data in the results section while waiting.**
