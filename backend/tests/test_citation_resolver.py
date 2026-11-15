"""Comprehensive Unit and Integration Test Suite for CitationResolver and Literature Citations.

Tests:
1. Canonical DOI and NTRS syntax validation and prefix sanitization.
2. CrossRef REST API client with Polite Pool User-Agent header.
3. DOI content negotiation for standard BibTeX retrieval.
4. NASA NTRS API client with rate-limit telemetry tracking.
5. Synthetic BibTeX synthesis for NASA STI technical reports and conference papers.
6. Multi-tier caching: Tier 1 in-memory LRU, Tier 2 raw disk with SHA-256 sidecars, Tier 3 DB.
7. Zero-fabrication validator: strict rejection of fake DOIs and hallucinated citations.
8. FastAPI endpoints: /citations/resolve, /citations/verify, /citations/bibtex, /citations/telemetry.
9. SQLAlchemy LiteratureCitation relational model, Alembic migration 0003, and cascade deletes.
10. Edge cases: Unicode accents in authors, 429 backoff, corrupted SHA-256 sidecars.
"""

from __future__ import annotations

import json
import logging
import uuid
from typing import Any
from unittest.mock import MagicMock, patch

import httpx
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

from backend.app.models.base import Base
from backend.app.models.citation import LiteratureCitation
from backend.app.models.investigation import Investigation
from backend.app.services.citation_resolver import (
    DEFAULT_POLITE_USER_AGENT,
    CitationResolver,
    ResolvedCitation,
    clean_doi,
    clean_ntrs_id,
)


# ==============================================================================
# 1. DOI & NTRS SYNTAX VALIDATION TESTS
# ==============================================================================

def test_clean_doi():
    """Verifies prefix stripping from diverse DOI formatting variants."""
    assert clean_doi("10.1016/j.combustflame.2013.11.014") == "10.1016/j.combustflame.2013.11.014"
    assert clean_doi("https://doi.org/10.1016/j.combustflame.2013.11.014") == "10.1016/j.combustflame.2013.11.014"
    assert clean_doi("http://doi.org/10.1016/j.combustflame.2013.11.014") == "10.1016/j.combustflame.2013.11.014"
    assert clean_doi("https://dx.doi.org/10.1016/j.combustflame.2013.11.014") == "10.1016/j.combustflame.2013.11.014"
    assert clean_doi("doi:10.1016/j.combustflame.2013.11.014") == "10.1016/j.combustflame.2013.11.014"
    assert clean_doi("   10.1000/182   ") == "10.1000/182"
    assert clean_doi(None) is None
    assert clean_doi("") is None


def test_is_valid_doi():
    """Verifies strict DOI syntax matching and rejection of fake/malformed DOIs."""
    resolver = CitationResolver()
    assert resolver.is_valid_doi("10.1016/j.combustflame.2013.11.014") is True
    assert resolver.is_valid_doi("https://doi.org/10.1016/j.combustflame.2013.11.014") is True
    assert resolver.is_valid_doi("10.1000/182") is True
    assert resolver.is_valid_doi("10.2514/6.2015-0818") is True

    # Rejection of invalid / fake strings
    assert resolver.is_valid_doi(None) is False
    assert resolver.is_valid_doi("") is False
    assert resolver.is_valid_doi("   ") is False
    assert resolver.is_valid_doi("not-a-doi") is False
    assert resolver.is_valid_doi("10.") is False
    assert resolver.is_valid_doi("10.1234") is False  # Missing suffix
    assert resolver.is_valid_doi("https://doi.org/") is False
    assert resolver.is_valid_doi("fake.paper.doi") is False


def test_clean_and_validate_ntrs_id():
    """Verifies NASA NTRS ID cleaning and validation."""
    resolver = CitationResolver()
    assert clean_ntrs_id("20150023456") == "20150023456"
    assert clean_ntrs_id("https://ntrs.nasa.gov/citations/20150023456") == "20150023456"
    assert clean_ntrs_id("https://ntrs.nasa.gov/api/citations/20150023456/") == "20150023456"

    assert resolver.is_valid_ntrs_id("20150023456") is True
    assert resolver.is_valid_ntrs_id("19980237145") is True
    assert resolver.is_valid_ntrs_id("https://ntrs.nasa.gov/citations/20150023456") is True

    # Rejections
    assert resolver.is_valid_ntrs_id(None) is False
    assert resolver.is_valid_ntrs_id("") is False
    assert resolver.is_valid_ntrs_id("abc") is False
    assert resolver.is_valid_ntrs_id("123") is False  # Too short
    assert resolver.is_valid_ntrs_id("99999999999999") is False  # Too long


# ==============================================================================
# 2. CROSSREF CLIENT & CONTENT NEGOTIATION TESTS
# ==============================================================================

MOCK_CROSSREF_METADATA = {
    "status": "ok",
    "message-type": "work",
    "message": {
        "DOI": "10.1016/j.combustflame.2013.11.014",
        "title": ["Detailed Droplet Combustion in Microgravity"],
        "author": [
            {"given": "Michaël", "family": "Bauerheim"},
            {"given": "Chung K.", "family": "Law"},
        ],
        "container-title": ["Combustion and Flame"],
        "issued": {"date-parts": [[2014, 4, 1]]},
        "volume": "161",
        "issue": "4",
        "page": "123-135",
        "URL": "https://doi.org/10.1016/j.combustflame.2013.11.014",
    },
}

MOCK_DOI_BIBTEX = """@article{Bauerheim_2014,
  title = {Detailed Droplet Combustion in Microgravity},
  author = {Bauerheim, Michaël and Law, Chung K.},
  journal = {Combustion and Flame},
  volume = {161},
  number = {4},
  pages = {123--135},
  year = {2014},
  doi = {10.1016/j.combustflame.2013.11.014}
}"""


def test_resolve_doi_crossref_mocked(tmp_path):
    """Verifies CrossRef resolution, Polite Pool header, and BibTeX content negotiation."""
    resolver = CitationResolver(raw_cache_dir=tmp_path)

    def mock_get(url, headers=None, follow_redirects=False):
        if "api.crossref.org" in str(url):
            assert headers is not None
            assert headers.get("User-Agent") == DEFAULT_POLITE_USER_AGENT
            return httpx.Response(200, json=MOCK_CROSSREF_METADATA, request=httpx.Request("GET", url))
        elif "doi.org" in str(url):
            assert headers is not None
            assert headers.get("Accept") == "application/x-bibtex"
            return httpx.Response(200, text=MOCK_DOI_BIBTEX, request=httpx.Request("GET", url))
        return httpx.Response(404, request=httpx.Request("GET", url))

    with patch.object(httpx.Client, "get", side_effect=mock_get):
        citation = resolver.resolve_doi("10.1016/j.combustflame.2013.11.014")

    assert citation is not None
    assert citation.doi == "10.1016/j.combustflame.2013.11.014"
    assert citation.title == "Detailed Droplet Combustion in Microgravity"
    assert citation.authors == ["Bauerheim, Michaël", "Law, Chung K."]
    assert citation.publication_year == 2014
    assert citation.journal_or_book == "Combustion and Flame"
    assert citation.volume == "161"
    assert citation.issue == "4"
    assert citation.pages == "123-135"
    assert citation.verified is True
    assert citation.verification_source == "crossref"
    assert "@article" in citation.bibtex
    assert len(citation.sha256_checksum) == 64


def test_resolve_doi_404_zero_fabrication(tmp_path):
    """Zero-Fabrication Validator: 404 from CrossRef strictly returns None."""
    resolver = CitationResolver(raw_cache_dir=tmp_path)

    def mock_get(url, headers=None, **kwargs):
        return httpx.Response(404, text="Resource not found.", request=httpx.Request("GET", url))

    with patch.object(httpx.Client, "get", side_effect=mock_get):
        citation = resolver.resolve_doi("10.99999/fake.doi.does.not.exist")

    assert citation is None


def test_resolve_doi_bibtex_synthetic_fallback(tmp_path):
    """Verifies synthetic BibTeX generation when doi.org content negotiation fails."""
    resolver = CitationResolver(raw_cache_dir=tmp_path)

    def mock_get(url, headers=None, **kwargs):
        if "api.crossref.org" in str(url):
            return httpx.Response(200, json=MOCK_CROSSREF_METADATA, request=httpx.Request("GET", url))
        # doi.org content negotiation fails with 500
        return httpx.Response(500, request=httpx.Request("GET", url))

    with patch.object(httpx.Client, "get", side_effect=mock_get):
        citation = resolver.resolve_doi("10.1016/j.combustflame.2013.11.014")

    assert citation is not None
    assert "@article{" in citation.bibtex
    assert "Bauerheim_2014" in citation.bibtex
    assert "Michaël" in citation.bibtex
    assert "Combustion and Flame" in citation.bibtex


def test_resolve_doi_429_rate_limit_backoff(tmp_path):
    """Verifies backoff on CrossRef 429 Too Many Requests."""
    resolver = CitationResolver(raw_cache_dir=tmp_path, max_retries=2)
    attempts = 0

    def mock_get(url, headers=None, **kwargs):
        nonlocal attempts
        attempts += 1
        if "api.crossref.org" in str(url):
            if attempts == 1:
                return httpx.Response(
                    429,
                    headers={"Retry-After": "0.01"},
                    request=httpx.Request("GET", url),
                )
            return httpx.Response(200, json=MOCK_CROSSREF_METADATA, request=httpx.Request("GET", url))
        return httpx.Response(200, text=MOCK_DOI_BIBTEX, request=httpx.Request("GET", url))

    with patch.object(httpx.Client, "get", side_effect=mock_get):
        citation = resolver.resolve_doi("10.1016/j.combustflame.2013.11.014")

    assert citation is not None
    assert attempts >= 2


# ==============================================================================
# 3. NASA NTRS CITATION CLIENT & RATE LIMIT TELEMETRY TESTS
# ==============================================================================

MOCK_NTRS_CITATION = {
    "id": 20150023456,
    "title": "Detailed Results from the Flame Extinguishment Experiment (FLEX)",
    "stiType": "TECHNICAL_PUBLICATION",
    "otherReportNumbers": ["NASA/TP-2015-216046"],
    "authorAffiliations": [
        {"meta": {"author": {"name": "Dietrich, Daniel L."}}},
        {"meta": {"author": {"name": "Ruff, Gary A."}}},
    ],
    "publications": [{"publicationDate": "2015-11-01"}],
    "downloads": [
        {"links": {"pdf": "https://ntrs.nasa.gov/api/citations/20150023456/downloads/FLEX_final.pdf"}}
    ],
}


def test_resolve_ntrs_mocked_and_telemetry(tmp_path):
    """Verifies NTRS resolution, rate limit telemetry tracking, and BibTeX synthesis."""
    resolver = CitationResolver(raw_cache_dir=tmp_path)

    mock_headers = {
        "x-ratelimit-limit": "500",
        "x-ratelimit-remaining": "488",
        "x-ratelimit-reset": "1794513196",
    }

    def mock_get(url, headers=None, **kwargs):
        return httpx.Response(
            200,
            json=MOCK_NTRS_CITATION,
            headers=mock_headers,
            request=httpx.Request("GET", url),
        )

    with patch.object(httpx.Client, "get", side_effect=mock_get):
        citation = resolver.resolve_ntrs("20150023456")

    assert citation is not None
    assert citation.ntrs_id == "20150023456"
    assert citation.title.startswith("Detailed Results from the Flame Extinguishment")
    assert citation.authors == ["Dietrich, Daniel L.", "Ruff, Gary A."]
    assert citation.publication_year == 2015
    assert citation.journal_or_book == "NASA/TP-2015-216046"
    assert citation.nasa_url == "https://ntrs.nasa.gov/citations/20150023456"
    assert citation.download_url == "https://ntrs.nasa.gov/api/citations/20150023456/downloads/FLEX_final.pdf"
    assert citation.verified is True
    assert citation.verification_source == "ntrs"
    assert "@techreport" in citation.bibtex
    assert "NASA/TP-2015-216046" in citation.bibtex

    # Rate limit telemetry checks
    assert resolver.rate_limit_telemetry["remaining"] == 488
    assert resolver.rate_limit_telemetry["limit"] == 500
    assert resolver.rate_limit_telemetry["reset"] == "1794513196"
    assert resolver.rate_limit_telemetry["last_updated"] is not None


def test_ntrs_rate_limit_warning_when_low(tmp_path, caplog):
    """Verifies that rate limit telemetry logs a warning when remaining < 20."""
    resolver = CitationResolver(raw_cache_dir=tmp_path)
    mock_headers = {"x-ratelimit-limit": "500", "x-ratelimit-remaining": "12"}

    def mock_get(url, headers=None, **kwargs):
        return httpx.Response(200, json=MOCK_NTRS_CITATION, headers=mock_headers, request=httpx.Request("GET", url))

    with caplog.at_level(logging.WARNING):
        with patch.object(httpx.Client, "get", side_effect=mock_get):
            resolver.resolve_ntrs("20150023456")

    assert "rate limit threshold alert" in caplog.text


def test_resolve_ntrs_404_zero_fabrication(tmp_path):
    """Zero-Fabrication Validator: 404 from NTRS returns None."""
    resolver = CitationResolver(raw_cache_dir=tmp_path)

    def mock_get(url, headers=None, **kwargs):
        return httpx.Response(404, json={"statusCode": 404, "message": "Not Found"}, request=httpx.Request("GET", url))

    with patch.object(httpx.Client, "get", side_effect=mock_get):
        res = resolver.resolve_ntrs("99999999999")

    assert res is None


def test_synthesize_ntrs_bibtex_conference_paper():
    """Verifies synthesis of @inproceedings for conference papers."""
    resolver = CitationResolver()
    record = {
        "id": "20180001234",
        "title": "Soot Particle Evolution in Microgravity Laminar Flames",
        "stiType": "CONFERENCE_PAPER",
        "authorAffiliations": [{"meta": {"author": {"name": "Urban, David L."}}}],
        "created": "2018-06-15",
        "otherReportNumbers": ["NASA/CP-2018-1234"],
    }
    bibtex = resolver.synthesize_ntrs_bibtex(record)
    assert bibtex.startswith("@inproceedings{")
    assert "Urban_2018" in bibtex
    assert "Soot Particle Evolution" in bibtex
    assert "NASA/CP-2018-1234" in bibtex


# ==============================================================================
# 4. 3-TIER CACHE TESTS (MEMORY -> DISK WITH SHA-256 SIDECAR -> DATABASE)
# ==============================================================================

def test_tier1_in_memory_lru_cache(tmp_path):
    """Verifies Tier 1 in-memory caching and LRU capacity eviction."""
    resolver = CitationResolver(raw_cache_dir=tmp_path, lru_cache_size=2)
    c1 = ResolvedCitation(doi="10.1000/1", title="Paper 1", verified=True)
    c2 = ResolvedCitation(doi="10.1000/2", title="Paper 2", verified=True)
    c3 = ResolvedCitation(doi="10.1000/3", title="Paper 3", verified=True)

    resolver._put_in_memory("doi:10.1000/1", c1)
    resolver._put_in_memory("doi:10.1000/2", c2)
    assert resolver._get_from_memory("doi:10.1000/1") is not None

    # Adding 3rd should evict oldest (which is 10.1000/2 because 10.1000/1 was accessed)
    resolver._put_in_memory("doi:10.1000/3", c3)
    assert resolver._get_from_memory("doi:10.1000/2") is None
    assert resolver._get_from_memory("doi:10.1000/1") is not None
    assert resolver._get_from_memory("doi:10.1000/3") is not None


def test_tier2_raw_disk_cache_with_sha256_sidecar(tmp_path):
    """Verifies Tier 2 raw disk cache creation and SHA-256 sidecar validation."""
    resolver = CitationResolver(raw_cache_dir=tmp_path)

    def mock_get(url, headers=None, **kwargs):
        if "api.crossref.org" in str(url):
            return httpx.Response(200, json=MOCK_CROSSREF_METADATA, request=httpx.Request("GET", url))
        return httpx.Response(200, text=MOCK_DOI_BIBTEX, request=httpx.Request("GET", url))

    # First fetch: writes to disk and sidecar
    with patch.object(httpx.Client, "get", side_effect=mock_get):
        res1 = resolver.resolve_doi("10.1016/j.combustflame.2013.11.014")

    assert res1 is not None

    json_files = list(tmp_path.glob("*.json"))
    sha_files = list(tmp_path.glob("*.sha256"))
    assert len(json_files) == 1
    assert len(sha_files) == 1

    # Verify sidecar contains hash
    sha_content = sha_files[0].read_text(encoding="utf-8").strip()
    assert len(sha_content.split()[0]) == 64

    # Second fetch: clear memory cache to force disk read
    resolver._memory_cache.clear()
    with patch.object(httpx.Client, "get", side_effect=Exception("Should not reach network")):
        res2 = resolver.resolve_doi("10.1016/j.combustflame.2013.11.014")

    assert res2 is not None
    assert res2.doi == res1.doi


def test_tier2_disk_cache_tamper_detection(tmp_path):
    """Verifies that tampering with cached JSON triggers SHA-256 mismatch and invalidation."""
    resolver = CitationResolver(raw_cache_dir=tmp_path)

    def mock_get(url, headers=None, **kwargs):
        if "api.crossref.org" in str(url):
            return httpx.Response(200, json=MOCK_CROSSREF_METADATA, request=httpx.Request("GET", url))
        return httpx.Response(200, text=MOCK_DOI_BIBTEX, request=httpx.Request("GET", url))

    with patch.object(httpx.Client, "get", side_effect=mock_get):
        resolver.resolve_doi("10.1016/j.combustflame.2013.11.014")

    resolver._memory_cache.clear()

    # Tamper with the JSON file
    json_path = list(tmp_path.glob("*.json"))[0]
    raw_data = json.loads(json_path.read_text(encoding="utf-8"))
    raw_data["title"] = "Tampered Malicious Title"
    json_path.write_text(json.dumps(raw_data), encoding="utf-8")

    # Resolver reading from disk should detect mismatch and reject cached data
    tampered_read = resolver._read_from_disk("doi", "10.1016/j.combustflame.2013.11.014")
    assert tampered_read is None


def test_tier3_database_persistence_and_cascade():
    """Verifies Tier 3 database model persistence, retrieval, and CASCADE deletion."""
    from sqlalchemy import event

    engine = create_engine("sqlite:///:memory:")

    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)

    with SessionLocal() as session:
        # Create parent investigation
        inv_id = uuid.uuid4()
        inv = Investigation(
            id=inv_id,
            slug="test-flex-experiment",
            title="Flame Extinguishment Experiment Test",
            short_name="FLEX-Test",
            project_acronym="FLEX",
            facility="CIR",
            combustion_regime="droplet_combustion",
            fuel_type="Heptane",
            gravity_level="Microgravity",
            summary="Test microgravity combustion experiment",
            nasa_source_url="https://ntrs.nasa.gov/citations/20150023456",
        )
        session.add(inv)
        session.commit()

        # Add literature citation
        citation = LiteratureCitation(
            investigation_id=inv_id,
            doi="10.1016/j.combustflame.2013.11.014",
            ntrs_id="20150023456",
            title="Detailed Results from the Flame Extinguishment Experiment",
            authors=["Dietrich, Daniel L.", "Ruff, Gary A."],
            publication_year=2015,
            journal_or_book="Combustion and Flame",
            bibtex="@article{Dietrich_2015, ...}",
            verification_status="VERIFIED_CROSSREF",
            sha256_checksum="a" * 64,
            raw_metadata={"source": "test"},
        )
        session.add(citation)
        session.commit()

        # Query verification
        retrieved = session.execute(
            select(LiteratureCitation).where(LiteratureCitation.doi == "10.1016/j.combustflame.2013.11.014")
        ).scalars().first()
        assert retrieved is not None
        assert retrieved.title == "Detailed Results from the Flame Extinguishment Experiment"
        assert retrieved.authors == ["Dietrich, Daniel L.", "Ruff, Gary A."]
        assert retrieved.investigation_id == inv_id

        # Verify CASCADE delete
        session.delete(inv)
        session.commit()

        remaining_citations = session.execute(
            select(LiteratureCitation).where(LiteratureCitation.investigation_id == inv_id)
        ).scalars().all()
        assert len(remaining_citations) == 0


# ==============================================================================
# 5. ZERO-FABRICATION CANDIDATE VERIFICATION TESTS
# ==============================================================================

def test_verify_citation_rejection_of_fake_identifiers():
    """Zero-Fabrication Rule: Fake/hallucinated citations strictly fail verification."""
    resolver = CitationResolver()

    # Completely fake DOI and NTRS
    res, cit = resolver.verify_citation({"doi": "fake-hallucinated-doi"})
    assert res is False
    assert cit is None

    # Invalid structure
    res, cit = resolver.verify_citation("not-a-dict")  # type: ignore
    assert res is False
    assert cit is None

    # Non-existent DOI (404 from upstream)
    def mock_get(url, **kwargs):
        return httpx.Response(404, request=httpx.Request("GET", url))

    with patch.object(httpx.Client, "get", side_effect=mock_get):
        res, cit = resolver.verify_citation({"doi": "10.99999/hallucinated.doi"})
        assert res is False
        assert cit is None


def test_verify_citation_authentic_doi_and_dual(tmp_path):
    """Verifies authentic single and dual citation verification."""
    resolver = CitationResolver(raw_cache_dir=tmp_path)

    def mock_get(url, headers=None, **kwargs):
        if "api.crossref.org" in str(url):
            return httpx.Response(200, json=MOCK_CROSSREF_METADATA, request=httpx.Request("GET", url))
        elif "doi.org" in str(url):
            return httpx.Response(200, text=MOCK_DOI_BIBTEX, request=httpx.Request("GET", url))
        elif "ntrs.nasa.gov" in str(url):
            return httpx.Response(200, json=MOCK_NTRS_CITATION, request=httpx.Request("GET", url))
        return httpx.Response(404, request=httpx.Request("GET", url))

    with patch.object(httpx.Client, "get", side_effect=mock_get):
        # 1. Single authentic DOI
        ok, cit = resolver.verify_citation({"doi": "10.1016/j.combustflame.2013.11.014"})
        assert ok is True
        assert cit is not None
        assert cit.verified is True

        # 2. Dual resolution
        ok_dual, cit_dual = resolver.verify_citation({
            "doi": "10.1016/j.combustflame.2013.11.014",
            "ntrs_id": "20150023456",
        })
        assert ok_dual is True
        assert cit_dual is not None
        assert cit_dual.verification_source == "both"
        assert cit_dual.ntrs_id == "20150023456"


# ==============================================================================
# 6. FASTAPI ENDPOINT INTEGRATION TESTS
# ==============================================================================

def test_api_resolve_doi_endpoint(client: TestClient):
    """Verifies GET /api/v1/citations/resolve/doi endpoint."""
    def mock_get(url, headers=None, **kwargs):
        if "api.crossref.org" in str(url):
            return httpx.Response(200, json=MOCK_CROSSREF_METADATA, request=httpx.Request("GET", url))
        return httpx.Response(200, text=MOCK_DOI_BIBTEX, request=httpx.Request("GET", url))

    with patch.object(httpx.AsyncClient, "get", side_effect=mock_get):
        res = client.get("/api/v1/citations/resolve/doi?doi=10.1016/j.combustflame.2013.11.014")

    assert res.status_code == 200
    data = res.json()
    assert data["doi"] == "10.1016/j.combustflame.2013.11.014"
    assert data["title"] == "Detailed Droplet Combustion in Microgravity"
    assert data["verified"] is True


def test_api_resolve_doi_invalid_format_422(client: TestClient):
    """Verifies that invalid DOI format returns HTTP 422."""
    res = client.get("/api/v1/citations/resolve/doi?doi=not-a-valid-doi")
    assert res.status_code in (422, 400)


def test_api_resolve_doi_not_found_404(client: TestClient):
    """Verifies that non-existent DOI returns HTTP 404."""
    def mock_get(url, **kwargs):
        return httpx.Response(404, request=httpx.Request("GET", url))

    with patch.object(httpx.AsyncClient, "get", side_effect=mock_get):
        res = client.get("/api/v1/citations/resolve/doi?doi=10.99999/does.not.exist")

    assert res.status_code == 404


def test_api_resolve_ntrs_endpoint(client: TestClient):
    """Verifies GET /api/v1/citations/resolve/ntrs endpoint."""
    mock_headers = {"x-ratelimit-limit": "500", "x-ratelimit-remaining": "495"}

    def mock_get(url, **kwargs):
        return httpx.Response(200, json=MOCK_NTRS_CITATION, headers=mock_headers, request=httpx.Request("GET", url))

    with patch.object(httpx.AsyncClient, "get", side_effect=mock_get):
        res = client.get("/api/v1/citations/resolve/ntrs?ntrs_id=20150023456")

    assert res.status_code == 200
    data = res.json()
    assert data["ntrs_id"] == "20150023456"
    assert "FLEX" in data["title"]
    assert data["verified"] is True


def test_api_verify_citation_endpoint(client: TestClient):
    """Verifies POST /api/v1/citations/verify endpoint."""
    def mock_get(url, **kwargs):
        if "api.crossref.org" in str(url):
            return httpx.Response(200, json=MOCK_CROSSREF_METADATA, request=httpx.Request("GET", url))
        return httpx.Response(200, text=MOCK_DOI_BIBTEX, request=httpx.Request("GET", url))

    with patch.object(httpx.AsyncClient, "get", side_effect=mock_get):
        res = client.post(
            "/api/v1/citations/verify",
            json={"doi": "10.1016/j.combustflame.2013.11.014"},
        )

    assert res.status_code == 200
    data = res.json()
    assert data["verified"] is True
    assert data["citation"]["doi"] == "10.1016/j.combustflame.2013.11.014"


def test_api_verify_citation_endpoint_fake_rejection(client: TestClient):
    """Verifies POST /api/v1/citations/verify strictly rejects hallucinated citations."""
    res = client.post(
        "/api/v1/citations/verify",
        json={"doi": "hallucinated-fake-doi"},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["verified"] is False
    assert data["citation"] is None


def test_api_bibtex_export_text_and_json(client: TestClient):
    """Verifies GET /api/v1/citations/bibtex export formats."""
    def mock_get(url, **kwargs):
        if "api.crossref.org" in str(url):
            return httpx.Response(200, json=MOCK_CROSSREF_METADATA, request=httpx.Request("GET", url))
        return httpx.Response(200, text=MOCK_DOI_BIBTEX, request=httpx.Request("GET", url))

    with patch.object(httpx.AsyncClient, "get", side_effect=mock_get):
        # 1. Plain text format
        res_text = client.get("/api/v1/citations/bibtex?doi=10.1016/j.combustflame.2013.11.014&format=text")
        assert res_text.status_code == 200
        assert "@article" in res_text.text
        assert "application/x-bibtex" in res_text.headers.get("content-type", "")

        # 2. JSON format
        res_json = client.get("/api/v1/citations/bibtex?doi=10.1016/j.combustflame.2013.11.014&format=json")
        assert res_json.status_code == 200
        data = res_json.json()
        assert "@article" in data["bibtex"]


def test_api_rate_limit_telemetry_endpoint(client: TestClient):
    """Verifies GET /api/v1/citations/telemetry endpoint."""
    res = client.get("/api/v1/citations/telemetry")
    assert res.status_code == 200
    data = res.json()
    assert "rate_limit" in data


def test_api_save_and_list_investigation_citations(client: TestClient):
    """Verifies POST /api/v1/citations/save and GET /api/v1/citations/investigation/{id}."""
    # First get an authentic investigation ID
    inv_res = client.get("/api/v1/investigations?limit=1")
    assert inv_res.status_code == 200
    items = inv_res.json()["items"]
    assert len(items) > 0
    slug = items[0]["slug"]

    detail_res = client.get(f"/api/v1/investigations/{slug}")
    assert detail_res.status_code == 200
    inv_id = detail_res.json()["investigation"]["id"]

    citation_payload = {
        "investigation_id": inv_id,
        "citation": {
            "doi": "10.1016/j.combustflame.2013.11.014",
            "ntrs_id": "20150023456",
            "title": "Flame Extinguishment in Microgravity",
            "authors": ["Dietrich, Daniel L.", "Law, Chung K."],
            "publication_year": 2015,
            "journal_or_book": "Combustion and Flame",
            "bibtex": "@article{Dietrich_2015, title={...}}",
            "verification_source": "both",
            "verified": True,
            "sha256_checksum": "f" * 64,
            "raw_metadata": {"verified": True},
        },
    }

    save_res = client.post("/api/v1/citations/save", json=citation_payload)
    assert save_res.status_code == 201
    saved_data = save_res.json()
    assert saved_data["doi"] == "10.1016/j.combustflame.2013.11.014"
    assert saved_data["investigation_id"] == inv_id
    assert saved_data["verification_status"] == "VERIFIED_DUAL"

    # List citations for this investigation
    list_res = client.get(f"/api/v1/citations/investigation/{inv_id}")
    assert list_res.status_code == 200
    list_data = list_res.json()
    assert len(list_data) >= 1
    assert any(c["doi"] == "10.1016/j.combustflame.2013.11.014" for c in list_data)


def test_unicode_authors_synthesis():
    """Verifies proper UTF-8 handling for international author names."""
    resolver = CitationResolver()
    data = {
        "DOI": "10.1000/182",
        "title": ["L'extinction des flammes sphériques"],
        "author": [
            {"family": "Bauerheim", "given": "Michaël"},
            {"family": "García-Ybarra", "given": "Pedro L."},
            {"family": "Vedha-Nayagam", "given": "M."},
        ],
        "container-title": ["Combustion Theory and Modelling"],
        "issued": {"date-parts": [[2016]]},
    }
    bibtex = resolver.synthesize_crossref_bibtex(data)
    assert "Michaël" in bibtex
    assert "García-Ybarra" in bibtex
    assert "Vedha-Nayagam" in bibtex
    assert "Bauerheim_2016" in bibtex


def test_alembic_migration_0003_definition():
    """Verifies that migration 0003_add_literature_citations has valid revision metadata and functions."""
    import importlib.util
    from pathlib import Path

    migration_file = Path("backend/alembic/versions/0003_add_literature_citations.py")
    assert migration_file.is_file()

    spec = importlib.util.spec_from_file_location("migration_0003", migration_file)
    assert spec is not None
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)

    assert mod.revision == "0003"
    assert mod.down_revision == "0002"
    assert callable(mod.upgrade)
    assert callable(mod.downgrade)


def test_api_investigations_citations_by_slug(client: TestClient):
    """Verifies GET /api/v1/citations/investigations/{slug} resolves citations by investigation slug."""
    # Retrieve existing investigation to use its slug
    res = client.get("/api/v1/investigations?limit=1")
    assert res.status_code == 200
    items = res.json().get("items", [])
    if items:
        slug = items[0]["slug"]
        cit_res = client.get(f"/api/v1/citations/investigations/{slug}")
        assert cit_res.status_code == 200
        assert isinstance(cit_res.json(), list)

        # Also verify bibtex export route
        bib_res = client.get(f"/api/v1/citations/investigations/{slug}/bibtex")
        assert bib_res.status_code == 200
        assert "text/plain" in bib_res.headers.get("content-type", "") or "x-bibtex" in bib_res.headers.get("content-type", "")


def test_api_investigations_citations_slug_404_envelope(client: TestClient):
    """Verifies that non-existent slugs return 404 with structured error envelope."""
    res = client.get("/api/v1/citations/investigations/non-existent-flight-experiment-999")
    assert res.status_code == 404
    data = res.json()
    assert "error" in data
    assert data["error"]["code"] == "HTTP_ERROR"
    assert data["error"]["status_code"] == 404
    assert "detail" in data

