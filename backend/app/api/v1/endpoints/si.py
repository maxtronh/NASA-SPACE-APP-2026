from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.core.semantic_cache import SemanticCache
from backend.app.db.session import get_db
from backend.app.schemas.si import SIQueryRequest, SIQueryResponse
from backend.app.services.si_service import SIService

router = APIRouter(prefix="/si", tags=["scientific-intelligence"])


@router.post("/query", response_model=SIQueryResponse)
async def scientific_intelligence_query(
    payload: SIQueryRequest,
    db: AsyncSession = Depends(get_db),
):
    """Processes natural language questions against authentic NASA combustion records with semantic caching."""
    cache = SemanticCache.get_instance()
    cached_val = cache.get(payload.query)
    if cached_val is not None:
        return cached_val

    response = await SIService.process_query(
        session=db,
        query_str=payload.query,
        filters=payload.filters,
    )
    cache.put(payload.query, response)
    return response


@router.get("/cache/stats")
async def get_si_cache_stats():
    """Returns semantic cache metrics, capacity, hits, and misses."""
    cache = SemanticCache.get_instance()
    return cache.get_stats()
