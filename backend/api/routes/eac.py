"""Isolated FraudRAG-EAC demonstration endpoints, disabled in normal deployment.

The API accepts only *built-in fictional scenario IDs*; clients cannot upload
bank records or assert issuer authority. No data persistence or API charges.
"""
from typing import Literal

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from backend.services.eac_service import SCENARIOS, run_sandbox

router = APIRouter()


class DemoRequest(BaseModel):
    scenario: Literal["consistent", "altered", "partial", "conflicting", "future"] = "consistent"
    policy: Literal["adaptive_dp", "greedy", "fixed"] = "adaptive_dp"
    budget_units: float = Field(default=4.0, ge=1, le=8, multiple_of=0.1)


def check_enabled(request: Request) -> None:
    if not getattr(request.app.state, "eac_demo_enabled", False):
        raise HTTPException(
            status_code=403,
            detail="Evidence acquisition sandbox disabled. Enable EAC_DEMO_ENABLED only in a controlled demo environment."
        )


@router.get("/demo/scenarios")
def demo_scenarios(request: Request):
    check_enabled(request)
    return {"sandbox_only": True, "scenarios": SCENARIOS,
            "policies": ["adaptive_dp", "greedy", "fixed"],
            "available_budget_units": {"minimum": 1, "maximum": 8, "step": 0.1},
            "no_real_bank_issuer_authentication": True}


@router.post("/demo/run")
def demo_run(payload: DemoRequest, request: Request):
    check_enabled(request)
    try:
        return run_sandbox(scenario=payload.scenario, strategy=payload.policy,
                           budget_units=payload.budget_units)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
