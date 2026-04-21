"""Health check endpoints."""
from fastapi import APIRouter, Request
from backend.core.config import get_settings

router = APIRouter()
settings = get_settings()


@router.get("/health")
async def health_check(request: Request):
    """System health status."""
    services = {}

    # Check Neo4j
    neo4j = getattr(request.app.state, "neo4j", None)
    if neo4j:
        try:
            async with neo4j.driver.session() as session:
                await session.run("RETURN 1")
            services["neo4j"] = "healthy"
        except Exception:
            services["neo4j"] = "unavailable"
    else:
        services["neo4j"] = "not_configured"

    # Check RAG service
    rag = getattr(request.app.state, "rag_service", None)
    services["rag_service"] = "healthy" if rag else "not_configured"

    overall = "healthy" if all(v == "healthy" for v in services.values()) else "degraded"

    return {
        "status": overall,
        "version": settings.APP_VERSION,
        "services": services,
    }


@router.get("/health/ready")
async def readiness():
    return {"ready": True}


@router.get("/health/live")
async def liveness():
    return {"alive": True}
