"""DesignMentor AI — FastAPI application entry point."""
from contextlib import asynccontextmanager
import os
from dotenv import load_dotenv

# Load .env explicitly before anything else
load_dotenv(override=True)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.core.config import settings
from app.core.logging import configure_logging, logger
from app.db.base import engine, Base
from app.api.routes import auth, learn, quiz, progress, interview, curriculum
from app.api.routes.admin import router as admin_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()
    logger.info("startup", app=settings.APP_NAME, version=settings.APP_VERSION, env=settings.ENVIRONMENT)

    # Create tables if they don't exist (in dev; prod uses alembic)
    if settings.ENVIRONMENT == "development":
        async with engine.begin() as conn:
            # Enable pgvector extension before creating tables
            await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
            await conn.run_sync(Base.metadata.create_all)

    # Initialise ML model
    from app.ml.rf_model import MasteryPredictor
    MasteryPredictor.load_or_init()

    yield

    logger.info("shutdown")
    await engine.dispose()


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Agentic AI system for learning Low-Level and High-Level Design",
    lifespan=lifespan,
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
)

# ── CORS ──────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routes ────────────────────────────────────────────────────────────────
app.include_router(auth.router,         prefix="/api/auth",       tags=["auth"])
app.include_router(curriculum.router,   prefix="/api/curriculum", tags=["curriculum"])
app.include_router(learn.router,        prefix="/api/learn",      tags=["learn"])
app.include_router(quiz.router,         prefix="/api/quiz",       tags=["quiz"])
app.include_router(progress.router,     prefix="/api/progress",   tags=["progress"])
app.include_router(interview.router,    prefix="/api/interview",  tags=["interview"])
app.include_router(admin_router,        prefix="/api/admin",      tags=["admin"])


@app.get("/health", tags=["health"])
async def health_check():
    return JSONResponse({"status": "ok", "app": settings.APP_NAME})
