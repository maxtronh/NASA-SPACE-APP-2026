from fastapi import APIRouter
from backend.app.api.v1.endpoints import (
    active_learning,
    analytics,
    antigravity,
    auth,
    citations,
    compare,
    graph,
    health,
    ingest,
    investigations,
    kinetics,
    multimodal,
    provenance,
    safety,
    si,
    stream,
    telemetry,
    ws_telemetry,
)

api_v1_router = APIRouter()

api_v1_router.include_router(health.router)
api_v1_router.include_router(auth.router)
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
api_v1_router.include_router(stream.router)
api_v1_router.include_router(telemetry.router)
api_v1_router.include_router(ws_telemetry.router)
api_v1_router.include_router(multimodal.router)
api_v1_router.include_router(active_learning.router)
