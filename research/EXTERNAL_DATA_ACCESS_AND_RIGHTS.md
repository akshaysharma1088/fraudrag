# FraudRAG external evidence acquisition and publication rights dossier
**Dated:** 2026-10-26 · **Owner:** author · **Status:** NO EXTERNAL REAL BANK STATEMENT FRAUD DATA APPROVED

## What has actually been verified

- **Bankstatemently Open Benchmark**: five released *synthetic publisher-created bank-statement* PDFs, source SHA-256 verified, but publisher keeps transaction-level gold labels server-side. This is a document parsing/text-edit test only. Already evaluated in FraudRAG v3. Upstream: https://github.com/bankstatemently/bank-statement-parsing-benchmark
- **SSBI / Enhanced Bank Check Security**: publicly described 4,360 synthetic check images, containing 3,360 genuine and 1,000 forged **signatures**, from 19 writers. Published with associated ICDAR 2024 workshop research. Code/data license **CC BY-NC 4.0**. Bank *check signature* forgery is a separate task from altered bank *statements*. The authors' repository supplies underlying example inputs, while the complete dataset must be obtained from the announced v1.0.0 release; do not claim we downloaded the full set until acquisition and hash verification. Source https://github.com/dfki-av/bank-check-security ; original publication https://doi.org/10.1007/978-3-031-70442-0_3
- **DocTamper**: CVPR 2023 (Qu et al.) describes 170,000 image documents with altered text localization. The official repository states **noncommercial only** and asks researchers to obtain the dataset password via an academic email or the application form. Neither approval nor dataset is presently in hand. It is generic document tampering, **not adjudicated real banking fraud**. Paper: https://openaccess.thecvf.com/content/CVPR2023/html/Qu_Towards_Robust_Tampered_Text_Detection_in_Document_Image_New_Dataset_CVPR_2023_paper.html ; official code and application: https://github.com/qcf-568/DocTamper
- **AIForge-Doc v2**: a gated Hugging Face dataset under **CC BY-NC-SA 4.0**, with paired original/artificially forged receipt/form images, pixel masks, and provenance. Dataset card lists 3,066 forged examples; access form requires accepting noncommercial terms. It is not bank-statement forgery. https://huggingface.co/datasets/Scam-AI/AIForge-Doc-v2
- **Bao et al. SEC AAER-linked 146,045 firm-year baseline**: already executed; this is public company **financial reporting misstatement**, not physical bank documents or authentic forged statements. Do not merge those outcomes with document-image studies. https://doi.org/10.1111/1475-679X.12292

## Permission and availability assessment

| Dataset | Ground-truth type | Available to this project | Rights constraints | Appropriate FraudRAG claim |
|---|---|---|---|---|
| Bankstatemently v2.4 five PDFs | Source PDF only; publisher withholds transaction labels | Verified and executed on 5 synthetic sources | MIT repository license with attribution | Synthetic PDF extraction/controlled text edits only |
| SSBI bank checks | Genuine or forged signatures on synthetic checks, COCO boxes | Metadata verified; **full release not ingested** | CC BY-NC 4.0; needs confirmation of intended research use | Supplemental bank-check signature verification only, never bank-statement tampering |
| DocTamper | Document-image tampered text and masks | **Application/approval required** | Noncommercial research and academic-email/password or author approval | Supplemental generic document forensics only |
| AIForge-Doc v2 | AI-inpainted receipt/form images and masks, paired authentic originals | **Hugging Face gating not accepted** | CC BY-NC-SA 4.0, acceptance required | Supplemental financial-adjacent receipt tampering only |
| SEC AAER / Bao panel | Enforcement-linked issuer-year accounting misstatement | Previously executed as separate baseline | Source dataset terms and third-party processing rights should be checked | Issuer accounting misstatement benchmark only |
| Real adjudicated bank-statement fraud | Authentic/forged bank PDFs with independent bank provenance | **NOT AVAILABLE** | Data use, PII, consent, bank rights, ethics/privacy review | **Required before any real bank-statement forgery performance claim** |

## Next authorization steps (human must complete)

1. **Legal/commercial-use clarification**: Author to confirm that running CC BY-NC or CC BY-NC-SA datasets as an independent academic research project is within the license given employment/EB-1A career purposes; if uncertain, obtain direct written permission. A public URL alone does not authorize every use.
2. **Apply for requested data** under research affiliation or personally, using the two request drafts below. Do not claim affiliation with a university or access to an education email that the author does not actually have.
3. **Real banking source partner**: Approach a bank/fintech, anti-fraud research partner, compliance expert or academic forensic lab for lawful, deidentified, adjudicated document pairs and dated independent bank reference records. No source may be exported from employer systems or personal accounts without authorization.
4. **Review and lock protocol**: Register dataset definitions, document-level and bank-level grouping, adjudicator agreement and precommitted hypotheses. Protect test set before model prompting. Treat security/PII issues as an explicit signoff.
5. **Admit data only through gate**: `benchmark/external_evidence_gate.py` must validate provenance, rights, byte SHA-256, grouping, time ordering and independent label origin. Failure to supply a verified, real bank-statement-fraud dataset keeps the promotion gate RED.
6. **Run comparable validation**: Compare rules, raw-text and image detection, external ledger, GPT, graph/vector and hybrid on identical independent records; report abstention, base-rate sensitivity, confidence intervals and error types. Separate check signatures / generic image tampering from bank statements in every table.
7. **Author and external-review signoff**: After verification and primary-source bibliography audit, select a journal fitting the actual evidence, check author consent, journal AI/ethics/data policies and previous editorial history.

## Data-request draft 1 — DocTamper

**To:** 202221012612@mail.scut.edu.cn  
**Subject:** Noncommercial research dataset access request — DocTamper

Dear DocTamper Research Team,

I am an independent researcher working on evidence-grounded document verification, with a particular interest in responsible detection of modified text in financial documents. I am studying your CVPR 2023 DocTamper work and would like to request authorized access to the dataset for noncommercial scholarly research.

My proposed study would evaluate document-image tampering as a separate task, including document-level and source-grouped splits, evidence provenance, abstention, and the limitations of generalizing to real bank statements. I would comply with the applicable access, citation, confidentiality, and nonredistribution conditions. I will not present this dataset as genuine banking fraud records.

Could you confirm the access application process, required academic affiliation or credentials, and whether the intended use is permissible given my professional employment and independent research status?

Thank you for your time.

Akshay Sharma
IEEE Senior Member

## Data-request draft 2 — SSBI authors

**To:** Use the verified official author contact or GitHub discussion; no unverified email addresses  
**Subject:** SSBI bank-check dataset research access and CC BY-NC use clarification

Dear Research Team,

I am conducting an independent, noncommercial scholarly evaluation of evidence-grounded financial document verification. I reviewed your bank-check signature research and the SSBI dataset of genuine and forged signatures in synthetic check images.

I would like to obtain the v1.0.0 dataset and verify the annotations and document-level grouping. Before using it, could you clarify whether my independent research and planned scientific publication comply with the CC BY-NC 4.0 terms, and provide the current dataset archive, any published SHA-256 checksum, and recommended reproducibility split? I will keep signature verification separate from bank-statement alteration and will credit your work.

Thank you,
Akshay Sharma
IEEE Senior Member

## Research practice constraints

- Never characterize publisher-synthetic images as actual bank-issued or fraud-adjudicated statements.
- No cross-dataset AUC table unless tasks, labels, metrics and sample groups are directly comparable.
- Never include bank personally identifying information, unlicensed PDF bytes or restricted corpora in a public repository.
- No automated final journal submission. Author, data owner and independent scientific review must all sign off.
- For EB-1A evidence, do not claim that a work has been accepted, peer reviewed or shown major external significance before that is independently documented.
