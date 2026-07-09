"""FastAPI dependency-injection helpers for the Intelligence REST API."""

from fastapi import Depends
from sqlalchemy.orm import Session

from app.database.dependencies import get_db
from app.modules.artifact.service.service import ArtifactService
from app.modules.intelligence.graph.api.service import GraphApiService
from app.modules.investigation.service.service import InvestigationService


def get_investigation_service(
    db: Session = Depends(get_db),
) -> InvestigationService:
    return InvestigationService(db)


def get_artifact_service(
    db: Session = Depends(get_db),
) -> ArtifactService:
    return ArtifactService(db)


def get_graph_service(
    db: Session = Depends(get_db),
) -> GraphApiService:
    return GraphApiService(db)
