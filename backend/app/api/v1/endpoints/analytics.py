from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.db.session import get_db
from backend.app.schemas.analytics import CorpusAnalyticsResponse
from backend.app.services.analytics_service import AnalyticsService

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/corpus", response_model=CorpusAnalyticsResponse)
async def get_corpus_analytics(
    db: AsyncSession = Depends(get_db),
):
    """Corpus completeness overview and missing measurement matrix across scientific channels."""
    data = await AnalyticsService.get_corpus_analytics(session=db)
    return data


@router.get("/overview")
async def get_analytics_overview(
    db: AsyncSession = Depends(get_db),
):
    """High-level analytics overview for dashboard metrics."""
    data = await AnalyticsService.get_corpus_analytics(session=db)
    return {
        "total_investigations": data["total_investigations"],
        "combustion_regimes": data["combustion_regimes"],
    }


@router.get("/missing-data-analysis")
async def get_missing_data_analysis(
    db: AsyncSession = Depends(get_db),
):
    """Detailed missing data matrix isolating unmeasured physical parameters."""
    data = await AnalyticsService.get_corpus_analytics(session=db)
    return {
        "total_investigations": data["total_investigations"],
        "missing_data_matrix": data["missing_data_matrix"],
    }
