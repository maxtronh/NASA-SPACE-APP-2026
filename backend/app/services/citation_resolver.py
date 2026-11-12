"""Automated CrossRef REST API & NASA NTRS BibTeX/DOI Resolution Service.

Implements polite-pool CrossRef client, DOI content-negotiation BibTeX fetcher,
NASA NTRS API client with rate-limit telemetry, synthetic BibTeX generation,
3-tier caching (In-memory LRU -> Raw disk with SHA-256 sidecars -> DB literature_citations),
and strict zero-fabrication validation.
"""

from __future__ import annotations

import collections
import hashlib
import json
import logging
import re
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

import httpx
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from backend.app.models.citation import LiteratureCitation

logger = logging.getLogger(__name__)

DOI_REGEX = re.compile(r"^10\.\d{4,9}/[-._;()/:A-Za-z0-9]+$")
NTRS_ID_REGEX = re.compile(r"^\d{5,12}$")
YEAR_REGEX = re.compile(r"\b(19\d\d|20\d\d)\b")

CROSSREF_API_BASE = "https://api.crossref.org"
NTRS_API_BASE = "https://ntrs.nasa.gov/api"
DEFAULT_POLITE_USER_AGENT = "CORTEXX/1.0 (mailto:flame-cortexx@spaceapps.org)"
DEFAULT_RAW_CACHE_DIR = Path("data/raw/citations")


class ResolvedCitation(BaseModel):
    """Normalized resolved scientific literature citation."""

    doi: Optional[str] = None
    ntrs_id: Optional[str] = None
    title: str = Field(..., description="Publication title")
    authors: list[str] = Field(default_factory=list, description="Author list")
    publication_year: Optional[int] = None
    journal_or_book: Optional[str] = None
    volume: Optional[str] = None
    issue: Optional[str] = None
    pages: Optional[str] = None
    bibtex: str = Field(default="", description="BibTeX entry")
    nasa_url: Optional[str] = None
    download_url: Optional[str] = None
    verification_source: str = Field(
        default="unverified",
        description="Source of verification: crossref, ntrs, both, or unverified",
    )
    verified: bool = Field(default=False, description="Verification flag")
    sha256_checksum: str = Field(default="", description="SHA-256 provenance checksum")
    raw_metadata: dict[str, Any] = Field(
        default_factory=dict, description="Raw upstream JSON metadata"
    )


def clean_doi(doi: str | None) -> str | None:
    """Cleans and standardizes DOI string by removing common URL prefixes."""
    if not doi or not isinstance(doi, str):
        return None
    cleaned = doi.strip()
    for prefix in (
        "https://doi.org/",
        "http://doi.org/",
        "https://dx.doi.org/",
        "http://dx.doi.org/",
        "doi:",
    ):
        if cleaned.lower().startswith(prefix):
            cleaned = cleaned[len(prefix) :]
    return cleaned.strip()


def clean_ntrs_id(ntrs_id: str | None) -> str | None:
    """Cleans and standardizes NASA NTRS Citation identifier."""
    if not ntrs_id or not isinstance(ntrs_id, str):
        return None
    cleaned = ntrs_id.strip()
    for prefix in (
        "https://ntrs.nasa.gov/citations/",
        "https://ntrs.nasa.gov/api/citations/",
        "http://ntrs.nasa.gov/citations/",
        "http://ntrs.nasa.gov/api/citations/",
    ):
        if cleaned.lower().startswith(prefix):
            cleaned = cleaned[len(prefix) :]
    return cleaned.strip().rstrip("/")


class CitationResolver:
    """Automated CrossRef & NASA NTRS citation and BibTeX resolution engine."""

    def __init__(
        self,
        user_agent: str = DEFAULT_POLITE_USER_AGENT,
        raw_cache_dir: Path | str = DEFAULT_RAW_CACHE_DIR,
        timeout: float = 10.0,
        max_retries: int = 3,
        lru_cache_size: int = 256,
    ):
        self.user_agent = user_agent
        self.raw_cache_dir = Path(raw_cache_dir)
        self.raw_cache_dir.mkdir(parents=True, exist_ok=True)
        self.timeout = timeout
        self.max_retries = max_retries
        self.lru_cache_size = lru_cache_size

        # Tier 1: In-memory LRU cache
        self._memory_cache: collections.OrderedDict[str, ResolvedCitation] = (
            collections.OrderedDict()
        )

        # Rate limit telemetry for NTRS API
        self.rate_limit_telemetry: dict[str, Any] = {
            "limit": None,
            "remaining": None,
            "reset": None,
            "last_updated": None,
        }

    # -------------------------------------------------------------------------
    # Validation helpers (Zero-Fabrication Guardrails)
    # -------------------------------------------------------------------------

    def is_valid_doi(self, doi: str | None) -> bool:
        """Validates DOI syntax strictly against canonical CrossRef pattern."""
        c = clean_doi(doi)
        if not c:
            return False
        return bool(DOI_REGEX.match(c))

    def is_valid_ntrs_id(self, ntrs_id: str | None) -> bool:
        """Validates NASA NTRS citation identifier syntax."""
        c = clean_ntrs_id(ntrs_id)
        if not c:
            return False
        return bool(NTRS_ID_REGEX.match(c))

    # -------------------------------------------------------------------------
    # Tier 1: In-memory Cache management
    # -------------------------------------------------------------------------

    def _get_from_memory(self, key: str) -> Optional[ResolvedCitation]:
        if key in self._memory_cache:
            self._memory_cache.move_to_end(key)
            return self._memory_cache[key]
        return None

    def _put_in_memory(self, key: str, citation: ResolvedCitation) -> None:
        if key in self._memory_cache:
            self._memory_cache.move_to_end(key)
        self._memory_cache[key] = citation
        if len(self._memory_cache) > self.lru_cache_size:
            self._memory_cache.popitem(last=False)

    # -------------------------------------------------------------------------
    # Tier 2: Raw Disk Cache with SHA-256 sidecars
    # -------------------------------------------------------------------------

    def _get_safe_filename(self, key_type: str, identifier: str) -> str:
        safe_id = re.sub(r"[^A-Za-z0-9_-]", "_", identifier)
        return f"{key_type}_{safe_id}"

    def _read_from_disk(self, key_type: str, identifier: str) -> Optional[ResolvedCitation]:
        prefix = self._get_safe_filename(key_type, identifier)
        json_path = self.raw_cache_dir / f"{prefix}.json"
        sha_path = self.raw_cache_dir / f"{prefix}.sha256"

        if not json_path.is_file():
            return None

        try:
            content_bytes = json_path.read_bytes()
            computed_sha = hashlib.sha256(content_bytes).hexdigest()

            if sha_path.is_file():
                expected_sha = sha_path.read_text(encoding="utf-8").strip()
                # Support "sha256  filename" standard format or pure sha256
                if " " in expected_sha:
                    expected_sha = expected_sha.split()[0]
                if computed_sha != expected_sha:
                    logger.warning(
                        f"SHA-256 sidecar checksum mismatch for disk cache {json_path}. "
                        f"Expected {expected_sha}, computed {computed_sha}. Invalidating cache."
                    )
                    return None

            data = json.loads(content_bytes.decode("utf-8"))
            citation = ResolvedCitation(**data)
            return citation
        except Exception as exc:
            logger.warning(f"Error reading disk cache {json_path}: {exc}")
            return None

    def _write_to_disk(self, key_type: str, identifier: str, citation: ResolvedCitation) -> None:
        prefix = self._get_safe_filename(key_type, identifier)
        json_path = self.raw_cache_dir / f"{prefix}.json"
        sha_path = self.raw_cache_dir / f"{prefix}.sha256"

        try:
            payload_str = json.dumps(citation.model_dump(), indent=2, sort_keys=True)
            content_bytes = payload_str.encode("utf-8")
            json_path.write_bytes(content_bytes)

            sha256_hash = hashlib.sha256(content_bytes).hexdigest()
            sha_path.write_text(f"{sha256_hash}  {json_path.name}\n", encoding="utf-8")
        except Exception as exc:
            logger.warning(f"Error writing disk cache {json_path}: {exc}")

    # -------------------------------------------------------------------------
    # Tier 3: Database Cache (LiteratureCitation)
    # -------------------------------------------------------------------------

    async def _get_from_db_async(
        self,
        session: AsyncSession,
        doi: Optional[str] = None,
        ntrs_id: Optional[str] = None,
    ) -> Optional[ResolvedCitation]:
        try:
            query = select(LiteratureCitation)
            if doi:
                query = query.where(LiteratureCitation.doi == doi)
            elif ntrs_id:
                query = query.where(LiteratureCitation.ntrs_id == ntrs_id)
            else:
                return None

            result = await session.execute(query)
            db_record = result.scalars().first()
            if db_record:
                return self._model_to_resolved(db_record)
        except Exception as exc:
            logger.warning(f"Error reading literature citation from DB: {exc}")
        return None

    def _get_from_db_sync(
        self,
        session: Session,
        doi: Optional[str] = None,
        ntrs_id: Optional[str] = None,
    ) -> Optional[ResolvedCitation]:
        try:
            query = select(LiteratureCitation)
            if doi:
                query = query.where(LiteratureCitation.doi == doi)
            elif ntrs_id:
                query = query.where(LiteratureCitation.ntrs_id == ntrs_id)
            else:
                return None

            db_record = session.execute(query).scalars().first()
            if db_record:
                return self._model_to_resolved(db_record)
        except Exception as exc:
            logger.warning(f"Error reading literature citation from DB (sync): {exc}")
        return None

    def _model_to_resolved(self, model: LiteratureCitation) -> ResolvedCitation:
        source = "unverified"
        if "CROSSREF" in model.verification_status:
            source = "crossref"
        elif "NTRS" in model.verification_status:
            source = "ntrs"
        elif "DUAL" in model.verification_status:
            source = "both"

        return ResolvedCitation(
            doi=model.doi,
            ntrs_id=model.ntrs_id,
            title=model.title,
            authors=model.authors or [],
            publication_year=model.publication_year,
            journal_or_book=model.journal_or_book,
            bibtex=model.bibtex or "",
            nasa_url=(
                f"https://ntrs.nasa.gov/citations/{model.ntrs_id}"
                if model.ntrs_id
                else None
            ),
            download_url=model.raw_metadata.get("download_url") or model.raw_metadata.get("URL"),
            verification_source=source,
            verified="VERIFIED" in model.verification_status,
            sha256_checksum=model.sha256_checksum,
            raw_metadata=model.raw_metadata or {},
        )

    async def save_to_database(
        self,
        session: AsyncSession,
        citation: ResolvedCitation,
        investigation_id: uuid.UUID,
    ) -> LiteratureCitation:
        """Persists a resolved citation into the database literature_citations table."""
        status_map = {
            "crossref": "VERIFIED_CROSSREF",
            "ntrs": "VERIFIED_NTRS",
            "both": "VERIFIED_DUAL",
        }
        v_status = status_map.get(citation.verification_source, "UNVERIFIED")

        db_citation = LiteratureCitation(
            investigation_id=investigation_id,
            doi=citation.doi,
            ntrs_id=citation.ntrs_id,
            title=citation.title,
            authors=citation.authors,
            publication_year=citation.publication_year,
            journal_or_book=citation.journal_or_book,
            bibtex=citation.bibtex,
            verification_status=v_status,
            sha256_checksum=citation.sha256_checksum,
            raw_metadata=citation.raw_metadata,
        )
        session.add(db_citation)
        await session.commit()
        await session.refresh(db_citation)
        return db_citation

    # -------------------------------------------------------------------------
    # Rate Limit & Telemetry Tracker
    # -------------------------------------------------------------------------

    def _update_ntrs_telemetry(self, headers: httpx.Headers) -> None:
        rem = headers.get("x-ratelimit-remaining") or headers.get("X-RateLimit-Remaining")
        lim = headers.get("x-ratelimit-limit") or headers.get("X-RateLimit-Limit")
        res = headers.get("x-ratelimit-reset") or headers.get("X-RateLimit-Reset")

        if rem is not None:
            try:
                rem_val = int(rem)
                self.rate_limit_telemetry["remaining"] = rem_val
                if rem_val < 20:
                    logger.warning(
                        f"NASA NTRS rate limit threshold alert: {rem_val} remaining. Reset epoch: {res}"
                    )
            except ValueError:
                pass

        if lim is not None:
            try:
                self.rate_limit_telemetry["limit"] = int(lim)
            except ValueError:
                pass

        if res is not None:
            self.rate_limit_telemetry["reset"] = res

        self.rate_limit_telemetry["last_updated"] = datetime.now(timezone.utc).isoformat()

    # -------------------------------------------------------------------------
    # BibTeX Synthesis Helpers
    # -------------------------------------------------------------------------

    def synthesize_bibtex(self, record: dict[str, Any], record_type: str = "crossref") -> str:
        """Synthesizes valid BibTeX entry from metadata."""
        if record_type.lower() == "ntrs":
            return self.synthesize_ntrs_bibtex(record)
        return self.synthesize_crossref_bibtex(record)

    def synthesize_crossref_bibtex(self, data: dict[str, Any]) -> str:
        """Synthesizes standard @article BibTeX entry from CrossRef JSON."""
        authors = []
        first_author_surname = "NASA"
        for idx, a in enumerate(data.get("author", [])):
            fam = a.get("family", "")
            giv = a.get("given", "")
            if fam and giv:
                name_str = f"{fam}, {giv}"
            else:
                name_str = fam or a.get("name", "Unknown")
            authors.append(name_str)
            if idx == 0 and fam:
                first_author_surname = re.sub(r"[^A-Za-z0-9]", "", fam)

        title_list = data.get("title", [])
        title = title_list[0] if title_list else "Unknown Title"
        container = data.get("container-title", [])
        journal = container[0] if container else "Journal"
        issued = data.get("issued", {}).get("date-parts", [[None]])[0]
        year = str(issued[0]) if issued and issued[0] else "Unknown"

        cite_key = f"{first_author_surname}_{year}"
        doi = data.get("DOI", "")
        volume = data.get("volume")
        issue = data.get("issue")
        page = data.get("page")

        lines = [f"@article{{{cite_key},"]
        lines.append(f"  title = {{{title}}},")
        if authors:
            lines.append(f"  author = {{{' and '.join(authors)}}},")
        lines.append(f"  journal = {{{journal}}},")
        if volume:
            lines.append(f"  volume = {{{volume}}},")
        if issue:
            lines.append(f"  number = {{{issue}}},")
        if page:
            lines.append(f"  pages = {{{page}}},")
        lines.append(f"  year = {{{year}}},")
        if doi:
            lines.append(f"  doi = {{{doi}}},")
            lines.append(f"  url = {{https://doi.org/{doi}}}")
        lines.append("}")
        return "\n".join(lines)

    def synthesize_ntrs_bibtex(self, record: dict[str, Any]) -> str:
        """Synthesizes standard @techreport or @inproceedings BibTeX entry from NTRS JSON."""
        sti_type = str(record.get("stiType", "TECHNICAL_REPORT")).upper()
        entry_type = (
            "inproceedings"
            if sti_type in ("CONFERENCE_PAPER", "CONFERENCE_PROCEEDINGS")
            else "techreport"
        )

        authors: list[str] = []
        first_author_surname = "NASA"
        for idx, aff in enumerate(record.get("authorAffiliations", [])):
            name = (
                aff.get("meta", {}).get("author", {}).get("name")
                or aff.get("name")
                or aff.get("author", {}).get("name")
            )
            if name:
                authors.append(name)
                if idx == 0:
                    parts = name.split()
                    if parts:
                        last = parts[0].rstrip(",") if "," in parts[0] else parts[-1]
                        first_author_surname = re.sub(r"[^A-Za-z0-9]", "", last)

        # Fallback author extraction
        if not authors and "authors" in record:
            for idx, a in enumerate(record["authors"]):
                if isinstance(a, str):
                    authors.append(a)
                    if idx == 0:
                        parts = a.split()
                        if parts:
                            last = parts[0].rstrip(",") if "," in parts[0] else parts[-1]
                            first_author_surname = re.sub(r"[^A-Za-z0-9]", "", last)

        # Extract year
        pub_year = "Unknown"
        pub_date = None
        pubs = record.get("publications", [])
        if pubs and isinstance(pubs, list) and isinstance(pubs[0], dict):
            pub_date = pubs[0].get("publicationDate")
        if not pub_date:
            pub_date = record.get("distributionDate") or record.get("created")

        if pub_date:
            match = YEAR_REGEX.search(str(pub_date))
            if match:
                pub_year = match.group(1)

        title = record.get("title", "NASA STI Technical Report")
        report_numbers = record.get("otherReportNumbers", [])
        report_num = report_numbers[0] if report_numbers else f"NASA/NTRS-{record.get('id', '')}"
        ntrs_id = str(record.get("id", ""))
        cite_key = f"{first_author_surname}_{pub_year}"

        lines = [f"@{entry_type}{{{cite_key},"]
        lines.append(f"  title = {{{title}}},")
        if authors:
            lines.append(f"  author = {{{' and '.join(authors)}}},")
        lines.append("  institution = {National Aeronautics and Space Administration (NASA)},")
        lines.append(f"  number = {{{report_num}}},")
        lines.append(f"  year = {{{pub_year}}},")
        if ntrs_id:
            lines.append(f"  url = {{https://ntrs.nasa.gov/citations/{ntrs_id}}}")
        lines.append("}")
        return "\n".join(lines)

    # -------------------------------------------------------------------------
    # DOI Resolution (CrossRef + Content Negotiation)
    # -------------------------------------------------------------------------

    def resolve_doi(
        self,
        doi: str,
        force_refresh: bool = False,
        session: Optional[Session] = None,
    ) -> Optional[ResolvedCitation]:
        """Synchronous DOI resolution via CrossRef and doi.org content negotiation."""
        clean = clean_doi(doi)
        if not self.is_valid_doi(clean):
            logger.warning(f"Zero-Fabrication Validator: Rejected invalid DOI: '{doi}'")
            return None
        assert clean is not None

        cache_key = f"doi:{clean}"

        # Tier 1: In-memory LRU
        if not force_refresh:
            mem = self._get_from_memory(cache_key)
            if mem:
                return mem

        # Tier 2: Raw Disk Cache
        if not force_refresh:
            disk = self._read_from_disk("doi", clean)
            if disk:
                self._put_in_memory(cache_key, disk)
                return disk

        # Tier 3: Database Cache (if session provided)
        if not force_refresh and session is not None:
            db_res = self._get_from_db_sync(session, doi=clean)
            if db_res:
                self._put_in_memory(cache_key, db_res)
                return db_res

        # Upstream resolution
        citation = self._fetch_doi_upstream(clean)
        if citation:
            self._write_to_disk("doi", clean, citation)
            self._put_in_memory(cache_key, citation)
        return citation

    async def resolve_doi_async(
        self,
        doi: str,
        force_refresh: bool = False,
        session: Optional[AsyncSession] = None,
    ) -> Optional[ResolvedCitation]:
        """Asynchronous DOI resolution via CrossRef and doi.org content negotiation."""
        clean = clean_doi(doi)
        if not self.is_valid_doi(clean):
            logger.warning(f"Zero-Fabrication Validator: Rejected invalid DOI: '{doi}'")
            return None
        assert clean is not None

        cache_key = f"doi:{clean}"

        if not force_refresh:
            mem = self._get_from_memory(cache_key)
            if mem:
                return mem

        if not force_refresh:
            disk = self._read_from_disk("doi", clean)
            if disk:
                self._put_in_memory(cache_key, disk)
                return disk

        if not force_refresh and session is not None:
            db_res = await self._get_from_db_async(session, doi=clean)
            if db_res:
                self._put_in_memory(cache_key, db_res)
                return db_res

        citation = await self._fetch_doi_upstream_async(clean)
        if citation:
            self._write_to_disk("doi", clean, citation)
            self._put_in_memory(cache_key, citation)
        return citation

    def _fetch_doi_upstream(self, clean_doi: str) -> Optional[ResolvedCitation]:
        url = f"{CROSSREF_API_BASE}/works/{clean_doi}"
        headers = {"User-Agent": self.user_agent}

        try:
            with httpx.Client(timeout=self.timeout) as client:
                resp = None
                for attempt in range(self.max_retries):
                    resp = client.get(url, headers=headers)
                    if resp.status_code == 429:
                        retry_after = float(resp.headers.get("Retry-After", 1.0))
                        time.sleep(retry_after)
                        continue
                    break

                if resp is None or resp.status_code == 404:
                    logger.warning(f"CrossRef DOI not found (404): {clean_doi}")
                    return None
                if resp.status_code != 200:
                    logger.warning(
                        f"CrossRef returned status {resp.status_code} for DOI {clean_doi}"
                    )
                    return None

                data = resp.json().get("message", {})

                # DOI Content Negotiation for BibTeX
                bibtex_resp = client.get(
                    f"https://doi.org/{clean_doi}",
                    headers={"Accept": "application/x-bibtex", "User-Agent": self.user_agent},
                    follow_redirects=True,
                )
                if bibtex_resp.status_code == 200 and "@" in bibtex_resp.text:
                    bibtex_str = bibtex_resp.text.strip()
                else:
                    bibtex_str = self.synthesize_crossref_bibtex(data)

                return self._build_crossref_resolved_citation(clean_doi, data, bibtex_str)

        except (httpx.HTTPError, OSError) as exc:
            logger.error(f"CrossRef upstream resolution error for {clean_doi}: {exc}")
            return None

    async def _fetch_doi_upstream_async(self, clean_doi: str) -> Optional[ResolvedCitation]:
        url = f"{CROSSREF_API_BASE}/works/{clean_doi}"
        headers = {"User-Agent": self.user_agent}

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = None
                for attempt in range(self.max_retries):
                    resp = await client.get(url, headers=headers)
                    if resp.status_code == 429:
                        retry_after = float(resp.headers.get("Retry-After", 1.0))
                        time.sleep(retry_after)
                        continue
                    break

                if resp is None or resp.status_code == 404:
                    logger.warning(f"CrossRef DOI not found (404): {clean_doi}")
                    return None
                if resp.status_code != 200:
                    logger.warning(
                        f"CrossRef returned status {resp.status_code} for DOI {clean_doi}"
                    )
                    return None

                data = resp.json().get("message", {})

                bibtex_resp = await client.get(
                    f"https://doi.org/{clean_doi}",
                    headers={"Accept": "application/x-bibtex", "User-Agent": self.user_agent},
                    follow_redirects=True,
                )
                if bibtex_resp.status_code == 200 and "@" in bibtex_resp.text:
                    bibtex_str = bibtex_resp.text.strip()
                else:
                    bibtex_str = self.synthesize_crossref_bibtex(data)

                return self._build_crossref_resolved_citation(clean_doi, data, bibtex_str)

        except (httpx.HTTPError, OSError) as exc:
            logger.error(f"CrossRef upstream resolution error for {clean_doi}: {exc}")
            return None

    def _build_crossref_resolved_citation(
        self, clean_doi: str, data: dict[str, Any], bibtex_str: str
    ) -> ResolvedCitation:
        authors = []
        for a in data.get("author", []):
            fam = a.get("family", "")
            giv = a.get("given", "")
            authors.append(f"{fam}, {giv}" if fam and giv else fam or a.get("name", "Unknown"))

        title_list = data.get("title", [])
        title = title_list[0] if title_list else "Unknown Title"
        container = data.get("container-title", [])
        journal = container[0] if container else None
        issued = data.get("issued", {}).get("date-parts", [[None]])[0]
        year = None
        if issued and issued[0]:
            try:
                year = int(issued[0])
            except (ValueError, TypeError):
                year = None

        raw_str = json.dumps(data, sort_keys=True)
        sha256 = hashlib.sha256(raw_str.encode("utf-8")).hexdigest()

        return ResolvedCitation(
            doi=clean_doi,
            ntrs_id=None,
            title=title,
            authors=authors,
            publication_year=year,
            journal_or_book=journal,
            volume=data.get("volume"),
            issue=data.get("issue"),
            pages=data.get("page"),
            bibtex=bibtex_str,
            nasa_url=None,
            download_url=data.get("URL"),
            verification_source="crossref",
            verified=True,
            sha256_checksum=sha256,
            raw_metadata=data,
        )

    # -------------------------------------------------------------------------
    # NASA NTRS Citation Resolution
    # -------------------------------------------------------------------------

    def resolve_ntrs(
        self,
        ntrs_id: str,
        force_refresh: bool = False,
        session: Optional[Session] = None,
    ) -> Optional[ResolvedCitation]:
        """Synchronous NASA NTRS citation resolution."""
        clean = clean_ntrs_id(ntrs_id)
        if not self.is_valid_ntrs_id(clean):
            logger.warning(f"Zero-Fabrication Validator: Rejected invalid NTRS ID: '{ntrs_id}'")
            return None
        assert clean is not None

        cache_key = f"ntrs:{clean}"

        # Tier 1: In-memory
        if not force_refresh:
            mem = self._get_from_memory(cache_key)
            if mem:
                return mem

        # Tier 2: Raw Disk Cache
        if not force_refresh:
            disk = self._read_from_disk("ntrs", clean)
            if disk:
                self._put_in_memory(cache_key, disk)
                return disk

        # Tier 3: DB Cache
        if not force_refresh and session is not None:
            db_res = self._get_from_db_sync(session, ntrs_id=clean)
            if db_res:
                self._put_in_memory(cache_key, db_res)
                return db_res

        # Upstream resolution
        citation = self._fetch_ntrs_upstream(clean)
        if citation:
            self._write_to_disk("ntrs", clean, citation)
            self._put_in_memory(cache_key, citation)
        return citation

    async def resolve_ntrs_async(
        self,
        ntrs_id: str,
        force_refresh: bool = False,
        session: Optional[AsyncSession] = None,
    ) -> Optional[ResolvedCitation]:
        """Asynchronous NASA NTRS citation resolution."""
        clean = clean_ntrs_id(ntrs_id)
        if not self.is_valid_ntrs_id(clean):
            logger.warning(f"Zero-Fabrication Validator: Rejected invalid NTRS ID: '{ntrs_id}'")
            return None
        assert clean is not None

        cache_key = f"ntrs:{clean}"

        if not force_refresh:
            mem = self._get_from_memory(cache_key)
            if mem:
                return mem

        if not force_refresh:
            disk = self._read_from_disk("ntrs", clean)
            if disk:
                self._put_in_memory(cache_key, disk)
                return disk

        if not force_refresh and session is not None:
            db_res = await self._get_from_db_async(session, ntrs_id=clean)
            if db_res:
                self._put_in_memory(cache_key, db_res)
                return db_res

        citation = await self._fetch_ntrs_upstream_async(clean)
        if citation:
            self._write_to_disk("ntrs", clean, citation)
            self._put_in_memory(cache_key, citation)
        return citation

    def _fetch_ntrs_upstream(self, clean_ntrs_id: str) -> Optional[ResolvedCitation]:
        url = f"{NTRS_API_BASE}/citations/{clean_ntrs_id}"
        headers = {"User-Agent": self.user_agent}

        try:
            with httpx.Client(timeout=self.timeout) as client:
                resp = client.get(url, headers=headers)
                self._update_ntrs_telemetry(resp.headers)

                if resp.status_code == 404:
                    logger.warning(f"NASA NTRS Citation ID not found (404): {clean_ntrs_id}")
                    return None
                if resp.status_code != 200:
                    logger.warning(
                        f"NASA NTRS returned status {resp.status_code} for ID {clean_ntrs_id}"
                    )
                    return None

                data = resp.json()
                return self._build_ntrs_resolved_citation(clean_ntrs_id, data)

        except (httpx.HTTPError, OSError) as exc:
            logger.error(f"NASA NTRS resolution error for {clean_ntrs_id}: {exc}")
            return None

    async def _fetch_ntrs_upstream_async(self, clean_ntrs_id: str) -> Optional[ResolvedCitation]:
        url = f"{NTRS_API_BASE}/citations/{clean_ntrs_id}"
        headers = {"User-Agent": self.user_agent}

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.get(url, headers=headers)
                self._update_ntrs_telemetry(resp.headers)

                if resp.status_code == 404:
                    logger.warning(f"NASA NTRS Citation ID not found (404): {clean_ntrs_id}")
                    return None
                if resp.status_code != 200:
                    logger.warning(
                        f"NASA NTRS returned status {resp.status_code} for ID {clean_ntrs_id}"
                    )
                    return None

                data = resp.json()
                return self._build_ntrs_resolved_citation(clean_ntrs_id, data)

        except (httpx.HTTPError, OSError) as exc:
            logger.error(f"NASA NTRS resolution error for {clean_ntrs_id}: {exc}")
            return None

    def _build_ntrs_resolved_citation(
        self, clean_ntrs_id: str, data: dict[str, Any]
    ) -> ResolvedCitation:
        title = data.get("title", f"NASA NTRS Record {clean_ntrs_id}")

        authors: list[str] = []
        for aff in data.get("authorAffiliations", []):
            name = (
                aff.get("meta", {}).get("author", {}).get("name")
                or aff.get("name")
                or aff.get("author", {}).get("name")
            )
            if name:
                authors.append(name)

        if not authors and "authors" in data:
            for a in data["authors"]:
                if isinstance(a, str):
                    authors.append(a)

        # Date & Year extraction
        pub_year = None
        pub_date = None
        pubs = data.get("publications", [])
        if pubs and isinstance(pubs, list) and isinstance(pubs[0], dict):
            pub_date = pubs[0].get("publicationDate")
        if not pub_date:
            pub_date = data.get("distributionDate") or data.get("created")

        if pub_date:
            match = YEAR_REGEX.search(str(pub_date))
            if match:
                try:
                    pub_year = int(match.group(1))
                except ValueError:
                    pub_year = None

        # Download URL
        download_url = None
        downloads = data.get("downloads", [])
        if downloads and isinstance(downloads, list) and isinstance(downloads[0], dict):
            links = downloads[0].get("links", {})
            download_url = links.get("pdf") or links.get("fulltext")

        bibtex_str = self.synthesize_ntrs_bibtex(data)
        raw_str = json.dumps(data, sort_keys=True)
        sha256 = hashlib.sha256(raw_str.encode("utf-8")).hexdigest()

        report_numbers = data.get("otherReportNumbers", [])
        report_num = report_numbers[0] if report_numbers else None

        return ResolvedCitation(
            doi=None,
            ntrs_id=clean_ntrs_id,
            title=title,
            authors=authors,
            publication_year=pub_year,
            journal_or_book=report_num or "NASA STI Technical Report",
            bibtex=bibtex_str,
            nasa_url=f"https://ntrs.nasa.gov/citations/{clean_ntrs_id}",
            download_url=download_url,
            verification_source="ntrs",
            verified=True,
            sha256_checksum=sha256,
            raw_metadata=data,
        )

    # -------------------------------------------------------------------------
    # Zero-Fabrication Candidate Verification
    # -------------------------------------------------------------------------

    def verify_citation(
        self,
        citation: dict[str, Any],
        session: Optional[Session] = None,
    ) -> tuple[bool, Optional[ResolvedCitation]]:
        """Strictly verifies an incoming candidate citation dictionary.

        Rejects hallucinated / fake citations with (False, None).
        Returns (True, ResolvedCitation) for genuine verified records.
        """
        if not isinstance(citation, dict):
            return False, None

        raw_doi = citation.get("doi")
        raw_ntrs_id = citation.get("ntrs_id")

        # Check if nasa_source_url contains NTRS ID
        nasa_url = citation.get("nasa_source_url") or citation.get("nasa_url")
        if not raw_ntrs_id and nasa_url and "ntrs.nasa.gov" in nasa_url:
            clean_url_id = clean_ntrs_id(nasa_url)
            if self.is_valid_ntrs_id(clean_url_id):
                raw_ntrs_id = clean_url_id

        has_valid_doi = self.is_valid_doi(raw_doi)
        has_valid_ntrs = self.is_valid_ntrs_id(raw_ntrs_id)

        # Rejection of unresolvable / fake identifiers
        if not has_valid_doi and not has_valid_ntrs:
            logger.warning(
                f"Zero-Fabrication Validator: Citation contains neither valid DOI nor NTRS ID: {citation}"
            )
            return False, None

        # Dual resolution
        if has_valid_doi and has_valid_ntrs:
            res_doi = self.resolve_doi(raw_doi, session=session)
            res_ntrs = self.resolve_ntrs(raw_ntrs_id, session=session)
            if res_doi and res_ntrs:
                # Merge into dual verified citation
                res_doi.ntrs_id = res_ntrs.ntrs_id
                res_doi.nasa_url = res_ntrs.nasa_url
                res_doi.verification_source = "both"
                return True, res_doi
            elif res_doi:
                return True, res_doi
            elif res_ntrs:
                return True, res_ntrs
            else:
                return False, None

        if has_valid_doi:
            res = self.resolve_doi(raw_doi, session=session)
            if res and res.verified:
                return True, res
            return False, None

        if has_valid_ntrs:
            res = self.resolve_ntrs(raw_ntrs_id, session=session)
            if res and res.verified:
                return True, res
            return False, None

        return False, None

    async def verify_citation_async(
        self,
        citation: dict[str, Any],
        session: Optional[AsyncSession] = None,
    ) -> tuple[bool, Optional[ResolvedCitation]]:
        """Asynchronous version of verify_citation."""
        if not isinstance(citation, dict):
            return False, None

        raw_doi = citation.get("doi")
        raw_ntrs_id = citation.get("ntrs_id")

        nasa_url = citation.get("nasa_source_url") or citation.get("nasa_url")
        if not raw_ntrs_id and nasa_url and "ntrs.nasa.gov" in nasa_url:
            clean_url_id = clean_ntrs_id(nasa_url)
            if self.is_valid_ntrs_id(clean_url_id):
                raw_ntrs_id = clean_url_id

        has_valid_doi = self.is_valid_doi(raw_doi)
        has_valid_ntrs = self.is_valid_ntrs_id(raw_ntrs_id)

        if not has_valid_doi and not has_valid_ntrs:
            return False, None

        if has_valid_doi and has_valid_ntrs:
            res_doi = await self.resolve_doi_async(raw_doi, session=session)
            res_ntrs = await self.resolve_ntrs_async(raw_ntrs_id, session=session)
            if res_doi and res_ntrs:
                res_doi.ntrs_id = res_ntrs.ntrs_id
                res_doi.nasa_url = res_ntrs.nasa_url
                res_doi.verification_source = "both"
                return True, res_doi
            elif res_doi:
                return True, res_doi
            elif res_ntrs:
                return True, res_ntrs
            return False, None

        if has_valid_doi:
            res = await self.resolve_doi_async(raw_doi, session=session)
            if res and res.verified:
                return True, res
            return False, None

        if has_valid_ntrs:
            res = await self.resolve_ntrs_async(raw_ntrs_id, session=session)
            if res and res.verified:
                return True, res
            return False, None

        return False, None
