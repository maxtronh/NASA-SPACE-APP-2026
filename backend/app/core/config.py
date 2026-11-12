import os
from typing import List, Union
from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "Flame in Freefall - Scientific Intelligence Platform"
    VERSION: str = "1.0.0"
    API_V1_PREFIX: str = "/api/v1"

    # Database Configuration (PostgreSQL 16 + pgvector with SQLite fallback)
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg://flame_user:flame_secure_pass@localhost:5432/flame_freefall"
    )
    SQLITE_FALLBACK_URL: str = os.getenv(
        "SQLITE_FALLBACK_URL",
        "sqlite+aiosqlite:///./test_flame.db"
    )
    SQLITE_SYNC_URL: str = os.getenv(
        "SQLITE_SYNC_URL",
        "sqlite:///./test_flame.db"
    )

    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "*"
    ]

    # Automatic Data Ingestion / Seeding on Startup
    ENABLE_AUTO_SEED: bool = True
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )


settings = Settings()
