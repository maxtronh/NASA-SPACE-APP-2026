from fastapi import APIRouter
from backend.app.api.v1.endpoints import (
    health,
    investigations,
    compare,
    analytics,
    si,
    ingest,
)

api_v1_router = APIRouter()

api_v1_router.include_router(health.router)
api_v1_router.include_router(investigations.router)
api_v1_router.include_router(compare.router)
api_v1_router.include_router(analytics.router)
api_v1_router.include_router(si.router)
api_v1_router.include_router(ingest.router)
