from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from myflightbook_api.api.routes import aircraft, auth, flights, health, images, profile, telemetry, totals
from myflightbook_api.core.config import get_settings
from myflightbook_api.core.logging import LoggingMiddleware, setup_logging

settings = get_settings()

app = FastAPI(
    title=settings.project_name,
    version="0.1.0",
    description="Canonical REST API for the MyFlightbook TypeScript + Python migration."
)
setup_logging(app)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)
app.add_middleware(LoggingMiddleware)

app.include_router(health.router)
app.include_router(auth.router, prefix=settings.api_v1_prefix)
app.include_router(profile.router, prefix=settings.api_v1_prefix)
app.include_router(aircraft.router, prefix=settings.api_v1_prefix)
app.include_router(flights.router, prefix=settings.api_v1_prefix)
app.include_router(totals.router, prefix=settings.api_v1_prefix)
app.include_router(telemetry.router, prefix=settings.api_v1_prefix)
app.include_router(images.router, prefix=settings.api_v1_prefix)
