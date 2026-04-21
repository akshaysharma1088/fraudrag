"""
FraudRAG: AI-Powered Financial Statement Fraud Detection
Using Knowledge Graph RAG + Medallion Architecture
"""

import logging
import time
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from prometheus_client import Counter, Histogram, make_asgi_app

from backend.api.routes import fraud, graph, health, statements, customers
from backend.core.config import get_settings
from backend.core.database import init_db
from backend.graph.neo4j_client import Neo4jClient
from backend.services.graph_rag_service import GraphRAGService

settings = get_settings()
logger = structlog.get_logger(__name__)

# Prometheus metrics
REQUEST_COUNT = Counter("fraudrag_requests_total", "Total requests", ["method", "endpoint", "status"])
REQUEST_LATENCY = Histogram("fraudrag_request_latency_seconds", "Request latency", ["endpoint"])
FRAUD_DETECTIONS = Counter("fraudrag_fraud_detections_total", "Fraud detection results", ["result"])


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown lifecycle manager."""
    logger.info("FraudRAG starting up", version=settings.APP_VERSION)

    # Initialize database connections
    await init_db()

    # Initialize Neo4j knowledge graph
    neo4j = Neo4jClient(settings.NEO4J_URI, settings.NEO4J_USER, settings.NEO4J_PASSWORD)
    await neo4j.initialize_schema()
    app.state.neo4j = neo4j

    # Initialize Graph RAG service
    rag_service = GraphRAGService(neo4j_client=neo4j)
    await rag_service.initialize()
    app.state.rag_service = rag_service

    logger.info("All services initialized successfully")
    yield

    # Cleanup
    await neo4j.close()
    logger.info("FraudRAG shutting down")


def create_app() -> FastAPI:
    app = FastAPI(
        title="FraudRAG — Statement Fraud Detection via Knowledge Graph RAG",
        description="""
## FraudRAG API

Knowledge Graph-Augmented Retrieval (Graph-RAG) system for detecting financial
statement fraud. Built on Domain-Driven Design + Medallion Architecture.

### Key Features
- 📄 PDF/image statement ingestion and OCR
- 🕸️ Neo4j knowledge graph for customer entity relationships
- 🔍 Semantic similarity via ChromaDB vector store
- 🤖 LangChain RAG pipeline with GPT-4/Claude reasoning
- 🏅 Medallion architecture (Bronze → Silver → Gold) for data quality
- 📊 Real-time fraud scoring with explainability

### Architecture
```
Bronze Layer  →  Raw statement ingestion, OCR, hashing
Silver Layer  →  Normalized entities, feature extraction
Gold Layer    →  Fraud signals, graph embeddings, risk scores
```
        """,
        version=settings.APP_VERSION,
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    # Middleware
    app.add_middleware(GZipMiddleware, minimum_size=1000)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Request timing middleware
    @app.middleware("http")
    async def add_process_time_header(request: Request, call_next):
        start = time.time()
        response = await call_next(request)
        duration = time.time() - start
        response.headers["X-Process-Time"] = str(duration)
        REQUEST_LATENCY.labels(endpoint=request.url.path).observe(duration)
        REQUEST_COUNT.labels(
            method=request.method,
            endpoint=request.url.path,
            status=response.status_code
        ).inc()
        return response

    # Routers
    app.include_router(health.router, prefix="/api/v1", tags=["Health"])
    app.include_router(statements.router, prefix="/api/v1/statements", tags=["Statements"])
    app.include_router(fraud.router, prefix="/api/v1/fraud", tags=["Fraud Detection"])
    app.include_router(graph.router, prefix="/api/v1/graph", tags=["Knowledge Graph"])
    app.include_router(customers.router, prefix="/api/v1/customers", tags=["Customers"])

    # Prometheus metrics endpoint
    metrics_app = make_asgi_app()
    app.mount("/metrics", metrics_app)

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info",
    )
