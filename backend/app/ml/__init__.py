"""Machine Learning and Scientific Intelligence package for NASA Microgravity Combustion Platform."""

from backend.app.ml.abstention import AbstentionEngine, AbstentionEvaluation
from backend.app.ml.citation_engine import CitationEngine
from backend.app.ml.embeddings import (
    DEFAULT_MODEL_NAME,
    VECTOR_DIMENSION,
    EmbeddingPipeline,
)
from backend.app.ml.entity_extractor import ScientificEntityExtractor
from backend.app.ml.pipeline import ScientificIntelligencePipeline
from backend.app.ml.retriever import HybridRetriever

__all__ = [
    "DEFAULT_MODEL_NAME",
    "VECTOR_DIMENSION",
    "AbstentionEngine",
    "AbstentionEvaluation",
    "CitationEngine",
    "EmbeddingPipeline",
    "HybridRetriever",
    "ScientificEntityExtractor",
    "ScientificIntelligencePipeline",
]
