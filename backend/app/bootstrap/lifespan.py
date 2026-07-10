"""FastAPI application lifespan handler.

Delegates startup and shutdown to the bootstrap module so that
the FastAPI entry point stays clean and the lifecycle logic is
testable independently.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.bootstrap.shutdown import shutdown_services
from app.bootstrap.startup import initialize_services
from app.core.logging import configure_logging
from app.health.service import record_startup_time
from app.observability.logger import get_logger

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    """Application lifespan context manager.

    Startup (before yield):
      - Configure structured logging.
      - Validate configuration and initialize services.

    Shutdown (after yield):
      - Gracefully release infrastructure resources.
    """
    configure_logging()
    record_startup_time()
    await initialize_services()
    yield
    await shutdown_services()
