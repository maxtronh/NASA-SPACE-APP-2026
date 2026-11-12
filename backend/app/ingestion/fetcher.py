"""
Official NASA NTRS & PSI REST API Fetcher with Caching and Rate-Limit Handling.
Retrieves authentic microgravity combustion publications, experimental flight tables,
and raw payloads from https://ntrs.nasa.gov/api/
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import httpx

from .preserver import save_raw_payload

logger = logging.getLogger(__name__)

DEFAULT_NTRS_BASE_URL = "https://ntrs.nasa.gov/api"
DEFAULT_RAW_DIR = Path("data/raw")


class NASADataFetcher:
    """
    Robust HTTP client for retrieving authentic NASA flight investigation data.
    Implements intelligent caching in data/raw/ to ensure test repeatability and
    respect upstream NASA rate limits.
    """

    def __init__(
        self,
        base_url: str = DEFAULT_NTRS_BASE_URL,
        raw_dir: Union[str, Path] = DEFAULT_RAW_DIR,
        timeout: float = 30.0,
        request_timeout: Optional[float] = None,
        max_retries: int = 3
    ):
        self.base_url = base_url.rstrip("/")
        self.raw_dir = Path(raw_dir)
        self.raw_dir.mkdir(parents=True, exist_ok=True)
        self.timeout = request_timeout or timeout
        self.max_retries = max_retries
        self.last_rate_limit: Dict[str, Any] = {}

    def _update_rate_limits(self, headers: httpx.Headers):
        """Monitors and records upstream NTRS rate limit telemetry."""
        limit = headers.get("X-RateLimit-Limit")
        remaining = headers.get("X-RateLimit-Remaining")
        reset = headers.get("X-RateLimit-Reset")
        if remaining is not None:
            rem_int = int(remaining)
            self.last_rate_limit = {
                "limit": limit,
                "remaining": rem_int,
                "reset": reset,
            }
            if rem_int < 20:
                logger.warning(
                    f"NASA NTRS API rate limit threshold warning: {rem_int} requests remaining. "
                    f"Reset epoch: {reset}"
                )

    def fetch_citation(
        self,
        citation_id: str,
        force_refresh: bool = False
    ) -> Dict[str, Any]:
        """
        Retrieves JSON citation metadata for a NASA Technical Report.
        Caches raw JSON response in data/raw/{citation_id}_citation.json.
        """
        cache_filename = f"{citation_id}_citation.json"
        cache_path = self.raw_dir / cache_filename

        if not force_refresh and cache_path.is_file():
            try:
                with open(cache_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except (OSError, json.JSONDecodeError) as e:
                logger.warning(f"Failed to read cache {cache_path}: {e}. Refetching.")

        url = f"{self.base_url}/citations/{citation_id}"
        with httpx.Client(timeout=self.timeout) as client:
            resp = client.get(url, headers={"User-Agent": "NASA-SpaceApps-FlameInFreefall/1.0"})
            self._update_rate_limits(resp.headers)
            resp.raise_for_status()
            data = resp.json()

        save_raw_payload(
            filename_or_url=cache_filename,
            content=json.dumps(data, indent=2),
            metadata={
                "source_url": url,
                "citation_id": citation_id,
                "http_etag": resp.headers.get("ETag"),
            },
            raw_dir=self.raw_dir
        )
        return data

    def get_citation(self, citation_id: str) -> Optional[Dict[str, Any]]:
        """Convenience alias for fetch_citation."""
        try:
            return self.fetch_citation(citation_id)
        except Exception as e:
            logger.error(f"Failed to get citation {citation_id}: {e}")
            return None

    def fetch_download(
        self,
        download_path_or_url: str,
        save_filename: str,
        force_refresh: bool = False
    ) -> bytes:
        """
        Downloads an authentic binary or text payload (e.g. PDF or fulltext TXT).
        Caches file in data/raw/{save_filename}.
        """
        cache_path = self.raw_dir / save_filename

        if not force_refresh and cache_path.is_file():
            with open(cache_path, "rb") as f:
                return f.read()

        if download_path_or_url.startswith(("http://", "https://")):
            url = download_path_or_url
        else:
            url = f"{self.base_url.replace('/api', '')}{download_path_or_url}"
            if not url.startswith("https://"):
                url = f"https://ntrs.nasa.gov{download_path_or_url}"

        with httpx.Client(timeout=self.timeout) as client:
            resp = client.get(url, headers={"User-Agent": "NASA-SpaceApps-FlameInFreefall/1.0"})
            self._update_rate_limits(resp.headers)
            resp.raise_for_status()
            content = resp.content

        save_raw_payload(
            filename_or_url=save_filename,
            content=content,
            metadata={
                "source_url": url,
                "save_filename": save_filename,
                "http_etag": resp.headers.get("ETag"),
            },
            raw_dir=self.raw_dir
        )
        return content

    def fetch_fulltext_by_citation_id(
        self,
        citation_id: str,
        force_refresh: bool = False
    ) -> str:
        """
        Fetches full-text ASCII publication report for a citation if available.
        """
        citation = self.fetch_citation(citation_id, force_refresh=force_refresh)
        downloads = citation.get("downloads", [])

        fulltext_link = None
        for d in downloads:
            links = d.get("links", {})
            if "fulltext" in links:
                fulltext_link = links["fulltext"]
                break
            elif d.get("mimetype") == "text/plain" and "pdf" in links:
                fulltext_link = links["pdf"]

        if not fulltext_link:
            fulltext_link = f"/api/citations/{citation_id}/downloads/{citation_id}.txt"

        filename = f"{citation_id}_fulltext.txt"
        bytes_data = self.fetch_download(fulltext_link, filename, force_refresh=force_refresh)
        return bytes_data.decode("utf-8", errors="replace")

    def search_citations(
        self,
        query: str = "microgravity combustion",
        page_size: int = 25
    ) -> Dict[str, Any]:
        """Queries NTRS search endpoint for microgravity combustion records."""
        url = f"{self.base_url}/citations/search"
        params = {"q": query, "page": {"size": page_size}}
        with httpx.Client(timeout=self.timeout) as client:
            resp = client.get(url, params=params, headers={"User-Agent": "NASA-SpaceApps-FlameInFreefall/1.0"})
            self._update_rate_limits(resp.headers)
            resp.raise_for_status()
            return resp.json()

    def search(
        self,
        query: str = "microgravity combustion",
        limit: int = 25
    ) -> List[Dict[str, Any]]:
        """Searches NTRS and returns list of items."""
        try:
            res = self.search_citations(query=query, page_size=limit)
            return res.get("results", [])
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []
