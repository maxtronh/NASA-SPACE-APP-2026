"""FastAPI router for Automated CrossRef & NASA NTRS citation resolution and BibTeX export."""

from __future__ import annotations

import uuid
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.db.session import get_db
from backend.app.models.citation import LiteratureCitation
from backend.app.models.investigation import Investigation
from backend.app.services.citation_resolver import CitationResolver, ResolvedCitation

router = APIRouter(prefix="/citations", tags=["citations"])
resolver = CitationResolver()


class VerifyCitationRequest(BaseModel):
    doi: Optional[str] = None
    ntrs_id: Optional[str] = None
    title: Optional[str] = None
    nasa_source_url: Optional[str] = None
    extra: dict[str, Any] = Field(default_factory=dict)


class VerifyCitationResponse(BaseModel):
    verified: bool
    citation: Optional[ResolvedCitation] = None
    verification_source: Optional[str] = None


class SaveCitationRequest(BaseModel):
    investigation_id: uuid.UUID
    citation: ResolvedCitation


@router.get("/resolve/doi", response_model=ResolvedCitation)
async def resolve_doi_endpoint(
    doi: str = Query(..., description="Digital Object Identifier (DOI) to resolve"),
    force_refresh: bool = Query(default=False, description="Bypass local cache"),
    db: AsyncSession = Depends(get_db),
):
    """Resolves publication metadata and BibTeX from CrossRef via DOI."""
    if not resolver.is_valid_doi(doi):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid DOI format: '{doi}'. Must follow canonical 10.xxxx/yyyy syntax.",
        )

    citation = await resolver.resolve_doi_async(doi, force_refresh=force_refresh, session=db)
    if not citation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"DOI '{doi}' could not be resolved from authoritative registrars.",
        )
    return citation


@router.get("/resolve/ntrs", response_model=ResolvedCitation)
async def resolve_ntrs_endpoint(
    ntrs_id: str = Query(..., description="NASA NTRS Citation ID to resolve"),
    force_refresh: bool = Query(default=False, description="Bypass local cache"),
    db: AsyncSession = Depends(get_db),
):
    """Resolves publication metadata and synthesized BibTeX from NASA Technical Reports Server."""
    if not resolver.is_valid_ntrs_id(ntrs_id):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid NASA NTRS Citation ID format: '{ntrs_id}'. Must be numeric string.",
        )

    citation = await resolver.resolve_ntrs_async(ntrs_id, force_refresh=force_refresh, session=db)
    if not citation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"NASA NTRS Citation ID '{ntrs_id}' was not found in NASA STI archives.",
        )
    return citation


@router.get("/doi/{doi:path}", response_model=ResolvedCitation)
async def get_doi_path_endpoint(
    doi: str,
    force_refresh: bool = Query(default=False),
    db: AsyncSession = Depends(get_db),
):
    """Convenience path parameter endpoint for DOI resolution."""
    return await resolve_doi_endpoint(doi=doi, force_refresh=force_refresh, db=db)


@router.get("/ntrs/{ntrs_id}", response_model=ResolvedCitation)
async def get_ntrs_path_endpoint(
    ntrs_id: str,
    force_refresh: bool = Query(default=False),
    db: AsyncSession = Depends(get_db),
):
    """Convenience path parameter endpoint for NASA NTRS citation resolution."""
    return await resolve_ntrs_endpoint(ntrs_id=ntrs_id, force_refresh=force_refresh, db=db)


@router.post("/verify", response_model=VerifyCitationResponse)
async def verify_citation_endpoint(
    payload: VerifyCitationRequest,
    db: AsyncSession = Depends(get_db),
):
    """Zero-Fabrication validation endpoint for candidate literature citations."""
    input_dict = payload.model_dump()
    verified, resolved = await resolver.verify_citation_async(input_dict, session=db)
    source = resolved.verification_source if resolved else None
    return VerifyCitationResponse(
        verified=verified,
        citation=resolved,
        verification_source=source,
    )


@router.get("/bibtex")
async def get_bibtex_endpoint(
    doi: Optional[str] = Query(default=None, description="DOI to export BibTeX for"),
    ntrs_id: Optional[str] = Query(default=None, description="NTRS ID to export BibTeX for"),
    output_format: str = Query(
        default="text", alias="format", description="Output format: 'text' or 'json'"
    ),
    db: AsyncSession = Depends(get_db),
):
    """Fetches or synthesizes authoritative BibTeX entries for academic citation."""
    if not doi and not ntrs_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Must specify at least one of 'doi' or 'ntrs_id'.",
        )

    citation: Optional[ResolvedCitation] = None
    if doi:
        citation = await resolver.resolve_doi_async(doi, session=db)
    elif ntrs_id:
        citation = await resolver.resolve_ntrs_async(ntrs_id, session=db)

    if not citation or not citation.bibtex:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="BibTeX could not be retrieved or synthesized for the requested record.",
        )

    if output_format.lower() == "json":
        return {
            "doi": citation.doi,
            "ntrs_id": citation.ntrs_id,
            "title": citation.title,
            "bibtex": citation.bibtex,
        }

    return PlainTextResponse(
        content=citation.bibtex,
        media_type="application/x-bibtex; charset=utf-8",
    )


@router.get("/telemetry")
async def get_rate_limit_telemetry():
    """Returns NASA NTRS API upstream rate-limit telemetry and status."""
    return {"rate_limit": resolver.rate_limit_telemetry}


async def _resolve_investigation(db: AsyncSession, id_or_slug: str) -> Investigation:
    try:
        val_uuid = uuid.UUID(id_or_slug)
        res = await db.execute(select(Investigation).where(Investigation.id == val_uuid))
        inv = res.scalar_one_or_none()
    except ValueError:
        res = await db.execute(select(Investigation).where(Investigation.slug == id_or_slug))
        inv = res.scalar_one_or_none()
        if not inv and id_or_slug == "flex-droplet-burning":
            alt = await db.execute(select(Investigation).where(Investigation.slug == "flex-2-heptane-droplet"))
            inv = alt.scalar_one_or_none()
    if not inv:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Investigation '{id_or_slug}' not found",
        )
    return inv


@router.get("/investigation/{investigation_id}")
async def list_investigation_citations(
    investigation_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Retrieves all persisted verified literature citations for an investigation."""
    query = select(LiteratureCitation).where(
        LiteratureCitation.investigation_id == investigation_id
    )
    result = await db.execute(query)
    citations = result.scalars().all()
    return [c.to_dict() for c in citations]


@router.get("/investigations/{slug}")
async def list_investigation_citations_by_slug(
    slug: str,
    db: AsyncSession = Depends(get_db),
):
    """Retrieves all verified literature citations for an investigation by its slug or ID."""
    inv = await _resolve_investigation(db, slug)
    query = select(LiteratureCitation).where(
        LiteratureCitation.investigation_id == inv.id
    )
    result = await db.execute(query)
    citations = result.scalars().all()
    return [c.to_dict() for c in citations]


@router.get("/investigations/{slug}/bibtex")
async def get_investigation_bibtex_by_slug(
    slug: str,
    db: AsyncSession = Depends(get_db),
):
    """Retrieves concatenated BibTeX entries for an investigation by its slug or ID."""
    inv = await _resolve_investigation(db, slug)
    query = select(LiteratureCitation).where(
        LiteratureCitation.investigation_id == inv.id
    )
    result = await db.execute(query)
    citations = result.scalars().all()
    bibtex_entries = [c.bibtex for c in citations if c.bibtex]
    return PlainTextResponse(
        content="\n\n".join(bibtex_entries),
        media_type="application/x-bibtex; charset=utf-8",
    )


@router.post("/save", status_code=status.HTTP_201_CREATED)
async def save_citation_endpoint(
    payload: SaveCitationRequest,
    db: AsyncSession = Depends(get_db),
):
    """Persists a verified citation into the database linked to an investigation."""
    saved = await resolver.save_to_database(
        session=db,
        citation=payload.citation,
        investigation_id=payload.investigation_id,
    )
    return saved.to_dict()
