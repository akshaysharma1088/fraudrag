"""
FraudRAG Test Suite
Tests for Medallion pipeline, domain models, and API endpoints.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from httpx import AsyncClient, ASGITransport


# ─── Domain Model Tests ───────────────────────────────────────

class TestFraudScore:
    def test_risk_level_high(self):
        from backend.models.domain import FraudScore
        fs = FraudScore(score=0.80, confidence=0.9, model_version="test")
        from backend.models.domain import RiskLevel
        assert fs.risk_level == RiskLevel.HIGH

    def test_risk_level_minimal(self):
        from backend.models.domain import FraudScore, RiskLevel
        fs = FraudScore(score=0.05, confidence=0.95, model_version="test")
        assert fs.risk_level == RiskLevel.MINIMAL

    def test_score_bounds(self):
        from backend.models.domain import FraudScore
        import pytest
        with pytest.raises(Exception):
            FraudScore(score=1.5, confidence=0.9, model_version="test")


class TestDocumentHash:
    def test_hash_deterministic(self):
        from backend.models.domain import DocumentHash
        data = b"test document content"
        h1 = DocumentHash.from_bytes(data)
        h2 = DocumentHash.from_bytes(data)
        assert h1 == h2

    def test_different_content_different_hash(self):
        from backend.models.domain import DocumentHash
        h1 = DocumentHash.from_bytes(b"content A")
        h2 = DocumentHash.from_bytes(b"content B")
        assert h1 != h2


# ─── Bronze Pipeline Tests ────────────────────────────────────

class TestBronzePipeline:
    @pytest.mark.asyncio
    async def test_ingest_text_file(self, tmp_path):
        from backend.pipelines.medallion import BronzePipeline
        pipeline = BronzePipeline(storage_path=str(tmp_path))
        result = await pipeline.ingest(
            file_bytes=b"Account: ****1234\nBalance: $1,000.00",
            filename="test.txt",
            customer_id="cust-001",
            statement_type="bank",
            mime_type="text/plain",
        )
        assert result["customer_id"] == "cust-001"
        assert result["status"] == "bronze_complete"
        assert result["layer"] == "bronze"
        assert "document_hash" in result
        assert len(result["document_hash"]) == 64  # SHA-256 hex

    @pytest.mark.asyncio
    async def test_ingest_stores_file(self, tmp_path):
        from backend.pipelines.medallion import BronzePipeline
        pipeline = BronzePipeline(storage_path=str(tmp_path))
        result = await pipeline.ingest(
            file_bytes=b"Bank Statement Content",
            filename="stmt.txt",
            customer_id="cust-002",
            statement_type="bank",
            mime_type="text/plain",
        )
        stored = tmp_path / f"{result['id']}.json"
        assert stored.exists()


# ─── Silver Pipeline Tests ────────────────────────────────────

class TestSilverPipeline:
    def test_extract_entities_account(self):
        from backend.pipelines.medallion import SilverPipeline
        pipeline = SilverPipeline()
        entities = pipeline._extract_entities("Account: ****5678\nFirst National Bank")
        assert "account_number_masked" in entities

    def test_parse_amount(self):
        from backend.pipelines.medallion import SilverPipeline
        assert SilverPipeline._parse_amount("1,234.56") == 1234.56
        assert SilverPipeline._parse_amount("$500.00") == 500.0
        assert SilverPipeline._parse_amount(None) is None

    def test_balance_validation_valid(self):
        from backend.pipelines.medallion import SilverPipeline
        pipeline = SilverPipeline()
        entities = {"opening_balance": 1000.0, "closing_balance": 1200.0}
        transactions = [{"amount": 200.0}, {"amount": 0.0}]
        result = pipeline._validate_balances(entities, transactions)
        assert result["is_valid"] is True

    def test_balance_validation_invalid(self):
        from backend.pipelines.medallion import SilverPipeline
        pipeline = SilverPipeline()
        entities = {"opening_balance": 1000.0, "closing_balance": 5000.0}  # Manipulated!
        transactions = [{"amount": 200.0}]
        result = pipeline._validate_balances(entities, transactions)
        assert result["is_valid"] is False
        assert result["discrepancy"] > 0

    def test_round_number_ratio(self):
        from backend.pipelines.medallion import GoldPipeline
        # All round numbers = suspicious
        amounts = [1000.0, 2000.0, 3000.0]
        ratio = GoldPipeline._round_number_ratio(amounts)
        assert ratio == 1.0

        # No round numbers
        amounts2 = [123.45, 67.89, 42.01]
        ratio2 = GoldPipeline._round_number_ratio(amounts2)
        assert ratio2 == 0.0


# ─── API Tests ────────────────────────────────────────────────

@pytest.fixture
def mock_app():
    """Create test app with mocked external services."""
    from backend.main import create_app
    app = create_app()
    # Mock external services
    app.state.neo4j = AsyncMock()
    app.state.neo4j.get_graph_context_for_rag = AsyncMock(return_value="Mock graph context")
    app.state.rag_service = AsyncMock()
    return app


@pytest.mark.asyncio
async def test_health_endpoint(mock_app):
    async with AsyncClient(transport=ASGITransport(app=mock_app), base_url="http://test") as client:
        response = await client.get("/api/v1/health/live")
    assert response.status_code == 200
    assert response.json()["alive"] is True


@pytest.mark.asyncio
async def test_fraud_dashboard_empty(mock_app):
    async with AsyncClient(transport=ASGITransport(app=mock_app), base_url="http://test") as client:
        response = await client.get("/api/v1/fraud/dashboard")
    assert response.status_code == 200
    data = response.json()
    assert "total_analyzed" in data
    assert data["total_analyzed"] == 0


@pytest.mark.asyncio
async def test_statement_not_found(mock_app):
    async with AsyncClient(transport=ASGITransport(app=mock_app), base_url="http://test") as client:
        response = await client.get("/api/v1/statements/nonexistent-id")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_upload_statement(mock_app, tmp_path):
    from unittest.mock import patch
    from backend.models.domain import FraudAnalysis, FraudScore, RiskLevel

    mock_analysis = FraudAnalysis(
        statement_id="test-stmt",
        customer_id="cust-001",
        fraud_score=FraudScore(score=0.1, confidence=0.9, model_version="test"),
        risk_level=RiskLevel.MINIMAL,
        llm_reasoning="No fraud indicators detected.",
        llm_model_used="test",
    )

    mock_app.state.rag_service.analyze_statement = AsyncMock(return_value=mock_analysis)

    async with AsyncClient(transport=ASGITransport(app=mock_app), base_url="http://test") as client:
        response = await client.post(
            "/api/v1/statements/upload",
            files={"file": ("statement.txt", b"Bank Statement\nAccount: ****1234\nBalance: $1000", "text/plain")},
            data={"customer_id": "cust-001", "statement_type": "bank"},
        )
    assert response.status_code == 202
    data = response.json()
    assert "statement_id" in data
    assert data["customer_id"] == "cust-001"
