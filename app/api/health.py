"""
Health check API router.
"""
from fastapi import APIRouter
from app.models.schemas import HealthResponse
from app.services.granite_llm import granite_llm
from app.services.vector_store import vector_store
from app.services.glossary_service import glossary_service
from app.core.config import get_settings
import app

router = APIRouter(prefix="/api", tags=["Health"])


@router.get("/health", response_model=HealthResponse, summary="System health check")
async def health_check():
    """Check the status of all system components."""
    settings = get_settings()
    glossary_service.load()
    return HealthResponse(
        status="ok",
        version=app.__version__,
        # Use cached connection state; avoid a live network call on every ping.
        # Call granite_llm.health_check() only if not yet connected.
        watsonx_connected=granite_llm.is_connected or granite_llm.health_check(),
        vector_store_ready=vector_store.is_ready,
        glossary_loaded=glossary_service.is_loaded,
        supported_languages=settings.supported_language_list,
    )
