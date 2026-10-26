# V7B verified complete external public-test paired QA experiment

**Date:** October 26, 2026  
**Result archive:** https://github.com/akshaysharma1088/fraudrag/actions/runs/40418080549  
**Status:** completed and strictly audited, 128 paid model calls, no failed/partial records. **NOT A BANK-FRAUD STUDY.**

## Design / preregistered conditions

- TAT-QA public TEST **gold** release was pinned to original upstream commit `870accc41953dcde885aabeb963d94aabdc0fbc3`, test Git blob `3d5d3b691af572646ba9b1ac4d8f78c5dca09732` and SHA-256 `c4d08418359c1d76468dec420ee748a37f48c06b63cb8ec2766f19d5d314b597`. Source license CC BY 4.0, cite Zhu et al., ACL 2021.
- 64 distinct public test table contexts, excluded 278 development contexts by table UID. One eligible human question per table selected deterministically using hashed IDs, requiring `answer_from=text`, `answer_type=span`, and a single gold answer string. **Gold answer values were not used to choose examples or passed to GPT.**
- Two model instructions: ordinary source-using GPT and evidence-cautious GPT; all other provided source paragraphs and exact question contexts matched pairwise. GPT-6.1 Sol, 650 maximum output tokens, 64 x 2 = 128 actual calls.
- The earlier V7 run [40417464827](https://github.com/akshaysharma1088/fraudrag/actions/runs/40417464827) stopped at 81/128 due to model output exhaustion under the originally lower 250-token cap. Its raw predictions and failure were **preserved**, not treated as a completed result. V7B is a whole-study rerun, not selective filling or exclusion.
- Both conditions used real report excerpts from **published financial-report question answering**, with no live bank documents or forgery labels. This public benchmark may have been encountered during model training.

## Verified results and independently recomputed paired sensitivity

| Metric, n=64 for each mode | Ordinary GPT | Evidence-cautious GPT |
| --- | ---: | ---: |
| Responded with an answer | 64/64 | 64/64 |
| Normalized exact string agreement | 0/64 | 1/64 |
| **Approximate** normalized token-overlap F1 (mean) | **0.518358** | **0.533526** |
| Response uses only IDs from provided passages | 64/64 | 64/64 |
| Generated answer has literal normalized substring inside cited passage | 6/64 | 6/64 |
| Model execution errors | 0 | 0 |

The evidence-cautious minus ordinary per-context token-overlap F1 difference is **+0.015169**, with 5,000-resample paired table-context bootstrap 95% interval **[−0.003970, +0.038431]**. This interval includes zero, and the study was not powered to prove a modest gain.

**Critical distinction:** Matching citation IDs does not establish semantic support. Literal whole-answer containment is overly strict when an answer is a paraphrase; 6/64 should **NOT** be interpreted as only six genuinely supported answers. Normalized token overlap is a rough similarity proxy and is **not** the official TAT-QA benchmark F1 or independent human evaluation. These comparisons do not support fraud-detection superiority, independent source authentication or a new RAG algorithm.

## Scope and open gates

The public TEST contexts are group-disjoint from the DEV table contexts but **not verified issuer/institution-disjoint**. Dataset-release labels are human gold for financial QA, **not adjudicated forged bank statements**. Both prompts answered every case, so the experiment cannot test differential abstention at matched decision coverage; the separate V6 true no-source condition tests 24 paired abstentions. Meaningful novel value over a strong equally informed deterministic source/reconciliation method remains unsupported. The IEEE OJ-CS scientific submission gate remains **NOT CLEARED** pending independent originality review, actual journal template verification, author/ethics and SSRN corrections, and any additional domain-specific external tests needed for the chosen claims.
