"""Plaid Link client respects explicit billing, date range, and URL action bounds."""
import json

import httpx
import pytest

from backend.services.plaid_link_client import PlaidLinkClient
from backend.services.signed_issuer_evidence import EvidenceRejected


def linked_client():
    requests=[]
    def handler(req):
        requests.append(req)
        assert req.url.host=="sandbox.plaid.com"
        assert req.headers["PLAID-CLIENT-ID"]=="fake-client"
        assert req.headers["PLAID-SECRET"]=="fake-secret-value"
        values=json.loads(req.content)
        if req.url.path=="/link/token/create":
            assert values["products"]==["statements"]
            assert values["country_codes"]==["US"]
            assert values["statements"]["start_date"]=="2026-01-01"
            assert values["statements"]["end_date"]=="2026-09-01"
            return httpx.Response(200,json={"link_token":"link-sandbox-new"})
        if req.url.path=="/item/public_token/exchange":
            assert values["public_token"]=="public-sandbox-one"
            return httpx.Response(200,json={
                "item_id":"item-001",
                "access_token":"access-sandbox-private",
            })
        if req.url.path=="/item/remove":
            assert values["access_token"]=="access-sandbox-private"
            return httpx.Response(200,json={"removed":True})
        raise AssertionError("Unexpected Plaid endpoint")
    transport=httpx.Client(transport=httpx.MockTransport(handler))
    return PlaidLinkClient(
        environment="sandbox",client_id="fake-client",
        secret="fake-secret-value",enabled=True,client=transport
    ),requests,transport


def test_billing_requires_explicit_user_optin_no_network():
    c,requests,client=linked_client()
    with client:
        with pytest.raises(EvidenceRejected,match="approved"):
            c.create_link_token(
                subject_key="opaque-subject-test",
                start_date="2026-01-01",end_date="2026-09-01",
                allow_billable_item=False,
            )
    assert requests==[]


def test_link_exchange_and_remove_restricted_to_pinned_paths():
    c,requests,client=linked_client()
    with client:
        assert c.create_link_token(
            subject_key="opaque-subject-test",start_date="2026-01-01",
            end_date="2026-09-01",allow_billable_item=True,
        )=="link-sandbox-new"
        assert c.exchange_public_token("public-sandbox-one")==(
            "item-001","access-sandbox-private"
        )
        assert c.remove_item("access-sandbox-private") is True
        with pytest.raises(EvidenceRejected):
            c._request("/statements/refresh",{})
    assert [x.url.path for x in requests]==[
        "/link/token/create","/item/public_token/exchange","/item/remove"
    ]


@pytest.mark.parametrize("start,end",[
    ("2025-01-01","2027-12-30"),
    ("2026-09-01","2026-01-01"),
    ("2026-01-01","2027-01-01"),
    ("invalid","2026-01-01"),
])
def test_unsupported_link_date_ranges_do_not_make_calls(start,end):
    c,requests,client=linked_client()
    with client:
        with pytest.raises(EvidenceRejected):
            c.create_link_token(
                subject_key="opaque-subject-test",start_date=start,
                end_date=end,allow_billable_item=True,
            )
    assert requests==[]


def test_client_is_disabled_by_default():
    c,requests,client=linked_client()
    c.enabled=False
    with client:
        with pytest.raises(EvidenceRejected,match="disabled"):
            c.exchange_public_token("public-sandbox-one")
    assert requests==[]


def test_redirect_and_malformed_lifecycle_response_fail_closed():
    def redirect(req):
        return httpx.Response(302,headers={"location":"https://evil.example"})
    with httpx.Client(transport=httpx.MockTransport(redirect)) as client:
        c=PlaidLinkClient(
            environment="sandbox",client_id="test",
            secret="test-secret-value",enabled=True,client=client,
        )
        with pytest.raises(EvidenceRejected):
            c.exchange_public_token("public-sandbox-one")
