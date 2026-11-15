"""
Flame in Freefall — FastAPI Core Application
CORTEXX Scientific Intelligence Platform
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from sqlalchemy.exc import SQLAlchemyError

from backend.app.api.v1.router import api_v1_router
from backend.app.core.config import settings
from backend.app.core.logging import logger, setup_logging
from backend.app.core.telemetry_metrics import MetricsRegistry, TelemetryMetricsMiddleware
from backend.app.db.session import check_db_health, get_db_engines, init_db
from backend.app.schemas.health import HealthResponse
from backend.app.services.seed_data import seed_database_if_empty


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle event handler for database initialization and authentic data seeding."""
    setup_logging()
    logger.info("Initializing Flame in Freefall Backend Services...")

    # Initialize tables and pgvector extension
    try:
        await init_db()
    except (SQLAlchemyError, OSError) as exc:
        logger.error(f"Error during init_db: {exc}")

    # Seed authentic NASA records if empty
    if settings.ENABLE_AUTO_SEED:
        _, session_factory, _, _ = get_db_engines()
        async with session_factory() as session:
            try:
                await seed_database_if_empty(session)
            except (SQLAlchemyError, OSError) as exc:
                logger.error(f"Error seeding authentic NASA records: {exc}")

    logger.info("Flame in Freefall Backend initialized successfully.")
    yield
    logger.info("Shutting down Flame in Freefall Backend Services...")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Scientific Intelligence Platform leveraging NASA microgravity combustion research data.",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# OpenTelemetry & Prometheus Metrics Middleware
app.add_middleware(TelemetryMetricsMiddleware)


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Unified HTTP error envelope preserving detail string and structured error code."""
    detail_str = str(exc.detail) if exc.detail else "HTTP Exception"
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.detail,
            "error": {
                "code": "HTTP_ERROR",
                "status_code": exc.status_code,
                "message": detail_str,
            },
        },
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Unified request validation error envelope preserving detail list and structured details."""
    errors = jsonable_encoder(exc.errors())
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": errors,
            "error": {
                "code": "VALIDATION_ERROR",
                "status_code": 422,
                "message": "Request parameter validation failed",
                "details": errors,
            },
        },
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global unhandled exception envelope preventing raw internal stack trace leaks."""
    logger.exception(f"Unhandled exception processing {request.method} {request.url.path}: {exc}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "Internal server error occurred",
            "error": {
                "code": "INTERNAL_ERROR",
                "status_code": 500,
                "message": "An unexpected error occurred processing the scientific request",
            },
        },
    )


@app.get("/health", response_model=HealthResponse, tags=["health"])
async def root_health():
    """Root health endpoint for container healthchecks."""
    return await check_db_health()


@app.get("/metrics", tags=["telemetry-metrics"])
async def prometheus_metrics():
    """Prometheus text-format metrics exporter for system monitoring and alerting."""
    reg = MetricsRegistry.get_instance()
    content = reg.export_prometheus_text()
    return Response(content=content, media_type="text/plain; version=0.0.4")


# Include API v1 routes
app.include_router(api_v1_router, prefix=settings.API_V1_PREFIX)


@app.get("/", tags=["root"])
async def root():
    return {
        "name": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "status": "operational",
        "docs_url": "/docs",
        "api_v1": settings.API_V1_PREFIX,
    }
