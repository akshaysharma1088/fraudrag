# ⧫ FraudRAG

**Knowledge Graph-Augmented Retrieval for Real-Time Financial Statement Fraud Detection**

[![CI/CD](https://github.com/your-org/fraudrag/actions/workflows/ci-cd.yml/badge.svg)](https://github.com/your-org/fraudrag/actions)
[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Neo4j 5.20](https://img.shields.io/badge/Neo4j-5.20-green.svg)](https://neo4j.com)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111-teal.svg)](https://fastapi.tiangolo.com)

---

## Overview

FraudRAG is a production-grade system that detects forged or manipulated financial statements by combining:

- **Knowledge Graph RAG** — Neo4j stores customer entity history, institution relationships, and known fraud patterns. At inference time, a multi-hop graph traversal retrieves rich contextual signals that are injected into the LLM prompt alongside vector-similarity results from ChromaDB.
- **Medallion Architecture** — Documents flow through three well-defined data quality layers (Bronze → Silver → Gold) before fraud scoring. Each layer is independently testable and observable.
- **Domain-Driven Design** — The codebase is organized around bounded contexts: `StatementContext`, `FraudContext`, `GraphContext`, and `CustomerContext`. Aggregates, value objects, and domain events follow DDD tactical patterns.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          FraudRAG System                               │
│                                                                         │
│  ┌──────────┐   ┌────────────────────────────────────────────────────┐  │
│  │ React UI │──▶│              FastAPI Backend                       │  │
│  └──────────┘   │                                                    │  │
│                 │  ┌─────────────────────────────────────────────┐   │  │
│                 │  │         Medallion Pipeline                  │   │  │
│                 │  │                                             │   │  │
│                 │  │  [BRONZE]  OCR + Hash + S3 ingestion        │   │  │
│                 │  │     ▼                                       │   │  │
│                 │  │  [SILVER]  NER + Normalize + Balance Check  │   │  │
│                 │  │     ▼                                       │   │  │
│                 │  │  [GOLD]    Feature Eng + Graph-RAG Scoring  │   │  │
│                 │  └────────────────────┬────────────────────────┘   │  │
│                 │                       │                             │  │
│                 │  ┌────────────────────▼────────────────────────┐   │  │
│                 │  │           Graph-RAG Service                 │   │  │
│                 │  │                                             │   │  │
│                 │  │  1. Neo4j subgraph traversal (k-hop)        │   │  │
│                 │  │  2. ChromaDB semantic similarity search     │   │  │
│                 │  │  3. Prompt augmentation                     │   │  │
│                 │  │  4. GPT-4o / Claude reasoning               │   │  │
│                 │  │  5. Structured output → FraudAnalysis       │   │  │
│                 │  └─────────────────────────────────────────────┘   │  │
│                 └────────────────────────────────────────────────────┘  │
│                                                                         │
│  ┌──────────────┐   ┌──────────────┐   ┌──────────┐   ┌───────────┐   │
│  │  Neo4j 5.20  │   │  ChromaDB    │   │PostgreSQL│   │   Redis   │   │
│  │  Knowledge   │   │  Vector Store│   │ Metadata │   │   Cache   │   │
│  │  Graph       │   │              │   │  + Audit │   │           │   │
│  └──────────────┘   └──────────────┘   └──────────┘   └───────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
```

### Medallion Architecture Layers

| Layer | Responsibility | Storage | Quality Check |
|-------|---------------|---------|---------------|
| **Bronze** | Raw ingestion: OCR, SHA-256 hash, mime detection, S3 write | `data/bronze/*.json` | File integrity, hash uniqueness |
| **Silver** | NER extraction, currency normalization, date parsing, balance arithmetic validation | `data/silver/*.json` | Accounting identity: `opening + Σcredits − Σdebits = closing` |
| **Gold** | ML features, graph embeddings, LLM fraud scoring, analyst verdicts | `data/gold/*.json` | Fraud score, confidence interval, RAG context quality |

### Knowledge Graph Schema

```cypher
// Nodes
(:Customer {id, name, risk_score, fraud_history_count})
(:Institution {id, name, routing_number_hash, institution_type})
(:Statement {id, period, fraud_flagged, fraud_score})
(:FraudPattern {id, pattern_name, pattern_type, frequency})
(:Transaction {id, date, amount, description})

// Relationships
(Customer)-[:FILED]->(Statement)
(Statement)-[:ISSUED_BY]->(Institution)
(Customer)-[:HAS_ACCOUNT]->(Institution)
(Customer)-[:MATCHES_PATTERN]->(FraudPattern)
(Statement)-[:DETECTED_IN]->(FraudPattern)
(Customer)-[:LINKED_TO]->(Customer)          // Fraud ring detection
(Customer)-[:SHARED_ACCOUNT]->(Customer)
```

### Graph-RAG Retrieval Pipeline

```
Upload
  │
  ▼
Bronze (OCR)
  │
  ├──▶ ChromaDB: embed statement text
  │           └──▶ ANN search: top-k similar historical statements
  │
  ├──▶ Neo4j: MATCH (c:Customer {id})-[*1..2]-(related)
  │           └──▶ Build natural-language context summary
  │
  └──▶ LLM Prompt:
          [SYSTEM]   Forensic analyst persona
          [CONTEXT]  Graph summary + vector-retrieved cases
          [DOCUMENT] Uploaded statement text
          [REFERENCE] Warehouse authoritative copy
          └──▶ Structured JSON output → FraudAnalysis aggregate
```

---

## Project Structure

```
fraudrag/
├── backend/
│   ├── api/routes/          # FastAPI routers (statements, fraud, graph, customers)
│   ├── core/                # Config, database init
│   ├── models/domain.py     # DDD aggregates & value objects
│   ├── services/
│   │   └── graph_rag_service.py   # Core Graph-RAG orchestration
│   ├── pipelines/
│   │   └── medallion.py     # Bronze / Silver / Gold pipeline
│   ├── graph/
│   │   └── neo4j_client.py  # Knowledge graph operations
│   └── main.py              # FastAPI app factory
│
├── frontend/
│   └── src/
│       ├── pages/           # Dashboard, Upload, Analysis, GraphView
│       ├── utils/api.js     # Axios client
│       └── index.css        # Design system (dark forensic theme)
│
├── tests/
│   └── test_pipeline.py     # Medallion + API tests
│
├── docker/                  # Dockerfiles, nginx.conf
├── data/{bronze,silver,gold}/
├── docker-compose.yml
└── .github/workflows/ci-cd.yml
```

---

## Quick Start

### Option A — Docker Compose (Recommended)

```bash
# 1. Clone
git clone https://github.com/your-org/fraudrag.git && cd fraudrag

# 2. Configure
cp .env.example .env
# Edit .env and add OPENAI_API_KEY or ANTHROPIC_API_KEY

# 3. Launch everything
docker compose up -d

# 4. Seed demo data
curl -X POST http://localhost:8000/api/v1/graph/seed

# 5. Open UI
open http://localhost:3000
```

Services will be available at:
| Service | URL |
|---------|-----|
| React UI | http://localhost:3000 |
| FastAPI docs | http://localhost:8000/docs |
| Neo4j Browser | http://localhost:7474 |
| Prometheus | http://localhost:9090 |
| Grafana | http://localhost:3001 (admin/fraudrag) |

---

### Option B — Local Development

**Prerequisites:** Python 3.12+, Node 20+, Neo4j 5.x, PostgreSQL 16

```bash
# Backend
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp ../.env.example ../.env   # fill in values
cd ..
uvicorn backend.main:app --reload --port 8000

# Frontend (new terminal)
cd frontend
npm install
npm run dev   # → http://localhost:3000
```

---

## API Reference

### Upload a Statement

```bash
curl -X POST http://localhost:8000/api/v1/statements/upload \
  -F "file=@bank_statement.pdf" \
  -F "customer_id=cust-001" \
  -F "statement_type=bank"
```

Response:
```json
{
  "statement_id": "3f8a2b1c-...",
  "customer_id": "cust-001",
  "status": "gold_complete",
  "layer": "gold",
  "quality_score": 0.85,
  "transaction_count": 42,
  "message": "Statement processed through Medallion pipeline. Fraud analysis complete."
}
```

### Get Fraud Analysis

```bash
curl http://localhost:8000/api/v1/fraud/analysis/3f8a2b1c-...
```

### Query Knowledge Graph

```bash
# Customer subgraph (2-hop neighborhood)
curl http://localhost:8000/api/v1/graph/customer/cust-001

# Fraud ring detection
curl http://localhost:8000/api/v1/graph/customer/cust-001/rings
```

### Full API docs: http://localhost:8000/docs

---

## Fraud Detection Capabilities

| Indicator | Detection Method |
|-----------|-----------------|
| Balance arithmetic manipulation | Silver layer accounting identity check |
| Amount digit substitution (1200 → 12000) | LLM + pattern matching |
| Date forgery / future dates | NER + date range validation |
| Institution font/format anomalies | LLM visual-semantic reasoning |
| Entity name mismatch | NER entity alignment |
| Metadata tampering | SHA-256 hash + PDF metadata inspection |
| Known fraud pattern match | Neo4j vector similarity search |
| Fraud ring membership | Neo4j multi-hop graph traversal |
| Semantic deviation from institution templates | ChromaDB cosine similarity |

---

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `LLM_PROVIDER` | `openai` | `openai` or `anthropic` |
| `LLM_MODEL` | `gpt-4o` | Model name |
| `FRAUD_SCORE_HIGH_RISK` | `0.75` | Threshold for HIGH risk |
| `FRAUD_SCORE_MEDIUM_RISK` | `0.45` | Threshold for MEDIUM risk |
| `NEO4J_URI` | `bolt://localhost:7687` | Neo4j connection |
| `CHROMA_PERSIST_DIR` | `./data/chroma` | Vector store path |

---

## Running Tests

```bash
pytest tests/ -v --cov=backend
```

---

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Commit with conventional commits: `git commit -m "feat: add X"`
4. Push and open a Pull Request

---

## Citation

If you use FraudRAG in research, please cite:

```bibtex
@article{fraudrag2025,
  title={FraudRAG: Knowledge Graph-Augmented Retrieval for Financial Statement Fraud Detection},
  author={Sharma, Akshay},
  journal={IEEE Transactions on Knowledge and Data Engineering},
  year={2025}
}
```

---
