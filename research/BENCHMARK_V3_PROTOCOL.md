# FraudRAG Benchmark v3 — external PDF evidence protocol

**Research status: controlled experiment, NOT real-world financial-fraud validation.**

## Primary third-party source

**Publisher:** Bankstatemently — [open parsing benchmark](https://github.com/bankstatemently/bank-statement-parsing-benchmark), MIT license.  
**Pinned Git commit:** `2d8d31d68dcedbf9028b87f6c7df286f53a6c7de`.  
**Publicly released originals:** bsb-001 through bsb-005, covering Singapore, US credit card, Netherlands, Hong Kong and French-language Canada. All five source PDFs are **synthetic publisher-created records**; none is a known genuine fraud case. The remaining ten announced PDF fixtures have not been publicly released at this version. The publisher stores transaction-level answer keys on its own server, not in the public repository.

The source PDFs are downloaded transiently from version-pinned paths, SHA-256-verified against the publisher's August 2026 corrected releases, and parsed locally with `pdfplumber`. Original PDFs and extracted full text are NOT committed or republished by FraudRAG. The source provides an external **document-layout distribution**, not independent real fraud adjudication.

## Completed source-hash and extraction verification

Successful GitHub Actions run: https://github.com/akshaysharma1088/fraudrag/actions/runs/40371198225  
Machine-readable record: [RESULTS_V3_EXTERNAL_PDF_2026-10-26.json](RESULTS_V3_EXTERNAL_PDF_2026-10-26.json)

- **5 of 5 SHA-256 checks passed** against publisher PDF checksums.
- **17 of 17 pages** contained selectable extracted text. This does **not** demonstrate OCR ability or field extraction accuracy.
- Each source creates four related examples: original, benign whitespace normalization, first monetary-string edit, and later monetary-string edit. **20 total controlled TEXT-level cases** from just five source PDF documents, with ten injected edits and ten unaltered/benign cases.
- Full-original text matching recognizes all known injected edits, **20 of 20**, by construction: the scorer has the literal extracted original.
- Comparing only the normalized first 30 source words yields **20 of 20 abstentions**; the available truncated reference contains no information that can disambiguate those controlled changes.
- No-reference mode also yields **20 of 20 abstentions**.

**A scientifically important bug was detected and corrected:** the initial partial-reference prototype compared the first 250 *characters* of original and submitted text, which turned harmless changes in whitespace lengths into apparent content mismatches. That earlier run has been preserved (https://github.com/akshaysharma1088/fraudrag/actions/runs/40370987339) and explicitly marked **superseded**. The corrected method compares the first 30 **normalized tokens**, with regression tests. All final numerical statements above use the corrected successful run.

## LLM study protocol (when executed)

`experiments/v3_pdf_gpt.py` precommits 60 GPT-6.1 Sol trials: 20 fixed cases in three conditions: submitted text alone, first 30 original source words, and exact original extracted text. The last one intentionally presents an **oracle**, not a separate trusted bank institution ledger. Outputs include edited/unchanged/uncertain, evidence source IDs, token usage, latency and response errors, all in a cost-capped workflow. Every actual result must be independently audited and labeled *text-edit recognition*; no model success here demonstrates forged PDF imaging, company misstatement detection, or consumer bank-document fraud detection.

## What would change publication eligibility

1. Obtain appropriately licensed, independently annotated image/document tampering materials. [Official DocTamper](https://github.com/qcf-568/DocTamper) lists academic noncommercial restrictions and an application process; do not scrape, bypass credentials, or conflate text-image tampering with financial-bank-specific fraud.
2. Identify legally usable **authentic bank documents** and independent confirmed forgery adjudications, including issuer/source validation, privacy permissions, and ethics review. No such data currently exists in this project.
3. Establish an independent bank-ledger reference process in which the original submitted PDF is **not** used as the trusted oracle. Include missing, partial, delayed, contradictory and counterfeit supporting evidence.
4. Use source-document-grouped and preferably institution-grouped held-out splits; five source documents are insufficient for generalization. Commit exact split manifests, not just shuffled row IDs.
5. Test scanned and adversarial image PDF input with licensed pixel-level tampering labels. Validate text extraction/OCR separately against independently withheld transaction answer keys.
6. Compare rule-only and complete-ledger deterministic methods against GPT, graph, vector and hybrid with precisely identical source availability.
7. Preserve all failed outcomes, unsupported source IDs, ambiguous judgments and abstentions; never tune the final test based on the published answers or experiment outputs.
8. Verify complete prior art and article references; report externally validated results without inferring that synthetic text edits are real financial misconduct.

**Editorial gate remains blocked until these scientific requirements are met.**
