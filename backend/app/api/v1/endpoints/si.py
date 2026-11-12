from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.db.session import get_db
from backend.app.schemas.si import SIQueryRequest, SIQueryResponse
from backend.app.services.si_service import SIService

router = APIRouter(prefix="/si", tags=["scientific-intelligence"])


@router.post("/query", response_model=SIQueryResponse)
async def scientific_intelligence_query(
    payload: SIQueryRequest,
    db: AsyncSession = Depends(get_db),
):
    """Processes natural language questions against authentic NASA combustion records with explicit abstention."""
    response = await SIService.process_query(
        session=db,
        query_str=payload.query,
        filters=payload.filters,
    )
    return response
