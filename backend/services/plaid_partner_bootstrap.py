"""Opt-in Plaid Statements client bootstrap for a future authorized tenant service.

Only app-level Plaid client credentials may be configured here; per-user
access_token is NEVER an environment setting. It must be obtained and bound
to a particular logged-in user, consent and Item in an approved token vault.
No real-data API endpoints or Plaid Link creation are exposed by this module.
"""
from backend.services.plaid_statements_provider import PlaidStatementsProvider
from backend.services.signed_issuer_evidence import EvidenceRejected


def build_plaid_statements_provider(settings):
    if not settings.EAC_PLAID_ENABLED:
        return None
    if not settings.EAC_PLAID_CLIENT_ID or not settings.EAC_PLAID_SECRET:
        raise EvidenceRejected("Plaid server application credentials missing")
    return PlaidStatementsProvider(
        environment=settings.EAC_PLAID_ENVIRONMENT,
        client_id=settings.EAC_PLAID_CLIENT_ID,
        secret=settings.EAC_PLAID_SECRET,
        enabled=True,
    )
