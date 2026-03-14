"""
Faust application configuration.

All settings are loaded from environment variables using Pydantic Settings.
Never store secrets in code — every sensitive value comes from the environment.
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )

    # ── App ──────────────────────────────────────────────────────────
    APP_NAME: str = "Faust"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False
    API_V1_PREFIX: str = "/api/v1"
    ENVIRONMENT: str = "development"  # development | staging | production

    # ── Database (PostgreSQL) ────────────────────────────────────────
    POSTGRES_USER: str = "faust"
    POSTGRES_PASSWORD: str  # Required — no default
    POSTGRES_HOST: str = "postgres"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "faust"
    DB_POOL_SIZE: int = 20
    DB_MAX_OVERFLOW: int = 10

    # ── Redis ────────────────────────────────────────────────────────
    REDIS_HOST: str = "redis"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0

    # ── JWT / Auth ───────────────────────────────────────────────────
    JWT_SECRET_KEY: str  # Required — no default. Generate with: openssl rand -hex 32
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # ── CORS ─────────────────────────────────────────────────────────
    CORS_ORIGINS: list[str] = ["http://localhost:3000"]

    # ── Scanning ─────────────────────────────────────────────────────
    SCAN_TIMEOUT_SECONDS: int = 3600
    MAX_CONCURRENT_SCANS: int = 5
    NMAP_BINARY_PATH: str = "/usr/bin/nmap"
    NUCLEI_BINARY_PATH: str = "/usr/local/bin/nuclei"
    TRIVY_BINARY_PATH: str = "/usr/local/bin/trivy"

    # ── AI Providers (all optional — pluggable) ──────────────────────
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o"
    ANTHROPIC_API_KEY: str = ""
    ANTHROPIC_MODEL: str = "claude-sonnet-4-20250514"
    GOOGLE_AI_API_KEY: str = ""
    GOOGLE_AI_MODEL: str = "gemini-2.0-flash"
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3.1:8b"
    DEFAULT_AI_PROVIDER: str = "ollama"  # openai | anthropic | google | ollama

    # ── NVD API ────────────────────────────────────────────────────────
    NVD_API_KEY: str = ""  # Optional — increases rate limit from 5 to 50 req/30s

    # ── First Admin (seeded on first run) ────────────────────────────
    FIRST_ADMIN_EMAIL: str = "admin@faust.local"
    FIRST_ADMIN_PASSWORD: str = ""  # Empty = skip seed

    # ── Derived properties ───────────────────────────────────────────

    @property
    def database_url(self) -> str:
        """Async database URL for SQLAlchemy (asyncpg driver)."""
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    @property
    def sync_database_url(self) -> str:
        """Sync database URL for Alembic migrations only (psycopg2 driver)."""
        return (
            f"postgresql+psycopg2://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    @property
    def redis_url(self) -> str:
        """Redis connection URL."""
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

    @property
    def celery_broker_url(self) -> str:
        """Celery broker URL (Redis)."""
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/1"

    @property
    def celery_result_backend(self) -> str:
        """Celery result backend URL (Redis)."""
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/2"


@lru_cache
def get_settings() -> Settings:
    """Return cached application settings singleton."""
    return Settings()
