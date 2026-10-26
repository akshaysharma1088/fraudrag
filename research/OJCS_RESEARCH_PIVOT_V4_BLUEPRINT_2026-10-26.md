# FraudRAG-OJCS: Research Pivot and Falsifiable Experiment Blueprint
**Version:** brainstorm and preregistration candidate v0.1 — 2026-10-26  
**Author signoff:** PENDING. **Actual novel contribution and external validity:** NOT ESTABLISHED.  
**This is design/protocol, NOT experimental results or a final manuscript.**  
**Target:** IEEE Open Journal of the Computer Society (OJ-CS), not IEEE Access.

## 0. One-sentence thesis

A financial-document verifier should **make only those document-consistency claims justified by trustworthy, timely, independently acquired evidence**; otherwise it must return a precise, reproducible reason for deferral, and optionally identify the lowest-cost missing evidence needed to resolve the case.

Do **not** claim that the system proves the document genuine, identifies criminal intent, or authenticates an issuer merely by attaching a graph reference. Certificates are **conditional on independently validated source attestation**. If exact deterministic reconciliation with the same source facts matches or beats this method, acknowledge that outcome prominently.

## 1. Candidate title and scope

**Recommended working title:**  
*FraudRAG: Evidence-Conditioned Selective Reconciliation with Provenance and Temporal Constraints for Financial Documents*

**Alternative, if the method proves weaker than deterministic baselines:**  
*When Retrieval Does Not Help: An Auditable Evaluation of Evidence Sufficiency and Abstention in Financial Document Checking*

The word **fraud** in the system name is a project label, not an assertion of independently adjudicated fraudulent bank records. In the paper, use "scripted document inconsistency," "counterfactual evidence availability," "forged-signature task" and "SEC accounting misstatement" for their respective datasets, never as equivalent labels.

## 2. Brainstormed options, scored BEFORE further experiments

| Candidate | Potential research value | Main risk | Verdict |
|---|---|---|---|
| A. Graph-RAG financial fraud superior to rules | Low: previous complete-ledger oracle already lets deterministic comparator match perfect GPT | Not supported, existing financial GraphRAG prior art | **REJECT** as central claim |
| B. Five-level evidence sufficiency + LLM abstention | Moderate pedagogical value | 2026 published evidence-sufficiency benchmark already covers five levels and LLM abstention | **REJECT** as novelty claim alone |
| C. Time-valid knowledge graph retrieval | Useful systems component | Temporal GraphRAG, TEQA and other methods already exist | **RETAIN AS COMPONENT**, not originality claim |
| D. Proof-carrying/citation-checked RAG answers | Useful accountability | Published proof-carrying answers, source provenance and related formal work already exist | **RETAIN AS COMPONENT**, not originality claim |
| E. Formal source-evidence contracts for selective financial reconciliation, explicitly tied to source completeness, independent issuer attestation and **bitemporal validity**, plus contradiction/missing-evidence certificates | Potentially defensible domain-method contribution if distinct formal rules and falsifiable demonstrations emerge | Could still be reducible to standard deterministic reconciliation | **PRIMARY HYPOTHESIS, not yet proven novel** |
| F. Adaptive minimum-cost evidence request planning over multi-source data with temporal and privacy constraints | Stronger research systems angle if measurable utility at matched error | Prior iterative/cost-aware fact-checking; optimization and privacy could be nontrivial | **SECONDARY HYPOTHESIS**; require baseline comparisons |

**Decision:** Focus on E. Add F only if a separately evaluated query-cost reduction exists over fair greedy and oracle planners. Avoid bloating the paper with unrelated SEC AAER classification, marketing architecture and unverified image forensics.

## 3. Exact semantics: "selective reconciliation" rather than binary fraud

Represent each normalized submitted document as **claims** (c_i=(field_key,value,period,statement_source)).  
Represent an independently obtained reference as:

`r_j = (record_id, issuer_id, source_family, field_key, field_value, valid_from, valid_until, recorded_at, ingested_at, issuer_attestation_id, source_is_verified, completeness_scope, extraction_lineage)`

- **Valid time:** when the reference statement/fact describes the world.
- **Transaction/observation time:** when the verifier actually knew the evidence. It is forbidden to inspect records learned after the document submission/decision cutoff, even if they describe a historical period.
- **Completeness scope:** an **externally attested** explicit statement that an issuer's reference enumerates all facts for some target account/period/field; the absence of an expected record in an incomplete response is never proof of nonexistence.
- **Independence:** two records copied from the same upstream issuer must not be counted as two corroborating confirmations merely because Neo4j and Chroma return them through distinct databases.
- **Citation validity:** source record ID, digest and time constraint must be traceable to a verified trust registry independent of the submitted document. **Hashing an unauthenticated source cannot establish its truth.**
- **LLM role:** optional extraction, candidate alignment and natural-language explanation. Final statuses and source citations are decided by a separately testable deterministic gate, never LLM self-confidence alone.

Define **field-level** status (not legal authentication):
1. `DIFFERENCE_PROVEN`: a timely independently verified issuer reference directly disagrees with a submitted field; no authoritative contradictory references remain unresolved.
2. `MATCH_SUPPORTED`: timely independently verified issuer reference matches the field **and** completeness for the comparison scope has been externally attested. For entire-document status, this must hold for every required field/transaction, not just a preview.
3. `EVIDENCE_CONFLICT`: independently verified, same-scope reference facts disagree and source precedence cannot be resolved from predefined authority policy.
4. `INSUFFICIENT_EVIDENCE`: relevant, timely authenticated evidence and/or coverage attestation are missing; never equate this with an authentic statement.
5. `SOURCE_UNTRUSTED_OR_STALE`: the only apparent witnesses are unverified, temporally invalid, derived solely from the submitted document or issued after decision cutoff.

**Case-level precedence:** Conflicting authoritative records for a relevant field require explicit `EVIDENCE_CONFLICT` and human review. Otherwise any `DIFFERENCE_PROVEN` supports "document differs from reference," NOT "fraud." Only all required fields `MATCH_SUPPORTED` authorize "consistent with these complete references"; any remaining inconclusive field ⇒ abstain. The certificate must list both witnesses and missing required evidence keys.

### Non-probabilistic safety invariants to test

- **I1 (No unsupported clearance):** no entire-document `MATCH_SUPPORTED` if any required claim lacks a complete, attested timely independent witness.
- **I2 (No unsupported mismatch):** no `DIFFERENCE_PROVEN` from a user-uploaded text, unverified citation, stale or future-ingested record alone.
- **I3 (Time):** moving a source's recorded/ingestion time beyond the as-of decision cannot increase warranted claim coverage.
- **I4 (Source independence):** duplicating the same issuer's fact in another retrieval index cannot increase corroborating source-family count.
- **I5 (Conflict visibility):** injecting a valid authoritative record incompatible with an earlier record on the same field does not silently retain a confident conclusive result.
- **I6 (Missing ≠ absence):** removing a supporting record without a completeness attestation can reduce clearance to abstention but cannot prove tampering.
- **I7 (Auditable witness):** every positive field-level consistency/inconsistency verdict has a valid source identifier with machine-replayable predicate and time.
- **I8 (Robustness):** instructions embedded in the uploaded financial text cannot override these deterministic checks.

These are conditional behavioral properties under a stated, manually/cryptographically verified reference trust boundary, **not global guarantees of real document truth**. The first implementation is an executable proof-of-concept with unit/property tests and no cryptographic issuer-authentication integration.

## 4. Research hypotheses and ways to FAIL them

**H1 — warranted decision under evidence gaps:** At matched **decision coverage**, the proposed verifier produces fewer unsupported `MATCH_SUPPORTED` decisions than reference-matching and GPT baselines **only if those baselines lack sufficient provenance/completeness policy**, with all methods seeing identical raw evidence. **Mandatory strongest counter-baseline:** a competent deterministic bitemporal coverage-aware verifier using exactly the same provenance registry. If it ties, report that and abandon predictive-superiority framing.

**H2 — bitemporal correctness:** Unlike naive timeless retrieval or transaction-date-only filters, excluding after-cutoff and expired evidence reduces future-data leakage and unsupported decisions, measured on deliberately seeded backdated, corrected and late-arriving references. A competent bitemporal deterministic baseline should also tie. Isolate timing contribution, not "GraphRAG magic."

**H3 — conflict handling:** Explicit inconsistent-source certificates improve **conflict detection and explanation replay correctness**, not automatically classification F1. Compare with a rule-only conflict detector given the same signed reference metadata and with GPT/GraphRAG prompted on that same metadata.

**H4 — evidence efficiency (optional):** A metadata-aware request planner reduces mean **trusted evidence fetch cost, number of lookup calls or p95 verification latency** at the same verified-decision coverage and equal false-clearance rate, compared with fixed query plans, greedy deficit-first lookup, equivalent deterministic planner and (where small enough) exact optimal plans. This is the most promising optimization contribution **if supported by measured results**, not a claim we have today.

**Precommitted failure outcome:** If none of the hypotheses meaningfully distinguish this method from fair deterministic methods, write a transparent *reproducible negative result and operational evaluation protocol* or target a systems/research software venue. OJ-CS is not automatic. Do NOT remove fair baselines or pretend synthetic labels are real fraud.

## 5. Concrete next benchmark (FraudRAG-v4) — no model costs until locked

### Dataset design (distinct from prior 28-case and 5-source pilots)

- Build a **new** scenario generator and release distinct source-group split manifests; no reusing the 28 held-out synthetic customers to tune the new approach.
- Intended pilot: at least **1,000 fictional account groups** across at least **6 disjoint generator/layout families**, with independent generator seeds and at least three disjoint study partitions: training/development, calibration and **sealed test**. A true unseen-family test is a separate cohort. The arbitrary counts are study targets, **not a powered guarantee**.
- Cases include honest arithmetic-consistent edits; legitimate rare high-value transfers; legitimate new accounts; amount/date/entity/transaction changes; balanced manipulations; unknown transaction IDs; source contamination; duplicate upstream issuer facts; account merges; reversed transfers; transaction corrections; backdated evidence; stale documents; delayed banking feeds; partial account closure; same-priority source contradictions; forged/unsigned reference records; prompt-injection text; scanned input **only if actual licensed images and OCR labels exist**.
- Assign each target claim one of five **evidence sufficiency** settings: fully supported, partially supported, irrelevant, absent, contradictory, plus timestamp/source-integrity perturbations. Explicitly cite Zhang and Wu (2026); these five levels are not new to our work.
- Source release and decision cutoff defined independently from tamper label; no mutation-type label, ground truth, or inaccessible future version enters the GPT prompt or machine-readable reference evidence.
- Bank/institution group, customer group, source document group and source template group are all tracked; splitting by one ID while sharing a generator family is NOT independent external validation.
- All public fixtures are **synthetic**, have nonidentifying issuer names, and record exact ground-truth generation. No claims about the real-world rate of banking fraud.

### Models and baselines (same facts and same retrieval budget)

**B0** Arithmetic and document-internal validity only.  
**B1** Plain exact bank-ledger matching without completeness/temporal guards.  
**B2** **Strongest deterministic bitemporal + completeness + conflict-aware verifier**, identical source registry and coverage definition. Primary falsification comparator.  
**B3** LLM using full provided evidence without forced abstention.  
**B4** LLM explicitly instructed to abstain (fair baseline; literature already studies this).  
**B5** Neo4j temporal retrieval + Chroma historical retrieval + LLM, same fixed budget.  
**B6** B5 with deterministic source-certificate gate.  
**B7 (optional)** B6 with **adaptive evidence retrieval**; compare with greedy and exact/ILP equivalent decision planners under same costs.

**Ablations:** remove completeness, recording-time filtering, source-family deduplication, conflicting-witness tracking, signed authority metadata, missing-key certificate, graph retrieval, vector retrieval, optional query planning. Each ablation must be runnable and disallow labels in input.

### Primary and secondary metrics

1. **False-clearance**: decisions marked consistent that actually conflict with the controlled original. Denominator and gold criterion explicit. **Only count non-abstained clearances**; report false-clearance per eligible case as well as per issued clearance.
2. **Risk–coverage:** classification error rate on nonabstained cases *versus* fraction of cases with decisions. Compare **at matched coverage and matched evidence budgets**, never "0 error" from always abstaining.
3. **Conflict recall / conflict-resolution error**, future-evidence leakage violations, independent witness validity, source-ID hallucination and evidence-certificate replay correctness.
4. **Abstention rate, deferral burden**, worst-group performance, false accusation rate on legitimate unusual behavior, cost per verified decision.
5. Actual **end-to-end** p50/p95 including PDF extraction/normalization, Neo4j, Chroma, LLM, source checks; separately report API-only timings and tokens.
6. Group/bootstrap confidence intervals over **independent original source groups**, not perturbation duplicates. Control family-wise comparisons or predeclare one primary comparison. Avoid claiming a 1% false-clearance upper bound from repeated mutations of five originals.
7. Measurement sensitivity to artificial fraud prevalence, incomplete-reference incidence, source-trust errors and missing-not-at-random conditions. State calibration validity assumptions and shifts. No generic conformal guarantee without exchangeability or explicitly justified assumptions.

### Review-proof experiment integrity

- Register exact hypotheses, random seed **before** looking at sealed test results and freeze the source/cost policy.
- Archive complete per-case outputs, retrieved facts, source versions, time cutoffs, replays, latency and cost with immutable source hashes. Keep private source bytes out of public GitHub.
- Human blind audit of a stratified held-out sample of labels/certificates; report inter-rater disagreement. Automated source assertions alone do not count as independently adjudicated genuine fraud.
- If external licensed data become available (DocTamper, AIForge-Doc, SSBI), **run and report each separate task separately**; they do NOT form a consumer bank statement forgery test.
- All expensive/paid model experiments require explicit budget and sealed protocols before any calls; rerun statistical analysis freely without reprompting, but do not repeatedly optimize on test.

## 6. Suggested four-part architecture

`Uploaded financial document (untrusted)` → **Claim extractor** (schema, precision, normalizer, field evidence spans) →  
**Time-and-origin-aware evidence index** (Neo4j for verified relationships and as-of retrieval; Chroma for candidate context only) →  
**Deterministic evidence-contract checker** (trust, valid-time, recording-time, completeness, conflict, minimum witnesses) →  
**Selective decision certificate** with justified status + replay IDs + missing evidence keys + optional next-source request.

GPT may assist retrieval planning, candidate matching and human explanation. It may NOT "promote" a low-trust passage to an independently attested bank source or change a verified field conclusion without a machine-verifiable witness.

**Certificate example (illustrative, NOT observed system output)**:

```json
{
  "doc_group": "fictional-C3",
  "cutoff": "2026-03-01T00:00:00Z",
  "status": "INSUFFICIENT_EVIDENCE",
  "supported_claims": ["account_id", "closing_balance"],
  "missing_required_claims": ["transaction:T-004:amount"],
  "contradictory_claims": [],
  "supporting_sources": ["issuer-sandbox://ledger-2026-02-28"],
  "limits": [
    "external completeness of transaction list not attested",
    "not a real-world bank fraud authenticity judgment"
  ]
}
```

## 7. Figures and manuscript structure for 12-page IEEE cap

- **Fig 1:** trust-boundary architecture and proof-carrying selective reconciliation (not a marketing diagram).
- **Fig 2:** bitemporal fact sequence showing correction arriving after decision, plus the prohibited future leakage edge.
- **Fig 3:** example certificate: why `MATCH_SUPPORTED`, `DIFFERENCE_PROVEN`, `EVIDENCE_CONFLICT` and `INSUFFICIENT_EVIDENCE` differ.
- **Fig 4:** **measured** risk–coverage and cost–coverage curves by independent test group. If no measurements, omit this figure rather than illustrate invented metrics.
- **Fig 5:** matched-coverage ablations with group confidence intervals, and hidden subgroup failures. Only after actual results.
- **Table 1:** threat model, admissibility and policy assumptions. **Table 2:** datasets/splits and label rights. **Table 3:** fair competing baselines. **Table 4:** metrics/CI/abstention. **Table 5:** external validity/limitations.

Proposed paper allocation: abstract 180–200 words; introduction and exact contributions 1.25 pages; formal problem and trust model 1.5; prior art 1; architecture and algorithm 2; experimental design and baselines 1.5; results/ablations 2; limitations/ethics 1; conclusion/reference material remainder, within IEEE's actual template and limit. **Page estimates are plans, not verified formatted pages**.

## 8. Prior-art challenges to cite explicitly (not novel by themselves)

1. Barry et al. (2025), [financial GraphRAG, ACL](https://aclanthology.org/2025.genaik-1.6/): financial graph + retrieval exists.
2. Han et al. (2025), [Temporal GraphRAG](https://arxiv.org/abs/2510.13590): time-aware graph retrieval exists (preprint; check version).
3. Ge et al. (2025), [CONFACT at IJCAI](https://ijcai.org/proceedings/2025/1073): conflicts and source credibility studied.
4. Zhang & Wu (2026), [Evidence Sufficiency Benchmark](https://doi.org/10.32604/cmc.2026.086343): five-level support/partial/irrelevant/missing/conflicting evidence and abstention already studied.
5. Shukla & Joshi (2025), [Proof-Carrying Answers at ACSAC workshops](https://doi.org/10.1109/acsacw69556.2025.00050): cryptographic evidence receipts / source admissibility exist.
6. Xie et al. (2025), [FIRE at NAACL](https://aclanthology.org/2025.findings-naacl.158/): iterative fact-checking with reduced costs exists.
7. [Selective Classification Under Distribution Shifts](https://pmc.ncbi.nlm.nih.gov/articles/PMC12470254/): risk–coverage and abstention under shift are established.
8. [CAP at JMLR 2025](https://www.jmlr.org/papers/v26/24-0452.html): adaptive selective predictions and coverage/error control prior art.
9. Bao et al. (2020), [SEC accounting fraud research](https://doi.org/10.1111/1475-679X.12292): accounting misstatements are a separate task.
10. Ma (2026), [knowledge-graph financial fraud](https://doi.org/10.1007/s44163-026-00977-y): graph-driven financial fraud is not new.

**Novelty risk:** The *combination* of known techniques is not automatically novel. A novel algorithm/contract, formal property not already in existing provenance literature, material incremental empirical benefit against competent baselines or valuable new reproducible benchmark is needed. Do not write "first" without a serious systematic search.

## 9. IMPORTANT PUBLIC PRIOR PREPRINT — MUST RECONCILE

The author's already-public SSRN working paper **"FraudRAG: Knowledge Graph-Augmented Retrieval for Real-Time Financial Statement Fraud Detection Using a Domain-Driven Medallion Architecture"**, posted **May 5, 2026**, revised **May 7, 2026**, public abstract https://papers.ssrn.com/sol3/papers.cfm?abstract_id=6714178 , currently contains claims that are **not supported** by the now verified research: "first" finance GraphRAG, `$5.38 trillion` supposedly bank/document fraud, Claude 3.5 Sonnet integrated calls, unverified fraud ring detection and legacy performance. **Immediate author task:** obtain preprint account/editor access and submit a corrected version, an erratum/revision note, or appropriate withdrawal/notice depending on SSRN procedures. Link to corrected results; never silently pretend that work did not exist.

Any new IEEE manuscript must explicitly disclose that prior public preprint, describe what is truly different, check rights/overlap policies, and avoid duplicate publication or recycling the invalid draft. Journal editor may need to be informed if a substantially overlapping version exists.

## 10. Kill criteria (do not submit to OJ-CS if triggered)

- No improvement over a fair deterministic certified-bitemporal verifier on the declared systems hypothesis; no alternative supported original contribution.
- Different retrieval methods see different source completeness or secretly receive future ground truth.
- Model/preprocessor gives labels, manipulation type, same-document original or hidden issuer record inaccessible to comparators.
- No independently useful experimental evidence beyond five correlated publisher-synthetic originals and four perfect exact-ledger cases per manipulation type.
- Stale/unauthenticated source treated as authoritative or claims derived from submitted document used to certify the submitted document.
- Historical fabricated charts, loss estimates, speed claims, or citations remain in final paper.
- SSRN overlap/unverified claims not corrected and disclosed; author human review, AI assistance disclosure, employer permissions and legal data rights not confirmed.
- Official IEEE template, figure files, references and final PDF not independently inspected.

## 11. Next work packages and tangible outputs

**WP1 — Formal method and reference implementation:** `benchmark/provenance_certificate_v4.py` with immutable evidence records, field-level and document-level statuses, machine-replayable source IDs; unit/property tests for I1–I8. This is **not yet implemented** by this blueprint.

**WP2 — Fair deterministic challenge:** compare V4 verifier against a fully featured deterministic completeness/temporal/contradiction competitor; state what, if anything, V4 adds.

**WP3 — Locked adversarial benchmark:** generate independently auditable synthetic out-of-distribution source groups, multiple issuer provenance families, bitemporal corrections, conflicts, hidden held-out variants, grouping manifests.

**WP4 — Contained evaluation:** implement non-LLM full grid first; freeze primary prediction; optional carefully budgeted LLM/Neo4j/Chroma experiments later.

**WP5 — Scientific audit:** independent annotators, sensitivity analysis, bibliographic and prior-SSRN overlap review.

**WP6 — IEEE package:** only after external/novelty gates pass, author-approved IEEE Open Journals 12-page max two-column editable source, final PDF, separate figures, clear AI-use disclosures and reproducibility links.

**Working decision:** The strongest path is a source-conditional method with machine-checkable reasons for abstention and **fair falsification by deterministic alternatives**. This could support a reputable article if meaningful new results emerge. It does **not** currently make the manuscript submission-ready.


## Execution update — V4 simulated adaptive acquisition actually run

The simulation and its **independent replay** now completed successfully.
Evidence: https://github.com/akshaysharma1088/fraudrag/actions/runs/40395485609 ;
per-case and metadata archive `research/verified_runs/fraudrag_v4_adaptive_20261026/` ;
detailed report `research/ADAPTIVE_V4_PRELIMINARY_FINDINGS.md`.

At budget **4 fictional price units**, finite-horizon deterministic DP
obtained full-source verification coverage **509/720 (70.69%)**
at average query cost **2.593**, versus **prior-aware deterministic
greedy** **495/720 (68.75%)**, cost **2.794**. Difference
in coverage **+1.94 percentage points** with paired 95% bootstrap
interval **[−0.14,+4.03]**, which includes zero. The mean cost
difference **−0.2011 fictional units** has 95% paired interval
**[−0.2294,−0.1731]**; this is not a real dollar saving.
Under the explicitly simulated source-availability shift, adaptive
coverage **35.00%** was fractionally BELOW greedy coverage **35.56%**,
with greater uncertainty and significantly worse absolute completion
than under ordinary simulation. **This directly falsifies an
unqualified stronger-acquisition-always-improves-coverage claim.**

The DP policy is itself deterministic and an established optimizer.
The experiment shows a cost/coverage trade-off in deliberately
fictional source outcomes, **not a new intelligent fraud-detection
method**. Claims of source signature authentication, bank-side
original authority, institution transfer, fraud-label validity,
actual Neo4j/Chroma/GPT or deployment efficiency remain untested.
Do not use the green workflow badge as paper novelty approval.

**Provisional component name** `FraudRAG-EAC` preserves the
already-cited original FraudRAG brand and SSRN DOI, without
claiming a trademark or separate reviewed publication.
