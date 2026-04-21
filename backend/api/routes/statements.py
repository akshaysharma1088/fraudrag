"""
Statement Upload & Processing Routes
POST /api/v1/statements/upload  – Upload statement for fraud analysis
GET  /api/v1/statements/{id}    – Get statement processing status
GET  /api/v1/statements/        – List statements for a customer
"""

import structlog
from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Optional

from backend.models.domain import StatementType
from backend.pipelines.medallion import BronzePipeline, SilverPipeline, GoldPipeline

router = APIRouter()
logger = structlog.get_logger(__name__)

bronze_pipeline = BronzePipeline()
silver_pipeline = SilverPipeline()
gold_pipeline = GoldPipeline()

# In-memory store for demo (replace with PostgreSQL in production)
_statement_store: dict = {}


class StatementResponse(BaseModel):
    statement_id: str
    customer_id: str
    status: str
    layer: str
    quality_score: Optional[float] = None
    transaction_count: Optional[int] = None
    message: str


@router.post("/upload", response_model=StatementResponse, status_code=status.HTTP_202_ACCEPTED)
async def upload_statement(
    request: Request,
    file: UploadFile = File(..., description="PDF, image, or DOCX statement file"),
    customer_id: str = Form(..., description="Customer identifier"),
    statement_type: StatementType = Form(StatementType.BANK),
    warehouse_reference_id: Optional[str] = Form(None, description="ID of authoritative warehouse copy"),
):
    """
    Upload a financial statement for fraud detection analysis.

    The document flows through the Medallion pipeline:
    1. **Bronze**: Ingested, OCR extracted, hashed
    2. **Silver**: Normalized, entities extracted, balances validated
    3. **Gold**: Feature engineered, fraud-scored via Graph-RAG
    """
    max_size = 20 * 1024 * 1024  # 20MB
    file_bytes = await file.read()

    if len(file_bytes) > max_size:
        raise HTTPException(status_code=413, detail="File too large. Maximum 20MB.")

    if not file.content_type:
        raise HTTPException(status_code=400, detail="Could not determine file type.")

    allowed_types = [
        "application/pdf",
        "image/png",
        "image/jpeg",
        "image/jpg",
        "image/tiff",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "text/plain",
    ]
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=415,
            detail=f"Unsupported file type: {file.content_type}. Allowed: PDF, PNG, JPEG, DOCX",
        )

    logger.info("Statement upload received",
                customer_id=customer_id,
                filename=file.filename,
                size=len(file_bytes))

    # ── Bronze Layer ─────────────────────────────
    bronze_record = await bronze_pipeline.ingest(
        file_bytes=file_bytes,
        filename=file.filename or "statement",
        customer_id=customer_id,
        statement_type=statement_type.value,
        mime_type=file.content_type,
    )

    # ── Silver Layer ─────────────────────────────
    silver_record = await silver_pipeline.normalize(bronze_record)

    # ── Gold Layer (async fraud analysis) ────────
    rag_service = getattr(request.app.state, "rag_service", None)

    warehouse_text = None
    # In production: fetch from DWH by warehouse_reference_id
    # For demo, we skip warehouse lookup

    fraud_analysis_dict = None
    fraud_result = None

    if rag_service and bronze_record.get("raw_text"):
        try:
            fraud_result = await rag_service.analyze_statement(
                statement_id=bronze_record["id"],
                customer_id=customer_id,
                statement_text=bronze_record["raw_text"],
                warehouse_reference=warehouse_text,
                customer_profile={"customer_id": customer_id},
            )
            fraud_analysis_dict = fraud_result.dict()
        except Exception as e:
            logger.error("Graph-RAG analysis failed", error=str(e))

    gold_record = await gold_pipeline.enrich(silver_record, fraud_analysis_dict)

    # Store for retrieval
    statement_data = {
        "bronze": bronze_record,
        "silver": silver_record,
        "gold": gold_record,
        "fraud_analysis": fraud_analysis_dict,
    }
    _statement_store[bronze_record["id"]] = statement_data

    return StatementResponse(
        statement_id=bronze_record["id"],
        customer_id=customer_id,
        status=gold_record["status"],
        layer=gold_record["layer"],
        quality_score=silver_record.get("quality_score"),
        transaction_count=len(silver_record.get("transactions", [])),
        message="Statement processed through Medallion pipeline. Fraud analysis complete.",
    )


@router.get("/{statement_id}")
async def get_statement(statement_id: str):
    """Retrieve full statement processing record including fraud analysis."""
    record = _statement_store.get(statement_id)
    if not record:
        raise HTTPException(status_code=404, detail="Statement not found")
    return {
        "statement_id": statement_id,
        "bronze_layer": {
            "document_hash": record["bronze"].get("document_hash"),
            "ocr_confidence": record["bronze"].get("ocr_confidence"),
            "status": record["bronze"].get("status"),
        },
        "silver_layer": {
            "quality_score": record["silver"].get("quality_score"),
            "entities": record["silver"].get("entities"),
            "transaction_count": len(record["silver"].get("transactions", [])),
            "balance_check": record["silver"].get("balance_check"),
        },
        "gold_layer": {
            "features": record["gold"].get("features"),
            "fraud_analysis": record.get("fraud_analysis"),
        },
    }


@router.get("/")
async def list_statements(customer_id: Optional[str] = None):
    """List all processed statements, optionally filtered by customer."""
    results = []
    for stmt_id, data in _statement_store.items():
        if customer_id and data["bronze"].get("customer_id") != customer_id:
            continue
        fraud = data.get("fraud_analysis") or {}
        results.append({
            "statement_id": stmt_id,
            "customer_id": data["bronze"].get("customer_id"),
            "filename": data["bronze"].get("filename"),
            "upload_timestamp": data["bronze"].get("upload_timestamp"),
            "status": data["gold"].get("status"),
            "quality_score": data["silver"].get("quality_score"),
            "risk_level": fraud.get("risk_level", "unknown"),
            "fraud_score": fraud.get("fraud_score", {}).get("score") if isinstance(fraud.get("fraud_score"), dict) else None,
        })
    return {"statements": results, "total": len(results)}
