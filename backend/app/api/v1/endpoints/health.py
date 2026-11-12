from fastapi import APIRouter
from backend.app.db.session import check_db_health
from backend.app.schemas.health import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def get_health():
    """System and database liveness health check."""
    status_info = await check_db_health()
    return status_info
