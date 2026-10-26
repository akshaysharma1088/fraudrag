"""Strict signed issuer-evidence ingestion, not yet connected to any bank.

A prospective issuer partner would sign EAC_RECORD_V1 with Ed25519.
The verification key must be provisioned OUT OF BAND through authorized
issuer onboarding, never via user uploads, HTTP response keys or kid URLs.
A valid signature proves possession of that pinned key, not document
authenticity, fact accuracy, legal consent or criminal fraud.

This is a versioned CANONICAL JSON signature protocol, NOT JWT/JWS/FDX.
"""
from __future__ import annotations

import base64
import hashlib
import json
from dataclasses import dataclass
from typing import Any, Mapping

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

from backend.services.eac_certificate import Claim, Reference, timestamp, verify

TYPE = "EAC_RECORD_V1"
ALGORITHM = "Ed25519"
MAX_ENVELOPE = 65536
MAX_RECORDS = 128
ALLOWED_CLAIM_KEYS = frozenset({"account", "closing", "transaction"})
PROTECTED_KEYS = frozenset({"alg", "typ", "kid"})
PAYLOAD_KEYS = frozenset({
    "iss", "aud", "tenant_id", "account_id", "consent_id",
    "issued_at", "expires_at", "records"
})
RECORD_KEYS = frozenset({
    "key", "value", "valid_from", "valid_until", "complete_for_field"
})


class EvidenceRejected(ValueError):
    """Fail closed on untrusted, unconsented or malformed source evidence."""


@dataclass(frozen=True)
class IssuerScope:
    issuer_id: str
    audience: str
    tenant_id: str
    account_id: str
    consent_id: str
    permission_authorized: bool = False


class IssuerTrustRegistry:
    """Configured from approved issuer public keys, never HTTP payload data."""

    def __init__(self, roots: Mapping[str, Mapping[str, Ed25519PublicKey]]):
        self._roots = {}
        for issuer, key_map in roots.items():
            if not issuer or not key_map:
                raise ValueError("Issuer and pinned public key required")
            self._roots[issuer] = {}
            for kid, public_key in key_map.items():
                if not isinstance(public_key, Ed25519PublicKey) or not kid:
                    raise ValueError("Only pinned Ed25519 issuer public keys supported")
                self._roots[issuer][kid] = public_key

    def lookup(self, issuer: str, kid: str) -> Ed25519PublicKey:
        try:
            return self._roots[issuer][kid]
        except KeyError as exc:
            raise EvidenceRejected("Issuer signing key not independently trusted") from exc


def canonical(value: Any) -> bytes:
    """Deterministic UTF-8 serialization; custom protocol, not RFC 8785."""
    try:
        return json.dumps(
            value, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError, UnicodeError) as exc:
        raise EvidenceRejected("Noncanonical evidence payload") from exc


def decode_signature(value: str) -> bytes:
    if not isinstance(value, str) or len(value) != 86:
        raise EvidenceRejected("Expected an Ed25519 base64url signature")
    if any(c not in "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_" for c in value):
        raise EvidenceRejected("Invalid base64url signature")
    try:
        raw = base64.urlsafe_b64decode(value + "==")
    except Exception as exc:
        raise EvidenceRejected("Malformed signature encoding") from exc
    if len(raw) != 64 or base64.urlsafe_b64encode(raw).rstrip(b"=").decode() != value:
        raise EvidenceRejected("Noncanonical Ed25519 signature")
    return raw


def _exact_fields(obj: Any, keys: frozenset[str], name: str) -> dict:
    if not isinstance(obj, dict) or set(obj) != keys:
        raise EvidenceRejected(f"{name}: missing or unexpected fields")
    return obj


def _text(value: Any, name: str, max_len: int = 256) -> str:
    if not isinstance(value, str) or not 0 < len(value) <= max_len or any(ord(c) < 32 for c in value):
        raise EvidenceRejected(f"Invalid {name}")
    return value


def verify_signed_envelope(
    envelope: Mapping[str, Any],
    *,
    registry: IssuerTrustRegistry,
    scope: IssuerScope,
    received_at: str,
    effective_at: str,
    decision_cutoff: str,
) -> tuple[Reference, ...]:
    """Validate a signature and turn signed fields into admissible references.

    The caller MUST independently authorize tenant/account/consent and use
    the local server ingestion timestamp as received_at; never user input.
    """
    if not scope.permission_authorized:
        raise EvidenceRejected("Account consent and caller authorization not established")
    for name in ("issuer_id", "audience", "tenant_id", "account_id", "consent_id"):
        _text(getattr(scope, name), name)
    _exact_fields(envelope, frozenset({"protected", "payload", "signature"}), "envelope")
    header = _exact_fields(envelope["protected"], PROTECTED_KEYS, "protected")
    payload = _exact_fields(envelope["payload"], PAYLOAD_KEYS, "payload")
    _text(header["kid"], "kid")
    if header["alg"] != ALGORITHM or header["typ"] != TYPE:
        raise EvidenceRejected("Unsupported issuer evidence signature type or algorithm")
    if len(canonical(envelope)) > MAX_ENVELOPE:
        raise EvidenceRejected("Signed payload exceeds safety limit")
    for key, expected in (
        ("iss", scope.issuer_id),
        ("aud", scope.audience),
        ("tenant_id", scope.tenant_id),
        ("account_id", scope.account_id),
        ("consent_id", scope.consent_id),
    ):
        if payload[key] != expected:
            raise EvidenceRejected(f"Signed evidence {key} not bound to authorized context")
    public_key = registry.lookup(scope.issuer_id, header["kid"])
    signed_data = canonical({"protected": header, "payload": payload})
    try:
        public_key.verify(decode_signature(envelope["signature"]), signed_data)
    except InvalidSignature as exc:
        raise EvidenceRejected("Issuer signature verification failed") from exc

    received = timestamp(received_at)
    effective = timestamp(effective_at)
    cutoff = timestamp(decision_cutoff)
    issued = timestamp(payload["issued_at"])
    expires = timestamp(payload["expires_at"])
    if not (effective <= cutoff and issued <= received <= cutoff
            and issued < expires and received < expires):
        raise EvidenceRejected("Signed source not available or expired at decision time")
    records = payload["records"]
    if not isinstance(records, list) or not 0 < len(records) <= MAX_RECORDS:
        raise EvidenceRejected("Expected bounded nonempty issuer evidence records")
    digest = hashlib.sha256(signed_data).hexdigest()
    result = []
    seen = set()
    for row in records:
        _exact_fields(row, RECORD_KEYS, "record")
        key = _text(row["key"], "record.key")
        if key not in ALLOWED_CLAIM_KEYS or key in seen:
            raise EvidenceRejected("Unexpected or duplicate issuer field claim")
        seen.add(key)
        value = _text(row["value"], "record.value", max_len=4096)
        if not isinstance(row["complete_for_field"], bool):
            raise EvidenceRejected("Completeness must be an explicit signed boolean")
        start = timestamp(row["valid_from"])
        end = timestamp(row["valid_until"])
        if not (start < end and start <= effective < end):
            raise EvidenceRejected("Field outside signed validity interval")
        result.append(Reference(
            source_id=f"issuer-signed://{scope.issuer_id}/{header['kid']}/{digest}/{key}",
            source_family=f"issuer:{scope.issuer_id}",
            key=key, value=value,
            valid_from=start.isoformat(), valid_until=end.isoformat(),
            recorded_at=issued.isoformat(), ingested_at=received.isoformat(),
            issuer_attested=True,
            completeness_attested_for_key=row["complete_for_field"],
            source_digest_sha256=digest,
        ))
    return tuple(result)


def certify_signed_sources(
    claims: tuple[Claim, ...],
    envelopes: tuple[Mapping[str, Any], ...],
    *,
    registry: IssuerTrustRegistry,
    scope: IssuerScope,
    received_at: str,
    effective_at: str,
    decision_cutoff: str,
) -> dict:
    """Reject entire batch if ANY source fails signature or scope validation."""
    if not envelopes or len(envelopes) > 16:
        raise EvidenceRejected("Expected 1 to 16 signed issuer responses")
    refs = tuple(
        ref for envelope in envelopes
        for ref in verify_signed_envelope(
            envelope, registry=registry, scope=scope,
            received_at=received_at, effective_at=effective_at,
            decision_cutoff=decision_cutoff,
        )
    )
    if len(refs) > MAX_RECORDS:
        raise EvidenceRejected("Too many issuer field records")
    certificate = verify(claims, refs, effective_at=effective_at,
                         as_of_cutoff=decision_cutoff)
    return {
        "mode": "pinned_ed25519_signed_issuer_fields",
        "source_attestation": "cryptographic_signature_verified_against_server_pinned_public_key",
        "issuer_identity_binding": "external partner onboarding still required",
        "tenant_account_consent_binding": "requires independently authorized server context",
        "signed_envelopes_verified": len(envelopes),
        "signed_field_records": len(refs),
        "certificate": certificate,
        "limits": (
            "A signature does not prove transaction truth, user authorization, "
            "legal fraud or entire-statement completeness. The inner certificate "
            "checker is non-cryptographic; validation is enforced by this wrapper."
        ),
    }
