# Publication evidence and scope — October 26, 2026

This directory documents **what can and cannot be claimed** about FraudRAG in the public repository. It is intentionally small and safe to merge into `main`: documentation only, **no backend changes, no secrets, no dependency upgrades, no paid API calls or new CI workflows**.

The executable experiments and immutable raw predictions live on `research/reproducibility-hardening-2026-10`, tracked in [draft research PR #1](https://github.com/akshaysharma1088/fraudrag/pull/1). That research branch remains unmerged pending substantive code/security and scientific review. Files in this documentation release are a citation map, *not a substitute for raw data*.

## Audited research at a glance

| Study | Provenance | Supported observation |
|---|---|---|
| V2: synthetic complete-reference reconciliation | [Integrated GPT run](https://github.com/akshaysharma1088/fraudrag/actions/runs/40366638447); [independent audit](https://github.com/akshaysharma1088/fraudrag/actions/runs/40368862175) | 28 fictional statement cases. GPT with ledger/graph evidence F1=1.000 **ties** same-information deterministic exact-ledger F1=1.000. |
| V3: synthetic PDF-derived text edits | [External-publisher synthetic PDF audit](https://github.com/akshaysharma1088/fraudrag/actions/runs/40372704350) | 20 edited/unaltered text cases from five synthetic originals, 60 GPT calls. Complete originals permit text comparison; other source states lead to abstention. Not real forgery adjudication. |
| V4: simulated evidence acquisition | [Verified frozen runs](https://github.com/akshaysharma1088/fraudrag/tree/research/reproducibility-hardening-2026-10/research/verified_runs/fraudrag_v4_adaptive_20261026); [paired secondary sensitivity](https://github.com/akshaysharma1088/fraudrag/actions/runs/40410179908) | 720 simulated test groups. At budget four artificial units DP 70.69% coverage vs strong prior-aware greedy 68.75%; 95% paired coverage interval includes zero. Not an independent real-bank cost result. |
| V5: externally sourced financial-report excerpt intervention | [Pinned-data experiment](https://github.com/akshaysharma1088/fraudrag/actions/runs/40410841687) | 329 gold-candidate single-span text questions over 187 TAT-QA source contexts. Deterministic source-integrity/temporal filters enforce constructed interventions. Gold answer **supplied** to these matching methods. |
| V5 GPT partial source (methodological warning) | [Pilot run](https://github.com/akshaysharma1088/fraudrag/actions/runs/40411893199); [critical audit](https://github.com/akshaysharma1088/fraudrag/blob/research/reproducibility-hardening-2026-10/research/ojcs_submission/V5_GPT_PILOT_CRITICAL_AUDIT_2026-10-26.md) | 96 API calls. Exact-string witness deletion left some semantically relevant passages: the difference in output rates is **not** a verified hallucination contrast. |
| V6: zero-source GPT control | [Complete 48-call run](https://github.com/akshaysharma1088/fraudrag/actions/runs/40412854350) | Both ordinary and evidence-cautious prompts abstained in all 24 paired no-evidence questions. No evidence of a difference between prompts in this control. |
| V7B: complete public financial QA test | [128-call run](https://github.com/akshaysharma1088/fraudrag/actions/runs/40418080549); [separately pinned test source](https://github.com/akshaysharma1088/fraudrag/actions/runs/40419378389) | 64 different TAT-QA public TEST table contexts; gold withheld from model inputs. Two prompting modes each answered 64/64. Approximate normalized token-overlap F1 0.518 vs 0.534; paired difference CI includes zero. Source-ID validity does not prove semantic entailment. |

The first V7 public test attempt stopped before all 128 paired calls due to output token exhaustion. The completed V7B repetition used a uniform larger output allowance and **did not delete** the earlier incomplete archive.

## Intended research contribution, bounded

This work examines whether financial-document claims should be supported, contradicted, or deferred according to **independently attested, complete, temporally admissible reference evidence**. The conditional verification prototype checks rule consistency *given* source-trust metadata. Neither issuer authenticity nor reference completeness is established cryptographically in this study.

The integrated retrieval setup's observed tie against full-information deterministic matching means **no measured incremental financial-fraud classification accuracy attributable to GPT/GraphRAG** has been demonstrated. Classical dynamic programming is not novel simply because its plan is adaptive. Combining prior-art components is not itself proof of scientific novelty.

The TAT-QA source contains excerpts from **real published corporate financial reports**; it is financial question answering, **not a source of adjudicated genuine/forged retail bank statements**. Its public test release is a known benchmark and possible model-training-contamination risk, and table-context isolation is not proof of isolation by issuing institution.

## Literature and upstream attribution

- Zhu et al. (ACL 2021), *TAT-QA: A Question Answering Benchmark on a Hybrid of Tabular and Textual Content in Finance*, DOI [10.18653/v1/2021.acl-long.254](https://doi.org/10.18653/v1/2021.acl-long.254); [dataset](https://github.com/NExTplusplus/TAT-QA), CC BY 4.0, pinned release commit `870accc41953dcde885aabeb963d94aabdc0fbc3`. The experiment code records the exact dev/test Git object IDs and validates original bytes.
- [Finance GraphRAG prior art](https://aclanthology.org/2025.genaik-1.6/) and [FinGEAR retrieval prior art](https://aclanthology.org/2025.findings-emnlp.382/) mean the repo must not claim to invent finance GraphRAG.
- Original FraudRAG [SSRN preprint DOI 10.2139/ssrn.6714178](https://doi.org/10.2139/ssrn.6714178): bibliographic history and existing citations should be preserved while the author corrects unsupported historical performance/novelty language.

## Publication disposition

A seven-page IEEE Open Journals class-format author-review manuscript and editable Word version were assembled on October 26, 2026 **outside the GitHub repo**. An IEEE-style class file and a visually inspected PDF are not a journal submission or editorial endorsement. Those binary manuscript artifacts are intentionally distributed to the author through the ChatGPT conversation and **are not hosted in this PR**.

**Scientific and submission gates remain open:** independent novelty/external-validity review, semantic answer/citation adjudication, employer IP/data use and conflict signoff, exact IEEE template verification, author affiliation/ORCID and AI disclosure approval, SSRN prior-overlap handling, and explicit author approval. See [publication checklist](SUBMISSION_GATE.md).

The user should not merge the full research PR, treat current code as security-vetted production software, claim real fraud sensitivity, or submit an unapproved manuscript as a final journal article.
