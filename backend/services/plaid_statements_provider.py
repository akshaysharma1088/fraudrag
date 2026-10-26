"""Plaid Statements API transport adapter: bank-provided original PDF comparison.

Only /statements/list and /statements/download. Does NOT create Plaid Items,
initiate Link, call /statements/refresh, or make billable product enrollments.
OFF by default; only server-owned client credentials and customer-consented
Item token can be used. No browser-facing route until identity, consent
lifecycle, audit persistence and access controls are independently built.

Plaid-Content-Hash checks bytes returned by Plaid. It is NOT a cryptographic
issuer signature or independently adjudicated evidence of forged documents.
A byte mismatch may arise from legitimate resaving/re-rendering of PDFs.
"""
from __future__ import annotations

import hashlib
import ipaddress
import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone

import httpx

from backend.services.signed_issuer_evidence import EvidenceRejected

PLAID_HOSTS = {"sandbox": "sandbox.plaid.com", "production": "production.plaid.com"}
MAX_PDF_BYTES = 16 * 1024 * 1024
MAX_LIST_BYTES = 512 * 1024
ID_RE = re.compile(r"^[A-Za-z0-9_-]{2,200}$")
HEX_SHA256 = re.compile(r"^[0-9a-fA-F]{64}$")


@dataclass(frozen=True)
class PlaidAuthorizedItem:
    """Authoritative consent/access mapping established by YOUR backend."""
    tenant_id: str
    consent_id: str
    item_id: str
    account_id: str
    access_token: str
    permission_authorized: bool = False


class PlaidStatementsProvider:
    def __init__(
        self, *, environment: str, client_id: str,
        secret: str, enabled: bool = False,
        client: httpx.Client | None = None
    ):
        if environment not in PLAID_HOSTS:
            raise EvidenceRejected("Only current Plaid Sandbox or Production hosts allowed")
        if not isinstance(client_id,str) or not client_id.strip() or not isinstance(secret,str) or len(secret)<8:
            raise EvidenceRejected("Plaid credential configuration missing")
        self.endpoint = "https://" + PLAID_HOSTS[environment]
        self.environment = environment
        self.enabled = enabled
        self._client_id = client_id
        self._secret = secret
        self._client = client

    def _call(self, path: str, item: PlaidAuthorizedItem,
              *, statement_id: str | None = None) -> tuple[bytes, dict]:
        if not self.enabled:
            raise EvidenceRejected("Plaid Statements integration disabled")
        if not item.permission_authorized:
            raise EvidenceRejected("Server-side user consent and item authorization missing")
        for attr in ("tenant_id", "consent_id", "item_id", "account_id", "access_token"):
            value = getattr(item,attr)
            if not isinstance(value,str) or not value:
                raise EvidenceRejected("Missing server-authorized Plaid Item context")
        if path not in ("/statements/list", "/statements/download"):
            raise EvidenceRejected("Plaid API action not allowlisted")
        if statement_id is not None and not ID_RE.fullmatch(statement_id):
            raise EvidenceRejected("Invalid Plaid statement identifier")
        body = {"access_token": item.access_token}
        if statement_id is not None:
            body["statement_id"] = statement_id
        headers = {
            "PLAID-CLIENT-ID": self._client_id,
            "PLAID-SECRET": self._secret,
            "Content-Type": "application/json",
        }
        client = self._client or httpx.Client(
            timeout=httpx.Timeout(10.0,connect=4.0), follow_redirects=False,
            trust_env=False,
        )
        owned = self._client is None
        try:
            try:
                with client.stream(
                    "POST", self.endpoint+path, json=body, headers=headers,
                    follow_redirects=False,
                ) as response:
                    if response.status_code!=200:
                        raise EvidenceRejected("Plaid statement request failed or redirected")
                    data=bytearray()
                    cap=MAX_PDF_BYTES if statement_id is not None else MAX_LIST_BYTES
                    for chunk in response.iter_bytes():
                        if len(data)+len(chunk)>cap:
                            raise EvidenceRejected("Plaid response exceeds maximum permitted size")
                        data.extend(chunk)
                    response_headers=dict(response.headers)
            except httpx.HTTPError as exc:
                raise EvidenceRejected("Plaid connection failed") from exc
        finally:
            if owned:
                client.close()
        return bytes(data),response_headers

    def list_statements(self, item:PlaidAuthorizedItem)->list[dict]:
        data,headers=self._call("/statements/list",item)
        if "application/json" not in headers.get("content-type","").lower():
            raise EvidenceRejected("Plaid statement list expected JSON")
        try:
            obj=json.loads(data)
        except (UnicodeDecodeError,ValueError) as exc:
            raise EvidenceRejected("Invalid Plaid statement list") from exc
        if not isinstance(obj,dict) or obj.get("item_id")!=item.item_id:
            raise EvidenceRejected("Plaid Item ID mismatch: refusing cross-Item statement access")
        accounts=obj.get("accounts")
        if not isinstance(accounts,list) or len(accounts)>100:
            raise EvidenceRejected("Invalid number of Plaid accounts")
        selected=[a for a in accounts if isinstance(a,dict) and a.get("account_id")==item.account_id]
        if len(selected)!=1:
            raise EvidenceRejected("Plaid account not uniquely bound to authorized Item")
        statements=selected[0].get("statements")
        if not isinstance(statements,list) or len(statements)>1000:
            raise EvidenceRejected("Invalid Plaid statements list")
        found=[]
        ids=set()
        for entry in statements:
            if not isinstance(entry,dict):
                raise EvidenceRejected("Malformed statement metadata")
            sid=entry.get("statement_id")
            year=entry.get("year")
            month=entry.get("month")
            if not isinstance(sid,str) or not ID_RE.fullmatch(sid) or sid in ids:
                raise EvidenceRejected("Duplicate or invalid Plaid statement reference")
            ids.add(sid)
            if not isinstance(year,int) or not isinstance(month,int) or not 2010<=year<=2100 or not 1<=month<=12:
                raise EvidenceRejected("Invalid statement month or year")
            found.append({"statement_id":sid,"year":year,"month":month})
        return found

    def compare_with_original(self, *,
            item:PlaidAuthorizedItem,statement_id:str,uploaded_pdf:bytes)->dict:
        if not isinstance(uploaded_pdf,bytes) or not 5<=len(uploaded_pdf)<=MAX_PDF_BYTES:
            raise EvidenceRejected("Expected bounded submitted PDF bytes")
        if not uploaded_pdf.startswith(b"%PDF-"):
            raise EvidenceRejected("Submitted file does not appear to be a PDF")
        allowed=self.list_statements(item)
        if statement_id not in {x["statement_id"] for x in allowed}:
            raise EvidenceRejected("Requested original not listed for authorized account")
        original,headers=self._call("/statements/download",item,statement_id=statement_id)
        if not original.startswith(b"%PDF-"):
            raise EvidenceRejected("Provider did not return PDF bytes")
        checksum=headers.get("plaid-content-hash","")
        if not HEX_SHA256.fullmatch(checksum):
            raise EvidenceRejected("Missing or unsupported Plaid-Content-Hash checksum encoding")
        digest=hashlib.sha256(original).hexdigest()
        if digest!=checksum.lower():
            raise EvidenceRejected("Plaid-reported downloaded PDF checksum mismatch")
        uploaded_digest=hashlib.sha256(uploaded_pdf).hexdigest()
        same=uploaded_digest==digest
        return {
            "provider":"Plaid Statements",
            "environment":self.environment,
            "account_bound_to_authorized_item":True,
            "statement_listed_for_item_and_account":True,
            "plaid_content_sha256_verified":True,
            "source_document_sha256":digest,
            "submitted_document_sha256":uploaded_digest,
            "retrieved_at":datetime.now(timezone.utc).isoformat(),
            "result":"EXACT_PDF_BYTES_MATCH" if same else "PDF_BYTES_DIFFER",
            "not_an_issuer_signature":True,
            "does_not_prove_fraud":True,
            "limits":(
                "Plaid's checksum verifies response integrity, not a bank-issued "
                "signature. Byte differences may arise from legitimate PDF "
                "re-exports, accessibility transforms, metadata or edits; "
                "manual examination is required. No adjudicated fraud claim."
            ),
        }
