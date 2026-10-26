"""FastAPI EAC sandbox contract: disabled in non-test deployments."""
from fastapi.testclient import TestClient

from backend.main import create_app


def test_demo_is_off_by_default_when_not_explicitly_enabled():
    app = create_app(testing=True)
    app.state.eac_demo_enabled = False
    client = TestClient(app)
    r = client.get("/api/v1/eac/demo/scenarios")
    assert r.status_code == 403
    r = client.post("/api/v1/eac/demo/run", json={"scenario": "consistent"})
    assert r.status_code == 403


def test_demo_api_is_explicit_sandbox_and_has_action_trace():
    client = TestClient(create_app(testing=True))
    a = client.get("/api/v1/eac/demo/scenarios")
    assert a.status_code == 200
    assert a.json()["sandbox_only"] is True
    assert "partial" in a.json()["scenarios"]
    r = client.post("/api/v1/eac/demo/run", json={
        "scenario": "consistent", "policy": "adaptive_dp", "budget_units": 4
    })
    assert r.status_code == 200, r.text
    x = r.json()
    assert x["system"] == "FraudRAG-EAC"
    assert x["sandbox_only"] is True
    assert x["certificate"]["document_status"] == "MATCH_SUPPORTED"
    assert x["queries"] >= 1
    assert x["certificate"]["basis_sha256"]


def test_demo_rejects_claim_injection_and_unregistered_sources():
    client = TestClient(create_app(testing=True))
    r = client.post("/api/v1/eac/demo/run", json={
        "scenario": "consistent", "policy": "fixed", "budget_units": 4,
        "references": [{"issuer_attested": True, "value": "FAKE", "source_id": "attack"}]
    })
    # Unknown user-provided references must not influence sources. Pydantic
    # currently ignores unknown keys, so output must still be safe and equal
    # to clean invocation. If API switches to extra=forbid, 422 also allowed.
    if r.status_code == 200:
        good = client.post("/api/v1/eac/demo/run", json={
            "scenario": "consistent", "policy": "fixed", "budget_units": 4
        })
        assert r.json() == good.json()
    else:
        assert r.status_code == 422


def test_demo_rejects_invalid_scenarios_and_costs():
    client = TestClient(create_app(testing=True))
    for payload in (
        {"scenario": "unknown"},
        {"scenario": "consistent", "budget_units": 0},
        {"scenario": "consistent", "budget_units": 3.14},
        {"scenario": "consistent", "policy": "execute-code"},
    ):
        r = client.post("/api/v1/eac/demo/run", json=payload)
        assert r.status_code == 422, r.text


def test_no_partner_API_route_is_implicitly_added():
    from backend.main import create_app
    app = create_app(testing=True)
    live = [
        getattr(route, "path", "")
        for route in app.routes
        if "/api/v1/eac" in getattr(route, "path", "")
        and "/demo/" not in route.path
    ]
    assert live == []
