"""API v1 router.

Aggregates all version-1 route collections under a single
``APIRouter`` that is mounted in ``main.py``.
"""

from fastapi import APIRouter

from app.health.routes import router as health_router
from app.modules.artifact.api.routes import router as artifact_router
from app.modules.bookmark.api.routes import router as bookmark_router
from app.modules.collection.api.routes import router as collection_router
from app.modules.copilot.api.routes import router as copilot_router
from app.modules.execution.api.routes import router as execution_router
from app.modules.intelligence.api.routes import router as intelligence_router
from app.modules.investigation.api.routes import router as investigation_router
from app.modules.notes.api.routes import router as notes_router
from app.modules.reading_status.api.routes import router as reading_status_router
from app.modules.retrieval.api.routes import router as retrieval_router

v1_router = APIRouter()
v1_router.include_router(health_router)
v1_router.include_router(artifact_router)
v1_router.include_router(bookmark_router)
v1_router.include_router(collection_router)
v1_router.include_router(execution_router)
v1_router.include_router(investigation_router)
v1_router.include_router(intelligence_router)
v1_router.include_router(notes_router)
v1_router.include_router(reading_status_router)
v1_router.include_router(retrieval_router)
v1_router.include_router(copilot_router)

__all__ = [
    "v1_router",
]
