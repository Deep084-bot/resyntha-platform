"""Institution Intelligence REST API.

Provides deep institution profiles computed from the ResearchGraph.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends

from app.cache import cached
from app.modules.institution.api.dependencies import (
    get_institution_profile_service,
)
from app.modules.institution.api.schemas import (
    AuthorEntryResponse,
    CollaborationEntryResponse,
    CompareRequest,
    EntityCountResponse,
    InstitutionProfileResponse,
    PaperEntryResponse,
    YearlyTrendResponse,
)
from app.modules.institution.domain.models import InstitutionProfile
from app.modules.institution.service.service import InstitutionProfileService
from app.observability.logger import get_logger

router = APIRouter(
    prefix="/investigations/{investigation_id}/institution-profiles",
    tags=["institution-intelligence"],
)
logger = get_logger(__name__)


@router.get("")
@cached("institution_profiles:{investigation_id}", ttl=1800)
async def list_institution_profiles(
    investigation_id: uuid.UUID,
    svc: InstitutionProfileService = Depends(get_institution_profile_service),
) -> list[InstitutionProfileResponse]:
    """List all institution profiles for this investigation, sorted by paper count."""
    profiles = svc.list_profiles(investigation_id)
    return [_to_response(p) for p in profiles]


@router.get("/{name}")
@cached("institution_profile:{investigation_id}:{name}", ttl=1800)
async def get_institution_profile(
    investigation_id: uuid.UUID,
    name: str,
    svc: InstitutionProfileService = Depends(get_institution_profile_service),
) -> InstitutionProfileResponse:
    """Get a detailed profile for a single institution."""
    profile = svc.get_profile(investigation_id, name)
    return _to_response(profile)


@router.post("/compare")
async def compare_institutions(
    investigation_id: uuid.UUID,
    body: CompareRequest,
    svc: InstitutionProfileService = Depends(get_institution_profile_service),
) -> list[InstitutionProfileResponse]:
    """Compare up to 5 institutions side-by-side."""
    profiles = svc.compare(investigation_id, body.institution_names)
    return [_to_response(p) for p in profiles]


def _to_response(p: InstitutionProfile) -> InstitutionProfileResponse:
    return InstitutionProfileResponse(
        name=p.name,
        type=p.type,
        total_papers=p.total_papers,
        total_authors=p.total_authors,
        total_citations=p.total_citations,
        research_domains=[
            EntityCountResponse(name=rd.name, count=rd.count) for rd in p.research_domains
        ],
        technologies=[EntityCountResponse(name=t.name, count=t.count) for t in p.technologies],
        datasets=[EntityCountResponse(name=d.name, count=d.count) for d in p.datasets],
        methodologies=[EntityCountResponse(name=m.name, count=m.count) for m in p.methodologies],
        top_authors=[
            AuthorEntryResponse(
                name=a.name,
                paper_count=a.paper_count,
                affiliated_institutions=a.affiliated_institutions,
            )
            for a in p.top_authors
        ],
        top_papers=[
            PaperEntryResponse(
                id=pp.id,
                title=pp.title,
                year=pp.year,
                citation_count=pp.citation_count,
                venue=pp.venue,
                authors=pp.authors,
                research_domains=pp.research_domains,
            )
            for pp in p.top_papers
        ],
        yearly_trends=[
            YearlyTrendResponse(year=yt.year, paper_count=yt.paper_count) for yt in p.yearly_trends
        ],
        collaborating_institutions=[
            CollaborationEntryResponse(
                institution_name=ci.institution_name,
                joint_paper_count=ci.joint_paper_count,
            )
            for ci in p.collaborating_institutions
        ],
        co_authors=[
            AuthorEntryResponse(name=ca.name, paper_count=ca.paper_count) for ca in p.co_authors
        ],
    )
