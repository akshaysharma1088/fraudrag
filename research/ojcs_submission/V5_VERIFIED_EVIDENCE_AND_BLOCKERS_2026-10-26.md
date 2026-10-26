# FraudRAG OJ-CS evidence freeze — external V5 and V4 secondary audits

**Date:** October 26, 2026  
**State:** external deterministic controlled study completed and archived; **NOT CLEARED TO SUBMIT**.  
**Code branch:** `research/reproducibility-hardening-2026-10`; main remains unchanged.

## Newly executed experiments

### V5 — licensed, authentic-financial-report-context witness stress test

- **Independently published source:** Zhu et al., TAT-QA, ACL 2021, DOI [10.18653/v1/2021.acl-long.254](https://doi.org/10.18653/v1/2021.acl-long.254), dataset **CC BY 4.0**; upstream commit `870accc41953dcde885aabeb963d94aabdc0fbc3`, dev Git blob `48075c812af3fe6698b1d5cb50d9dbf358d52784`. Download checked by Git blob SHA-1 before analysis.
- **Successful GitHub execution and archived raw predictions:** [run 40410841687](https://github.com/akshaysharma1088/fraudrag/actions/runs/40410841687), artifact `v5-pinned-tatqa-financial-source-evidence-report`.
- **Observed sample:** 329 eligible text-span gold-answer questions from 187 distinct table contexts; selected by answer-type, answer-from and literal gold witness existence; **not a random or independent company/report-level sample**.
- **Methodology:** verify whether a **supplied human-gold answer candidate** can be supported by source text, compare raw literal matching, release-integrity filtering, temporal filtering and combined conflict-aware filtering. Six conditions per candidate: intact, witness removed, untrusted copied excerpt, future-observed excerpt, *constructed* conflicting assertion, and modified incorrect candidate. All methods see the same sources and metadata.
- **Observed control checks (329 instances per condition):** in the untrusted-replay condition, raw literal matcher supported 329/329 despite the only matching copy being untrusted, while release-integrity and later stricter checks supported 0/329. In the synthetic late-record condition, raw literal and provenance-only controls supported 329/329, while temporal/combined controls supported 0/329. The combined contract passed all required controlled intervention checks.
- **Most important interpretation:** These outcomes are largely *designed into the verification policy*. They demonstrate correct execution of explicit source/time/contradiction invariants, **NOT learned accuracy, automatic QA success, independent source authenticity, a novel superior algorithm, real bank forgery sensitivity, fraud accuracy, or GPT/GraphRAG effectiveness**. All artificial source metadata are simulations, and the gold-answer candidate is provided to each method.
- **Cluster uncertainty:** the script archives seeded bootstrap resampling by table-context group, **not by issuing institution/report**. Its intervals cannot establish cross-institution generalization.

### V4 — independent paired deterministic-policy reanalysis

- Independent tests and code: `benchmark/v4_paired_sensitivity.py`, `tests/test_v4_paired_sensitivity.py`.
- Successful GitHub Actions run: [40410179908](https://github.com/akshaysharma1088/fraudrag/actions/runs/40410179908). Based on frozen **fictional** source-mask traces only. The tests add exact paired-discordance sensitivity, not a newly run acquisition experiment.
- Test (720 simulated groups) coverage for DP versus prior-aware greedy:
  - Budget 3 hypothetical units: 54.03% vs 51.53% (+2.50 pp).
  - Budget 4: 70.69% vs 68.75% (+1.94 pp), pre-existing paired coverage bootstrap 95% CI [−0.14,+4.03] pp.
  - Budget 5: 78.19% vs 71.25% (+6.94 pp); exploratory across-budget contrast.
- At budget 4 under simulated shift (360 groups), DP 35.00% versus prior-aware greedy 35.56%, and neither method generalizes conclusively beyond the six source-profile families.
- **Strict limitation:** All price units, issuer references, source distributions and attestation flags are invented. DP is an existing classical optimizer. No real bank payments or query latency are measured. Budget and split multiplicity prevent interpreting posthoc unadjusted p-values as confirmatory novelty evidence.

## What is still mandatory for an original journal result

1. **Independent end-to-end test**, with answers generated without using gold candidates in inference; compare LLM with or without source and evidence-contract gating, at matched answered-question coverage. The V5 gold candidate witness test **does not satisfy** this.
2. **A meaningful distinct contribution over a complete deterministic policy** given precisely the same raw provenance, temporal fields, source availability and costs. Component conjunction alone is not original.
3. **Independent report/institution held-out evaluation**, or explicit limitations if only available public QA context groups; disclose possible training contamination.
4. **Real adjudicated bank-document fraud labels if and only if claiming authentic bank-forgery detection**. Public company report QA cannot establish this.
5. **Reviewer-ready paper in the actual IEEE Open Journals template**, source-generated figures/tables, broader cited literature, author employer/IP/ethics/overlap/AI signoff.
6. **Correct earlier SSRN preprint DOI [10.2139/ssrn.6714178](https://doi.org/10.2139/ssrn.6714178)** by the author's account; preserve its publication history and accurately disclose overlap.

## Publication decision

A methodological/negative-comparison paper can present these results transparently, but a competitive IEEE OJ-CS submission still requires independently convincing novelty and external validation. **Do not mark the research as accepted, journal-submission-ready, independently bank-adjudicated, or proven more accurate than deterministic reconciliation.** No SSRN correction, bank consent, publisher submission, independent third-party review, or author approval has been performed by these CI jobs.
