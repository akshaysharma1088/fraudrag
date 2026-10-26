# FraudRAG-EAC — pilot evaluation of adaptive evidence acquisition
**Exploratory report** · October 26, 2026 · NOT independently adjudicated bank fraud
**Software module name:** FraudRAG Evidence Acquisition Controller (**FraudRAG-EAC**), provisional research name only. Product/repo may remain `FraudRAG`; no trademark-clearance assertion is implied.

## Research question

Can a *deterministic*, source-availability-calibrated, adaptive querying
policy obtain complete attested **synthetic** issuer-field evidence for
fictional financial statements more cost-efficiently than other
**equally informed deterministic policies**?

The principal planning method is a classical finite-horizon Bellman
dynamic program that maximizes success of obtaining complete field
coverage minus a fixed cost penalty. **This is not a new algorithm by
itself.** It competes with fixed order, naive greedy and a strong
**training-prior-aware** greedy baseline. No language model was used,
and no source retrieval ran through actual bank APIs or charged fees.

## Executed source and replay provenance

- Trial workflow: https://github.com/akshaysharma1088/fraudrag/actions/runs/40395485609 .
- The experiment and independent source-response replay both **passed**.
- Permanent frozen source records, predictions, and audit:
  `research/verified_runs/fraudrag_v4_adaptive_20261026/`.
- `benchmark/adaptive_acquisition_v4.py`,
  `benchmark/audit_adaptive_v4.py`,
  `tests/test_adaptive_acquisition_v4.py`,
  `tests/test_audit_adaptive_v4.py`.
- 1,080 fictional **train-calibration cases**; 720 **test** cases,
  360 **synthetically distribution-shifted** cases. Cases and
  fictional original-account IDs are distinct across train/test/shift.
  All three sets share only six **simulated source-availability profile
  families**; this is **not** an institution-held-out test.
- Five simulated evidence sources per case: three single-field sources
  plus two bundle sources, with differing fictional cost and availability.
  Every policy sees the *same* source action metadata, costs and
  train-estimated outcome probabilities before choosing a source. Real
  coverage masks are disclosed only after query. Budgets are 3, 4 and 5
  **synthetic price units, not dollars**.
- At the end of each acquisition policy, exactly the same deterministic
  conditional-evidence contract assesses original/edited **fictional**
  fields, with full required three-claim coverage before any conclusive
  decision. No independent source signatures or real bank issuer
  authentication were performed. All future factual fields were
  generated within a fictional simulator.

## Main quantitative comparison — budget = 4 invented cost units

| Policy | Test certificate coverage (n=720) | Avg. source-access cost / test case | Avg. cost / completed case | Shift coverage (n=360) | Shift average cost |
|---|---:|---:|---:|---:|---:|
| Fixed order (deterministic) | 382/720 = 53.06% | 2.751 | 5.186 | 68/360 = 18.89% | 3.033 |
| Naive cost-aware greedy (deterministic) | 382/720 = 53.06% | 2.751 | 5.186 | 68/360 = 18.89% | 3.033 |
| **Prior-aware greedy (deterministic fair baseline)** | **495/720 = 68.75%** | **2.794** | **4.064** | **128/360 = 35.56%** | **3.006** |
| **Full-lookahead adaptive DP (also deterministic)** | **509/720 = 70.69%** | **2.593** | **3.668** | **126/360 = 35.00%** | **2.513** |

On the ordinary held-out test, adaptive DP versus prior-aware greedy:
- Difference in coverage **+1.94 percentage points**, paired
  1,500-resample percentile bootstrap **95% interval
  [−0.14, +4.03] percentage points**. **This does not establish
  statistically persuasive coverage improvement**.
- Difference in average simulated access cost **−0.2011 units per case**,
  paired bootstrap interval **[−0.2294, −0.1731]**. Roughly **7.2%
  lower mean source-access cost** at *nearly* (but not provably
  identically) matched case decision coverage.
- Cost per completed case 3.668 versus 4.064 invented units.
- No policy had a false clearance **against its own exactly generated
  fictional issuer truth**, expected from the perfect, internally
  consistent synthetic source generation.

On the shifted cases, the adaptive controller's coverage was
**35.0%**, versus prior-aware greedy **35.56%**: the coverage
difference was **−0.56 percentage points** with paired 95% interval
**[−2.50,+1.39]**. DP used **0.4922 fewer units** per case
([−0.5444,−0.4400]), but the success rate dropped substantially
under the simulated shift for *both* methods. Do not imply the method
remained calibrated under deployment shift.

The archives include results at all three budgets (3/4/5), *every*
query sequence, action cost, source response mask, source group ID,
simulated issuer value and comparison status. The independent replay
checks all **8,640** ordinary-case and **4,320** shift-case
policy/budget paths, verifies each charge and acquired mask, and
rejects group leakage, budget overrun or unsupported source
certification.

## Strongest reviewer objections / what this experiment does NOT prove

1. **All evaluated planners are deterministic.** The DP policy is an
   established mathematical optimization technique; it cannot be
   advertised as novel just for being adaptive.
2. The source availability probabilities, costs and evidence contents
   are generated by our own simulator. We trained a predictive prior
   on cases from the **same six profile families** that generate the
   nominal held-out cases. A shift stress check partially addresses
   this but does not validate external institutions.
3. All references are programmatically complete if found,
   and their *issuer-attested* flag is assumed, not validated by
   cryptographic signatures or bank contracts. This is a study of
   **evidence acquisition cost under coverage uncertainty**, not a
   demonstration of real issuer authenticity or bank fraud detection.
4. No GPT, Neo4j, ChromaDB, documents, PDF parsing, optical character
   recognition, bank integrations or financial wrongdoing labels are
   evaluated **in this pilot**. Existing V2/V3 studies are separate.
5. The before/after outcome source masks are correlated through
   the synthetic scenario profile. The Bellman planner uses
   independent action-outcome probability models from training;
   misspecification may deteriorate results under real network and
   source-availability shifts.
6. The paired bootstrap uses fictional case groups independent within
   a simulated source family, not independent institution clusters.
   Intervals do not justify cross-institution inference.
7. The ordinary coverage interval contains zero, meaning improvement
   over the strong prior-aware greedy baseline is inconclusive. The
   cost advantage is within the **artificial** prices chosen by the
   simulator, not money saved.
8. The previously published public FraudRAG SSRN preprint is cited.
   A new paper must clearly cite/differentiate the earlier work,
   acknowledge invalid claims, and preserve the old DOI/history.

## Publication implication

**Positive pilot signal:** for this specified cost-and-coverage
simulation, dynamic planning made source requests more economically
than a strong prior-aware greedy policy, with similar certificate
coverage. **Negative:** the method is not yet shown novel, and gains
on synthetic source availability do not establish an original
GraphRAG method, real bank-fraud accuracy or deployment reliability.

A publishable OJ-CS contribution would require independent non-oracle
source outcomes, realistic cost/time audit, a validated new algorithm,
a source attestation implementation, or a distinct methodological
contribution rigorous enough to survive a baseline with access to the
same model and data. Compare to 2025–26 active acquisition, budgeted
RAG and sequential source planning research, including
https://arxiv.org/abs/2606.02245 ,
https://papers.ssrn.com/sol3/papers.cfm?abstract_id=7172681 , and
https://proceedings.mlr.press/v258/li25h.html .

**Submission gate: REMAINS BLOCKED pending stronger externally grounded
evidence, originality and author review.**
