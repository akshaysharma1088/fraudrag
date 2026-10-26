"""End-to-end Plaid Link -> AES-GCM vault -> Statements hash -> revoke.

This is an HTTP-MOCK integration that exercises actual provider/client
code. No Plaid credentials, financial account or billable network request.
"""
from __future__ import annotations

import hashlib
import json
import secrets

import httpx
import pytest

from backend.services.eac_consent_vault import AuthenticatedPrincipal, ConsentVault
from backend.services.plaid_link_client import PlaidLinkClient
from backend.services.plaid_statements_provider import PlaidStatementsProvider
from backend.services.plaid_consent_workflow import PlaidConsentWorkflow
from backend.services.signed_issuer_evidence import EvidenceRejected

PDF=b"%PDF-1.4\nmock-Plaid-bank-statement\n%%EOF\n"
PDF_CHECKSUM=hashlib.sha256(PDF).hexdigest()


def test_full_offline_http_workflow_and_revocation(tmp_path):
    audit=[]
    def handler(req):
        audit.append(req.url.path)
        assert req.url.host=="sandbox.plaid.com"
        assert req.headers.get("plaid-client-id")=="dummy-client"
        assert req.headers.get("plaid-secret")=="dummy-secret-value"
        body=json.loads(req.content)
        if req.url.path=="/link/token/create":
            assert body["products"]==["statements"]
            assert body["country_codes"]==["US"]
            assert body["statements"]=={"start_date":"2026-01-01","end_date":"2026-09-01"}
            return httpx.Response(200,json={"link_token":"link-sandbox-fixture"})
        if req.url.path=="/item/public_token/exchange":
            assert body["public_token"]=="public-sandbox-fixture"
            return httpx.Response(200,json={
                "item_id":"item-fixture-001",
                "access_token":"access-sandbox-fixture-private-token",
            })
        if req.url.path=="/statements/list":
            assert body["access_token"]=="access-sandbox-fixture-private-token"
            return httpx.Response(200,json={
                "item_id":"item-fixture-001",
                "accounts":[{
                    "account_id":"account-fixture-001",
                    "statements":[{"statement_id":"statement-fixture-001",
                                   "year":2026,"month":7}]
                }],
            })
        if req.url.path=="/statements/download":
            assert body["statement_id"]=="statement-fixture-001"
            return httpx.Response(200,content=PDF,headers={
                "content-type":"application/pdf",
                "Plaid-Content-Hash":PDF_CHECKSUM,
            })
        if req.url.path=="/item/remove":
            assert body["access_token"]=="access-sandbox-fixture-private-token"
            return httpx.Response(200,json={"removed":True})
        raise AssertionError("Endpoint not in narrow Plaid workflow")

    vault_path=tmp_path/"consent-vault.sqlite"
    vault=ConsentVault(str(vault_path),secrets.token_bytes(32))
    principal=AuthenticatedPrincipal(
        "tenant-test","user-test",
        frozenset({"plaid:connect","plaid:compare","plaid:revoke"}),
    )
    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        link=PlaidLinkClient(
            environment="sandbox",client_id="dummy-client",
            secret="dummy-secret-value",enabled=True,client=client
        )
        statements=PlaidStatementsProvider(
            environment="sandbox",client_id="dummy-client",
            secret="dummy-secret-value",enabled=True,client=client
        )
        flow=PlaidConsentWorkflow(vault=vault,link=link,statements=statements)
        with pytest.raises(EvidenceRejected):
            flow.start(
                principal=principal,start_date="2026-01-01",
                end_date="2026-09-01",user_approved_potential_charge=False
            )
        assert audit==[]
        session=flow.start(
            principal=principal,start_date="2026-01-01",
            end_date="2026-09-01",user_approved_potential_charge=True
        )
        assert "link_token" in session
        linked=flow.complete(
            principal=principal,
            one_time_completion_state=session["one_time_completion_state"],
            public_token="public-sandbox-fixture",
            selected_account_id="account-fixture-001",
        )
        assert linked["vault_encrypted_token"] is True
        assert "access-sandbox-fixture-private-token" not in vault_path.read_bytes().decode("latin1")
        compared=flow.compare(
            principal=principal,item_id="item-fixture-001",
            account_id="account-fixture-001",
            statement_id="statement-fixture-001",submitted_pdf=PDF
        )
        assert compared["result"]=="EXACT_PDF_BYTES_MATCH"
        assert compared["does_not_prove_fraud"]
        diff=flow.compare(
            principal=principal,item_id="item-fixture-001",
            account_id="account-fixture-001",
            statement_id="statement-fixture-001",submitted_pdf=PDF+b"postprocessing"
        )
        assert diff["result"]=="PDF_BYTES_DIFFER"
        assert diff["not_an_issuer_signature"]
        revoked=flow.revoke(principal=principal,item_id="item-fixture-001")
        assert revoked["remote_item_removed"]
        with pytest.raises(EvidenceRejected):
            flow.compare(
                principal=principal,item_id="item-fixture-001",
                account_id="account-fixture-001",
                statement_id="statement-fixture-001",submitted_pdf=PDF
            )
    assert audit==[
        "/link/token/create", "/item/public_token/exchange",
        "/statements/list", "/statements/list",
        "/statements/download", "/statements/list",
        "/statements/download", "/item/remove",
    ]
