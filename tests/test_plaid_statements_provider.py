"""Offline Plaid Statements adapter tests using mock transport, no Plaid API calls."""
import hashlib
import json

import httpx
import pytest

from backend.services.plaid_statements_provider import (
    PlaidAuthorizedItem, PlaidStatementsProvider,
)
from backend.services.signed_issuer_evidence import EvidenceRejected

PDF = b"%PDF-1.4\n1 0 obj\n<< >>\nendobj\n%%EOF\n"
OTHER = PDF + b"\nlegitimate-copy-change"
DIGEST = hashlib.sha256(PDF).hexdigest()


@pytest.fixture
def item():
    return PlaidAuthorizedItem(
        tenant_id="test-tenant",
        consent_id="test-consent",
        item_id="item-test-001",
        account_id="account-test-001",
        access_token="test-consented-item-access-token",
        permission_authorized=True,
    )


def mkclient(item, *, override=None):
    calls=[]
    def handler(req):
        calls.append(req)
        assert req.url.host=="sandbox.plaid.com"
        assert req.headers["PLAID-CLIENT-ID"]=="test-client"
        assert req.headers["PLAID-SECRET"]=="test-secret-value"
        request=json.loads(req.content)
        assert request["access_token"]==item.access_token
        if req.url.path=="/statements/list":
            assert "statement_id" not in request
            reply={
                "item_id":item.item_id,
                "institution_id":"ins_test",
                "accounts":[{
                    "account_id":item.account_id,
                    "statements":[{
                        "statement_id":"statement-test-001",
                        "year":2026,"month":7,
                    }],
                }],
            }
            return override("list",reply) if override else httpx.Response(200,json=reply)
        if req.url.path=="/statements/download":
            assert request["statement_id"]=="statement-test-001"
            return override("download",None) if override else httpx.Response(
                200,content=PDF,
                headers={
                    "Content-Type":"application/pdf",
                    "Plaid-Content-Hash":DIGEST,
                },
            )
        raise AssertionError("Unapproved paid Plaid endpoint")
    client=httpx.Client(transport=httpx.MockTransport(handler))
    adapter=PlaidStatementsProvider(
        environment="sandbox",client_id="test-client",secret="test-secret-value",
        enabled=True,client=client
    )
    return client,adapter,calls


def test_exact_bank_provided_original_pdf_transport_integrity(item):
    client,adapter,calls=mkclient(item)
    with client:
        out=adapter.compare_with_original(
            item=item,statement_id="statement-test-001",uploaded_pdf=PDF
        )
    assert out["result"]=="EXACT_PDF_BYTES_MATCH"
    assert out["plaid_content_sha256_verified"] is True
    assert out["not_an_issuer_signature"] is True
    assert out["does_not_prove_fraud"] is True
    assert out["source_document_sha256"]==DIGEST
    assert len(calls)==2


def test_pdf_binary_difference_never_classified_as_criminal_fraud(item):
    client,adapter,calls=mkclient(item)
    with client:
        result=adapter.compare_with_original(
            item=item,statement_id="statement-test-001",uploaded_pdf=OTHER
        )
    assert result["result"]=="PDF_BYTES_DIFFER"
    assert result["does_not_prove_fraud"] is True
    assert result["submitted_document_sha256"]!=result["source_document_sha256"]


def test_no_permission_no_plaid_calls(item):
    from dataclasses import replace
    client,adapter,calls=mkclient(item)
    with client:
        with pytest.raises(EvidenceRejected,match="authorization"):
            adapter.list_statements(replace(item,permission_authorized=False))
    assert not calls


def test_default_off_and_environment_restricted(item):
    with pytest.raises(EvidenceRejected):
        PlaidStatementsProvider(
            environment="development",client_id="test-client",secret="test-secret-value"
        )
    client,_,calls=mkclient(item)
    with client:
        blocked=PlaidStatementsProvider(
            environment="sandbox",client_id="test-client",secret="test-secret-value",
            client=client,
        )
        with pytest.raises(EvidenceRejected,match="disabled"):
            blocked.list_statements(item)
    assert not calls


def test_statement_must_be_listed_under_authorized_item_account(item):
    def spoof(route,body):
        if route=="list":
            body["item_id"]="different-item"
            return httpx.Response(200,json=body)
        raise AssertionError("Must never attempt unlisted download")
    client,adapter,calls=mkclient(item,override=spoof)
    with client:
        with pytest.raises(EvidenceRejected,match="Item ID"):
            adapter.compare_with_original(
                item=item,statement_id="statement-test-001",uploaded_pdf=PDF
            )
    assert len(calls)==1


def test_statement_not_owned_by_selected_account_never_downloaded(item):
    def spoof(route,body):
        if route=="list":
            body["accounts"][0]["account_id"]="somebody-elses-account"
            return httpx.Response(200,json=body)
        raise AssertionError("Should refuse cross-account download")
    client,adapter,calls=mkclient(item,override=spoof)
    with client:
        with pytest.raises(EvidenceRejected,match="account"):
            adapter.compare_with_original(
                item=item,statement_id="statement-test-001",uploaded_pdf=PDF
            )
    assert len(calls)==1


def test_statement_id_not_in_original_listing_is_rejected(item):
    client,adapter,calls=mkclient(item)
    with client:
        with pytest.raises(EvidenceRejected,match="not listed"):
            adapter.compare_with_original(
                item=item,statement_id="other-statement-id",uploaded_pdf=PDF
            )
    assert len(calls)==1


@pytest.mark.parametrize("case",["missing_hash","wrong_hash","not_pdf","too_large","redirect"])
def test_download_checksum_and_response_requirements_fail_closed(item,case):
    def override(route,body):
        if route=="list":
            return httpx.Response(200,json=body)
        if case=="redirect":
            return httpx.Response(302,headers={"location":"https://evil.example"})
        content=PDF if case!="not_pdf" else b"THIS IS NOT A PDF"
        if case=="too_large":
            content=b"%PDF-"+b"a"*(17*1024*1024)
        headers={
            "content-type":"application/pdf",
            "Plaid-Content-Hash":(
                "0"*64 if case=="wrong_hash" else
                hashlib.sha256(content).hexdigest()
            ),
        }
        if case=="missing_hash":
            del headers["Plaid-Content-Hash"]
        return httpx.Response(200,content=content,headers=headers)
    client,adapter,calls=mkclient(item,override=override)
    with client:
        with pytest.raises(EvidenceRejected):
            adapter.compare_with_original(
                item=item,statement_id="statement-test-001",uploaded_pdf=PDF
            )


def test_download_not_attempted_with_non_pdf_submission(item):
    client,adapter,calls=mkclient(item)
    with client:
        with pytest.raises(EvidenceRejected,match="does not appear"):
            adapter.compare_with_original(
                item=item,statement_id="statement-test-001",uploaded_pdf=b"NOT A PDF"
            )
    assert not calls


def test_no_link_refresh_or_billing_workflows_are_called(item):
    client,adapter,calls=mkclient(item)
    with client:
        adapter.compare_with_original(
            item=item,statement_id="statement-test-001",uploaded_pdf=PDF
        )
    paths=[r.url.path for r in calls]
    assert paths==["/statements/list","/statements/download"]
    assert "/link/token/create" not in paths and "/statements/refresh" not in paths
