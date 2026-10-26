# SSRN FraudRAG public preprint — author-controlled correction draft
**Prepared:** 2026-10-26 · **Status:** NOT SENT, NOT UPDATED ON SSRN
**Public preprint:** https://papers.ssrn.com/sol3/papers.cfm?abstract_id=6714178
**First posted:** 2026-05-05 · **Revised:** 2026-05-07

## Existing citation — preserve SSRN bibliographic identity

As of October 26, 2026, the public SSRN listing shows **one citing paper**:
*A Hybrid Neuro-Symbolic Framework for Corporate Fraud Detection Using Large
Language Models, Graph Neural Networks, and Automata-Based Reasoning*
(authors Ankita N. Patil, Mritunjay K. Ranjan, Tushar Thorat, Vaidik Gharat
and Samruddhi Sonawane, *Cureus Journal of Computer Science*, 2026).
Source: https://papers.ssrn.com/sol3/papers.cfm?abstract_id=6714178 .

**Recommendation changes because the paper is already cited:**
- Do **not** delete the SSRN entry, reassign its DOI or erase its cited
  bibliographic history in an attempt to improve a new journal submission.
- Preserve original authorship, SSRN identifier **6714178** and DOI
  **10.2139/ssrn.6714178**; use a dated transparent revision/erratum
  explaining which old claims were not reproducible. The existing citation
  does NOT validate the unverified old performance claims.
- Treat the new evidence-acquisition study as a **distinct follow-on
  contribution**, provisionally "FraudRAG-EAC" (Evidence Acquisition
  Controller), and explicitly reference and differentiate it from the
  cited SSRN project. Do not represent it as an independent publication
  until accepted.
- Revision handling and whether the citation/indexing remains intact must
  be confirmed with SSRN; no access to the user's SSRN account or permission
  to change its public entry has been granted.

## Why urgent

The publicly indexed older FraudRAG abstract contains claims that later
reproducibility work cannot verify. It presents $5.38 trillion as if
attributable to financial document forgery, claims "first" financial
GraphRAG/forensic architecture and discusses a Claude 3.5 Sonnet
Neo4j/Chroma inference path and passive fraud rings not established by
actual recovered raw runs. The historical FraudRAG-2400 results are not
independently recoverable. Author should not leave these claims as the
current, outward-facing research description if they are unsupported.

SSRN author revision workflow (August 2026): log into account, choose
**My Papers**, then **Revise**, edit abstract/PDF/title as needed,
then **Submit Revision**. Publisher-restricted postings may require
SSRN support. Primary official instructions:
https://www.elsevier.support/ssrn/answer/how-do-i-revise-a-submission

IEEE expressly requires disclosure of prior similar material and
explanation of incremental contribution:
https://journals.ieeeauthorcenter.ieee.org/become-an-ieee-journal-author/publishing-ethics/guidelines-and-policies/submission-and-peer-review-policies/
**IEEE-approved preprint-posting locations and any restrictions applicable
to this existing SSRN posting should be verified with OJ-CS editorial staff,
rather than assuming all preprint hosts are equivalent.**
https://journals.ieeeauthorcenter.ieee.org/become-an-ieee-journal-author/publishing-ethics/guidelines-and-policies/post-publication-policies/

## Proposed revised SSRN title

**FraudRAG: Evidence-Grounded Consistency Checking with Graph Retrieval and Large Language Models — A Reproducibility Study**

This title reflects current verified experiments, but should not be
adopted if significant overlap/previous submission constraints advise
another wording.

## Proposed SSRN public abstract (author review REQUIRED)

*The original FraudRAG preprint proposed a graph-augmented architecture
for financial-document analysis. Subsequent reproducibility work found
that the originally described dataset and raw performance evidence were
not available for independent verification. This revised working paper
therefore reports new, clearly delimited experiments rather than
repeating earlier accuracy or novelty claims.*

*FraudRAG-v2 generates 840 fictional statement cases from 120 fictional
customers, with 28 customer-disjoint held-out evaluations. A deterministic
comparison against a complete synthetic bank-side reference achieved
F1 = 1.0. A subsequent 112-call GPT experiment using actual Neo4j and
ChromaDB lookups matched that result when given the same full reference;
it did not exceed the deterministic comparator. We additionally
validated the source hashes and text extraction of five openly released,
third-party synthetic bank-statement PDFs, deriving 20 controlled
text-level cases. In a separate 60-call GPT experiment, the model
abstained without adequate references and recognized all text edits
when supplied with each exact original document.*

*These tests support implementation reproducibility and underscore the
limits of evidence availability, but they do not establish real
bank-statement fraud detection, production performance or novel
predictive superiority. We disclose unresolved validity limitations
and retain the underlying experiments and provenance records for
inspection.*

## Supplementary PDF revision notes (include in PDF, not necessarily public abstract)

1. Supersede the unexplained `$5.38 trillion` fraud losses reference
   rather than implying bank-forgery-specific loss data.
2. Supersede unverifiable historical AUC=0.943, F1=0.883 and sub-3-second
   performance claims. Do not cite original charts as empirical evidence.
3. Withdraw all "first GraphRAG in finance" and unverified fraud-ring
   detection or Claude 3.5 Sonnet actual inference claims.
4. Cite actual completed synthetic runs and differentiate the first
   serialized-reference pilot from the later actual Neo4j/Chroma GPT study.
5. Explain experiment labels = scripted text edits **not bank-fraud
   adjudications**, and no external issuer trust has been independently
   verified.
6. Disclose substantive AI assistance, coauthor/editor/affiliation
   responsibilities and permissions accurately.
7. Link to public archived verified results and version history for
   provenance, with earlier claims clearly labeled superseded.
8. If a new OJ-CS paper is built as a substantially different method,
   distinguish it and cite this original SSRN work as preceding public
   disclosure. Ask the editor to confirm SSRN preprint policy as
   necessary.

**This markdown is only a proposed revision. Neither the public SSRN
abstract nor attached PDF has been changed.** Author must sign in,
inspect the current posting, confirm research facts and submit an
appropriate revision or author-controlled withdrawal notice.
