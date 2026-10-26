# FraudRAG V6 independently checked zero-source GPT control

**Completed:** 2026-10-26 | **Status:** empirical pilot complete; journal submission still blocked  
**GitHub Actions:** https://github.com/akshaysharma1088/fraudrag/actions/runs/40412854350  
**Source code:** `experiments/tatqa_no_source_v6.py`; workflow `.github/workflows/tatqa-no-source-v6.yml`  
**Archive:** `tatqa-v6-no-source-gpt-independent-control` (protocol, metrics, every model prediction).

## Why this correction was necessary

The previous V5 GPT run (https://github.com/akshaysharma1088/fraudrag/actions/runs/40411893199) removed paragraphs containing the **literal** gold answer from published TAT-QA financial-report excerpts. Manual independent inspection demonstrated that remaining paragraphs still contained *semantic evidence* for some answers. Therefore its ordinary-prompt 5/24 versus explicit-abstention 3/24 returned answers cannot be called hallucinations or unsupported answers. Exact-string scoring also incorrectly penalizes many paraphrases; the V5 GPT evaluation is exploratory and **cannot support a claim of improved grounding or superiority**.

To make the evidence-availability intervention unambiguous, V6 used the SAME 24 selected TAT-QA development questions and gave GPT an empty `sources=[]` list. True answers were excluded from model input. This tests abstention with *no supplied supporting sources*, not a claim about what the pretrained model knows.

## Independently checked results

| Condition | Ordinary instruction | Explicit abstention instruction |
|---|---:|---:|
| Unique questions | 24 | 24 |
| Real GPT-6.1 Sol calls | 24 | 24 |
| Model answers despite no supplied sources | **0/24** | **0/24** |
| Abstentions | **24/24** | **24/24** |
| Nonexistent source IDs cited | 0 | 0 |

All 48 predictions have no `error` entry; V5 and V6 case-ID sets match. Source dev-file SHA-256 `8da095a819af6db3c14877c6df2d4d29960e41d1a63dd1fa853507bd2a616af5`, verified against pinned Git blob `48075c812af3fe6698b1d5cb50d9dbf358d52784`. The workflow records USD **0.254316 reserved** under study price assumptions; this is not a confirmed bank charge or OpenAI invoice.

**Interpretation:** The ordinary prompt already declined to answer every no-source case, so there is *no measured abstention improvement* attributable to the stronger instruction in this experiment. No bank documents, independently adjudicated fraud, issuer attestation, model-vs-equally-informed-detector superiority, or publication-quality novelty were demonstrated. A small sample of 24 context-distinct questions, selected after a witnessability filter on a public development dataset, cannot establish cross-institution safety or generalization.

## Research and journal gate

The evidence ledger now contains:
- V2: 28 synthetic documents, full constructed ledger: non-LLM exact-match F1=1.0 equals graph-GPT F1=1.0.
- V3: 20 controlled text edits from five outside-published **synthetic** PDFs: 60 GPT calls, exact complete original source is an oracle.
- V4: 720 fictional held-out simulated source-acquisition profiles; the primary budget-four DP-vs-strong-greedy coverage confidence interval crosses zero.
- V5 deterministic: 329 **gold candidate supplied** questions over 187 published TAT-QA contexts under synthetic source-condition interventions.
- V5 GPT: 96 actual calls; gold-literal-witness deletion does not guarantee semantic absence; no valid unsupported-answer rate available.
- V6 GPT: 48 actual calls; both policies abstain 24/24 with no sources.

Still outstanding: genuinely new, demonstrably original approach under fair baselines; independent held-out source-report/institution generalization; rigorous semantic correctness adjudication; real adjudicated bank-document evidence **if fraud detection is claimed**; correct official IEEE Open Journals template; full ethics/IP/AI/prior-preprint disclosures and author review. Do not submit to OJ-CS yet.
