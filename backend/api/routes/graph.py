"""
Knowledge Graph Routes
GET  /api/v1/graph/customer/{id}         – Customer subgraph
GET  /api/v1/graph/customer/{id}/rings   – Fraud ring detection
POST /api/v1/graph/seed                  – Seed demo data
GET  /api/v1/graph/patterns              – Known fraud patterns
"""

import structlog
from fastapi import APIRouter, HTTPException, Request
from typing import Optional

router = APIRouter()
logger = structlog.get_logger(__name__)


@router.get("/customer/{customer_id}")
async def get_customer_graph(customer_id: str, depth: int = 2, request: Request = None):
    """Retrieve the knowledge graph neighborhood of a customer."""
    neo4j = getattr(request.app.state, "neo4j", None) if request else None
    if not neo4j:
        raise HTTPException(status_code=503, detail="Graph service not available")
    try:
        subgraph = await neo4j.get_customer_subgraph_simple(customer_id, depth)
        context = await neo4j.get_graph_context_for_rag(customer_id)
        return {
            "customer_id": customer_id,
            "subgraph": subgraph,
            "rag_context": context,
            "node_count": len(subgraph.get("nodes", [])),
            "edge_count": len(subgraph.get("relationships", [])),
        }
    except Exception as e:
        logger.error("Graph query failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Graph query failed: {str(e)}")


@router.get("/customer/{customer_id}/rings")
async def detect_fraud_rings(customer_id: str, request: Request = None):
    """Detect potential fraud rings connected to this customer."""
    neo4j = getattr(request.app.state, "neo4j", None) if request else None
    if not neo4j:
        raise HTTPException(status_code=503, detail="Graph service not available")
    suspects = await neo4j.find_fraud_ring(customer_id)
    return {
        "customer_id": customer_id,
        "suspected_ring_members": suspects,
        "ring_size": len(suspects),
        "risk_assessment": "HIGH" if len(suspects) > 3 else ("MEDIUM" if suspects else "LOW"),
    }


@router.post("/seed")
async def seed_demo_data(request: Request):
    """Seed the knowledge graph with demo data for development."""
    neo4j = getattr(request.app.state, "neo4j", None)
    if not neo4j:
        raise HTTPException(status_code=503, detail="Graph service not available")
    await neo4j.seed_demo_data()
    return {"message": "Demo graph data seeded successfully"}


@router.get("/patterns")
async def get_fraud_patterns(request: Request):
    """List all known fraud patterns in the knowledge graph."""
    neo4j = getattr(request.app.state, "neo4j", None)
    if not neo4j:
        raise HTTPException(status_code=503, detail="Graph service not available")
    query = """
    MATCH (p:FraudPattern)
    RETURN p.id AS id, p.pattern_name AS name, p.pattern_type AS type,
           p.description AS description, p.frequency AS frequency
    ORDER BY p.frequency DESC LIMIT 50
    """
    async with neo4j.driver.session(database=neo4j.database) as session:
        result = await session.run(query)
        patterns = [dict(r) async for r in result]
    return {"patterns": patterns, "total": len(patterns)}
