"""API v1 router.

Aggregates all version-1 route collections under a single
``APIRouter`` that is mounted in ``main.py``.
"""

from fastapi import APIRouter

from app.api.v1.health import router as health_router
from app.modules.artifact.api.routes import router as artifact_router
from app.modules.execution.api.routes import router as execution_router
from app.modules.investigation.api.routes import router as investigation_router
from app.modules.retrieval.api.routes import router as retrieval_router

v1_router = APIRouter()
v1_router.include_router(health_router)
v1_router.include_router(artifact_router)
v1_router.include_router(execution_router)
v1_router.include_router(investigation_router)
v1_router.include_router(retrieval_router)

__all__ = [
    "v1_router",
]
