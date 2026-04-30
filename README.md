# ⧫ FraudRAG

**Knowledge Graph-Augmented Retrieval for Real-Time Financial Statement Fraud Detection**

[![CI/CD](https://github.com/akshaysharma1088/fraudrag/actions/workflows/ci-cd.yml/badge.svg)](https://github.com/akshaysharma1088/fraudrag/actions)
[![Python 3.12](https://img.shields.io/badge/python-3.12.3-blue.svg)](https://python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Neo4j 5.25](https://img.shields.io/badge/Neo4j-5.25-green.svg)](https://neo4j.com)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-teal.svg)](https://fastapi.tiangolo.com)
[![Claude 3.5](https://img.shields.io/badge/LLM-Claude%203.5%20Sonnet-orange.svg)](https://anthropic.com)
[![IEEE TKDE](https://img.shields.io/badge/Paper-IEEE%20TKDE%20Submission-red.svg)](docs/)
[![Docker](https://img.shields.io/badge/Docker-ghcr.io%2Fakshaysharma1088-blue.svg)](https://github.com/akshaysharma1088/fraudrag/pkgs/container/fraudrag-api)

---

## Overview

FraudRAG is a production-grade system that detects forged or manipulated financial statements by combining three innovations:

- **Knowledge Graph RAG** — Neo4j stores customer entity history, institution relationships, and known fraud patterns. At inference time, a multi-hop graph traversal retrieves rich contextual signals injected into the LLM prompt alongside ChromaDB vector-similarity results from historical statements.
- **Medallion Architecture** — Documents flow through Bronze (OCR + hashing) → Silver (NER + balance validation) → Gold (Graph-RAG scoring) with explicit data quality contracts at each layer boundary.
- **Domain-Driven Design** — Four bounded contexts: `StatementContext`, `FraudContext`, `GraphContext`, `CustomerContext`. Aggregates, value objects, and domain events follow DDD tactical patterns.

> **IEEE TKDE Submission** — This system is the subject of an ongoing submission to IEEE Transactions on Knowledge and Data Engineering (IF=8.9).

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         FraudRAG System                              │
│                                                                      │
│  ┌──────────┐    ┌──────────────────────────────────────────────┐   │
│  │ React UI │───▶│              FastAPI Backend                  │   │
│  └──────────┘    │                                              │   │
│                  │  ┌───────────────────────────────────────┐   │   │
│                  │  │         Medallion Pipeline             │   │   │
│                  │  │  [BRONZE]  OCR + Hash + Provenance     │   │   │
│                  │  │     ▼                                  │   │   │
│                  │  │  [SILVER]  NER + Balance Validation    │   │   │
│                  │  │     ▼                                  │   │   │
│                  │  │  [GOLD]    Graph-RAG + LLM Scoring     │   │   │
│                  │  └───────────────┬───────────────────────┘   │   │
│                  │                  │                            │   │
│                  │  ┌───────────────▼───────────────────────┐   │   │
│                  │  │         Graph-RAG Service              │   │   │
│                  │  │  1. Neo4j k-hop traversal (k=2)        │   │   │
│                  │  │  2. ChromaDB ANN retrieval (top-k=4)   │   │   │
│                  │  │  3. Prompt augmentation                 │   │   │
│                  │  │  4. Claude 3.5 Sonnet inference         │   │   │
│                  │  └───────────────────────────────────────┘   │   │
│                  └──────────────────────────────────────────────┘   │
│                                                                      │
│  ┌──────────┐  ┌──────────┐  ┌────────────┐  ┌─────┐  ┌────────┐  │
│  │ Neo4j    │  │ChromaDB  │  │PostgreSQL  │  │Redis│  │AWS S3  │  │
│  │Knowledge │  │Vector    │  │Metadata    │  │Cache│  │Delta   │  │
│  │Graph     │  │Store     │  │+ Audit     │  │     │  │Lake    │  │
│  └──────────┘  └──────────┘  └────────────┘  └─────┘  └────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

### Medallion Architecture

| Layer | Responsibility | Key Operation |
|-------|---------------|---------------|
| **Bronze** | Raw ingestion: OCR, SHA-256 hash, provenance | Tamper-evident fingerprinting |
| **Silver** | NER extraction, balance arithmetic validation | `open + Σcredits − Σdebits = close ± $0.50` |
| **Gold** | ML features, Graph-RAG scoring, analyst review | AUC=0.943, F1=0.883 |

### Knowledge Graph Schema

```cypher
(:Customer {id, name, risk_score, fraud_history_count})
(:Institution {id, name, routing_number_hash, institution_type})
(:Statement {id, period, fraud_flagged, fraud_score})
(:FraudPattern {id, pattern_name, pattern_type, frequency})

(Customer)-[:FILED]->(Statement)
(Statement)-[:ISSUED_BY]->(Institution)
(Customer)-[:HAS_ACCOUNT]->(Institution)
(Customer)-[:MATCHES_PATTERN]->(FraudPattern)
(Customer)-[:LINKED_TO]->(Customer)   // Fraud ring detection
```

---

## Results

| Method | AUC | Precision | Recall | F1 | Latency |
|--------|-----|-----------|--------|-----|---------|
| Rule-Based | 0.741 | 0.683 | 0.712 | 0.697 | < 10 ms |
| LLM-Only | 0.819 | 0.771 | 0.748 | 0.759 | 1.8 s |
| RAG-Only | 0.877 | 0.831 | 0.804 | 0.817 | 2.1 s |
| Graph-Only | 0.893 | 0.847 | 0.831 | 0.839 | 2.3 s |
| **FraudRAG (ours)** | **0.943** | **0.891** | **0.876** | **0.883** | **2.8 s** |

*Benchmark: FraudRAG-2400 synthetic dataset · LLM: Claude 3.5 Sonnet · k-hop=2, top-k=4*

---

## Project Structure

```
fraudrag/
├── backend/
│   ├── api/routes/          # FastAPI routers (statements, fraud, graph, customers)
│   ├── core/                # Config, database initialization
│   ├── models/domain.py     # DDD aggregates & value objects
│   ├── services/
│   │   └── graph_rag_service.py   # Core Graph-RAG orchestration
│   ├── pipelines/
│   │   └── medallion.py     # Bronze / Silver / Gold pipeline
│   ├── graph/
│   │   └── neo4j_client.py  # Knowledge graph operations
│   ├── requirements.txt     # Production dependencies
│   └── requirements-ci.txt  # CI/testing dependencies (no Spark/heavy ML)
├── frontend/
│   └── src/
│       ├── pages/           # Dashboard, Upload, Analysis, GraphView
│       └── index.css        # Design system (dark forensic theme)
├── tests/
│   ├── test_pipeline.py     # Medallion + API tests (23 tests)
│   └── conftest.py          # Pytest configuration
├── docker/
│   ├── Dockerfile.backend   # API container (python:3.12.3-slim)
│   ├── Dockerfile.frontend  # UI container (nginx)
│   └── Dockerfile.backend-spark  # Batch pipeline (with Java/PySpark)
├── docs/                    # IEEE TKDE manuscript & figures
├── scripts/                 # Paper generation, figure generation
├── docker-compose.yml       # Full stack: API + UI + Neo4j + PostgreSQL + Redis
└── .github/workflows/
    └── ci-cd.yml            # Test → Security Scan → Docker Build → Deploy
```

---

## Quick Start

### Docker Compose (Recommended)

```bash
# 1. Clone
git clone https://github.com/akshaysharma1088/fraudrag.git
cd fraudrag

# 2. Configure
cp .env.example .env
# Edit .env — add ANTHROPIC_API_KEY or OPENAI_API_KEY

# 3. Launch
docker compose up -d

# 4. Seed demo knowledge graph
curl -X POST http://localhost:8000/api/v1/graph/seed

# 5. Open UI
open http://localhost:3000
```

| Service | URL |
|---------|-----|
| React UI | http://localhost:3000 |
| FastAPI Docs | http://localhost:8000/docs |
| Neo4j Browser | http://localhost:7474 |
| Prometheus | http://localhost:9090 |
| Grafana | http://localhost:3001 |

### Local Development

```bash
# Backend
cd fraudrag
python -m venv .venv && source .venv/bin/activate
pip install -r backend/requirements-ci.txt
uvicorn backend.main:app --reload --port 8000

# Frontend (new terminal)
cd frontend
npm install
npm run dev   # → http://localhost:3000
```

---

## API Reference

### Upload a Statement for Fraud Analysis

```bash
curl -X POST http://localhost:8000/api/v1/statements/upload \
  -F "file=@bank_statement.pdf" \
  -F "customer_id=cust-001" \
  -F "statement_type=bank"
```

```json
{
  "statement_id": "3f8a2b1c-...",
  "customer_id": "cust-001",
  "status": "gold_complete",
  "quality_score": 0.85,
  "message": "Statement processed. Fraud analysis complete."
}
```

### Get Fraud Analysis

```bash
curl http://localhost:8000/api/v1/fraud/analysis/3f8a2b1c-...
```

### Query Knowledge Graph

```bash
# 2-hop customer neighborhood
curl http://localhost:8000/api/v1/graph/customer/cust-001

# Fraud ring detection
curl http://localhost:8000/api/v1/graph/customer/cust-001/rings
```

Full API docs: **http://localhost:8000/docs**

---

## Running Tests

```bash
pytest tests/ -v --cov=backend
# 23 tests, ~4.5s
```

---

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `LLM_PROVIDER` | `openai` | `openai` or `anthropic` |
| `ANTHROPIC_API_KEY` | — | Required for Claude 3.5 Sonnet |
| `OPENAI_API_KEY` | — | Required for GPT-4o |
| `NEO4J_URI` | `bolt://localhost:7687` | Neo4j connection |
| `FRAUD_SCORE_HIGH_RISK` | `0.75` | HIGH risk threshold |
| `CHROMA_PERSIST_DIR` | `./data/chroma` | Vector store path |

---

## Fraud Detection Capabilities

| Indicator | Detection Method |
|-----------|-----------------|
| Balance arithmetic manipulation | Silver layer accounting identity check |
| Amount digit substitution (1200→12000) | Claude 3.5 Sonnet + pattern matching |
| Date forgery / future dates | NER + date range validation |
| Entity name mismatch | NER entity alignment |
| Metadata tampering | SHA-256 hash comparison |
| Known fraud pattern match | Neo4j vector similarity |
| Fraud ring membership | Neo4j multi-hop traversal |
| Semantic deviation from institution templates | ChromaDB cosine similarity |

---

## Tech Stack

| Component | Technology |
|-----------|-----------|
| API | FastAPI 0.115, Python 3.12 |
| LLM | Claude 3.5 Sonnet (Anthropic) |
| LLM Orchestration | LangChain 0.2 |
| Knowledge Graph | Neo4j 5.25 |
| Vector Store | ChromaDB 0.5 |
| Embeddings | text-embedding-3-large |
| OCR | Tesseract 5 + pdfplumber |
| Batch Processing | PySpark 3.5 + AWS EMR |
| Frontend | React 18 + Vite |
| Monitoring | Prometheus + Grafana |
| CI/CD | GitHub Actions |

---

## IEEE TKDE Publication

This system is the subject of:

> **FraudRAG: Knowledge Graph-Augmented Retrieval for Real-Time Financial Statement Fraud Detection Using a Domain-Driven Medallion Architecture**
> Akshay Sharma, IEEE Senior Member, IET Member
> *Submitted to IEEE Transactions on Knowledge and Data Engineering (IF=8.9), 2025*

The manuscript, figures, and benchmark generation scripts are available in the [`docs/`](docs/) directory.

---

## Citation

```bibtex
@article{fraudrag2025,
  title={FraudRAG: Knowledge Graph-Augmented Retrieval for Real-Time
         Financial Statement Fraud Detection Using a Domain-Driven
         Medallion Architecture},
  author={Sharma, Akshay},
  journal={IEEE Transactions on Knowledge and Data Engineering},
  year={2025},
  publisher={IEEE}
}
```

---

## License

MIT License — see [LICENSE](LICENSE)

---

## Author

**Akshay Sharma** · IEEE Senior Member · IET Member
- LinkedIn: [linkedin.com/in/akshay-sharma-1088](https://linkedin.com/in/akshay-sharma-1088)
- Medium: [medium.com/@akshay.sharma1088](https://medium.com/@akshay.sharma1088)
- IEEE: [akshay.sharma1088@ieee.org](mailto:akshay.sharma1088@ieee.org)
