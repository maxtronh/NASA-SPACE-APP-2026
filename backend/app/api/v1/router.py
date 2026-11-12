from fastapi import APIRouter
from backend.app.api.v1.endpoints import (
    analytics,
    citations,
    compare,
    health,
    ingest,
    investigations,
    si,
)

api_v1_router = APIRouter()

api_v1_router.include_router(health.router)
api_v1_router.include_router(investigations.router)
api_v1_router.include_router(compare.router)
api_v1_router.include_router(analytics.router)
api_v1_router.include_router(si.router)
api_v1_router.include_router(ingest.router)
api_v1_router.include_router(citations.router)
