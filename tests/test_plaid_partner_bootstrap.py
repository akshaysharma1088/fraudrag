"""Plaid Statements integration must be explicitly enabled with server secrets.

No bank link is automatically created and no Item access token is configured
at app level; per-user consent authorization must remain separate.
"""
from types import SimpleNamespace

import pytest

from backend.services.plaid_partner_bootstrap import build_plaid_statements_provider
from backend.services.signed_issuer_evidence import EvidenceRejected


def config(**changes):
    data = dict(
        EAC_PLAID_ENABLED=False,
        EAC_PLAID_ENVIRONMENT="sandbox",
        EAC_PLAID_CLIENT_ID="offline-test-client",
        EAC_PLAID_SECRET="offline-test-secret",
    )
    data.update(changes)
    return SimpleNamespace(**data)


def test_no_plaid_connector_until_opted_in():
    assert build_plaid_statements_provider(config()) is None


def test_plaid_sandbox_can_be_instantiated_without_any_api_calls():
    provider=build_plaid_statements_provider(config(EAC_PLAID_ENABLED=True))
    assert provider.enabled
    assert provider.endpoint=="https://sandbox.plaid.com"


@pytest.mark.parametrize("changes",[
    {"EAC_PLAID_CLIENT_ID":""},
    {"EAC_PLAID_SECRET":None},
    {"EAC_PLAID_ENVIRONMENT":"development"},
    {"EAC_PLAID_ENVIRONMENT":"http://evil.example"},
])
def test_unsafe_plaid_config_fails_closed(changes):
    with pytest.raises(EvidenceRejected):
        build_plaid_statements_provider(config(EAC_PLAID_ENABLED=True,**changes))
