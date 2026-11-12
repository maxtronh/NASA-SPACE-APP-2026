from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.db.session import get_db
from backend.app.schemas.compare import CompareRequest, CompareResponse
from backend.app.services.comparison_service import ComparisonService

router = APIRouter(prefix="/compare", tags=["compare"])


@router.post("", response_model=CompareResponse)
async def compare_investigations(
    payload: CompareRequest,
    db: AsyncSession = Depends(get_db),
):
    """Compares multiple microgravity investigations and evaluates experimental condition equivalence."""
    result = await ComparisonService.compare(
        session=db,
        investigation_ids=payload.investigation_ids,
    )
    return result
