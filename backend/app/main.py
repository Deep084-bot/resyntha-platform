"""FastAPI application entry point for Resyntha.

Wires together the lifespan handler, CORS middleware, and versioned
API routes.  The application instance is created at module level so
that ASGI servers (Uvicorn, Gunicorn) can discover ``app`` directly.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import v1_router
from app.config import get_settings
from app.core.lifespan import lifespan


def create_app() -> FastAPI:
    """Build and return the configured FastAPI application instance."""
    settings = get_settings()

    cors_origins = [
        o.strip()
        for o in settings.CORS_ORIGINS.split(",")
        if o.strip()
    ]

    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(v1_router, prefix=settings.API_V1_PREFIX)

    @app.get("/")
    async def root() -> dict[str, str]:
        return {
            "application": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "environment": settings.ENVIRONMENT,
            "status": "running",
        }

    return app


app = create_app()
