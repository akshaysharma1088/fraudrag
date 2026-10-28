# LedgerShift

A benchmark and method for verifying a submitted bank statement against a bank's own ledger records when the evidence is messy.

**Task.** Given a statement and the ledger evidence, decide one of four states: SUPPORTED, DIFFERENT, CONFLICTING, or DEFER (insufficient evidence).

**Conditions.** Six evidence conditions keep the facts fixed but change how hard they are to line up:
- clean
- format shift (raw bank descriptors, posting lag)
- OCR noise
- split and merged postings
- partial ledger extract
- conflicting sources

Half of the statements carry one balance-preserving manipulation: amount, date, payee, an inserted line or a deleted line.

**Methods.** All methods share one deterministic decision contract.
- `exact`: exact string, amount and date matching.
- `fuzzy`: OCR repair, a posting window and string similarity. The similarity threshold is tuned on the dev split only.
- `alias`: fuzzy plus a curated merchant alias table. It shows what hand-maintained rules can reach.
- `llm_only`: an LLM sees the whole statement and evidence and returns the state.
- `escalate`: selective escalation (the proposed method).
  - Deterministic links are kept where similarity is at least 0.9. That threshold was fixed before any test run.
  - Every other line goes to an LLM, which only proposes *which record* is the same transaction and whether the payee is the same.
  - The contract then compares amount and date and decides.
- `escalate_residual`: the same, but it escalates only the lines the tuned fuzzy matcher leaves open.
- `escalate_oracle`: escalation with a perfect linker. This is the ceiling.

## Run

```bash
cd ledgershift
python -m ledgershift.run build      # dev/test sets (hash-checked) and dev-only threshold tuning
python -m ledgershift.run rules      # deterministic methods
# LLM methods need a local Ollama server: ollama serve & ollama pull qwen2.5:7b
python -m ledgershift.run llm --shard 0 --nshards 1
python -m ledgershift.run evaluate   # results/results.json
```

The GitHub workflow `LedgerShift benchmark` runs the LLM part on 20 parallel runners with an open-weights model, so no paid API is used.
