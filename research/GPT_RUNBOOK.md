# GPT experiment setup and outstanding research work

## Preferred LLM
- **Primary:** `gpt-6.1-sol` via OpenAI Responses API.
- **Cost comparator:** `gpt-6-luna`.
- The script's standard list-price assumptions (checked October 26, 2026) are
  $2/M input and $10/M output tokens for GPT-6.1 Sol, and $0.10/M input
  and $0.50/M output tokens for GPT-6 Luna. These can change. The runner records
  model, tokens and a documented **estimate**, not a guaranteed final bill.
- Actual model availability depends on API account access, which cannot be
  established by the connected GitHub repository alone.

## A controlled, matched first GPT experiment

`experiments/gpt_finfact_study.py` uses exactly the same 24 Fin-Fact claim
indices (seed 2026) as the earlier Qwen pilot. Both GPT results and the TF-IDF
and majority baselines on these 24 cases are computed without leaking the
held-out labels into GPT prompts.

Default runs are **dry runs** (data provenance, model/cost preview). No paid
API requests are made unless `--execute` is explicitly supplied.

To run locally:

```bash
python -m pip install 'scikit-learn>=1.4,<2'
python experiments/gpt_finfact_study.py --limit 24
# After obtaining API billing and setting a secret only in your shell:
export OPENAI_API_KEY=...  # NEVER commit or paste API keys into chat
python experiments/gpt_finfact_study.py --execute --model gpt-6.1-sol \
  --limit 24 --max-estimated-usd 2
```

To run using GitHub Actions, merge the draft PR after review so the new
workflow is registered on the default branch. In **Settings > Secrets and
variables > Actions**, add a repository secret named `OPENAI_API_KEY`.
Then open **Actions > GPT Fin-Fact paired evaluation > Run workflow**,
enable paid API inference, and select the model, sample size and estimated
cost limit.

**IMPORTANT:** The workflow caps conservative projected per-request token
costs; it is not a hard organization-level spending cap. Configure spending
limits in the API billing account as well. Your ChatGPT plan is separate
from API credits. Do not supply payment credentials or API keys in chat.

## Research status / what is left

1. **Target data**: legitimate and systematically modified financial
   documents, source provenance, annotation process, hard negative
   examples, licensed access and train/validation/test splits.
2. **Graph construction**: temporally valid customer/institution/document
   nodes and links with evidence IDs; rule out future information and label
   leakage from graph history.
3. **True Graph-RAG**: implement document parsing, retrieval and GPT fusion
   and compare rule-only, GPT-only, vector-only, graph-only and combined
   variants on identical test documents.
4. **Statistical verification**: seed repeats, macro F1, fraud precision,
   recall, AUC if defined, calibration and confidence intervals; p50/p95
   latency, token usage and failure/abstention rates.
5. **Publication preparation**: a current-literature novelty analysis,
   full error analysis, disclosures, validated tables/figures, documented
   source/release versions and a new manuscript consistent with experiments.

Fin-Fact financial-claim classification is **not a proxy** for bank-statement
forgery performance. Report it separately or leave it out of the primary
FraudRAG manuscript. The original manuscript's AUC=0.943/F1=0.883 remains
unverified because the original experiment data is missing.
