"""FastAPI application entry point."""
from contextlib import asynccontextmanager
from pathlib import Path

import structlog
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer(),
    ],
)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.config import get_settings
from backend.api.routes import health, voice, doctors
from backend.api.middleware import LatencyMiddleware
from backend.db.database import init_db
from backend.scheduler.campaign_scheduler import start_scheduler, shutdown_scheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown lifecycle."""
    init_db()
    start_scheduler()
    yield
    shutdown_scheduler()


def create_app() -> FastAPI:
    settings = get_settings()
    
    app = FastAPI(
        title="2Care Voice AI Agent",
        description="Real-time multilingual voice AI for clinical appointment booking",
        version="1.0.0",
        lifespan=lifespan,
    )
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list(),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(LatencyMiddleware)
    
    app.include_router(health.router, tags=["health"])
    app.include_router(voice.router, prefix="/ws", tags=["voice"])
    app.include_router(doctors.router, tags=["doctors"])

    frontend = Path(__file__).resolve().parent.parent / "frontend"
    if frontend.exists():
        app.mount("/", StaticFiles(directory=str(frontend), html=True), name="frontend")
    
    return app


app = create_app()
