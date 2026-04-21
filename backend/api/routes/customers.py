"""Customer management routes."""
import uuid
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from typing import Optional

router = APIRouter()

_customer_store: dict = {}


class CustomerCreate(BaseModel):
    name: str
    email: Optional[str] = None


@router.post("/")
async def create_customer(payload: CustomerCreate, request: Request):
    customer_id = str(uuid.uuid4())
    customer = {"id": customer_id, "name": payload.name, "email": payload.email, "risk_level": "minimal"}
    _customer_store[customer_id] = customer

    neo4j = getattr(request.app.state, "neo4j", None)
    if neo4j:
        await neo4j.upsert_customer({"id": customer_id, "name": payload.name, "risk_score": 0.0, "fraud_history_count": 0})

    return {"customer_id": customer_id, "message": "Customer created"}


@router.get("/{customer_id}")
async def get_customer(customer_id: str):
    customer = _customer_store.get(customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    return customer


@router.get("/")
async def list_customers():
    return {"customers": list(_customer_store.values()), "total": len(_customer_store)}
