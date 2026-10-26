# FraudRAG scholarly release and submission gate

**Current determination: AUTHOR-REVIEW MANUSCRIPT; NOT SCIENTIFICALLY CLEARED FOR IEEE OJ-CS SUBMISSION.**

This is a **human-author decision checklist**, not a signal that GitHub Actions or ChatGPT can certify journal acceptance. Results in the project README and [evidence ledger](README.md) should retain their exact benchmark/task limitations.

## Merge scope of this documentation PR

- [x] Replace misleading main-branch README "production-grade" and unverified AUC/F1/latency language with research-prototype scope.
- [x] Remove unsupported "submitted to IEEE TKDE"/accepted IEEE publication and fake BibTeX journal designation from the public project README.
- [x] Link to existing raw experiments and provenance rather than copy unreleased proprietary data.
- [x] Preserve both favorable, tied, inconclusive, and flawed pilot results transparently.
- [x] Keep backend changes, model workflows, tokens, raw financial data, and all 176-file research PR content **out of this PR**.
- [ ] Reviewer verifies this small diff and main's documentation CI completes.
- [ ] Maintainer expressly approves this small docs-only merge.

## Pre-journal review — not yet complete

- [ ] Independent scientific reviewer tests whether the comparative/negative finding constitutes sufficient original computer-science contribution for OJ-CS, given fair deterministic baselines and already-published GraphRAG work.
- [ ] Human semantic review of GPT answers, citation entailment, and dataset/task applicability. Normalized token-overlap F1 cannot substitute for this.
- [ ] Independently adjudicated real-bank statement records, issuer authenticity and ethics consent **only if** the paper will assert real-world bank-document forgery detection; current manuscript must **not** assert that claim.
- [ ] Confirm genuine institution-/source-issuer-separated external validity. Current TAT-QA isolation is by table context and public development/test files only.
- [ ] Confirm authors, ORCID, institution/affiliation, funding, employer intellectual property and disclosures.
- [ ] Correct the author-owned SSRN preprint DOI `10.2139/ssrn.6714178` or submit a transparent revision, accurately disclose overlap to the intended journal, preserve original DOI/citations.
- [ ] Verify latest officially provided IEEE Open Journals author template and final word count/figures/references. A pinned public mirror class is not proof of current publisher endorsement.
- [ ] Confirm third-party data and figure licenses and acknowledge TAT-QA CC BY 4.0 source/public benchmark contamination caveat.
- [ ] Author inspect every assertion against raw per-sample predictions and approve AI-assisted-content description under actual journal rules.
- [ ] Obtain final explicit author permission to submit the checked files via the journal portal.

## Scientific outcome protection

**Must stay visible:** V2 complete-reference GPT vs exact-ledger F1 tie; V4 ordinary-budget paired coverage uncertainty includes zero; V5 pilot semantic evidence deletion flaw; V6 no-source both approaches abstain; V7B GPT F1 difference CI crosses zero; no bank-forgery ground truth or cryptographically verified reference attestation. A successful workflow means execution and archiving, **not** technical superiority, fraud adjudication, or statistical significance.

If novelty remains unpersuasive after independent review, revise the paper's claims or select an appropriately scoped experimental methodology/research software venue. Do not remove strong baselines to improve presentation.
