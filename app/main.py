"""
FastAPI application factory.
"""
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from jinja2 import FileSystemLoader, Environment
from pathlib import Path

import app as app_pkg
from app.core.config import get_settings
from app.core.logging_config import logger
from app.services.glossary_service import glossary_service
from app.api import translate, documents, health

BASE_DIR = Path(__file__).resolve().parent.parent


def create_app() -> FastAPI:
    settings = get_settings()

    # ── Lifespan (replaces deprecated on_event) ────────────────────────────────
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        logger.info("=== AICTE Translator Agent starting up ===")
        glossary_service.load()
        logger.info("Glossary loaded: %d entries", glossary_service.entry_count)
        logger.info("Supported languages: %s", ", ".join(settings.supported_language_list))
        logger.info("IBM Granite model: %s", settings.granite_model_id)
        logger.info("watsonx.ai URL: %s", settings.watsonx_url)
        yield
        logger.info("=== AICTE Translator Agent shutting down ===")

    application = FastAPI(
        title="AICTE Multi-language Course Content Translator Agent",
        description=(
            "RAG-powered academic content translator using IBM Granite (watsonx.ai). "
            "Supports Hindi, Marathi, Tamil, Bengali, Telugu, Kannada, Gujarati, "
            "Punjabi, Malayalam, Odia, Urdu, and English."
        ),
        version=app_pkg.__version__,
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    # CORS
    application.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Static files & templates
    static_dir = BASE_DIR / "static"
    templates_dir = BASE_DIR / "templates"
    static_dir.mkdir(exist_ok=True)
    templates_dir.mkdir(exist_ok=True)

    application.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

    # Use a fresh Jinja2 Environment (avoids a cache-key bug in newer Jinja2/starlette)
    jinja_env = Environment(loader=FileSystemLoader(str(templates_dir)), autoescape=True)
    templates = Jinja2Templates(env=jinja_env)

    # Routers
    application.include_router(health.router)
    application.include_router(translate.router)
    application.include_router(documents.router)

    # ── Frontend route ─────────────────────────────────────────────────────────
    @application.get("/", response_class=HTMLResponse, include_in_schema=False)
    async def serve_index(request: Request):
        return templates.TemplateResponse(request, "index.html")

    return application
