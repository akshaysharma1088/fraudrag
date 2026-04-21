"""
Fraud Detection Routes
GET  /api/v1/fraud/analysis/{statement_id}  – Get fraud analysis for a statement
POST /api/v1/fraud/reanalyze/{statement_id} – Rerun analysis
GET  /api/v1/fraud/dashboard                – Aggregated fraud metrics
POST /api/v1/fraud/review/{statement_id}    – Submit analyst review
"""

import structlog
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from typing import Any, Dict, List, Optional

router = APIRouter()
logger = structlog.get_logger(__name__)

# Imported from statements route (shared store) – in production use a DB
from backend.api.routes.statements import _statement_store


class ReviewPayload(BaseModel):
    analyst_id: str
    verdict: str  # "confirmed_fraud" | "false_positive" | "needs_investigation"
    notes: Optional[str] = None


class FraudMetrics(BaseModel):
    total_analyzed: int
    high_risk_count: int
    medium_risk_count: int
    low_risk_count: int
    average_fraud_score: float
    confirmed_fraud_rate: float


@router.get("/analysis/{statement_id}")
async def get_fraud_analysis(statement_id: str):
    """
    Retrieve the complete fraud analysis for a processed statement.
    Includes risk score, fraud indicators, graph evidence, and LLM reasoning.
    """
    record = _statement_store.get(statement_id)
    if not record:
        raise HTTPException(status_code=404, detail="Statement not found")

    fraud = record.get("fraud_analysis")
    if not fraud:
        return {
            "statement_id": statement_id,
            "status": "no_analysis",
            "message": "Statement was processed but fraud analysis is not available.",
        }

    return {
        "statement_id": statement_id,
        "customer_id": record["bronze"].get("customer_id"),
        "analysis": fraud,
        "silver_metadata": {
            "quality_score": record["silver"].get("quality_score"),
            "balance_check": record["silver"].get("balance_check"),
            "transaction_count": len(record["silver"].get("transactions", [])),
        },
        "pipeline_metadata": {
            "bronze_hash": record["bronze"].get("document_hash"),
            "ocr_confidence": record["bronze"].get("ocr_confidence"),
            "upload_timestamp": record["bronze"].get("upload_timestamp"),
        },
    }


@router.post("/reanalyze/{statement_id}")
async def reanalyze_statement(statement_id: str, request: Request):
    """
    Rerun Graph-RAG analysis on an already-ingested statement.
    Useful after updating fraud patterns in the knowledge graph.
    """
    record = _statement_store.get(statement_id)
    if not record:
        raise HTTPException(status_code=404, detail="Statement not found")

    rag_service = getattr(request.app.state, "rag_service", None)
    if not rag_service:
        raise HTTPException(status_code=503, detail="RAG service not available")

    raw_text = record["bronze"].get("raw_text", "")
    if not raw_text:
        raise HTTPException(status_code=400, detail="No text available for reanalysis")

    customer_id = record["bronze"].get("customer_id", "unknown")
    fraud_result = await rag_service.analyze_statement(
        statement_id=statement_id,
        customer_id=customer_id,
        statement_text=raw_text,
    )

    record["fraud_analysis"] = fraud_result.dict()
    _statement_store[statement_id] = record

    return {
        "message": "Reanalysis complete",
        "statement_id": statement_id,
        "new_risk_level": str(fraud_result.risk_level),
        "new_fraud_score": fraud_result.fraud_score.score,
    }


@router.post("/review/{statement_id}")
async def submit_review(statement_id: str, payload: ReviewPayload):
    """Submit analyst review verdict for model feedback loop."""
    record = _statement_store.get(statement_id)
    if not record:
        raise HTTPException(status_code=404, detail="Statement not found")

    if record.get("fraud_analysis"):
        record["fraud_analysis"]["reviewed_by"] = payload.analyst_id
        record["fraud_analysis"]["analyst_verdict"] = payload.verdict
        record["fraud_analysis"]["analyst_notes"] = payload.notes
        _statement_store[statement_id] = record

    logger.info("Analyst review submitted",
                statement_id=statement_id,
                verdict=payload.verdict,
                analyst=payload.analyst_id)

    return {"message": "Review submitted", "statement_id": statement_id, "verdict": payload.verdict}


@router.get("/dashboard", response_model=FraudMetrics)
async def fraud_dashboard():
    """Aggregated fraud detection metrics across all analyzed statements."""
    total = len(_statement_store)
    scores = []
    risk_counts = {"high": 0, "critical": 0, "medium": 0, "low": 0, "minimal": 0}
    confirmed = 0

    for data in _statement_store.values():
        fraud = data.get("fraud_analysis")
        if not fraud:
            continue
        risk = fraud.get("risk_level", "minimal")
        risk_counts[risk] = risk_counts.get(risk, 0) + 1

        fs = fraud.get("fraud_score")
        if isinstance(fs, dict):
            scores.append(fs.get("score", 0))
        if fraud.get("analyst_verdict") == "confirmed_fraud":
            confirmed += 1

    avg_score = sum(scores) / len(scores) if scores else 0.0
    confirmed_rate = confirmed / total if total > 0 else 0.0

    return FraudMetrics(
        total_analyzed=total,
        high_risk_count=risk_counts.get("high", 0) + risk_counts.get("critical", 0),
        medium_risk_count=risk_counts.get("medium", 0),
        low_risk_count=risk_counts.get("low", 0),
        average_fraud_score=round(avg_score, 4),
        confirmed_fraud_rate=round(confirmed_rate, 4),
    )


@router.get("/recent-alerts")
async def get_recent_alerts(limit: int = 10):
    """Get most recent high-risk fraud alerts."""
    alerts = []
    for stmt_id, data in _statement_store.items():
        fraud = data.get("fraud_analysis")
        if not fraud:
            continue
        risk = fraud.get("risk_level", "minimal")
        if risk in ("high", "critical"):
            fs = fraud.get("fraud_score") or {}
            alerts.append({
                "statement_id": stmt_id,
                "customer_id": data["bronze"].get("customer_id"),
                "risk_level": risk,
                "fraud_score": fs.get("score") if isinstance(fs, dict) else None,
                "indicators_count": len(fraud.get("indicators", [])),
                "upload_timestamp": data["bronze"].get("upload_timestamp"),
            })

    alerts.sort(key=lambda x: x.get("fraud_score") or 0, reverse=True)
    return {"alerts": alerts[:limit], "total_alerts": len(alerts)}
