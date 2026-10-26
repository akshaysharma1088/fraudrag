# IEEE Open Journal of the Computer Society (OJ-CS): FraudRAG Submission Gap Audit

**Checked:** 2026-10-26  
**Scope:** Current draft research PR #1, the validated six-page working DOCX, the larger archival DOCX, executed GitHub Actions and primary IEEE journal instructions.  
**Current verdict:** **DO NOT SUBMIT YET**. Engineering reproducibility is encouraging; final paper and scientific contribution are not cleared.

## Journal requirements (primary sources)

- Official OJ-CS call: https://www.computer.org/digital-library/journals/oj/cfp-open-journal
- IEEE Computer Society author instructions: https://www.computer.org/publications/author-resources
- IEEE OJ-CS expedited schedule: https://www.computer.org/publications/peer-review-schedules
- IEEE author use-of-AI disclosure policy: https://journals.ieeeauthorcenter.ieee.org/become-an-ieee-journal-author/publishing-ethics/guidelines-and-policies/submission-and-peer-review-policies/

OJ-CS requires the **IEEE Open Journals Word or LaTeX template**, a maximum **12 double-column pages**, separately uploaded figure assets (supported vector/raster formats) and original technically complete results. IEEE Computer Society specifies **100–200 words** for regular journal abstracts, and strongly expects figures/tables near their initial mention. The rapid-review scheme has **no formal revision option**, so a manuscript needing a new major experiment should not be sent speculatively. Artificial intelligence-generated text, code and figure content must be disclosed in acknowledgments with the tool and affected sections; editing-only usage is treated differently.

## Artifact inspection

| Artifact | Observed on 2026-10-26 | Readiness |
|---|---|---|
| `FraudRAG_Evidence_Grounded_Research_Draft_2026-10-26.docx` (working container copy) | Six rendered US-letter single-column pages, 68 paragraphs, 2 tables, **zero embedded figures**, 8 selected references; abstract **187 words**; explicitly calls itself unapproved review draft | **Not IEEE template**. Abstract word count fits the 100–200-word requirement |
| `FraudRAG_Manuscript.docx` (working container archival copy) | 1.2 MB, 8 images, 4 tables; abstract includes unsupported **$5.38T losses**, **first financial Graph-RAG**, unverified Claude model and novel fraud ring performance | **Unsafe to submit**. Do not copy images, numbers or references into final paper without proof |
| `docs/FraudRAG_VERIFIED_WORKING_DRAFT.md` | 28k-character substantial working draft with actual experiments and caveats; section 7 still contains earlier temporal language implying the already completed GPT audits remain undone | Reconcile all sections and claim sources before regenerating a new Word/LaTeX paper |
| `docs/FraudRAG_IEEE_Paper*.docx` in repo | Unverified archival drafts, historically blocked by manuscript claims preflight | No publication use without source-by-source correction |
| Research PR #1 | Draft, main untouched. Latest reviewed HEAD `6de5ebd301dcecc86c05dd1e851a567c8586d998`. 102 files changed. Recent general CI **passed** (run `40390921004`); source evidence and anti-leakage controls passed | Engineering and evidence archives are substantial, but CI ≠ peer review |

## Scientific decision

**Completed and reproducible:** 840 source-generated synthetic cases, 28 customer-disjoint primary test statements, 112 paid calls in original serial-context pilot, **112 actually integrated Neo4j/Chroma/GPT calls** archived with independent audits, 4,900 multi-seed fictional cases with 525 deterministic held-outs, five publisher-synthetic PDFs generating 20 text perturbation cases, and **60 additional GPT calls** for three source-access conditions. Real SEC AAER data have a separately reported **issuer accounting misstatement** task, not document forgery.

**Key non-novelty result:** a **complete synthetic bank-side ledger oracle** yields F1=1.0 both for exact non-LLM matching and GPT with graph/ledger evidence; combined Graph-RAG does not demonstrate added fraud-detection benefit over the equally informed deterministic comparator. On five publisher-synthetic original PDFs, the complete original text also yields trivial perfect text change detection. No independent real bank fraud labels or adjudicated forged PDF pairs are present. No production inference or broad institution shift is established.

**What this means for scope:** A real bank-document fraud-detection performance paper is **not substantiated**. An honest negative-result/reproducible benchmarking paper may be possible *in principle*, but OJ-CS asks for high-impact original computer science work; the current study must articulate and empirically test a distinctive, useful contribution that cannot be explained simply by supplying a complete reference oracle. Do not fabricate superior results or make real-world generalization claims.

## Mandatory actions before author uploads an OJ-CS manuscript

- [ ] **Commit a frozen citation-to-result map:** each manuscript table/figure generated from immutable raw predictions; reconcile duplicated pilot/integrated studies and correct stale status lines.
- [ ] **Choose one actual contribution and experimentally challenge it:** e.g., formally specified selective verification, time-valid provenance or source-conflict detection under incomplete and contradictory independently sourced records, compared with strong deterministic baselines that receive identical evidence.
- [ ] **Improve generalization evaluation:** source-group/institution-disjoint cases and realistic errors, calibration/abstention/error rates, confidence intervals, data provenance, false-positive impacts; release a dataset or documented access process that supports the claims.
- [ ] **Avoid unsupported real-fraud labels:** real bank fraud effectiveness requires legally usable independently adjudicated genuine/forged documents. Related signature forgery/AAER/receipt data are separate tasks.
- [ ] **Retire unsupported legacy media:** no old F1=.883 / AUC=.943 / petabyte-scale, unsupported original Graph-RAG novelty, $5.38T banking-loss extrapolation, or fabricated chart results.
- [ ] **Rebuild the OJ-CS paper in official IEEE Open Journals two-column template**; no more than 12 pages including references/author information, final read-only PDF and editable DOCX/LaTeX.
- [ ] **Build and upload final stand-alone figure files:** accurate system boundaries, temporal data flow and results/uncertainty/abstention plots sourced from actual reproducible runs. No unsupported visualized score gains.
- [ ] **Bibliographic review:** verify all primary papers cited and map claims to source; eight selected references in the short working document are not proof of sufficient related-work coverage. No formal IEEE eight-reference limit is implied.
- [ ] **IEEE disclosures:** complete title/author/affiliation, abstract, index terms, source/data and code availability, ethics/licensing, funding/conflict and IEEE AI acknowledgments identifying substantive GPT code/writing help; independently human review the content.
- [ ] **Publication ethics:** determine prior overlap/submissions and employer or other IP and data rights, select target journal and author-approved final files. Do not concurrently submit same manuscript elsewhere.
- [ ] **External technical review:** obtain qualified third-party methodologist and subject-matter assessment; resolve major novelty/external-validity critiques **before** OJ-CS (expedited schedule without revisions).

## Current decision and preservation

**Decision: Not technically/paper-scientifically ready for OJ-CS.** Preserve all archived experimental predictions, successful runs, unsupported-citation counts and failures. Do not move current draft PR to `main` or upload any paper to OJ-CS automatically. Human author retains final editorial control.

**Live code/safety evidence:**
- https://github.com/akshaysharma1088/fraudrag/actions/runs/40390921004 (general CI success)
- https://github.com/akshaysharma1088/fraudrag/actions/runs/40375765482 (readiness gate correctly blocks)
- https://github.com/akshaysharma1088/fraudrag/actions/runs/40372704350 (v3 GPT independent audit)
- https://github.com/akshaysharma1088/fraudrag/actions/runs/40368862175 (integrated GPT independent audit)
