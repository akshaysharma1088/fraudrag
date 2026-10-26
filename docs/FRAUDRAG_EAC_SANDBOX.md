# FraudRAG-EAC — Evidence Acquisition Controller (implemented sandbox)

**Status:** integrated opt-in interactive **FICTIONAL evidence verification demo**, not production bank authentication, not fraud adjudication, not a research paper acceptance claim.

## What is built

- `backend/services/eac_certificate.py`: a backend-packaged version of the bitemporal issuer-reference certificate checker (canonical runtime copy), reporting five evidence outcomes: `MATCH_SUPPORTED`, `DIFFERENCE_PROVEN`, `EVIDENCE_CONFLICT`, `INSUFFICIENT_EVIDENCE`, and `SOURCE_UNTRUSTED_OR_STALE`. SHA-256 identifies replay content but is not a bank digital signature. Issuer attestation metadata in the demo is assumed.
- `backend/services/eac_service.py`: executable source selector, classical dynamic programming with a fictional availability prior, prior-aware greedy and fixed-order comparators, source provider contract, per-request costs and source provenance trace. All planners are **deterministic** and act on the same fiction-only source catalog.
- `backend/api/routes/eac.py`: **gated** `GET /api/v1/eac/demo/scenarios` and `POST /api/v1/eac/demo/run` API endpoints, accepts only predefined scenario names, strategy and budget. It **rejects** arbitrary source uploads/issuer attestation metadata. No write to a customer DB. No API billing.
- `frontend/src/pages/EvidenceAcquisition.jsx`: interactive Evidence Acquisition tab with scenario, strategy, fictional budget, source-query trace, per-field source witnesses, remaining unknown fields, decision status and replay digest.
- `tests/test_eac_service.py` and `tests/test_eac_api.py`: verify consistent source, altered source, missing evidence, conflicting issuer facts, future-dated references, determinism, budget controls, restricted caller fields and default-off access.
- `EAC_DEMO_ENABLED=false` defaults off in `backend/core/config.py` and `.env.example`. Explicitly opt into a local test environment.

The earlier research pilot `benchmark/adaptive_acquisition_v4.py` remains a **separate** 1,080 calibration/720 held-out/360 shift simulation. The new interactive sample data must not be mixed into that model's experimental metrics.

## Enable locally

Copy `.env.example` to `.env` and set `EAC_DEMO_ENABLED=true` in a controlled local environment. Or set the environment variable when launching FastAPI. The normal backend still initializes its PostgreSQL/Neo4j/Graph RAG services; start these as described in the project README or use a deliberately test-only app with `create_app(testing=True)`.

In the web app, open **Evidence Acquisition** in the left navigation. Choose a fictional scenario and click **Acquire evidence and verify**.

Or use the API:

```bash
curl http://localhost:8000/api/v1/eac/demo/scenarios

curl -s -X POST http://localhost:8000/api/v1/eac/demo/run \
  -H 'Content-Type: application/json' \
  -d '{"scenario":"consistent","policy":"adaptive_dp","budget_units":4.0}'

curl -s -X POST http://localhost:8000/api/v1/eac/demo/run \
  -H 'Content-Type: application/json' \
  -d '{"scenario":"future","policy":"fixed","budget_units":4.0}'
```

Compare identical cases under `adaptive_dp`, `greedy` and `fixed`.

### Fixture semantics

- **consistent**: all relevant fictional issuer references agree with submitted values.
- **altered**: submitted closing balance differs from the original fictional issuer record. This is an observed discrepancy, **not proof of criminal fraud**.
- **partial**: the required transaction-level reference cannot be obtained; absent facts are not interpreted as valid.
- **conflicting**: two independently *represented* pre-fetched fictional issuer references disagree; the checker requires further review and does not silently rank them.
- **future**: response records were learned after the decision cutoff and cannot authorize a supported match.

EAC is a **separate, optional tab**; it does not silently override the existing document-upload or fraud-scoring routes. This is deliberate until real source identity, consent and authorization are validated.

## How this moves toward a real deployment

The `EvidenceProvider` protocol defines a future issuer-evidence adapter, but **no authenticated real-bank provider exists today**. A real connector would require all of:

1. Authorized bank/issuer data use and subject consent, an approved API/OAuth arrangement and a bank-issued authority trust root; do not use user-submitted assertions as issuer credentials.
2. Cryptographic checks of authenticity *before* setting attestation and completeness flags, and independent verification of issuer signatures, source record byte digests, fact scope and record provenance.
3. Authenticated per-tenant request access, PII security, rate limiting, encrypted audit storage, retention policies, explicit query-cost budgets and error handling.
4. Verified bitemporal as-of snapshots, source corrections, conflict handling, no future information leakage, proof that one issuer's duplicate data across Neo4j/Chroma is a single evidence family.
5. No automatic allegation of bank fraud. Human review for contradictory/ambiguous cases and fairness/false-accusation monitoring.
6. Real authorized institution-held test evidence before reporting deployable fraud detection rates or source-cost improvements.

**No real account statements, customer identifiers, or bank APIs have been added to this demo.**

## Tests and reporting

```bash
pytest tests/test_eac_service.py tests/test_eac_api.py -q
```

This repository runs the existing CI backend and React build on PR #1. The sandbox's passing tests measure scenario correctness and API behavior, **not fraud-detection validation or novel algorithm performance**.

Original SSRN FraudRAG DOI and existing citation should remain intact. `FraudRAG-EAC` is only a provisional module name, not a claim of trademark ownership. See `research/SSRN_CORRECTION_DRAFT.md`.
