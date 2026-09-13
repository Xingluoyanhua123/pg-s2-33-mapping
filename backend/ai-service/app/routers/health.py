from fastapi import APIRouter
from app.config import settings

router = APIRouter()


@router.get("/health")
def health():
    """Works without requiring the main backend — pure liveness check."""
    return {
        "status": "ok",
        "service": settings.service_name,
        "llm_provider": settings.llm_provider,
        "embedding_provider": settings.embedding_provider,
    }
