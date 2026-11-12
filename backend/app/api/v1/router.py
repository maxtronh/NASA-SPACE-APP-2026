from fastapi import APIRouter
from backend.app.api.v1.endpoints import (
    analytics,
    antigravity,
    citations,
    compare,
    graph,
    health,
    ingest,
    investigations,
    kinetics,
    provenance,
    safety,
    si,
    telemetry,
    ws_telemetry,
)

api_v1_router = APIRouter()

api_v1_router.include_router(health.router)
api_v1_router.include_router(investigations.router)
api_v1_router.include_router(compare.router)
api_v1_router.include_router(antigravity.router)
api_v1_router.include_router(analytics.router)
api_v1_router.include_router(si.router)
api_v1_router.include_router(ingest.router)
api_v1_router.include_router(citations.router)
api_v1_router.include_router(provenance.router)
api_v1_router.include_router(safety.router)
api_v1_router.include_router(kinetics.router)
api_v1_router.include_router(graph.router)
api_v1_router.include_router(telemetry.router)
api_v1_router.include_router(ws_telemetry.router)
