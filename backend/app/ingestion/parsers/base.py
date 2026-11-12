"""
Base Flight Parser Interface for NASA Microgravity Combustion Experiments.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Union
from ..models import IngestionPayload


class BaseFlightParser(ABC):
    """Abstract base parser for processing raw NASA publications and flight data."""

    @abstractmethod
    def parse(
        self,
        raw_text: str,
        citation_metadata: Dict[str, Any],
        source_url: str
    ) -> IngestionPayload:
        """
        Parses raw report text and citation metadata into an IngestionPayload.
        Must normalize values to SI units and strictly preserve missing data as None/NULL.
        """
        pass
