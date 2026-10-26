"""Encrypted consent vault contract tests; no access to bank accounts or Plaid."""
from dataclasses import replace
from pathlib import Path
import secrets
import sqlite3

import pytest

from backend.services.eac_consent_vault import (
    AuthenticatedPrincipal, ConsentVault,
)
from backend.services.signed_issuer_evidence import EvidenceRejected


@pytest.fixture
def kit(tmp_path):
    key=secrets.token_bytes(32)
    path=tmp_path/"consent.sqlite3"
    vault=ConsentVault(str(path),key)
    p=AuthenticatedPrincipal("tenant-A","user-A",
                             frozenset({"plaid:connect","plaid:compare","plaid:revoke"}))
    return vault,p,path,key


def grant(vault,principal,account="account-A",item="item-A"):
    vault.grant_account(
        principal,item_id=item,account_id=account,
        consent_id="consent-A",access_token="access-sandbox-test-very-secret",
    )


def test_encrypted_token_never_persisted_as_plaintext(kit):
    vault,p,path,_=kit
    grant(vault,p)
    assert b"access-sandbox-test-very-secret" not in path.read_bytes()
    item=vault.access(p,item_id="item-A",account_id="account-A")
    assert item.access_token=="access-sandbox-test-very-secret"
    assert item.consent_id=="consent-A"
    assert path.stat().st_mode & 0o077 == 0


def test_token_survives_restart_with_same_key_not_wrong_key(kit):
    vault,p,path,key=kit
    grant(vault,p)
    again=ConsentVault(str(path),key)
    assert again.access(p,item_id="item-A",account_id="account-A").access_token.startswith("access-")
    wrong=ConsentVault(str(path),secrets.token_bytes(32))
    with pytest.raises(EvidenceRejected,match="integrity"):
        wrong.access(p,item_id="item-A",account_id="account-A")


def test_no_cross_tenant_user_or_account_read_or_revoke(kit):
    vault,p,path,key=kit
    grant(vault,p)
    outsiders=[
        replace(p,tenant_id="tenant-B"),
        replace(p,subject_id="user-B"),
        replace(p,scopes=frozenset({"plaid:connect"})),
    ]
    for outside in outsiders:
        with pytest.raises(EvidenceRejected):
            vault.access(outside,item_id="item-A",account_id="account-A")
    with pytest.raises(EvidenceRejected):
        vault.access(p,item_id="item-A",account_id="unconsented-account")
    assert vault.revoke(replace(p,tenant_id="tenant-B"),item_id="item-A")==0
    assert vault.access(p,item_id="item-A",account_id="account-A").access_token


def test_link_session_one_time_and_bound_to_same_principal(kit):
    vault,p,*_=kit
    state=vault.begin_link(p)
    outsider=replace(p,subject_id="attacker")
    with pytest.raises(EvidenceRejected):
        vault.consume_link(outsider,state)
    vault.consume_link(p,state)
    with pytest.raises(EvidenceRejected,match="not authorized"):
        vault.consume_link(p,state)


def test_expired_link_session_rejected(kit):
    vault,p,path,*_=kit
    state=vault.begin_link(p)
    import hashlib
    with sqlite3.connect(path) as con:
        con.execute("UPDATE sessions SET expires=0 WHERE state_hash=?",
                    (hashlib.sha256(state.encode()).hexdigest(),))
    with pytest.raises(EvidenceRejected):
        vault.consume_link(p,state)


def test_revocation_immediately_blocks_reads_but_keeps_remote_delete_secret(kit):
    vault,p,path,*_=kit
    grant(vault,p)
    assert vault.revoke(p,item_id="item-A")==1
    with pytest.raises(EvidenceRejected):
        vault.access(p,item_id="item-A",account_id="account-A")
    assert vault.pending_remote_removal(p,item_id="item-A")=="access-sandbox-test-very-secret"
    assert vault.confirm_remote_removal(p,item_id="item-A")==1
    with pytest.raises(EvidenceRejected,match="No pending"):
        vault.pending_remote_removal(p,item_id="item-A")
    assert b"access-sandbox-test-very-secret" not in path.read_bytes()


def test_revoked_account_cannot_be_silently_reactivated(kit):
    vault,p,*_=kit
    grant(vault,p)
    vault.revoke(p,item_id="item-A")
    with pytest.raises(EvidenceRejected,match="revoked"):
        grant(vault,p)


def test_one_token_can_be_bound_to_multiple_consented_accounts(kit):
    vault,p,*_=kit
    grant(vault,p,account="account-A")
    grant(vault,p,account="account-B")
    assert vault.revoke(p,item_id="item-A")==2
    assert vault.pending_remote_removal(p,item_id="item-A")=="access-sandbox-test-very-secret"
    assert vault.confirm_remote_removal(p,item_id="item-A")==2


def test_audit_contains_no_raw_item_identifiers_or_access_tokens(kit):
    vault,p,path,*_=kit
    grant(vault,p)
    with sqlite3.connect(path) as con:
        rows=con.execute("SELECT event,actor_digest,object_digest,epoch FROM audit").fetchall()
    assert rows
    assert all("tenant-A" not in str(row) and "item-A" not in str(row)
               and "access-" not in str(row) for row in rows)
    assert vault.prune(retention_days=30)>=0


def test_vault_symlink_and_missing_key_fail_closed(tmp_path):
    with pytest.raises(ValueError):
        ConsentVault(str(tmp_path/"vault.db"),b"too-short")
    existing=tmp_path/"real.sqlite"
    existing.write_bytes(b"")
    sym=tmp_path/"linked.sqlite"
    sym.symlink_to(existing)
    with pytest.raises(ValueError,match="Symlink"):
        ConsentVault(str(sym),secrets.token_bytes(32))
