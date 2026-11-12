"""Sentence embedding module for NASA Microgravity Combustion Scientific Intelligence.

Provides FastEmbed ONNX sentence embedding pipeline (BAAI/bge-small-en-v1.5)
with a resilient deterministic vector projection fallback if network download or ONNX
is blocked.
"""

from __future__ import annotations

import hashlib
import logging
from collections.abc import Sequence

import numpy as np

logger = logging.getLogger(__name__)

DEFAULT_MODEL_NAME = "BAAI/bge-small-en-v1.5"
VECTOR_DIMENSION = 384


def _deterministic_projection(text: str, dim: int = VECTOR_DIMENSION) -> list[float]:
    """Generates a reproducible 384-dimensional normalized dense vector via word-hash projection.

    Used as an offline/resilient fallback when ONNX or FastEmbed model files are unavailable.
    """
    clean = text.lower().strip()
    words = [w for w in clean.replace("-", " ").split() if w]
    if not words:
        vec = np.zeros(dim, dtype=np.float32)
        vec[0] = 1.0
        return vec.tolist()

    accum = np.zeros(dim, dtype=np.float32)
    for word in words:
        digest = hashlib.sha256(word.encode("utf-8")).digest()
        seed = int.from_bytes(digest[:4], "big")
        rng = np.random.RandomState(seed)
        w_vec = rng.standard_normal(dim).astype(np.float32)
        accum += w_vec

    norm = float(np.linalg.norm(accum))
    if norm > 1e-9:
        accum /= norm
    else:
        accum[0] = 1.0
    return accum.tolist()


class EmbeddingPipeline:
    """Manages dense vector generation using FastEmbed ONNX with deterministic projection fallback."""

    def __init__(self, model_name: str = DEFAULT_MODEL_NAME, prefer_onnx: bool = True):
        self.model_name = model_name
        self.dim = VECTOR_DIMENSION
        self._embedder = None
        self._using_fallback = False

        if prefer_onnx:
            try:
                from fastembed import TextEmbedding

                logger.info(f"Initializing FastEmbed ONNX model '{model_name}'...")
                self._embedder = TextEmbedding(model_name=model_name)
                # Warm-up run to ensure runtime is healthy
                _ = list(self._embedder.embed(["NASA combustion"]))
                logger.info("FastEmbed ONNX pipeline initialized successfully.")
            except (ImportError, RuntimeError, ValueError, OSError, TypeError) as exc:
                logger.warning(
                    f"FastEmbed ONNX initialization failed ({exc}). "
                    "Falling back to resilient deterministic vector projection."
                )
                self._embedder = None
                self._using_fallback = True
        else:
            self._using_fallback = True

    @property
    def is_fallback(self) -> bool:
        """Returns True if the pipeline is operating in fallback projection mode."""
        return self._using_fallback

    def embed_text(self, text: str) -> list[float]:
        """Generates a 384-dimensional normalized dense vector for a single string."""
        if not text or not text.strip():
            # Return unit zero-vector with leading 1.0 for valid dimensionality
            v = [0.0] * self.dim
            v[0] = 1.0
            return v

        if self._embedder is not None and not self._using_fallback:
            try:
                embeddings = list(self._embedder.embed([text]))
                arr = np.array(embeddings[0], dtype=np.float32)
                norm = float(np.linalg.norm(arr))
                if norm > 1e-9:
                    arr /= norm
                return arr.tolist()
            except (RuntimeError, ValueError, OSError, TypeError) as exc:
                logger.warning(f"FastEmbed runtime failed during embed ({exc}), using projection fallback.")

        return _deterministic_projection(text, dim=self.dim)

    def embed_batch(self, texts: Sequence[str]) -> list[list[float]]:
        """Generates dense vectors for a sequence of texts."""
        if not texts:
            return []

        if self._embedder is not None and not self._using_fallback:
            try:
                embeddings = list(self._embedder.embed(list(texts)))
                result: list[list[float]] = []
                for e in embeddings:
                    arr = np.array(e, dtype=np.float32)
                    norm = float(np.linalg.norm(arr))
                    if norm > 1e-9:
                        arr /= norm
                    result.append(arr.tolist())
                return result
            except (RuntimeError, ValueError, OSError, TypeError) as exc:
                logger.warning(f"FastEmbed batch failed ({exc}), falling back to projection.")

        return [_deterministic_projection(t, dim=self.dim) for t in texts]

    @staticmethod
    def cosine_similarity(
        vec_a: Sequence[float] | np.ndarray,
        vec_b: Sequence[float] | np.ndarray,
    ) -> float:
        """Calculates cosine similarity between two dense vectors."""
        a = np.asarray(vec_a, dtype=np.float32)
        b = np.asarray(vec_b, dtype=np.float32)
        norm_a = float(np.linalg.norm(a))
        norm_b = float(np.linalg.norm(b))
        if norm_a < 1e-9 or norm_b < 1e-9:
            return 0.0
        dot = float(np.dot(a, b))
        similarity = dot / (norm_a * norm_b)
        return float(np.clip(similarity, -1.0, 1.0))
