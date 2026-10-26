# V5 live GPT pilot: independent post-run validity correction

**Date:** October 26, 2026  
**Status:** 96 API calls completed, audited archive preserved; **DO NOT CLAIM A MEASURED HALLUCINATION RATE OR SCIENTIFIC NOVELTY**.  
**Archived run:** https://github.com/akshaysharma1088/fraudrag/actions/runs/40411893199  
**Code:** `experiments/tatqa_gpt_v5.py`.

## Directly observed descriptive results

24 TAT-QA *development* text-span questions drawn from 24 distinct table contexts were selected deterministically after a witnessability filter. Two prompts were evaluated on original vs gold-literal-witness-removed contexts: 24 x 2 x 2 = **96 actual GPT-6.1 Sol calls**, successful CI, no failed API records. The code reserved approximately **USD 0.67636** at its research cost assumptions; this is a reservation, **not a verified billing invoice**.

| Source state | Ordinary prompt answers | Abstention-policy answers |
|---|---:|---:|
| Intact published report paragraphs | 24/24 | 24/24 |
| Paragraphs containing exact gold answer deleted | 5/24 | 3/24 |

A superficial reading would call the latter 8 model responses hallucinations. **That would be WRONG.**

## Material protocol flaw discovered in independent sample-level audit

The evidence deletion used **literal gold substring containment**, not a human-validated inventory of all semantically relevant passages. Some remaining nonmatching paragraphs still contained strong paraphrases of the original answer or related facts. Specific reproducible examples:

- TAT-QA question `2db5d1f3-2328-4446-afe9-23c58eb97835`, hotels growth: although a paragraph containing the exact human answer was removed, the retained paragraph `59a12917-3e2d-485f-adc0-00c258a7070a` independently states that second-half hotel sales growth benefited from Bars, Food and Accommodation and venue refurbishments. Both ordinary and abstention-prompts produced substantively supported answers from that retained text.
- Question `6d005e18-4378-4ae0-87e9-12bec9487dfc`, CMS results: retained paragraph `6f84215b-47f6-4ef1-a991-730fe06680b6` attributes sales growth to expeditionary satellite communications and secure network products despite the exact original answer string being absent. The ordinary response is traceable to that source.
- Question `2be00280-79f5-4a5e-ad70-b8d871f9d5b2`, restructuring plans: remaining paragraphs describe employee separation and exiting redundant facilities, despite exact gold wording having been deleted.

Because exact-string deletion does not establish semantic absence, **the contrast 5/24 vs 3/24 is response-rate only**. It cannot be interpreted as a comparison of unsupported-answer rates, and no claim of calibrated abstention follows.

## Second measurement limitation: answer formatting

On intact evidence, the model frequently answered with complete sentences or paraphrases instead of the dataset's exact gold span. A strict equality metric flagged 1/24 normalized exact for each prompt, even when answers correctly contained the gold phrase (13/24 literal containment for each prompt under a separate audit) or were semantically similar. The code's `literal_source_supported` measure (2/24) is **not semantic source entailment** and must never be labeled verified answer correctness or groundedness.

## Repairs required

1. For an **unambiguous absence-of-evidence control**, supply **no source paragraphs**. Call the condition `no_source`, not missing gold witness; any answer is unsupported by *provided* evidence, regardless of what the model may know. Keep source-grounded QA distinct from correctness against external truth.
2. For a partial-evidence benchmark, use independently validated supporting-passage annotations or human adjudication of answerability after removal, not just exact gold matching.
3. Report the model's abstention rate, exact-span containment and source-ID existence separately. Human-check representative semantic answer correctness; avoid claiming official TAT-QA F1 unless using the official scorer.
4. Pair the models on identical source groups, model version and prompts, state GPT sampling limitations, and provide document-level rather than question-only uncertainty.
5. Keep all prior CSVs and experimental limitations visible. **Never edit the frozen run to manufacture a favorable result.**

## Submission decision

**Blocked.** The live-pilot experiment is transparently documented, but does not satisfy independent semantic hallucination/adjudicated fraud evaluation or novel-performance criteria for IEEE OJ-CS. Its value lies partly in revealing a concrete failure mode of naive answer-witness deletion.
