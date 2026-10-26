"""Server-to-server adapter for an approved signed-evidence issuer endpoint.

Transport is deliberately DISABLED until an authorized provider, OAuth token,
independently onboarded issuer public key, per-tenant consent system and egress
allowlist are provisioned. No EAC live route exposes this client to browsers.

This is an INTEGRATION CONTRACT, not Plaid/FDX compliance. Upstream must
implement the versioned EAC_RECORD_V1 response signature explicitly.
"""
from __future__ import annotations

import ipaddress
import json
from datetime import datetime, timezone
from urllib.parse import urlsplit

import httpx

from backend.services.eac_certificate import Claim
from backend.services.signed_issuer_evidence import (
    EvidenceRejected, IssuerScope, IssuerTrustRegistry, certify_signed_sources
)

MAX_RESPONSE_BYTES = 256 * 1024
MAX_SOURCE_ENVELOPES = 16


def _approved_endpoint(endpoint: str, hostname: str) -> str:
    """Reject browser-selected hosts, IP addresses, redirects and URL tricks."""
    if not isinstance(endpoint, str) or not isinstance(hostname, str):
        raise EvidenceRejected("Issuer host must be provisioned out of band")
    parsed = urlsplit(endpoint)
    if parsed.scheme != "https" or parsed.username or parsed.password:
        raise EvidenceRejected("Issuer transport requires a fixed HTTPS origin")
    if parsed.fragment or parsed.query or not parsed.path.startswith("/"):
        raise EvidenceRejected("Unsupported issuer endpoint URL")
    if parsed.port not in (None, 443):
        raise EvidenceRejected("Only the standard HTTPS port is allowed")
    host = parsed.hostname
    if not host or host != hostname.lower() or not host.isascii():
        raise EvidenceRejected("Issuer endpoint not in the configured allowlist")
    if host in ("localhost",) or host.endswith((".local", ".internal", ".localhost")):
        raise EvidenceRejected("Private/local issuer host prohibited")
    try:
        ipaddress.ip_address(host)
    except ValueError:
        pass
    else:
        raise EvidenceRejected("IP-address issuer endpoint prohibited")
    if host.count(".") < 1:
        raise EvidenceRejected("Issuer host must be a DNS name")
    return endpoint


def _reject_duplicate_json_keys(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise EvidenceRejected("Duplicate issuer JSON object key")
        result[key] = value
    return result


class AuthorizedIssuerHTTPAdapter:
    """No user-controlled URL, no password logging, no credential generation.

    The caller supplies a server-validated IssuerScope and a server-managed
    OAuth access token. Constructor defaults disabled. An independent egress
    firewall/DNS pinning is still required for production SSRF defense.
    """

    def __init__(
        self, *, endpoint: str, allowed_hostname: str,
        access_token: str, registry: IssuerTrustRegistry,
        enabled: bool = False,
        client: httpx.Client | None = None,
    ):
        self.enabled = enabled
        self.endpoint = _approved_endpoint(endpoint, allowed_hostname)
        if not isinstance(access_token, str) or len(access_token) < 12:
            raise EvidenceRejected("Provider must have a server-managed access token")
        self._token = access_token
        self._registry = registry
        self._client = client

    def fetch_and_certify(
        self, *, claims: tuple[Claim, ...], scope: IssuerScope,
        effective_at: str, decision_cutoff: str,
        received_at: str | None = None,
    ) -> dict:
        if not self.enabled:
            raise EvidenceRejected("Signed issuer provider integration disabled")
        if not scope.permission_authorized:
            raise EvidenceRejected("Issuer consent and caller authentication required")
        received_at = received_at or datetime.now(timezone.utc).isoformat()
        # Call site MUST omit received_at when using a live provider. Parameter
        # is only for deterministically testing the transport with a fake clock.
        request = {
            "tenant_id": scope.tenant_id,
            "account_id": scope.account_id,
            "consent_id": scope.consent_id,
            "fields": [c.key for c in claims],
        }
        owned = self._client is None
        client = self._client or httpx.Client(
            timeout=httpx.Timeout(5.0, connect=3.0),
            follow_redirects=False, trust_env=False,
        )
        try:
            try:
                with client.stream(
                    "POST", self.endpoint,
                    headers={
                        "Authorization": f"Bearer {self._token}",
                        "Accept": "application/json",
                    },
                    json=request,
                    follow_redirects=False,
                ) as response:
                    if response.status_code != 200:
                        raise EvidenceRejected("Issuer request failed or redirected")
                    if "application/json" not in response.headers.get("content-type", "").lower():
                        raise EvidenceRejected("Issuer returned wrong content type")
                    content = bytearray()
                    for part in response.iter_bytes():
                        if len(content) + len(part) > MAX_RESPONSE_BYTES:
                            raise EvidenceRejected("Issuer response too large")
                        content.extend(part)
                data = json.loads(
                    content.decode("utf-8"),
                    object_pairs_hook=_reject_duplicate_json_keys
                )
            except (httpx.HTTPError, UnicodeDecodeError, json.JSONDecodeError) as exc:
                raise EvidenceRejected("Issuer connection or response validation failed") from exc
        finally:
            if owned:
                client.close()
        if not isinstance(data, dict) or set(data) != {"envelopes"}:
            raise EvidenceRejected("Issuer must return only signed envelope list")
        envelopes = data["envelopes"]
        if not isinstance(envelopes, list) or not 0 < len(envelopes) <= MAX_SOURCE_ENVELOPES:
            raise EvidenceRejected("Invalid number of signed issuer envelopes")
        return certify_signed_sources(
            claims, tuple(envelopes),
            registry=self._registry, scope=scope,
            received_at=received_at, effective_at=effective_at,
            decision_cutoff=decision_cutoff,
        )
