"""Server-owned Plaid Statements consent onboarding and comparison orchestrator.

No API route exposes these methods: they require a real authenticated user,
pre-approved Plaid access, secure operator key storage and an external bank
consent event. The frontend must never directly provide AuthenticatedPrincipal
or Plaid access tokens to these services.

Plaid Link creation can cause per-Item charges when the customer finishes
Link. Explicit user intent and operator billing controls are mandatory.
"""
from __future__ import annotations

import hashlib
import hmac
import secrets

from backend.services.eac_consent_vault import (
    AuthenticatedPrincipal, ConsentVault, require,
)
from backend.services.plaid_link_client import PlaidLinkClient
from backend.services.plaid_statements_provider import (
    PlaidAuthorizedItem, PlaidStatementsProvider
)
from backend.services.signed_issuer_evidence import EvidenceRejected


class PlaidConsentWorkflow:
    def __init__(self, *, vault: ConsentVault,
                 link: PlaidLinkClient,
                 statements: PlaidStatementsProvider):
        if link.environment != statements.environment:
            raise EvidenceRejected("Plaid Link and Statements environments must match")
        self.vault = vault
        self.link = link
        self.statements = statements

    def start(self, *, principal: AuthenticatedPrincipal,
              start_date: str, end_date: str,
              user_approved_potential_charge: bool) -> dict:
        """Initiate Link only after an explicit, authenticated user action."""
        require(principal, "plaid:connect")
        if not user_approved_potential_charge:
            raise EvidenceRejected("Explicit consent and potential Statements billing acknowledgment required")
        # Pseudonymous subject sent to Plaid, not raw internal user ID.
        opaque = hmac.new(
            self.vault.key,
            (principal.tenant_id+"\x1f"+principal.subject_id).encode(),
            hashlib.sha256,
        ).hexdigest()
        state = self.vault.begin_link(principal)
        token = self.link.create_link_token(
            subject_key="fraudrag-"+opaque,
            start_date=start_date,
            end_date=end_date,
            allow_billable_item=True,
        )
        return {
            "link_token": token,
            "one_time_completion_state": state,
            "statements_product_requested": True,
            "may_create_billable_item_in_production": True,
            "no_bank_credentials_collected_by_fraudrag": True,
        }

    def complete(self, *, principal: AuthenticatedPrincipal,
                 one_time_completion_state: str,
                 public_token: str, selected_account_id: str) -> dict:
        """Validate one-use state and account ownership before encrypting token."""
        require(principal, "plaid:connect")
        self.vault.consume_link(principal, one_time_completion_state)
        item_id, token = self.link.exchange_public_token(public_token)
        # The account_id is untrusted until matched to the list for this Item.
        pending = PlaidAuthorizedItem(
            tenant_id=principal.tenant_id, consent_id="pending-link",
            item_id=item_id, account_id="pending-selection",
            access_token=token, permission_authorized=True,
        )
        try:
            account_ids = self.statements.discover_account_ids(pending)
            if selected_account_id not in account_ids:
                raise EvidenceRejected("User-selected account not available under newly authorized Plaid Item")
            consent_id=secrets.token_urlsafe(24)
            self.vault.grant_account(
                principal,item_id=item_id,account_id=selected_account_id,
                consent_id=consent_id,access_token=token
            )
        except Exception:
            # Upstream public-token exchange may already have created a
            # billable Item. Do not silently lose the only delete credential.
            try:
                self.link.remove_item(token)
            except Exception:
                self.vault.stage_remote_removal(
                    principal,item_id=item_id,access_token=token
                )
            raise
        return {
            "item_id":item_id,
            "account_id":selected_account_id,
            "consent_id":consent_id,
            "vault_encrypted_token":True,
            "plaid_token_exposed_in_response":False,
        }

    def compare(self, *, principal: AuthenticatedPrincipal,
                item_id: str, account_id: str, statement_id: str,
                submitted_pdf: bytes) -> dict:
        """Only compares a PDF with consented account's Plaid original."""
        grant=self.vault.access(principal,item_id=item_id,account_id=account_id)
        item=PlaidAuthorizedItem(
            tenant_id=principal.tenant_id,consent_id=grant.consent_id,
            item_id=grant.item_id,account_id=grant.account_id,
            access_token=grant.access_token,permission_authorized=True,
        )
        # Compare hashes in memory; never persist downloaded/source PDF.
        return self.statements.compare_with_original(
            item=item,statement_id=statement_id,uploaded_pdf=submitted_pdf
        )

    def retry_pending_removal(self, *, principal:AuthenticatedPrincipal,
                              item_id:str) -> dict:
        """Operator/user-authorized retry; never a scheduled background promise."""
        require(principal,"plaid:revoke")
        token=self.vault.pending_remote_removal(principal,item_id=item_id)
        self.link.remove_item(token)
        wiped=self.vault.confirm_remote_removal(principal,item_id=item_id)
        return {"remote_item_removed":True,"encrypted_token_records_cleared":wiped}

    def revoke(self, *, principal: AuthenticatedPrincipal,
               item_id: str) -> dict:
        """Immediate local revoke and best-effort confirmed remote removal.

        Retain encrypted token only while remote removal is pending so that
        a controlled server revocation worker can retry without client data.
        """
        changes=self.vault.revoke(principal,item_id=item_id)
        if changes == 0:
            # Fail closed if this principal never had the Item; still allow
            # a retry for an already locally revoked Item awaiting cleanup.
            self.vault.pending_remote_removal(principal,item_id=item_id)
        try:
            token=self.vault.pending_remote_removal(principal,item_id=item_id)
            self.link.remove_item(token)
            cleared=self.vault.confirm_remote_removal(principal,item_id=item_id)
            return {"local_access_revoked":True,"remote_item_removed":True,
                    "encrypted_token_records_cleared":cleared}
        except EvidenceRejected:
            # A real revocation queue/alert should retry; never reauthorize.
            return {"local_access_revoked":True,"remote_item_removed":False,
                    "retry_required":True}
