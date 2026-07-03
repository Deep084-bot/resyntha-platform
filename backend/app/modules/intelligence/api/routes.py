"""Intelligence REST API — serves stored landscape artifacts only.

Every endpoint retrieves data already persisted by the pipeline.
No graph building, no analyzer execution, no recomputation.
"""

from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status

from app.modules.artifact.domain.models import ArtifactType
from app.modules.artifact.service.service import ArtifactService
from app.modules.intelligence.api.dependencies import (
    get_artifact_service,
    get_investigation_service,
)
from app.modules.intelligence.api.schemas import (
    CollaborationSectionResponse,
    DatasetSectionResponse,
    InstitutionSectionResponse,
    LandscapeResponse,
    MarkdownResponse,
    MethodologySectionResponse,
    OverviewSectionResponse,
    TechnologySectionResponse,
    TemporalSectionResponse,
)
from app.modules.investigation.service.service import InvestigationService
from app.observability.logger import get_logger

router = APIRouter(
    prefix="/investigations/{investigation_id}",
    tags=["intelligence"],
)
logger = get_logger(__name__)


# ── Internal helpers ───────────────────────────────────────────


def _verify_investigation(
    inv_id: uuid.UUID,
    inv_service: InvestigationService,
) -> None:
    if inv_service.get_investigation(inv_id) is None:
        logger.warning("investigation_not_found", id=str(inv_id))
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)


def _load_json_content(
    inv_id: uuid.UUID,
    art_service: ArtifactService,
) -> dict[str, Any]:
    for a in art_service.list_artifacts(inv_id):
        if (
            a.artifact_type == ArtifactType.RESEARCH_LANDSCAPE
            and a.payload
            and a.payload.get("format") == "json"
        ):
            return a.payload["content"]
    logger.warning("landscape_artifact_not_found", investigation_id=str(inv_id))
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)


def _load_markdown_content(
    inv_id: uuid.UUID,
    art_service: ArtifactService,
) -> str:
    for a in art_service.list_artifacts(inv_id):
        if (
            a.artifact_type == ArtifactType.RESEARCH_LANDSCAPE
            and a.payload
            and a.payload.get("format") == "markdown"
        ):
            return a.payload["content"]
    logger.warning("landscape_markdown_not_found", investigation_id=str(inv_id))
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)


def _json_to_landscape(content: dict[str, Any]) -> LandscapeResponse:
    return LandscapeResponse.model_validate(content)


# ── Landscape endpoints ────────────────────────────────────────


@router.get(
    "/landscape",
    response_model=LandscapeResponse,
)
async def get_landscape(
    investigation_id: uuid.UUID,
    inv_service: InvestigationService = Depends(get_investigation_service),
    art_service: ArtifactService = Depends(get_artifact_service),
) -> LandscapeResponse:
    """Return the full research landscape as a strongly typed model."""
    _verify_investigation(investigation_id, inv_service)
    content = _load_json_content(investigation_id, art_service)
    result = _json_to_landscape(content)
    logger.info("landscape_retrieved", id=str(investigation_id))
    return result


@router.get(
    "/landscape/markdown",
    response_model=MarkdownResponse,
)
async def get_landscape_markdown(
    investigation_id: uuid.UUID,
    inv_service: InvestigationService = Depends(get_investigation_service),
    art_service: ArtifactService = Depends(get_artifact_service),
) -> MarkdownResponse:
    """Return the raw markdown content from the stored artifact."""
    _verify_investigation(investigation_id, inv_service)
    markdown = _load_markdown_content(investigation_id, art_service)
    logger.info("landscape_markdown_retrieved", id=str(investigation_id))
    return MarkdownResponse(markdown=markdown)


@router.get(
    "/landscape/json",
)
async def get_landscape_json(
    investigation_id: uuid.UUID,
    inv_service: InvestigationService = Depends(get_investigation_service),
    art_service: ArtifactService = Depends(get_artifact_service),
) -> dict[str, Any]:
    """Return the raw JSON dict from the stored artifact."""
    _verify_investigation(investigation_id, inv_service)
    content = _load_json_content(investigation_id, art_service)
    logger.info("landscape_json_retrieved", id=str(investigation_id))
    return content


# ── Section endpoints ──────────────────────────────────────────


@router.get(
    "/overview",
    response_model=OverviewSectionResponse,
)
async def get_overview(
    investigation_id: uuid.UUID,
    inv_service: InvestigationService = Depends(get_investigation_service),
    art_service: ArtifactService = Depends(get_artifact_service),
) -> OverviewSectionResponse:
    """Return only the overview section."""
    _verify_investigation(investigation_id, inv_service)
    content = _load_json_content(investigation_id, art_service)
    raw = content.get("overview") or {}
    logger.info("overview_retrieved", id=str(investigation_id))
    return OverviewSectionResponse.model_validate(raw)


@router.get(
    "/institutions",
    response_model=InstitutionSectionResponse,
)
async def get_institutions(
    investigation_id: uuid.UUID,
    inv_service: InvestigationService = Depends(get_investigation_service),
    art_service: ArtifactService = Depends(get_artifact_service),
) -> InstitutionSectionResponse:
    """Return only the institutions section."""
    _verify_investigation(investigation_id, inv_service)
    content = _load_json_content(investigation_id, art_service)
    raw = content.get("institutions") or {}
    logger.info("institutions_retrieved", id=str(investigation_id))
    return InstitutionSectionResponse.model_validate(raw)


@router.get(
    "/methodologies",
    response_model=MethodologySectionResponse,
)
async def get_methodologies(
    investigation_id: uuid.UUID,
    inv_service: InvestigationService = Depends(get_investigation_service),
    art_service: ArtifactService = Depends(get_artifact_service),
) -> MethodologySectionResponse:
    """Return only the methodologies section."""
    _verify_investigation(investigation_id, inv_service)
    content = _load_json_content(investigation_id, art_service)
    raw = content.get("methodologies") or {}
    logger.info("methodologies_retrieved", id=str(investigation_id))
    return MethodologySectionResponse.model_validate(raw)


@router.get(
    "/technologies",
    response_model=TechnologySectionResponse,
)
async def get_technologies(
    investigation_id: uuid.UUID,
    inv_service: InvestigationService = Depends(get_investigation_service),
    art_service: ArtifactService = Depends(get_artifact_service),
) -> TechnologySectionResponse:
    """Return only the technologies section."""
    _verify_investigation(investigation_id, inv_service)
    content = _load_json_content(investigation_id, art_service)
    raw = content.get("technologies") or {}
    logger.info("technologies_retrieved", id=str(investigation_id))
    return TechnologySectionResponse.model_validate(raw)


@router.get(
    "/datasets",
    response_model=DatasetSectionResponse,
)
async def get_datasets(
    investigation_id: uuid.UUID,
    inv_service: InvestigationService = Depends(get_investigation_service),
    art_service: ArtifactService = Depends(get_artifact_service),
) -> DatasetSectionResponse:
    """Return only the datasets section."""
    _verify_investigation(investigation_id, inv_service)
    content = _load_json_content(investigation_id, art_service)
    raw = content.get("datasets") or {}
    logger.info("datasets_retrieved", id=str(investigation_id))
    return DatasetSectionResponse.model_validate(raw)


@router.get(
    "/temporal",
    response_model=TemporalSectionResponse,
)
async def get_temporal(
    investigation_id: uuid.UUID,
    inv_service: InvestigationService = Depends(get_investigation_service),
    art_service: ArtifactService = Depends(get_artifact_service),
) -> TemporalSectionResponse:
    """Return only the temporal section."""
    _verify_investigation(investigation_id, inv_service)
    content = _load_json_content(investigation_id, art_service)
    raw = content.get("temporal") or {}
    logger.info("temporal_retrieved", id=str(investigation_id))
    return TemporalSectionResponse.model_validate(raw)


@router.get(
    "/collaborations",
    response_model=CollaborationSectionResponse,
)
async def get_collaborations(
    investigation_id: uuid.UUID,
    inv_service: InvestigationService = Depends(get_investigation_service),
    art_service: ArtifactService = Depends(get_artifact_service),
) -> CollaborationSectionResponse:
    """Return only the collaborations section."""
    _verify_investigation(investigation_id, inv_service)
    content = _load_json_content(investigation_id, art_service)
    raw = content.get("collaborations") or {}
    logger.info("collaborations_retrieved", id=str(investigation_id))
    return CollaborationSectionResponse.model_validate(raw)
