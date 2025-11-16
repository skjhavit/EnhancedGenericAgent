"""Health check and monitoring routes."""

from fastapi import APIRouter
from pydantic import BaseModel
from datetime import datetime

router = APIRouter()


class HealthResponse(BaseModel):
    status: str
    timestamp: datetime
    version: str


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        timestamp=datetime.utcnow(),
        version="1.0.0",
    )


@router.get("/metrics")
async def get_metrics():
    """Prometheus-compatible metrics endpoint."""
    # TODO: Implement actual metrics collection
    return {"message": "Metrics endpoint (TODO: implement Prometheus metrics)"}
