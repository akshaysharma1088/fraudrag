"""Plaid Link lifecycle client, for an explicitly consented bank connection.

No public route exposes this client. A caller must independently authenticate
the user, approve billable Item creation, and mint a one-use state in the
server-side ConsentVault. Network calls are OFF by default.

Statements-only product requires a start/end date (<= 2 years). Creating an
Item may be billed in Production EVEN if statements are never downloaded.
"""
from __future__ import annotations

import json
from datetime import date
import httpx

from backend.services.signed_issuer_evidence import EvidenceRejected
from backend.services.plaid_statements_provider import PLAID_HOSTS

_ALLOWED_PATHS = frozenset({
    "/link/token/create", "/item/public_token/exchange", "/item/remove"
})
MAX_BYTES = 128*1024


class PlaidLinkClient:
    def __init__(self, *, environment: str, client_id: str, secret: str,
                 enabled: bool=False, client: httpx.Client | None=None):
        if environment not in PLAID_HOSTS:
            raise EvidenceRejected("Unsupported Plaid environment")
        if not isinstance(client_id,str) or not client_id or not isinstance(secret,str) or len(secret)<8:
            raise EvidenceRejected("Missing server Plaid API credentials")
        self.origin = "https://" + PLAID_HOSTS[environment]
        self.environment=environment
        self._client_id=client_id
        self._secret=secret
        self._client=client
        self.enabled=enabled

    def _request(self,path:str,payload:dict)->dict:
        if not self.enabled:
            raise EvidenceRejected("Plaid account connection disabled")
        if path not in _ALLOWED_PATHS:
            raise EvidenceRejected("Unapproved Plaid API path")
        owned=self._client is None
        client=self._client or httpx.Client(
            timeout=httpx.Timeout(10.0,connect=4.0),
            follow_redirects=False,trust_env=False,
        )
        try:
            try:
                with client.stream(
                    "POST",self.origin+path,
                    headers={"PLAID-CLIENT-ID":self._client_id,
                             "PLAID-SECRET":self._secret,
                             "Content-Type":"application/json"},
                    json=payload, follow_redirects=False,
                ) as response:
                    if response.status_code!=200:
                        raise EvidenceRejected("Plaid Link/token lifecycle request failed")
                    if "application/json" not in response.headers.get("content-type","").lower():
                        raise EvidenceRejected("Expected JSON from Plaid")
                    data=bytearray()
                    for part in response.iter_bytes():
                        if len(data)+len(part)>MAX_BYTES:
                            raise EvidenceRejected("Plaid lifecycle response oversized")
                        data.extend(part)
                parsed=json.loads(data)
            except (httpx.HTTPError, UnicodeDecodeError, ValueError) as exc:
                if isinstance(exc,EvidenceRejected):
                    raise
                raise EvidenceRejected("Untrusted Plaid lifecycle response") from exc
        finally:
            if owned: client.close()
        if not isinstance(parsed,dict):
            raise EvidenceRejected("Plaid lifecycle response must be object")
        return parsed

    def create_link_token(self, *, subject_key: str, start_date: str,
                          end_date: str, allow_billable_item: bool,
                          client_name: str="FraudRAG Evidence Verification")->str:
        if not allow_billable_item:
            raise EvidenceRejected("User has not approved potential billed Statements Item creation")
        if not isinstance(subject_key,str) or len(subject_key)<6 or len(subject_key)>256:
            raise EvidenceRejected("Invalid opaque server-side subject identifier")
        try:
            begin=date.fromisoformat(start_date)
            end=date.fromisoformat(end_date)
        except (ValueError,TypeError) as exc:
            raise EvidenceRejected("Invalid Plaid Statements date interval") from exc
        if begin>end or (end-begin).days>730 or end>date.today():
            raise EvidenceRejected("Statement date range must be historical and <= 2 years")
        resp=self._request("/link/token/create",{
            "user":{"client_user_id":subject_key},
            "client_name":client_name,
            "products":["statements"],
            "statements":{"start_date":begin.isoformat(),"end_date":end.isoformat()},
            "country_codes":["US"],"language":"en",
        })
        token=resp.get("link_token")
        if not isinstance(token,str) or not token.startswith("link-"):
            raise EvidenceRejected("Plaid Link did not return valid link_token")
        return token

    def exchange_public_token(self, public_token: str)->tuple[str,str]:
        if not isinstance(public_token,str) or not public_token.startswith("public-"):
            raise EvidenceRejected("Expected Plaid Link public_token")
        out=self._request("/item/public_token/exchange",{"public_token":public_token})
        access=out.get("access_token")
        item=out.get("item_id")
        if not isinstance(access,str) or not access.startswith("access-") or not isinstance(item,str) or not item:
            raise EvidenceRejected("Plaid did not provide Item and access token")
        return item,access

    def remove_item(self, access_token: str) -> bool:
        """Call after explicit user revocation. This is external token removal."""
        if not isinstance(access_token,str) or not access_token.startswith("access-"):
            raise EvidenceRejected("Invalid Item token")
        out=self._request("/item/remove",{"access_token":access_token})
        if out.get("removed") is not True:
            raise EvidenceRejected("Plaid did not confirm Item removal")
        return True
