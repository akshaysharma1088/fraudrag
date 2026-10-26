"""Trust-onboarding bootstrap for OPTIONAL server-side signed issuer adapter.

No issuer endpoint/keys/tokens are supplied by users or response documents.
Merely setting these variables does not establish a legal data agreement,
consent authorization, or the fact that a bank signs the custom EAC schema.

There is deliberately NO public HTTP endpoint for live source queries.
"""
from __future__ import annotations

import base64
import binascii

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

from backend.services.authorized_issuer_transport import AuthorizedIssuerHTTPAdapter
from backend.services.signed_issuer_evidence import EvidenceRejected, IssuerTrustRegistry


def build_partner_adapter(settings):
    """Fail closed on incomplete optional issuer integration configuration."""
    if not settings.EAC_PARTNER_ENABLED:
        return None
    required = {
        "EAC_PARTNER_ENDPOINT": settings.EAC_PARTNER_ENDPOINT,
        "EAC_PARTNER_HOST": settings.EAC_PARTNER_HOST,
        "EAC_PARTNER_ISSUER_ID": settings.EAC_PARTNER_ISSUER_ID,
        "EAC_PARTNER_KEY_ID": settings.EAC_PARTNER_KEY_ID,
        "EAC_PARTNER_PUBLIC_KEY_B64": settings.EAC_PARTNER_PUBLIC_KEY_B64,
        "EAC_PARTNER_ACCESS_TOKEN": settings.EAC_PARTNER_ACCESS_TOKEN,
    }
    missing = sorted(k for k, v in required.items() if not isinstance(v, str) or not v.strip())
    if missing:
        raise EvidenceRejected("Issuer adapter configuration incomplete: " + ", ".join(missing))
    try:
        encoded = settings.EAC_PARTNER_PUBLIC_KEY_B64
        if any(ch not in "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/" for ch in encoded.rstrip("=")):
            raise ValueError("Unexpected base64 characters")
        raw = base64.b64decode(encoded, validate=True)
        if len(raw) != 32:
            raise ValueError("Invalid Ed25519 public key length")
        key = Ed25519PublicKey.from_public_bytes(raw)
    except (ValueError, binascii.Error) as exc:
        raise EvidenceRejected("Invalid partner-pinned Ed25519 public key") from exc
    roots = IssuerTrustRegistry({
        settings.EAC_PARTNER_ISSUER_ID: {settings.EAC_PARTNER_KEY_ID: key}
    })
    return AuthorizedIssuerHTTPAdapter(
        endpoint=settings.EAC_PARTNER_ENDPOINT,
        allowed_hostname=settings.EAC_PARTNER_HOST,
        access_token=settings.EAC_PARTNER_ACCESS_TOKEN,
        registry=roots,
        enabled=True,
    )
