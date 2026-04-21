"""
FraudRAG Test Suite
Tests for Medallion pipeline, domain models, and API endpoints.
All external services (Neo4j, LLM, ChromaDB) are mocked for CI.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock


# ─── Domain Model Tests ───────────────────────────────────────

class TestFraudScore:
    def test_risk_level_high(self):
        from backend.models.domain import FraudScore, RiskLevel
        fs = FraudScore(score=0.80, confidence=0.9, model_version="test")
        assert fs.risk_level == RiskLevel.HIGH

    def test_risk_level_minimal(self):
        from backend.models.domain import FraudScore, RiskLevel
        fs = FraudScore(score=0.05, confidence=0.95, model_version="test")
        assert fs.risk_level == RiskLevel.MINIMAL

    def test_risk_level_medium(self):
        from backend.models.domain import FraudScore, RiskLevel
        fs = FraudScore(score=0.55, confidence=0.8, model_version="test")
        assert fs.risk_level == RiskLevel.MEDIUM

    def test_score_bounds_invalid(self):
        from backend.models.domain import FraudScore
        with pytest.raises(Exception):
            FraudScore(score=1.5, confidence=0.9, model_version="test")


class TestDocumentHash:
    def test_hash_deterministic(self):
        from backend.models.domain import DocumentHash
        data = b"test document content"
        assert DocumentHash.from_bytes(data) == DocumentHash.from_bytes(data)

    def test_different_content_different_hash(self):
        from backend.models.domain import DocumentHash
        assert DocumentHash.from_bytes(b"A") != DocumentHash.from_bytes(b"B")

    def test_hash_is_64_chars(self):
        from backend.models.domain import DocumentHash
        assert len(DocumentHash.from_bytes(b"data").value) == 64


# ─── Bronze Pipeline Tests ────────────────────────────────────

class TestBronzePipeline:
    @pytest.mark.asyncio
    async def test_ingest_text_file(self, tmp_path):
        from backend.pipelines.medallion import BronzePipeline
        pipeline = BronzePipeline(storage_path=str(tmp_path))
        result = await pipeline.ingest(
            file_bytes=b"Account: ****1234\nBalance: $1,000.00",
            filename="test.txt", customer_id="cust-001",
            statement_type="bank", mime_type="text/plain",
        )
        assert result["customer_id"] == "cust-001"
        assert result["status"] == "bronze_complete"
        assert result["layer"] == "bronze"
        assert len(result["document_hash"]) == 64

    @pytest.mark.asyncio
    async def test_ingest_stores_file(self, tmp_path):
        from backend.pipelines.medallion import BronzePipeline
        pipeline = BronzePipeline(storage_path=str(tmp_path))
        result = await pipeline.ingest(
            file_bytes=b"content", filename="stmt.txt",
            customer_id="c2", statement_type="bank", mime_type="text/plain",
        )
        assert (tmp_path / f"{result['id']}.json").exists()

    @pytest.mark.asyncio
    async def test_ingest_correct_hash(self, tmp_path):
        import hashlib
        from backend.pipelines.medallion import BronzePipeline
        content = b"deterministic"
        pipeline = BronzePipeline(storage_path=str(tmp_path))
        result = await pipeline.ingest(
            file_bytes=content, filename="f.txt",
            customer_id="c1", statement_type="bank", mime_type="text/plain",
        )
        assert result["document_hash"] == hashlib.sha256(content).hexdigest()


# ─── Silver Pipeline Tests ────────────────────────────────────

class TestSilverPipeline:
    def test_parse_amount_comma(self):
        from backend.pipelines.medallion import SilverPipeline
        assert SilverPipeline._parse_amount("1,234.56") == 1234.56

    def test_parse_amount_dollar(self):
        from backend.pipelines.medallion import SilverPipeline
        assert SilverPipeline._parse_amount("$500.00") == 500.0

    def test_parse_amount_none(self):
        from backend.pipelines.medallion import SilverPipeline
        assert SilverPipeline._parse_amount(None) is None

    def test_balance_valid(self):
        from backend.pipelines.medallion import SilverPipeline
        result = SilverPipeline()._validate_balances(
            {"opening_balance": 1000.0, "closing_balance": 1200.0},
            [{"amount": 200.0}]
        )
        assert result["is_valid"] is True

    def test_balance_invalid(self):
        from backend.pipelines.medallion import SilverPipeline
        result = SilverPipeline()._validate_balances(
            {"opening_balance": 1000.0, "closing_balance": 5000.0},
            [{"amount": 200.0}]
        )
        assert result["is_valid"] is False

    def test_balance_missing_fields(self):
        from backend.pipelines.medallion import SilverPipeline
        result = SilverPipeline()._validate_balances({}, [])
        assert result["confidence"] == 0.0

    def test_balance_rounding_tolerance(self):
        from backend.pipelines.medallion import SilverPipeline
        result = SilverPipeline()._validate_balances(
            {"opening_balance": 1000.0, "closing_balance": 1200.30},
            [{"amount": 200.0}]
        )
        assert result["is_valid"] is True

    @pytest.mark.asyncio
    async def test_normalize_produces_silver_record(self, tmp_path):
        from backend.pipelines.medallion import SilverPipeline
        result = await SilverPipeline(storage_path=str(tmp_path)).normalize({
            "id": "b-001", "customer_id": "c-001",
            "raw_text": "Account: ****1234\nOpening Balance: $1000.00\nClosing Balance: $1200.00",
            "statement_type": "bank", "ocr_confidence": 0.95,
        })
        assert result["layer"] == "silver"
        assert result["status"] == "silver_complete"
        assert result["raw_statement_id"] == "b-001"


# ─── Gold Pipeline Tests ──────────────────────────────────────

class TestGoldPipeline:
    def test_round_number_ratio_all_round(self):
        from backend.pipelines.medallion import GoldPipeline
        assert GoldPipeline._round_number_ratio([1000.0, 2000.0]) == 1.0

    def test_round_number_ratio_none_round(self):
        from backend.pipelines.medallion import GoldPipeline
        assert GoldPipeline._round_number_ratio([123.45, 67.89]) == 0.0

    def test_round_number_ratio_empty(self):
        from backend.pipelines.medallion import GoldPipeline
        assert GoldPipeline._round_number_ratio([]) == 0.0

    @pytest.mark.asyncio
    async def test_enrich_produces_gold_record(self, tmp_path):
        from backend.pipelines.medallion import GoldPipeline
        result = await GoldPipeline(storage_path=str(tmp_path)).enrich({
            "id": "s-001", "raw_statement_id": "b-001", "customer_id": "c-001",
            "transactions": [{"amount": 100.0}, {"amount": 200.0}],
            "entities": {"institution_name": "Test Bank"},
            "balance_check": {"is_valid": True}, "quality_score": 0.85,
        })
        assert result["layer"] == "gold"
        assert result["features"]["transaction_count"] == 2


# ─── API Endpoint Tests ───────────────────────────────────────

@pytest.fixture
def mock_app():
    # testing=True bypasses real lifespan (no Neo4j/ChromaDB connections needed)
    from backend.main import create_app
    app = create_app(testing=True)
    mock_neo4j = AsyncMock()
    mock_neo4j.initialize_schema = AsyncMock()
    mock_neo4j.close = AsyncMock()
    mock_neo4j.get_graph_context_for_rag = AsyncMock(return_value="ctx")
    mock_neo4j.driver = MagicMock()
    mock_neo4j.database = "neo4j"
    mock_rag = AsyncMock()
    mock_rag.initialize = AsyncMock()
    app.state.neo4j = mock_neo4j
    app.state.rag_service = mock_rag
    yield app


@pytest.mark.asyncio
async def test_health_live(mock_app):
    from httpx import AsyncClient, ASGITransport
    async with AsyncClient(transport=ASGITransport(app=mock_app), base_url="http://test") as c:
        r = await c.get("/api/v1/health/live")
    assert r.status_code == 200
    assert r.json()["alive"] is True


@pytest.mark.asyncio
async def test_health_ready(mock_app):
    from httpx import AsyncClient, ASGITransport
    async with AsyncClient(transport=ASGITransport(app=mock_app), base_url="http://test") as c:
        r = await c.get("/api/v1/health/ready")
    assert r.status_code == 200


@pytest.mark.asyncio
async def test_fraud_dashboard_empty(mock_app):
    from httpx import AsyncClient, ASGITransport
    async with AsyncClient(transport=ASGITransport(app=mock_app), base_url="http://test") as c:
        r = await c.get("/api/v1/fraud/dashboard")
    assert r.status_code == 200
    assert r.json()["total_analyzed"] == 0


@pytest.mark.asyncio
async def test_statement_not_found(mock_app):
    from httpx import AsyncClient, ASGITransport
    async with AsyncClient(transport=ASGITransport(app=mock_app), base_url="http://test") as c:
        r = await c.get("/api/v1/statements/does-not-exist")
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_list_statements_empty(mock_app):
    from httpx import AsyncClient, ASGITransport
    async with AsyncClient(transport=ASGITransport(app=mock_app), base_url="http://test") as c:
        r = await c.get("/api/v1/statements/")
    assert r.status_code == 200
    assert r.json()["total"] == 0


@pytest.mark.asyncio
async def test_upload_statement(mock_app):
    from httpx import AsyncClient, ASGITransport
    from backend.models.domain import FraudAnalysis, FraudScore, RiskLevel
    mock_app.state.rag_service.analyze_statement = AsyncMock(return_value=FraudAnalysis(
        statement_id="test-001", customer_id="cust-001",
        fraud_score=FraudScore(score=0.1, confidence=0.9, model_version="test"),
        risk_level=RiskLevel.MINIMAL,
        llm_reasoning="No fraud.", llm_model_used="test/mock",
    ))
    async with AsyncClient(transport=ASGITransport(app=mock_app), base_url="http://test") as c:
        r = await c.post(
            "/api/v1/statements/upload",
            files={"file": ("s.txt", b"Bank Statement\nAccount: ****1234", "text/plain")},
            data={"customer_id": "cust-001", "statement_type": "bank"},
        )
    assert r.status_code == 202
    assert r.json()["customer_id"] == "cust-001"


@pytest.mark.asyncio
async def test_create_customer(mock_app):
    from httpx import AsyncClient, ASGITransport
    mock_app.state.neo4j.upsert_customer = AsyncMock(return_value={"id": "new"})
    async with AsyncClient(transport=ASGITransport(app=mock_app), base_url="http://test") as c:
        r = await c.post("/api/v1/customers/", json={"name": "Alice", "email": "a@b.com"})
    assert r.status_code == 200
    assert "customer_id" in r.json()
