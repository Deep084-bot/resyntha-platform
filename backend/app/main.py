"""FastAPI application entry point for Resyntha.

Wires together middleware, lifespan, and versioned API routes.
The application instance is created at module level so that ASGI
servers (Uvicorn, Gunicorn) can discover ``app`` directly.
"""

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.v1 import v1_router
from app.bootstrap.lifespan import lifespan
from app.config import get_settings
from app.core.exceptions import (
    http_exception_handler,
    unhandled_exception_handler,
    validation_exception_handler,
)
from app.core.middleware.request_id import RequestIDMiddleware
from app.core.middleware.request_logging import RequestLoggingMiddleware
from app.core.middleware.request_size import RequestSizeLimitMiddleware
from app.core.middleware.timeout import TimeoutMiddleware
from app.metrics import MetricsMiddleware
from app.rate_limit import RateLimitMiddleware
from app.security import SecurityHeadersMiddleware


def create_app() -> FastAPI:
    """Build and return the configured FastAPI application instance."""
    settings = get_settings()

    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        lifespan=lifespan,
        openapi_url=f"{settings.API_V1_PREFIX}/openapi.json" if settings.OPENAPI_ENABLED else None,
        docs_url=f"{settings.API_V1_PREFIX}/docs" if settings.DOCS_ENABLED else None,
        redoc_url=f"{settings.API_V1_PREFIX}/redoc" if settings.REDOC_ENABLED else None,
    )

    # ── Exception handlers ───────────────────────────────────────────
    # Registered first so they can catch errors from any middleware or route.

    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)

    # ── Middleware ────────────────────────────────────────────────────
    # Middleware is applied in reverse registration order —
    # first registered = innermost, last registered = outermost.
    #
    # Desired order (outermost → innermost):
    #   TrustedHost → CORS → Security Headers → Request Size →
    #   Timeout → Rate Limiting → Metrics → Request ID → Logging → handler

    app.add_middleware(RequestLoggingMiddleware)      # innermost
    app.add_middleware(RequestIDMiddleware)
    app.add_middleware(MetricsMiddleware)
    app.add_middleware(RateLimitMiddleware)
    app.add_middleware(TimeoutMiddleware)
    app.add_middleware(RequestSizeLimitMiddleware)
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
        allow_methods=settings.cors_method_list,
        allow_headers=settings.cors_header_list,
    )
    if settings.trusted_host_list:
        app.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=settings.trusted_host_list,
        )                                       # outermost

    app.include_router(v1_router, prefix=settings.API_V1_PREFIX)

    @app.get("/")
    async def root() -> dict[str, str]:
        return {
            "application": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "environment": settings.ENVIRONMENT.value,
            "git_commit": settings.GIT_COMMIT,
            "build_time": settings.BUILD_TIME,
            "status": "running",
        }

    return app


app = create_app()
