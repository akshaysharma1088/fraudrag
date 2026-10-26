# FraudRAG-EAC: external financial evidence provider integrations

**Engineering status (2026-10-26): IMPLEMENTED AND OFF BY DEFAULT.** These are two distinct integration contracts, both tested using offline fake providers and independently generated test keys. **No real bank, customer account, Plaid session, production authorization, issuer key, cost-bearing request or actual bank-statement PDF has been connected or retrieved.**

## Path A — real bank statement PDFs from Plaid Statements

**This is the preferred next real-data integration** when a consenting customer and approved Plaid Statements product account are available. Official source: https://plaid.com/docs/statements/ and https://plaid.com/docs/api/products/statements/ .

What Plaid says it provides:
- US-only Statements product that retrieves a **bank-branded PDF copy of the customer's original bank statement** from supported financial institutions.
- `POST /statements/list` provides authorized Plaid Item account-specific metadata including `statement_id`.
- `POST /statements/download` returns original PDF bytes and `Plaid-Content-Hash` SHA-256 download-integrity header.
- Institution coverage is incomplete. Access requires legitimate account authorization and an approved Plaid account/Statements entitlement.
- **Billing:** Plaid Statements may charge **when an Item is created** even if you never download a statement; refresh is separately billed. This code deliberately does **not** create Items, initiate Plaid Link, call `/statements/refresh` or start any billable process.

Implementation:
- `backend/services/plaid_statements_provider.py`: strict current Plaid environments `sandbox` and `production` only; server-only Plaid client-id/secret; customer-consented per-Item access token; exact Item/account binding; statement ownership validation; bounded PDF download; required SHA-256 content header validation; exact source-PDF byte comparison to submitted PDF; explicit disclaimers.
- `backend/services/plaid_partner_bootstrap.py`: opt-in app client setup. The per-user access token is intentionally **NOT** an app environment variable. It must be obtained through the authenticated Plaid Link/public-token exchange workflow and held securely under a tenant/user/consent authorization store **that is not yet implemented**.
- App configuration defaults:
  ```dotenv
  EAC_PLAID_ENABLED=false
  EAC_PLAID_ENVIRONMENT=sandbox
  EAC_PLAID_CLIENT_ID=
  EAC_PLAID_SECRET=
  ```
- No public live-account API route exists. The browser's EAC tab remains fiction-only. The app stores a configured server provider in `app.state.eac_plaid_provider` **only if** the operator explicitly enables the feature and configures valid server credentials. No requests occur on app startup.

**Important truth boundaries:**
- SHA-256 here validates that a downloaded file matches the checksum Plaid returned **over the authenticated HTTPS channel**. It is **not a bank-issued digital signature**, nor evidence of a criminally forged document.
- `EXACT_PDF_BYTES_MATCH` supports exact byte equality with the source obtained by Plaid for the authorized account/statement.
- `PDF_BYTES_DIFFER` is only a byte-level difference: re-rendering, legitimate edits, accessibility conversion and metadata changes can all produce a different hash. Deeper visual/semantic comparison and analyst review are mandatory before alleging tampering.
- This adapter does not assert the bank API's transaction list is complete, perform OCR, claim fraud accuracy, or certify document authenticity.
- The currently supported Plaid checksum encoding is **64-character hexadecimal SHA-256**. Verify this assumption with an authorized Sandbox response before production use; the public documentation does not specify the exact text encoding of this response header. Fail closed for unknown encodings.

### Plaid mock test

```bash
python -m pytest tests/test_plaid_statements_provider.py tests/test_plaid_partner_bootstrap.py -q
```

Tests deliberately simulate Plaid via `httpx.MockTransport`; no real Plaid API calls occur. They cover account/Item binding, consent denial, valid/mismatched hashes, missing checksum, invalid PDF bytes, unapproved calls, redirect blocking and size limits.

## Path B — institution-issued signed field evidence

A future financial institution partner may provide field-level references that it **explicitly signs**. The current implementation specifies a custom `EAC_RECORD_V1` Ed25519 canonical-JSON signature format, **not FDX, JWS or an interoperable banking industry specification**. It requires a bank-side signer implementing the agreed schema before it can become a real integration.

- `backend/services/signed_issuer_evidence.py` validates Ed25519 signatures using **only server-pinned, independently approved issuer public keys**. A signature never becomes trusted because a user uploaded a matching key or the response supplied a key ID.
- Strictly binds issuer, intended recipient, tenant, bank account, approved consent ID, observed/issued/expiry timestamps, statement-validity interval, field identity and explicitly signed completeness assertions.
- Unknown issuer, wrong key, altered payload, duplicate field, expired/future evidence, cross-account/tenant reuse, unsigned source, conflict and incompleteness **fail closed**.
- `backend/services/authorized_issuer_transport.py` provides an opt-in server-to-server HTTPS adapter that rejects browser-selected hosts, IP literals, redirects, local endpoints and oversized responses. Requires an **independent egress firewall and DNS hardening** before any production bank requests.
- `backend/services/issuer_partner_bootstrap.py` accepts server-only configuration for pinned public keys and managed OAuth bearer tokens. Defaults `EAC_PARTNER_ENABLED=false`. No public route calls it.

This route supplies independently **cryptographically verified signature provenance when—and only when—the operator genuinely controls a bank-approved key registry**. It still cannot prove the bank's facts are true or that completeness guarantees are satisfied beyond the signed field scope.

Security reference: https://www.rfc-editor.org/rfc/rfc8725.html stresses algorithm allowlisting, issuer/key binding, audience and input validation. This custom protocol is not itself JWT, so RFC 8725 should be treated as related security guidance, **not a claim of compliance**.

### Signed partner mock test

```bash
python -m pytest tests/test_signed_issuer_evidence.py tests/test_issuer_partner_bootstrap.py -q
```

No private keys are committed. Tests generate ephemeral Ed25519 keypairs during execution and use mocked HTTPS transport.

## Why not simply label Plaid Transactions as authoritative ledger?

Plaid Transactions data are standardized and periodically refreshed, so they may **lag the official bank statement**. Plaid documents both delayed updates and that `/transactions/sync` returns the current synchronized view of authorized transactions, not a signed certificate of all bank activity. See https://plaid.com/docs/api/products/transactions/ and https://support.plaid.com/hc/en-us/articles/15373384920599-Do-the-transactions-get-and-transactions-sync-endpoints-provide-real-time-data .

For **bank document consistency**, an original statement PDF retrieved through authorized Plaid Statements is a more direct comparator than inferring authenticity from incomplete transactions, provided the actual bank supports Statements.

## Before ANY real-data use

- Contract or provider account permitting research/product use, explicit user consent, authorized Plaid Link/Item acquisition or signed bank partner integration, and bank/institution scope verification.
- Per-user credentials and consent registry, tenancy isolation, OAuth lifecycle and revocation handling, no browser-provided Item access token, no hardcoded credentials, approved access-control policies.
- Encryption at rest, minimal retention, PII-safe logging, source download audit trail, rate limits, key rotation and approved security controls; securely delete source PDF bytes after authorized processing.
- Source PDF provenance and checker semantics must be reviewed; a source checksum is **not** a digital signature or independently adjudicated fraud outcome.
- For OJ-CS, seek a legally licensed independent benchmark or authorized study. Unit tests and fictional mock Plaid data are **NOT external scientific validation**.
- Do not turn on production live endpoints until an authenticated user/session API and consent vault are implemented and audited. At present **NONE is exposed**.

FDX's consent-based API model and security recommendations are relevant architectural context: https://financialdataexchange.org/about-fdx/faqs/ . The custom Ed25519 adapter does not claim to implement FDX.

**Repository continuity:** the original FraudRAG project and its already-cited SSRN DOI are preserved; this is a follow-on engineering module, not a new paper publication. No deployment or change to main has been made.
