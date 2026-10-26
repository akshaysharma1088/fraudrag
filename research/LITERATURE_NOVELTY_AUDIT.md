# FraudRAG literature and novelty audit — primary-source, version 1
**Reviewed:** October 26, 2026. **Status:** targeted source audit, NOT a systematic review.

## Verified primary research records (titles, dates and scope)

1. Barry, M., Caillaut, G., Halftermeyer, P., Qader, R., Mouayad, M., Le Deit, F., Cariolaro, D., & Gesnouin, J. (2025). **GraphRAG: Leveraging Graph-Based Efficiency to Minimize Hallucinations in LLM-Driven RAG for Finance Data**. *Proceedings of GenAIK*, pp. 54–65. Primary venue record: https://aclanthology.org/2025.genaik-1.6/ . The record describes graph and hybrid retrieval on financial/regulatory documentation. **Implication**: “first Graph-RAG applied to finance” is false; this precedent needs discussion. It is not itself a published validation of individual bank-statement forgery detection.
2. Li, Y., Wang, M., de Carvalho, M., Sabanis, S., & Ma, T. (2025). **FinGEAR: Financial Mapping-Guided Enhanced Answer Retrieval**. *Findings of EMNLP*. Primary venue record: https://aclanthology.org/2025.findings-emnlp.382/ . Financial 10-K retrieval with hierarchy-aware representations, evaluated on FinQA. **Implication**: financial-context retrieval is prior art and should be a retrieval baseline if task/data align, not mischaracterized as non-existent.
3. Ma, X. (2026). **Detection of false financial statements in enterprises based on dual-layer knowledge graph and graph-driven approach**. *Discover Artificial Intelligence*, 6, article 298. DOI: https://doi.org/10.1007/s44163-026-00977-y . Publisher states published March 2, 2026. **Implication**: knowledge-graph-based financial statement fraud detection is established prior art. This paper works with enterprise false financial statements and graph-driven analysis; its task is not necessarily bank document forgery, so direct score comparisons would be inappropriate.
4. **Expanding and Interpreting Financial Statement Fraud Detection Using Supply Chain Knowledge Graphs** (2025), *Journal of Theoretical and Applied Electronic Commerce Research*, 20(1), 26. DOI https://doi.org/10.3390/jtaer20010026 . Primary publisher record: https://www.mdpi.com/0718-1876/20/1/26 . Supply-chain relationships improve interpretation of financial statement risk. **Implication**: graph-augmented financial fraud is previously studied. Verify all author names and all specific result claims from the full original before inclusion in formal bibliography.
5. **Occupational Fraud 2024: A Report to the Nations**, ACFE, media summary https://www.acfe.com/about-the-acfe/newsroom-for-media/press-releases/press-release-detail?s=2024-Report-to-the-Nations . March 20, 2024. ACFE analyzed 1,921 occupational fraud cases with $3.1 billion aggregate reported case losses; CFEs estimate organizations lose 5% of revenue annually to fraud. **No source-supported direct estimate of $5.38 trillion financial-document fraud losses**.
6. **Bankstatemently Open Benchmark**. https://github.com/bankstatemently/bank-statement-parsing-benchmark . Research resource, NOT fraud labels. Describes 15 synthetic PDFs across difficulty tiers; public released subset may be smaller, with ground truth held server-side. Use only for supported parsing/structure evaluation, not artificial fraud-classification accuracy.

## Claims explicitly **not** established

- FraudRAG is “the first” Graph-RAG applied to financial documents, “first” Medallion for fraud detection, or “state of the art.”
- A combined GPT/Neo4j/vector architecture materially outperforms independent ledger matching.
- Earlier historical AUC=0.943/F1=0.883, ablations or latency values.
- Synthetic bank-statement edits generalize to real forensic fraud investigations.
- The six primary sources above constitute an exhaustive literature search.
- Any reported 2025–2026 paper can be directly compared unless it evaluates the SAME data and task with a compatible metric.

## Research contribution worth experimentally testing

A narrowly stated hypothesis is **time-respecting, evidence-cited GPT document
consistency analysis across independently held bank-ledger and historical
relationship context**, with auditability of sources and explicit abstention.
This is a *hypothesis*, not a validated novel contribution. A rigorous study
must compare to arithmetic rules and a complete deterministic comparison of the
same trusted records. If simple exact matching is equal or better, report that
truth and redefine the paper as an analysis of limits/tradeoffs rather than
claiming Graph-RAG dominates all baselines.

## Full bibliography still outstanding

This targeted audit does **not** clear the old manuscript's other 29 citation
entries. For each, inspect original record/DOI and full text as necessary, check
that it supports the adjacent sentence, fix incorrect year/authors, and mark
cleared in `CLAIM_VERIFICATION_REGISTER.md`. Avoid importing unverified citations
from the historical manuscript into a revised submission.
