"""Encrypted, scoped Plaid Item consent vault for authorized server workflows.

This is a standalone reusable service, NOT a substitute for user login,
legal consent, hosted KMS or a production compliance review. The calling
service MUST supply an AuthenticatedPrincipal verified by its auth middleware,
not construct one from browser JSON. No HTTP endpoints currently use it.

SQLite is intended for single-host development and integration tests; migrate
to encrypted managed PostgreSQL + KMS and RBAC before multi-instance production.
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import os
import secrets
import sqlite3
import time
from dataclasses import dataclass
from contextlib import contextmanager
from pathlib import Path

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from backend.services.signed_issuer_evidence import EvidenceRejected


@dataclass(frozen=True)
class AuthenticatedPrincipal:
    tenant_id: str
    subject_id: str
    scopes: frozenset[str]


@dataclass(frozen=True)
class AuthorizedItem:
    item_id: str
    account_id: str
    consent_id: str
    access_token: str


def require(principal: AuthenticatedPrincipal, permission: str) -> None:
    if not isinstance(principal, AuthenticatedPrincipal):
        raise EvidenceRejected("Authenticated server principal required")
    if not principal.tenant_id or not principal.subject_id:
        raise EvidenceRejected("Missing authenticated tenant or subject")
    if permission not in principal.scopes:
        raise EvidenceRejected("Principal lacks permission: " + permission)


class ConsentVault:
    """Single-host encrypted token vault with account-scoped grants and audit.

    All stored access tokens are encrypted with AES-256-GCM. The AES key MUST
    originate from a server-side secrets manager; do not generate it per
    request or accept it from a document/bank API response.
    """

    def __init__(self, path: str, master_key: bytes):
        if not isinstance(master_key, bytes) or len(master_key) != 32:
            raise ValueError("A server-managed 32-byte AES-GCM master key is required")
        if not path:
            raise ValueError("A private vault path is required")
        self.key = master_key
        self.path = path
        if path != ":memory:":
            if Path(path).is_symlink():
                raise ValueError("Symlink vault path prohibited")
            target = Path(path).resolve()
            if target.exists() and target.is_symlink():
                raise ValueError("Symlink vault path prohibited")
            target.parent.mkdir(parents=True, exist_ok=True)
            # Operator is responsible for protected directory and volume.
            if not target.exists():
                fd = os.open(str(target), os.O_CREAT | os.O_EXCL | os.O_RDWR, 0o600)
                os.close(fd)
            os.chmod(str(target), 0o600)
        with self._db() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS sessions (
                    state_hash TEXT PRIMARY KEY, tenant TEXT NOT NULL,
                    subject TEXT NOT NULL, expires INTEGER NOT NULL
                );
                CREATE TABLE IF NOT EXISTS items (
                    tenant TEXT NOT NULL, subject TEXT NOT NULL,
                    item TEXT NOT NULL, account TEXT NOT NULL,
                    consent TEXT NOT NULL, sealed_token BLOB NOT NULL,
                    revoked_at INTEGER,
                    PRIMARY KEY(tenant,subject,item,account)
                );
                CREATE TABLE IF NOT EXISTS audit (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event TEXT NOT NULL, actor_digest TEXT NOT NULL,
                    object_digest TEXT NOT NULL, epoch INTEGER NOT NULL
                );
            """)

    @contextmanager
    def _db(self):
        conn = sqlite3.connect(self.path, timeout=4)
        try:
            conn.execute("PRAGMA busy_timeout=4000")
            yield conn
            conn.commit()
        except BaseException:
            conn.rollback()
            raise
        finally:
            conn.close()

    def _audit(self, conn, event: str, actor: str, obj: str):
        # HMAC pseudonyms prevent raw account identifiers in audit history,
        # but operator must protect the audit store and signing key.
        digest = lambda x: hmac.new(self.key, x.encode(), hashlib.sha256).hexdigest()
        conn.execute(
            "INSERT INTO audit (event,actor_digest,object_digest,epoch) VALUES(?,?,?,?)",
            (event,digest(actor),digest(obj),int(time.time())),
        )

    def _aad(self, p: AuthenticatedPrincipal, item: str, account: str, consent: str) -> bytes:
        return "\x1f".join((p.tenant_id,p.subject_id,item,account,consent)).encode()

    def _seal(self, p: AuthenticatedPrincipal, item: str, account: str, consent: str, token: str) -> bytes:
        if not isinstance(token,str) or len(token)<12 or len(token)>4096:
            raise EvidenceRejected("Invalid Plaid access token")
        nonce = os.urandom(12)
        return nonce + AESGCM(self.key).encrypt(
            nonce,token.encode(),self._aad(p,item,account,consent)
        )

    def _open(self, p: AuthenticatedPrincipal, item: str, account: str, consent: str, blob: bytes) -> str:
        try:
            return AESGCM(self.key).decrypt(
                blob[:12],blob[12:],self._aad(p,item,account,consent)
            ).decode()
        except Exception as exc:
            raise EvidenceRejected("Stored Item token integrity or scope invalid") from exc

    def begin_link(self, principal: AuthenticatedPrincipal, *, ttl_seconds:int=600) -> str:
        require(principal,"plaid:connect")
        if not 60<=ttl_seconds<=900:
            raise EvidenceRejected("Invalid one-time Link authorization TTL")
        state=secrets.token_urlsafe(32)
        state_hash=hashlib.sha256(state.encode()).hexdigest()
        with self._db() as conn:
            conn.execute(
                "INSERT INTO sessions VALUES (?,?,?,?)",
                (state_hash,principal.tenant_id,principal.subject_id,int(time.time())+ttl_seconds),
            )
            self._audit(conn,"LINK_SESSION_STARTED",principal.tenant_id+":"+principal.subject_id,state_hash)
        return state

    def consume_link(self, principal:AuthenticatedPrincipal, state:str) -> None:
        require(principal,"plaid:connect")
        if not isinstance(state,str) or len(state)>200:
            raise EvidenceRejected("Invalid Link session state")
        state_hash=hashlib.sha256(state.encode()).hexdigest()
        with self._db() as conn:
            row=conn.execute(
                "SELECT tenant,subject,expires FROM sessions WHERE state_hash=?",
                (state_hash,)
            ).fetchone()
            if not row or row[0]!=principal.tenant_id or row[1]!=principal.subject_id or row[2]<=time.time():
                raise EvidenceRejected("Link completion not authorized or expired")
            conn.execute("DELETE FROM sessions WHERE state_hash=?",(state_hash,))
            self._audit(conn,"LINK_SESSION_CONSUMED",principal.tenant_id+":"+principal.subject_id,state_hash)

    def grant_account(self, principal:AuthenticatedPrincipal, *, item_id:str,
                      account_id:str, consent_id:str, access_token:str) -> None:
        require(principal,"plaid:connect")
        if not all(isinstance(x,str) and 1<=len(x)<=200 for x in (item_id,account_id,consent_id)):
            raise EvidenceRejected("Incomplete Item/account/consent scope")
        ciphertext=self._seal(principal,item_id,account_id,consent_id,access_token)
        with self._db() as conn:
            # Once revoked, re-onboarding must produce new consent reference.
            exists=conn.execute(
                "SELECT consent,revoked_at FROM items WHERE tenant=? AND subject=? AND item=? AND account=?",
                (principal.tenant_id,principal.subject_id,item_id,account_id)
            ).fetchone()
            if exists and (exists[1] is not None or exists[0]!=consent_id):
                raise EvidenceRejected("Existing or revoked scope cannot be silently replaced")
            conn.execute(
                """INSERT INTO items VALUES (?,?,?,?,?,?,NULL)
                   ON CONFLICT(tenant,subject,item,account) DO UPDATE SET
                   sealed_token=excluded.sealed_token
                """,
                (principal.tenant_id,principal.subject_id,item_id,account_id,consent_id,ciphertext),
            )
            self._audit(conn,"ACCOUNT_GRANTED",principal.tenant_id+":"+principal.subject_id,item_id+":"+account_id)

    def access(self, principal:AuthenticatedPrincipal, *,
               item_id:str, account_id:str) -> AuthorizedItem:
        require(principal,"plaid:compare")
        with self._db() as conn:
            row=conn.execute(
                """SELECT consent,sealed_token FROM items
                   WHERE tenant=? AND subject=? AND item=? AND account=?
                     AND revoked_at IS NULL""",
                (principal.tenant_id,principal.subject_id,item_id,account_id),
            ).fetchone()
            if not row:
                raise EvidenceRejected("No active consent for this tenant/user/Item/account")
            token=self._open(principal,item_id,account_id,row[0],row[1])
            self._audit(conn,"ITEM_ACCESS_GRANTED",principal.tenant_id+":"+principal.subject_id,item_id+":"+account_id)
            return AuthorizedItem(item_id,account_id,row[0],token)

    def revoke(self, principal:AuthenticatedPrincipal, *, item_id:str) -> int:
        """Local access revoked immediately; encrypted remote-removal token retained."""
        require(principal,"plaid:revoke")
        with self._db() as conn:
            cur=conn.execute(
                "UPDATE items SET revoked_at=? WHERE tenant=? AND subject=? AND item=? AND revoked_at IS NULL",
                (int(time.time()),principal.tenant_id,principal.subject_id,item_id),
            )
            self._audit(conn,"LOCAL_CONSENT_REVOKED",principal.tenant_id+":"+principal.subject_id,item_id)
            return cur.rowcount

    def pending_remote_removal(self, principal:AuthenticatedPrincipal, *, item_id:str)->str:
        """Return token only to authenticated server-side revocation worker.

        No browser route should ever expose this value. A worker must then
        call Plaid /item/remove and securely wipe the token after success.
        """
        require(principal,"plaid:revoke")
        with self._db() as conn:
            rows=conn.execute(
                """SELECT account,consent,sealed_token FROM items
                   WHERE tenant=? AND subject=? AND item=? AND revoked_at IS NOT NULL
                   AND length(sealed_token)>0""",
                (principal.tenant_id,principal.subject_id,item_id),
            ).fetchall()
            if not rows:
                raise EvidenceRejected("No pending remote Item removal for principal")
            values={self._open(principal,item_id,account,consent,blob)
                    for account,consent,blob in rows}
            if len(values)!=1:
                raise EvidenceRejected("Multiple token versions require manual revocation review")
            return values.pop()

    def confirm_remote_removal(self, principal:AuthenticatedPrincipal, *, item_id:str)->int:
        """Remove ciphertext only once upstream provider confirms Item deletion."""
        require(principal,"plaid:revoke")
        with self._db() as conn:
            cur=conn.execute(
                """UPDATE items SET sealed_token=x'' WHERE tenant=? AND subject=? AND item=?
                   AND revoked_at IS NOT NULL AND length(sealed_token)>0""",
                (principal.tenant_id,principal.subject_id,item_id),
            )
            self._audit(conn,"PLAID_ITEM_REMOVED",principal.tenant_id+":"+principal.subject_id,item_id)
            return cur.rowcount

    def prune(self, *, retention_days:int=30) -> int:
        """Remove spent Link states and old pseudonymous audit events."""
        if not 1<=retention_days<=365:
            raise EvidenceRejected("Invalid retention period")
        with self._db() as conn:
            conn.execute("DELETE FROM sessions WHERE expires < ?",(int(time.time()),))
            cur=conn.execute("DELETE FROM audit WHERE epoch < ?",(int(time.time())-retention_days*86400,))
            return cur.rowcount
