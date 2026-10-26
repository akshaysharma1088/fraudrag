# FraudRAG author accountability and AI assistance disclosure
**Drafted 2026-10-26. Must be reviewed and approved by human author before any scholarly submission.**

## Transparent research assistance

OpenAI ChatGPT (GPT-6) substantially assisted with creating, refactoring
and reviewing research scripts and tests, setting up GitHub Actions,
research analysis plans, evaluation safeguards, audit and bibliography
checklists, and drafting research text. OpenAI GPT-6.1 Sol was separately
called through a metered API to produce the saved experimental predictions
as a **model under evaluation**, not as a human author or reviewer.
Some earlier application components may have been independently written;
do not assume all repo code was AI-generated or human-written without
reviewing the Git commit history and files.

Neither a passing unit test nor a generated manuscript certifies research
originality, legal rights, factual accuracy, software safety or authorship.
Research lead must review and understand the code and make the conceptual
and publication decisions. Any journal-required AI disclosure and citations
to the particular tools/models used must be included in its specified
format. Do not claim a human independently reviewed generated outputs
until that actually happened.

## Human-author signoff checklist (ALL PENDING)

- [ ] Confirm research framing, hypotheses and distinction between
      synthetic text alterations, check signatures, actual fraud and
      public issuer-year accounting misstatements.
- [ ] Independently inspect training/held-out splits, code, raw run
      predictions, provenance and failed runs. Verify metrics calculations.
- [ ] Verify each literature entry and that each citation specifically
      supports the sentence where it appears.
- [ ] Inspect dataset licenses, obligations, IRB/privacy/data-controller
      requirements, PII handling and author/employer intellectual property.
- [ ] Confirm all author names and affiliations, coauthor consent,
      funding/conflict disclosures and previous manuscript submission status.
- [ ] Determine author contribution and originality, rather than assume
      assistance and automation replace author judgment.
- [ ] Validate any accessibility/data-availability/licensing claims in final
      submitted files and adhere to selected journal's AI-writing policy.
- [ ] Author explicitly approves final proof for journal submission.

## Example draft disclosure, pending human approval

> AI-assisted tools were used for software scaffolding and refactoring,
> test generation, experiment orchestration, literature organization
> and manuscript drafting/editing. OpenAI ChatGPT (GPT-6) assisted in
> those activities; OpenAI GPT-6.1 Sol was the language model evaluated
> in the reported experiments. All numerical results shown originate
> from archived actual experiments and separately implemented auditing
> scripts. The author is responsible for verifying and approving all
> code, sources, analysis, interpretation, authorship and research
> integrity. [Author to confirm actual independent review and edit this
> statement before submission.]

JOSS policy specifically requires tool/version, use scope and affirmative
human review statements (https://joss.readthedocs.io/en/latest/submitting.html);
IEEE Access submission guidance requires AI text acknowledgment and
citations in affected sections (https://ieeeaccess.ieee.org/authors/submission-guidelines/).
Neither policy is automatically satisfied by this draft.
