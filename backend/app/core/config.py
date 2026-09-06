from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache
from typing import Literal


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── App ──────────────────────────────────────────────────────────────
    APP_NAME: str = "DesignMentor AI"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    ENVIRONMENT: Literal["development", "staging", "production"] = "development"

    # ── Security ─────────────────────────────────────────────────────────
    SECRET_KEY: str = "change-me-in-production-use-a-long-random-string"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24        # 24 hours
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    # ── Database ─────────────────────────────────────────────────────────
    DATABASE_URL: str = "postgresql+asyncpg://designmentor:designmentor_secret@localhost:5432/designmentor_db"

    # ── Redis ────────────────────────────────────────────────────────────
    REDIS_URL: str = "redis://localhost:6379"
    CACHE_TTL_SECONDS: int = 300

    # ── OpenAI ───────────────────────────────────────────────────────────
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o"
    OPENAI_EMBEDDING_MODEL: str = "text-embedding-ada-002"
    OPENAI_MAX_TOKENS: int = 2048
    OPENAI_TEMPERATURE: float = 0.4

    # ── LangGraph / Agents ───────────────────────────────────────────────
    AGENT_MAX_ITERATIONS: int = 10
    AGENT_TIMEOUT_SECONDS: int = 120

    # ── Learning ─────────────────────────────────────────────────────────
    MASTERY_THRESHOLD: float = 75.0          # min % to move to next concept
    QUIZ_QUESTIONS_PER_SESSION: int = 5
    MAX_RETEACH_ATTEMPTS: int = 3

    # ── Spaced Repetition (SM-2) ─────────────────────────────────────────
    SM2_INITIAL_INTERVAL: int = 1            # days
    SM2_EASY_BONUS: float = 1.3
    SM2_MIN_EASE: float = 1.3

    # ── ML (Random Forest) ───────────────────────────────────────────────
    RF_MODEL_PATH: str = "app/ml/models/rf_mastery_predictor.pkl"
    RF_RETRAIN_EVERY_N_ATTEMPTS: int = 50

    # ── RAG ──────────────────────────────────────────────────────────────
    RAG_CHUNK_SIZE: int = 800
    RAG_CHUNK_OVERLAP: int = 100
    RAG_TOP_K: int = 5
    KNOWLEDGE_BASE_DIR: str = "knowledge_base"

    # ── CORS ─────────────────────────────────────────────────────────────
    CORS_ORIGINS: list[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
