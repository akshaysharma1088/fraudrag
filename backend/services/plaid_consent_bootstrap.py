"""Operator-only Plaid consent workflow composition. Default off.

The master key and Plaid credentials are loaded by server secret management.
No user or Item credentials are accepted from browser settings or logs.
Single-node SQLite vault is a staging backend, not approved hosted production
tenancy; use dedicated database + KMS/retention compliance for production.
"""
import base64
import binascii

from backend.services.eac_consent_vault import ConsentVault
from backend.services.plaid_link_client import PlaidLinkClient
from backend.services.plaid_partner_bootstrap import build_plaid_statements_provider
from backend.services.plaid_consent_workflow import PlaidConsentWorkflow
from backend.services.signed_issuer_evidence import EvidenceRejected


def build_plaid_consent_workflow(settings):
    if not settings.EAC_PLAID_LINK_ENABLED:
        return None
    if not settings.EAC_PLAID_ENABLED:
        raise EvidenceRejected("Cannot allow Plaid onboarding without Plaid Statements provider enabled")
    for field in ("EAC_PLAID_VAULT_PATH", "EAC_PLAID_VAULT_KEY_B64"):
        value=getattr(settings, field, None)
        if not isinstance(value,str) or not value:
            raise EvidenceRejected("Server secret configuration missing: "+field)
    try:
        secret=base64.b64decode(settings.EAC_PLAID_VAULT_KEY_B64,validate=True)
        if len(secret)!=32:
            raise ValueError("Not 32 bytes")
    except (binascii.Error,ValueError) as exc:
        raise EvidenceRejected("Vault AES-256 master key invalid") from exc
    provider=build_plaid_statements_provider(settings)
    client=PlaidLinkClient(
        environment=settings.EAC_PLAID_ENVIRONMENT,
        client_id=settings.EAC_PLAID_CLIENT_ID,
        secret=settings.EAC_PLAID_SECRET,
        enabled=True,
    )
    vault=ConsentVault(settings.EAC_PLAID_VAULT_PATH,secret)
    return PlaidConsentWorkflow(vault=vault,link=client,statements=provider)
