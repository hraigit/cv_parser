"""Health check routes."""
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.schemas.common import HealthResponse

router = APIRouter(tags=["Health"])


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health check",
    description="Check if the API and database are operational"
)
async def health_check(db: AsyncSession = Depends(get_db)) -> HealthResponse:
    """Check health of the API."""
    # Check database connection
    try:
        await db.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception:
        db_status = "disconnected"
    
    return HealthResponse(
        status="operational" if db_status == "connected" else "degraded",
        version=settings.APP_VERSION,
        database=db_status
    )


@router.get(
    "/",
    summary="Root endpoint",
    description="API information"
)
async def root():
    """Root endpoint."""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "operational"
    }