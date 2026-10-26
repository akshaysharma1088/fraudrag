"""Consent workflow composition stays disabled until operator secrets provided."""
import base64
import secrets
from types import SimpleNamespace

import pytest

from backend.services.plaid_consent_bootstrap import build_plaid_consent_workflow
from backend.services.signed_issuer_evidence import EvidenceRejected


def settings(tmp_path, **kwargs):
    d=dict(
        EAC_PLAID_LINK_ENABLED=False,
        EAC_PLAID_ENABLED=True,
        EAC_PLAID_ENVIRONMENT="sandbox",
        EAC_PLAID_CLIENT_ID="offline-client-id",
        EAC_PLAID_SECRET="offline-client-secret",
        EAC_PLAID_VAULT_PATH=str(tmp_path/"vault.db"),
        EAC_PLAID_VAULT_KEY_B64=base64.b64encode(secrets.token_bytes(32)).decode()
    )
    d.update(kwargs)
    return SimpleNamespace(**d)


def test_link_workflow_off_by_default(tmp_path):
    assert build_plaid_consent_workflow(settings(tmp_path)) is None


def test_link_workflow_wires_with_synthetic_configuration_without_network(tmp_path):
    flow=build_plaid_consent_workflow(settings(tmp_path,EAC_PLAID_LINK_ENABLED=True))
    assert flow.link.environment=="sandbox"
    assert flow.statements.environment=="sandbox"
    assert flow.vault.path.endswith("vault.db")


@pytest.mark.parametrize("bad",[
    {"EAC_PLAID_ENABLED":False},
    {"EAC_PLAID_VAULT_KEY_B64":""},
    {"EAC_PLAID_VAULT_KEY_B64":"abc"},
    {"EAC_PLAID_VAULT_PATH":None},
    {"EAC_PLAID_ENVIRONMENT":"http://localhost"},
    {"EAC_PLAID_SECRET":""},
])
def test_incomplete_secrets_do_not_activate_onboarding(tmp_path,bad):
    with pytest.raises((EvidenceRejected,ValueError)):
        build_plaid_consent_workflow(
            settings(tmp_path,EAC_PLAID_LINK_ENABLED=True,**bad)
        )
