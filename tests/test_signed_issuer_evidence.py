"""Offline contract tests: pin Ed25519 issuer identity and reject untrusted source.

All records and keys generated per test; private keys NEVER committed.
No actual bank APIs, credentials or user financial data.
"""
from __future__ import annotations

import base64
import copy
import json

import httpx
import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from backend.services.eac_certificate import Claim
from backend.services.signed_issuer_evidence import (
    ALGORITHM, TYPE, EvidenceRejected, IssuerScope, IssuerTrustRegistry,
    canonical, certify_signed_sources, verify_signed_envelope,
)
from backend.services.authorized_issuer_transport import (
    AuthorizedIssuerHTTPAdapter, _approved_endpoint,
)

RECEIVED = "2026-07-30T13:00:00Z"
EFFECTIVE = "2026-07-30T12:00:00Z"
CUTOFF = "2026-07-30T23:00:00Z"


@pytest.fixture
def fixture():
    private = Ed25519PrivateKey.generate()
    other = Ed25519PrivateKey.generate()
    issuer = "fictional-issuer-001"
    scope = IssuerScope(
        issuer_id=issuer, audience="fraudrag-eac-staging",
        tenant_id="tenant-fixture-1", account_id="account-fixture-1",
        consent_id="consent-fixture-1", permission_authorized=True
    )
    registry = IssuerTrustRegistry({issuer: {"test-key-1": private.public_key()}})
    records = [
        {
            "key": key, "value": val,
            "valid_from": "2026-07-01T00:00:00Z",
            "valid_until": "2026-08-01T00:00:00Z",
            "complete_for_field": True,
        }
        for key, val in (
            ("account", "ACC-1"), ("closing", "100.00"),
            ("transaction", "T1:20.00"),
        )
    ]
    payload = {
        "iss": issuer,
        "aud": scope.audience,
        "tenant_id": scope.tenant_id,
        "account_id": scope.account_id,
        "consent_id": scope.consent_id,
        "issued_at": "2026-07-30T12:30:00Z",
        "expires_at": "2026-07-31T23:00:00Z",
        "records": records,
    }
    head = {"alg": ALGORITHM, "typ": TYPE, "kid": "test-key-1"}
    def sign(body=None, head_override=None, signer=None):
        signed = {
            "protected": copy.deepcopy(head if head_override is None else head_override),
            "payload": copy.deepcopy(payload if body is None else body),
        }
        key = private if signer is None else signer
        sig = key.sign(canonical(signed))
        signed["signature"] = base64.urlsafe_b64encode(sig).rstrip(b"=").decode()
        return signed

    def certify(envelopes, claims=None, req_scope=None, req_registry=None, received=None,
                effective=EFFECTIVE, cutoff=CUTOFF):
        return certify_signed_sources(
            (Claim("account", "ACC-1"), Claim("closing", "100.00"),
             Claim("transaction", "T1:20.00")) if claims is None else claims,
            tuple(envelopes),
            registry=registry if req_registry is None else req_registry,
            scope=scope if req_scope is None else req_scope,
            received_at=RECEIVED if received is None else received,
            effective_at=effective, decision_cutoff=cutoff,
        )

    return private, other, registry, scope, records, payload, head, sign, certify


def test_valid_signed_source_supports_all_required_fields(fixture):
    *_, sign, certify = fixture
    result = certify([sign()])
    assert result["source_attestation"].startswith("cryptographic_signature_verified")
    assert result["signed_field_records"] == 3
    assert result["certificate"]["document_status"] == "MATCH_SUPPORTED"
    assert len(result["certificate"]["basis_sha256"]) == 64


def test_signature_makes_mismatch_evidence_conditional_not_fraud(fixture):
    *_, sign, certify = fixture
    result = certify([sign()], claims=(Claim("closing", "200.00"),))
    assert result["certificate"]["document_status"] == "DIFFERENCE_PROVEN"
    assert "criminal" not in result["certificate"]["document_status"].lower()


def test_not_all_fields_signed_never_approve_full_document(fixture):
    _, _, _, _, _, body, _, sign, certify = fixture
    missing = copy.deepcopy(body)
    missing["records"] = missing["records"][:2]
    result = certify([sign(missing)])
    assert result["certificate"]["document_status"] == "INSUFFICIENT_EVIDENCE"
    assert "transaction" in result["certificate"]["unresolved_fields"]


def test_unattested_field_does_not_authorize_a_clearance(fixture):
    _, _, _, _, _, body, _, sign, certify = fixture
    incomplete = copy.deepcopy(body)
    incomplete["records"][2]["complete_for_field"] = False
    result = certify([sign(incomplete)])
    assert result["certificate"]["document_status"] == "INSUFFICIENT_EVIDENCE"


def test_wrong_signature_public_key_is_rejected(fixture):
    _, wrong, _, _, _, _, _, sign, certify = fixture
    with pytest.raises(EvidenceRejected, match="signature"):
        certify([sign(signer=wrong)])


@pytest.mark.parametrize("field,wrong", [
    ("iss", "another-issuer"),
    ("aud", "other-service"),
    ("tenant_id", "another-tenant"),
    ("account_id", "someone-else-account"),
    ("consent_id", "another-consent"),
])
def test_signed_record_cannot_cross_scope_boundaries(fixture, field, wrong):
    _, _, _, _, _, payload, _, sign, certify = fixture
    changed = copy.deepcopy(payload)
    changed[field] = wrong
    with pytest.raises(EvidenceRejected, match=field):
        certify([sign(changed)])


def test_unsigned_attestation_booleans_and_spoofed_kid_rejected(fixture):
    _, _, _, _, _, body, head, sign, certify = fixture
    env = sign()
    env["payload"]["records"][0]["value"] = "INJECTED"
    with pytest.raises(EvidenceRejected, match="signature"):
        certify([env])
    spoofed = copy.deepcopy(head)
    spoofed["kid"] = "attacker-key"
    with pytest.raises(EvidenceRejected, match="not independently trusted"):
        certify([sign(body, spoofed)])
    unknown_algo = copy.deepcopy(head)
    unknown_algo["alg"] = "none"
    with pytest.raises(EvidenceRejected, match="algorithm"):
        certify([sign(body, unknown_algo)])


def test_server_only_consent_authorization_is_mandatory(fixture):
    from dataclasses import replace
    _, _, _, scope, _, _, _, sign, certify = fixture
    with pytest.raises(EvidenceRejected, match="consent"):
        certify([sign()], req_scope=replace(scope, permission_authorized=False))


@pytest.mark.parametrize("changed,expected", [
    ({"issued_at": "2026-08-02T12:00:00Z"}, "available"),
    ({"expires_at": "2026-07-30T12:45:00Z"}, "expired"),
])
def test_issuer_signed_timestamps_must_be_valid(fixture, changed, expected):
    _, _, _, _, _, body, _, sign, certify = fixture
    mod = copy.deepcopy(body)
    mod.update(changed)
    with pytest.raises(EvidenceRejected, match="available or expired"):
        certify([sign(mod)])


def test_backdated_trusted_issuer_record_not_usable_after_future_ingestion(fixture):
    *_, sign, certify = fixture
    with pytest.raises(EvidenceRejected, match="available or expired"):
        certify([sign()], received="2026-08-01T00:00:00Z")
    with pytest.raises(EvidenceRejected, match="available or expired"):
        certify([sign()], cutoff="2026-07-30T12:00:00Z")


def test_field_period_scope_and_duplicate_field_rejected(fixture):
    _, _, _, _, _, body, _, sign, certify = fixture
    wrong = copy.deepcopy(body)
    wrong["records"][0]["valid_until"] = "2026-07-29T00:00:00Z"
    with pytest.raises(EvidenceRejected, match="validity"):
        certify([sign(wrong)])
    duplicate = copy.deepcopy(body)
    duplicate["records"].append(duplicate["records"][0])
    with pytest.raises(EvidenceRejected, match="duplicate"):
        certify([sign(duplicate)])


def test_conflicting_distinct_verified_signatures_defers(fixture):
    _, _, _, _, _, body, _, sign, certify = fixture
    changed = copy.deepcopy(body)
    changed["records"][1]["value"] = "900.00"
    result = certify([sign(), sign(changed)])
    assert result["certificate"]["document_status"] == "EVIDENCE_CONFLICT"
    assert len(result["certificate"]["field_results"]["closing"]["witness_source_ids"]) == 2


def test_complete_response_batch_fail_closed_if_one_document_is_untrusted(fixture):
    _, wrong, _, _, _, _, _, sign, certify = fixture
    with pytest.raises(EvidenceRejected):
        certify([sign(), sign(signer=wrong)])


@pytest.mark.parametrize("endpoint,host", [
    ("http://evidence.example.com/api", "evidence.example.com"),
    ("https://127.0.0.1/api", "127.0.0.1"),
    ("https://localhost/api", "localhost"),
    ("https://evidence.example.com:8443/api", "evidence.example.com"),
    ("https://evidence.example.com@evil.example/x", "evil.example"),
    ("https://evidence.example.com/api?url=https://evil.example", "evidence.example.com"),
    ("https://evil.example/api", "evidence.example.com"),
])
def test_transport_endpoint_allowlist_rejects_ssrf_patterns(endpoint, host):
    with pytest.raises(EvidenceRejected):
        _approved_endpoint(endpoint, host)


def test_remote_transport_off_by_default_and_never_calls_host(fixture):
    _, _, registry, scope, _, _, _, sign, _ = fixture
    count = []
    def handle(req):
        count.append(req)
        return httpx.Response(200, json={"envelopes": [sign()]})
    with httpx.Client(transport=httpx.MockTransport(handle)) as client:
        adapter = AuthorizedIssuerHTTPAdapter(
            endpoint="https://evidence.example.com/api",
            allowed_hostname="evidence.example.com",
            access_token="offline-test-token", registry=registry,
            client=client,
        )
        with pytest.raises(EvidenceRejected, match="disabled"):
            adapter.fetch_and_certify(
                claims=(Claim("closing", "100.00"),), scope=scope,
                effective_at=EFFECTIVE, decision_cutoff=CUTOFF,
                received_at=RECEIVED,
            )
    assert count == []


def test_mocked_https_transport_authenticated_signed_response(fixture):
    _, _, registry, scope, _, _, _, sign, _ = fixture
    calls = []
    def handle(request):
        calls.append(request)
        assert request.headers["authorization"] == "Bearer offline-test-token"
        assert request.url.host == "evidence.example.com"
        body = json.loads(request.content)
        assert body == {
            "tenant_id": scope.tenant_id, "account_id": scope.account_id,
            "consent_id": scope.consent_id,
            "fields": ["account", "closing", "transaction"],
        }
        return httpx.Response(200, json={"envelopes": [sign()]})
    with httpx.Client(transport=httpx.MockTransport(handle)) as client:
        adapter = AuthorizedIssuerHTTPAdapter(
            endpoint="https://evidence.example.com/api",
            allowed_hostname="evidence.example.com",
            access_token="offline-test-token", registry=registry,
            enabled=True, client=client,
        )
        result = adapter.fetch_and_certify(
            claims=(Claim("account", "ACC-1"), Claim("closing", "100.00"),
                    Claim("transaction", "T1:20.00")),
            scope=scope, effective_at=EFFECTIVE,
            decision_cutoff=CUTOFF, received_at=RECEIVED,
        )
    assert len(calls) == 1
    assert result["certificate"]["document_status"] == "MATCH_SUPPORTED"


@pytest.mark.parametrize("kind", ["unsigned", "redirect", "oversize", "duplicate"])
def test_transport_fail_closed_on_untrusted_or_malformed_response(fixture, kind):
    _, _, registry, scope, _, _, _, sign, _ = fixture
    def handle(_request):
        if kind == "redirect":
            return httpx.Response(302, headers={"location": "https://evil.example/a"})
        if kind == "oversize":
            return httpx.Response(
                200, content=b"X"*300000,
                headers={"content-type": "application/json"}
            )
        if kind == "duplicate":
            return httpx.Response(
                200, content=b'{"envelopes":[],"envelopes":[]}',
                headers={"content-type": "application/json"}
            )
        altered = sign()
        altered["payload"]["records"][0]["value"] = "tampered"
        return httpx.Response(200, json={"envelopes": [altered]})
    with httpx.Client(transport=httpx.MockTransport(handle)) as client:
        adapter = AuthorizedIssuerHTTPAdapter(
            endpoint="https://evidence.example.com/api",
            allowed_hostname="evidence.example.com",
            access_token="offline-test-token", registry=registry,
            enabled=True, client=client,
        )
        with pytest.raises(EvidenceRejected):
            adapter.fetch_and_certify(
                claims=(Claim("closing", "100.00"),), scope=scope,
                effective_at=EFFECTIVE, decision_cutoff=CUTOFF,
                received_at=RECEIVED,
            )
