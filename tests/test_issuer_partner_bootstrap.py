"""Partner integration is disabled until trusted operator onboarding is complete."""
import base64
from types import SimpleNamespace

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from backend.services.issuer_partner_bootstrap import build_partner_adapter
from backend.services.signed_issuer_evidence import EvidenceRejected


def partner_config(**overrides):
    key = Ed25519PrivateKey.generate().public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    defaults = dict(
        EAC_PARTNER_ENABLED=False,
        EAC_PARTNER_ENDPOINT="https://partner.example.com/eac/evidence",
        EAC_PARTNER_HOST="partner.example.com",
        EAC_PARTNER_ISSUER_ID="fictional-partner-test",
        EAC_PARTNER_KEY_ID="kid-2026",
        EAC_PARTNER_PUBLIC_KEY_B64=base64.b64encode(key).decode(),
        EAC_PARTNER_ACCESS_TOKEN="server-only-offline-fixture-token",
    )
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


def test_partner_adapter_disabled_by_default():
    assert build_partner_adapter(partner_config()) is None


def test_bootstrap_accepts_offline_signed_provider_configuration_but_does_not_connect():
    adapter = build_partner_adapter(partner_config(EAC_PARTNER_ENABLED=True))
    assert adapter.enabled is True
    assert adapter.endpoint == "https://partner.example.com/eac/evidence"


@pytest.mark.parametrize("bad", [
    {"EAC_PARTNER_ENDPOINT": ""},
    {"EAC_PARTNER_HOST": None},
    {"EAC_PARTNER_ACCESS_TOKEN": ""},
    {"EAC_PARTNER_PUBLIC_KEY_B64": "abc"},
    {"EAC_PARTNER_PUBLIC_KEY_B64": "@@@not-base64@@@"},
    {"EAC_PARTNER_ENDPOINT": "http://partner.example.com/eac/evidence"},
    {"EAC_PARTNER_ENDPOINT": "https://localhost/bank"},
    {"EAC_PARTNER_ENDPOINT": "https://evil.example/eac/evidence"},
])
def test_incomplete_or_unsafe_live_partner_configuration_fails_closed(bad):
    with pytest.raises(EvidenceRejected):
        build_partner_adapter(partner_config(EAC_PARTNER_ENABLED=True, **bad))


def test_no_partner_API_route_is_implicitly_added():
    from backend.main import create_app
    app = create_app(testing=True)
    live = [
        getattr(route, "path", "")
        for route in app.routes
        if "/api/v1/eac" in getattr(route, "path", "")
        and "/demo/" not in route.path
    ]
    assert live == []
