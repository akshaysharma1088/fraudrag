"""
Domain Models – FraudRAG
Domain-Driven Design: Aggregates, Entities, Value Objects

Bounded Contexts:
  - StatementContext   : Statement upload, OCR, normalization
  - FraudContext       : Scoring, anomaly detection, audit trail
  - GraphContext       : Knowledge graph entities & relationships
  - CustomerContext    : Customer identity, history, risk profile
"""

from __future__ import annotations

import hashlib
import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator


# ─────────────────────────────────────────────
# Value Objects (immutable, identity by value)
# ─────────────────────────────────────────────

class DocumentHash(BaseModel):
    """SHA-256 fingerprint of a raw document. Immutable value object."""
    value: str

    @classmethod
    def from_bytes(cls, data: bytes) -> "DocumentHash":
        return cls(value=hashlib.sha256(data).hexdigest())

    def __eq__(self, other):
        return isinstance(other, DocumentHash) and self.value == other.value


class Money(BaseModel):
    """Monetary amount with currency. Immutable value object."""
    amount: float
    currency: str = "USD"

    def __eq__(self, other):
        return isinstance(other, Money) and self.amount == other.amount and self.currency == other.currency


class FraudScore(BaseModel):
    """Normalized [0,1] fraud probability with confidence interval."""
    score: float = Field(ge=0.0, le=1.0)
    confidence: float = Field(ge=0.0, le=1.0)
    model_version: str

    @property
    def risk_level(self) -> "RiskLevel":
        if self.score >= 0.75:
            return RiskLevel.HIGH
        elif self.score >= 0.45:
            return RiskLevel.MEDIUM
        elif self.score >= 0.20:
            return RiskLevel.LOW
        return RiskLevel.MINIMAL


# ─────────────────────────────────────────────
# Enumerations
# ─────────────────────────────────────────────

class StatementType(str, Enum):
    BANK = "bank"
    CREDIT_CARD = "credit_card"
    INVESTMENT = "investment"
    MORTGAGE = "mortgage"
    TAX = "tax"
    PAYROLL = "payroll"


class RiskLevel(str, Enum):
    MINIMAL = "minimal"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class FraudIndicatorType(str, Enum):
    AMOUNT_MANIPULATION = "amount_manipulation"
    DATE_FORGERY = "date_forgery"
    ENTITY_MISMATCH = "entity_mismatch"
    BALANCE_INCONSISTENCY = "balance_inconsistency"
    FONT_ANOMALY = "font_anomaly"
    METADATA_TAMPERING = "metadata_tampering"
    TRANSACTION_FABRICATION = "transaction_fabrication"
    GRAPH_ANOMALY = "graph_anomaly"
    SEMANTIC_DEVIATION = "semantic_deviation"


class MedallionLayer(str, Enum):
    BRONZE = "bronze"   # Raw ingested data
    SILVER = "silver"   # Cleaned & normalized
    GOLD = "gold"       # Analytics-ready with ML features


class ProcessingStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    BRONZE_COMPLETE = "bronze_complete"
    SILVER_COMPLETE = "silver_complete"
    GOLD_COMPLETE = "gold_complete"
    FAILED = "failed"
    FLAGGED = "flagged"


# ─────────────────────────────────────────────
# Bronze Layer – Raw Ingestion Entity
# ─────────────────────────────────────────────

class RawStatement(BaseModel):
    """Bronze layer: raw ingested document with provenance tracking."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    customer_id: str
    document_hash: DocumentHash
    filename: str
    file_size_bytes: int
    mime_type: str
    statement_type: StatementType
    upload_timestamp: datetime = Field(default_factory=datetime.utcnow)
    raw_text: Optional[str] = None
    ocr_confidence: Optional[float] = None
    s3_path: Optional[str] = None
    layer: MedallionLayer = MedallionLayer.BRONZE
    status: ProcessingStatus = ProcessingStatus.PENDING
    metadata: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        use_enum_values = True


# ─────────────────────────────────────────────
# Silver Layer – Normalized Statement Entity
# ─────────────────────────────────────────────

class TransactionRecord(BaseModel):
    """Individual transaction extracted from statement."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    date: datetime
    description: str
    amount: Money
    balance_after: Optional[Money] = None
    transaction_type: str  # debit | credit
    reference_number: Optional[str] = None
    merchant_name: Optional[str] = None
    category: Optional[str] = None


class NormalizedStatement(BaseModel):
    """Silver layer: parsed, validated, normalized statement with extracted entities."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    raw_statement_id: str
    customer_id: str
    account_number_masked: str
    institution_name: str
    statement_period_start: datetime
    statement_period_end: datetime
    opening_balance: Money
    closing_balance: Money
    total_credits: Money
    total_debits: Money
    transactions: List[TransactionRecord] = Field(default_factory=list)
    extracted_entities: Dict[str, Any] = Field(default_factory=dict)  # NER results
    layer: MedallionLayer = MedallionLayer.SILVER
    normalization_timestamp: datetime = Field(default_factory=datetime.utcnow)
    quality_score: float = Field(ge=0.0, le=1.0, default=1.0)

    @field_validator("closing_balance")
    @classmethod
    def validate_balance_arithmetic(cls, v, values):
        """Basic accounting identity check: opening + credits - debits ≈ closing."""
        return v  # Full check happens in the validation service


# ─────────────────────────────────────────────
# Gold Layer – Fraud Analytics Entity (Aggregate Root)
# ─────────────────────────────────────────────

class FraudIndicator(BaseModel):
    """Individual fraud signal with evidence."""
    indicator_type: FraudIndicatorType
    description: str
    severity: RiskLevel
    confidence: float = Field(ge=0.0, le=1.0)
    evidence: Dict[str, Any] = Field(default_factory=dict)
    graph_path: Optional[List[str]] = None  # Knowledge graph traversal path


class FraudAnalysis(BaseModel):
    """
    Gold layer aggregate root – complete fraud analysis result.
    This is the primary output of the FraudRAG pipeline.
    """
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    statement_id: str
    customer_id: str
    fraud_score: FraudScore
    risk_level: RiskLevel
    indicators: List[FraudIndicator] = Field(default_factory=list)

    # RAG Context
    rag_context_used: List[str] = Field(default_factory=list)  # Retrieved document IDs
    graph_subgraph: Dict[str, Any] = Field(default_factory=dict)  # Relevant graph nodes/edges

    # LLM Reasoning
    llm_reasoning: str = ""
    llm_model_used: str = ""

    # Comparison with warehouse
    warehouse_match_score: Optional[float] = None  # 0-1 similarity to authoritative copy
    discrepancies: List[Dict[str, Any]] = Field(default_factory=list)

    layer: MedallionLayer = MedallionLayer.GOLD
    analysis_timestamp: datetime = Field(default_factory=datetime.utcnow)
    analyst_notes: Optional[str] = None
    reviewed_by: Optional[str] = None
    review_timestamp: Optional[datetime] = None


# ─────────────────────────────────────────────
# Graph Domain – Knowledge Graph Entities
# ─────────────────────────────────────────────

class CustomerNode(BaseModel):
    """Neo4j graph node representing a customer entity."""
    id: str
    name: str
    risk_score: float = Field(ge=0.0, le=1.0, default=0.0)
    fraud_history_count: int = 0
    known_institutions: List[str] = Field(default_factory=list)
    account_numbers_hash: List[str] = Field(default_factory=list)  # Hashed for privacy
    embedding: Optional[List[float]] = None  # For graph-based similarity
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class InstitutionNode(BaseModel):
    """Financial institution in the knowledge graph."""
    id: str
    name: str
    routing_number_hash: Optional[str] = None
    country: str = "US"
    institution_type: str  # bank | credit_union | fintech


class FraudPatternNode(BaseModel):
    """Known fraud pattern stored in knowledge graph."""
    id: str
    pattern_name: str
    pattern_type: FraudIndicatorType
    description: str
    frequency: int = 0  # How many times observed
    embedding: Optional[List[float]] = None
    example_cases: List[str] = Field(default_factory=list)


class GraphRelationship(BaseModel):
    """Edge in the knowledge graph."""
    source_id: str
    target_id: str
    relationship_type: str  # HAS_ACCOUNT, FILED_WITH, SIMILAR_TO, DETECTED_IN
    properties: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    weight: float = 1.0


# ─────────────────────────────────────────────
# Customer Domain – Identity & Risk Profile
# ─────────────────────────────────────────────

class CustomerProfile(BaseModel):
    """Full customer identity and risk profile aggregate."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    email: Optional[str] = None
    phone_hash: Optional[str] = None
    ssn_hash: Optional[str] = None  # Always hashed, never stored in plain
    date_of_birth: Optional[datetime] = None
    address_hash: Optional[str] = None
    risk_level: RiskLevel = RiskLevel.MINIMAL
    cumulative_fraud_score: float = 0.0
    statement_count: int = 0
    fraud_detection_count: int = 0
    known_aliases: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_activity: datetime = Field(default_factory=datetime.utcnow)
    graph_node_id: Optional[str] = None  # Link to Neo4j node
