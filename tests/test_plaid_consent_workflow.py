"""End-to-end offline Plaid Link, consent vault and statement comparison.

Uses in-memory fake provider; no Plaid credentials, external API, paid
Items, issuer statements or actual customer financial information.
"""
from dataclasses import replace
import secrets

import pytest

from backend.services.eac_consent_vault import (
    AuthenticatedPrincipal, ConsentVault,
)
from backend.services.plaid_consent_workflow import PlaidConsentWorkflow
from backend.services.signed_issuer_evidence import EvidenceRejected


class FakeLink:
    environment="sandbox"
    def __init__(self):
        self.calls=[]
        self.fail_remote=False

    def create_link_token(self, **kwargs):
        self.calls.append(("create",kwargs))
        if not kwargs["allow_billable_item"]:
            raise AssertionError("User approval not enforced")
        return "link-sandbox-test-id"

    def exchange_public_token(self, public_token):
        self.calls.append(("exchange",public_token))
        if public_token!="public-sandbox-test":
            raise EvidenceRejected("Bad public token")
        return "item-test-1","access-sandbox-secret-token"

    def remove_item(self,token):
        self.calls.append(("remove",token))
        if self.fail_remote:
            raise EvidenceRejected("Network error on remote Item deletion")
        return True


class FakeProvider:
    environment="sandbox"
    def __init__(self):
        self.calls=[]
        self.allowed=("account-1","account-2")

    def discover_account_ids(self,item):
        self.calls.append(("discover",item.item_id))
        assert item.access_token=="access-sandbox-secret-token"
        return list(self.allowed)

    def compare_with_original(self,*,item,statement_id,uploaded_pdf):
        self.calls.append(("compare",item.item_id,item.account_id,statement_id))
        return {
            "result":"EXACT_PDF_BYTES_MATCH",
            "plaid_content_sha256_verified":True,
            "no_actual_issuer":True,
        }


@pytest.fixture
def rig(tmp_path):
    vault=ConsentVault(str(tmp_path/"vault.db"),secrets.token_bytes(32))
    principal=AuthenticatedPrincipal("tenant-1","user-1",
        frozenset({"plaid:connect","plaid:compare","plaid:revoke"}))
    link=FakeLink()
    provider=FakeProvider()
    return PlaidConsentWorkflow(vault=vault,link=link,statements=provider),principal,link,provider


def onboard(flow,p, account="account-1"):
    start=flow.start(
        principal=p,start_date="2026-01-01",end_date="2026-09-01",
        user_approved_potential_charge=True,
    )
    result=flow.complete(
        principal=p,one_time_completion_state=start["one_time_completion_state"],
        public_token="public-sandbox-test",selected_account_id=account,
    )
    return start,result


def test_complete_explicitly_consented_item_and_comparison(rig):
    flow,p,link,provider=rig
    begin,result=onboard(flow,p)
    assert begin["may_create_billable_item_in_production"]
    assert begin["link_token"].startswith("link-")
    assert "access_token" not in str(result)
    assert result["vault_encrypted_token"]
    result=flow.compare(
        principal=p,item_id="item-test-1",account_id="account-1",
        statement_id="statement-test",submitted_pdf=b"%PDF-1.4 x",
    )
    assert result["result"]=="EXACT_PDF_BYTES_MATCH"
    assert [x[0] for x in link.calls]==["create","exchange"]
    assert provider.calls[-1][0]=="compare"


def test_no_approval_no_link_or_vault_access(rig):
    flow,p,link,provider=rig
    with pytest.raises(EvidenceRejected,match="acknowledgment"):
        flow.start(
            principal=p,start_date="2026-01-01",end_date="2026-09-01",
            user_approved_potential_charge=False,
        )
    assert link.calls == []


def test_untrusted_account_selection_does_not_create_consent_grant(rig):
    flow,p,link,provider=rig
    start=flow.start(
        principal=p,start_date="2026-01-01",end_date="2026-09-01",
        user_approved_potential_charge=True,
    )
    with pytest.raises(EvidenceRejected,match="not available"):
        flow.complete(
            principal=p,one_time_completion_state=start["one_time_completion_state"],
            public_token="public-sandbox-test",
            selected_account_id="outside-account",
        )
    assert link.calls[-1][0]=="remove"
    with pytest.raises(EvidenceRejected):
        flow.compare(principal=p,item_id="item-test-1",
                     account_id="outside-account",statement_id="a",
                     submitted_pdf=b"ignored")


def test_session_replay_or_different_user_cannot_exchange_twice(rig):
    flow,p,link,provider=rig
    start,result=onboard(flow,p)
    with pytest.raises(EvidenceRejected):
        flow.complete(
            principal=p,
            one_time_completion_state=start["one_time_completion_state"],
            public_token="public-sandbox-test",
            selected_account_id="account-2",
        )
    assert len([x for x in link.calls if x[0]=="exchange"])==1


def test_foreign_tenant_cannot_compare_or_revoke_another_users_item(rig):
    flow,p,link,provider=rig
    onboard(flow,p)
    outsider=replace(p,tenant_id="another-tenant")
    with pytest.raises(EvidenceRejected):
        flow.compare(principal=outsider,item_id="item-test-1",account_id="account-1",
                     statement_id="statement-1",submitted_pdf=b"%PDF x")
    assert flow.vault.revoke(outsider,item_id="item-test-1")==0
    assert flow.compare(principal=p,item_id="item-test-1",
                        account_id="account-1",statement_id="statement-1",
                        submitted_pdf=b"%PDF x")["result"]=="EXACT_PDF_BYTES_MATCH"


def test_revocation_removes_local_and_remote_access(rig):
    flow,p,link,provider=rig
    onboard(flow,p)
    revoked=flow.revoke(principal=p,item_id="item-test-1")
    assert revoked["local_access_revoked"] is True
    assert revoked["remote_item_removed"] is True
    assert revoked["encrypted_token_records_cleared"]==1
    assert link.calls[-1][0]=="remove"
    with pytest.raises(EvidenceRejected):
        flow.compare(principal=p,item_id="item-test-1",account_id="account-1",
                     statement_id="a",submitted_pdf=b"%PDF x")


def test_revocation_remote_fail_preserves_offline_retry_and_denies_local_reads(rig):
    flow,p,link,provider=rig
    onboard(flow,p)
    link.fail_remote=True
    revoked=flow.revoke(principal=p,item_id="item-test-1")
    assert revoked["local_access_revoked"] is True
    assert revoked["remote_item_removed"] is False
    assert revoked["retry_required"] is True
    with pytest.raises(EvidenceRejected):
        flow.compare(principal=p,item_id="item-test-1",account_id="account-1",
                     statement_id="a",submitted_pdf=b"%PDF x")
    assert flow.vault.pending_remote_removal(p,item_id="item-test-1").startswith("access-")
    link.fail_remote=False
    second=flow.revoke(principal=p,item_id="item-test-1")
    assert second["remote_item_removed"] is True


def test_failed_onboarding_remote_cleanup_is_recoverable_without_bank_access(rig):
    flow,p,link,provider=rig
    link.fail_remote=True
    session=flow.start(
        principal=p,start_date="2026-01-01",end_date="2026-09-01",
        user_approved_potential_charge=True,
    )
    with pytest.raises(EvidenceRejected,match="not available"):
        flow.complete(
            principal=p,one_time_completion_state=session["one_time_completion_state"],
            public_token="public-sandbox-test", selected_account_id="outsider-account"
        )
    with pytest.raises(EvidenceRejected):
        flow.compare(principal=p,item_id="item-test-1",account_id="account-1",
                     statement_id="a",submitted_pdf=b"%PDF-1.4 x")
    assert flow.vault.pending_remote_removal(p,item_id="item-test-1")=="access-sandbox-secret-token"
    link.fail_remote=False
    result=flow.retry_pending_removal(principal=p,item_id="item-test-1")
    assert result["remote_item_removed"] is True
    with pytest.raises(EvidenceRejected,match="No pending"):
        flow.vault.pending_remote_removal(p,item_id="item-test-1")
