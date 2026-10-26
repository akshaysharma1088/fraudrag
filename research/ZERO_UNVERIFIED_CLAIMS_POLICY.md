# Zero-unverified-claims manuscript rule

**Publication is blocked until evidence is complete.** We may propose models,
architectures and hypotheses, but must never present them as validated outcomes.

1. Reproduce every numerical outcome from an immutable input dataset,
   version-locked model(s), script, seed, sample-level predictions and
   actual execution logs. Report context, known failures and limitations.
2. Verify each third-party fact from a specific primary source and check
   that the manuscript wording matches its *scope and measurement*. Provide
   DOI/version/access date as appropriate.
3. Demonstrate implemented behavior with source paths + an executed test;
   no inference from code comments, diagrams, a README, or mocks alone.
4. Do not use “first”, “novel”, “state of the art” or “outperforms” without
   a dated, documented literature/baseline comparison supporting the claim.
5. Never turn an *LLM-generated fraud score* into a calibrated probability
   without independent evidence. Never treat graph association as guilt.
6. Classify qualitative architecture as **design / implementation**,
   experiments as **observed within stated population**, and extrapolation
   as **limitation or future work**.
7. Distinguish Fin-Fact *fact checking*, PaySim *transaction fraud*,
   synthetic *document manipulation*, and real *bank statement forgery*.
8. Keep copies of original results and failed/negative runs; do not edit
   experiment outputs manually or cherry-pick seeds.
9. Cite the source and author-date for every factual statement,
   check the source actually supports it, and audit bibliography entry by entry.
10. Freeze the submission copy until the complete
    `CLAIM_VERIFICATION_REGISTER.md` is approved by the author.
    Archive draft versions; do not silently overwrite their scientific history.

In a draft under development, use visibly marked `[UNVERIFIED — DO NOT
SUBMIT]` blocks or omission. **Never soften an unsupported result into a
different invented number.**

The author must explicitly approve any final journal submission. Passing CI
and this register are necessary controls, not guarantees of research validity.
