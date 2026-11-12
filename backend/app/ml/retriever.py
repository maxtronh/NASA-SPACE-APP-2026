"""Hybrid retrieval engine combining BM25 lexical ranking and dense vector similarity.

Implements Reciprocal Rank Fusion (RRF with parameter k=60) across authenticated
NASA microgravity combustion records (corpus_index.json and database models).
"""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import Any

from rank_bm25 import BM25Okapi

from backend.app.ml.embeddings import EmbeddingPipeline
from backend.app.ml.reranker import CrossEncoderReranker

logger = logging.getLogger(__name__)

STOPWORDS = {
    "a", "about", "above", "after", "again", "against", "all", "am", "an", "and",
    "any", "are", "aren't", "as", "at", "be", "because", "been", "before", "being",
    "below", "between", "both", "but", "by", "can't", "cannot", "could", "couldn't",
    "did", "didn't", "do", "does", "doesn't", "doing", "don't", "down", "during",
    "each", "few", "for", "from", "further", "had", "hadn't", "has", "hasn't",
    "have", "haven't", "having", "he", "her", "here", "hers", "herself", "him",
    "himself", "his", "how", "how's", "i", "if", "in", "into", "is", "isn't", "it",
    "its", "itself", "let's", "me", "more", "most", "mustn't", "my", "myself", "no",
    "nor", "not", "of", "off", "on", "once", "only", "or", "other", "ought", "our",
    "ours", "ourselves", "out", "over", "own", "same", "shan't", "she", "should",
    "shouldn't", "so", "some", "such", "than", "that", "the", "their", "theirs",
    "them", "themselves", "then", "there", "these", "they", "this", "those",
    "through", "to", "too", "under", "until", "up", "very", "was", "wasn't", "we",
    "were", "weren't", "what", "when", "where", "which", "while", "who", "whom",
    "why", "with", "won't", "would", "wouldn't", "you", "your", "yours", "yourself",
}


def tokenize_text(text: str) -> list[str]:
    """Tokenizes text into normalized lowercase alphanumeric words filtering stopwords."""
    clean = re.sub(r"[^a-zA-Z0-9]+", " ", text.lower())
    words = [w for w in clean.split() if len(w) > 1 and w not in STOPWORDS]
    return words if words else clean.split()


class HybridRetriever:
    """Hybrid retrieval engine combining BM25 and dense vector similarity using RRF."""

    DEFAULT_RRF_K = 60

    def __init__(
        self,
        embedder: EmbeddingPipeline | None = None,
        reranker: CrossEncoderReranker | None = None,
        rrf_k: int = DEFAULT_RRF_K,
    ):
        self.embedder = embedder or EmbeddingPipeline()
        self.reranker = reranker or CrossEncoderReranker()
        self.rrf_k = rrf_k
        self._documents: list[dict[str, Any]] = []
        self._document_texts: list[str] = []
        self._document_vectors: list[list[float]] = []
        self._bm25: BM25Okapi | None = None
        self._slug_to_index: dict[str, int] = {}

        self._load_corpus()

    def _load_corpus(self) -> None:
        """Loads and indexes authenticated records from seed data and processed data lake."""
        docs_by_slug: dict[str, dict[str, Any]] = {}

        # 1. Load authentic seed data records
        try:
            from backend.app.services.seed_data import AUTHENTIC_NASA_DATA
            for item in AUTHENTIC_NASA_DATA:
                slug = item.get("slug")
                if slug:
                    docs_by_slug[slug] = dict(item)
        except (ImportError, KeyError, TypeError) as exc:
            logger.warning(f"Could not load seed_data records: {exc}")

        # 2. Load processed corpus index if present
        data_dir = Path("data/processed")
        corpus_index_file = data_dir / "corpus_index.json"
        if corpus_index_file.exists():
            try:
                with open(corpus_index_file, encoding="utf-8") as f:
                    data = json.load(f)
                    for item in data.get("investigations", []):
                        slug = item.get("slug")
                        if slug == "flex-droplet-burning":
                            slug = "flex-2-heptane-droplet"
                        if slug and slug not in docs_by_slug:
                            item_copy = dict(item)
                            item_copy["slug"] = slug
                            docs_by_slug[slug] = item_copy
            except (OSError, json.JSONDecodeError) as exc:
                logger.warning(f"Could not read corpus_index.json: {exc}")

        # 3. Load processed individual investigation JSONs
        if data_dir.exists():
            for p in data_dir.glob("*.json"):
                if p.name == "corpus_index.json":
                    continue
                try:
                    with open(p, encoding="utf-8") as f:
                        payload = json.load(f)
                        inv = payload.get("investigation")
                        if inv and isinstance(inv, dict):
                            slug = inv.get("slug")
                            if slug == "flex-droplet-burning":
                                slug = "flex-2-heptane-droplet"
                            if slug and slug not in docs_by_slug:
                                inv_copy = dict(inv)
                                inv_copy["slug"] = slug
                                docs_by_slug[slug] = inv_copy
                except (OSError, json.JSONDecodeError) as exc:
                    logger.debug(f"Skipping unreadable JSON {p}: {exc}")

        self.index_documents(list(docs_by_slug.values()))

    def index_documents(self, docs: list[dict[str, Any]]) -> None:
        """Indexes document list, building BM25 and dense embedding indices."""
        self._documents = []
        self._document_texts = []
        self._slug_to_index = {}

        for doc in docs:
            slug = doc.get("slug")
            if not slug:
                continue
            idx = len(self._documents)
            self._slug_to_index[slug] = idx
            self._documents.append(doc)

            title = doc.get("title", "")
            acronym = doc.get("project_acronym", "")
            regime = doc.get("combustion_regime", "")
            fuel = doc.get("fuel_type", "")
            facility = doc.get("facility", "")
            summary = doc.get("summary", "")
            objectives = doc.get("objectives", "")

            combined_text = f"{title}. {acronym} {regime} {fuel} {facility}. {summary} {objectives}"
            self._document_texts.append(combined_text)

        # Build BM25 index
        tokenized_corpus = [tokenize_text(t) for t in self._document_texts]
        if tokenized_corpus:
            self._bm25 = BM25Okapi(tokenized_corpus)
        else:
            self._bm25 = None

        # Build dense vector representations
        self._document_vectors = self.embedder.embed_batch(self._document_texts)
        logger.info(f"HybridRetriever successfully indexed {len(self._documents)} NASA records.")

    def retrieve(
        self,
        query: str,
        top_k: int = 5,
        filters: dict[str, Any] | None = None,
        rerank: bool = True,
    ) -> list[dict[str, Any]]:
        """Executes hybrid retrieval using BM25, dense vector similarity, and two-stage cross-encoder re-ranking."""
        if not self._documents or not query.strip():
            return []

        clean_query = query.strip()
        q_tokens = tokenize_text(clean_query)
        num_docs = len(self._documents)

        # 1. BM25 Lexical Ranking
        if self._bm25 is not None and q_tokens:
            bm25_raw_scores = self._bm25.get_scores(q_tokens)
        else:
            bm25_raw_scores = [0.0] * num_docs

        bm25_sorted_indices = sorted(
            range(num_docs), key=lambda i: bm25_raw_scores[i], reverse=True
        )
        bm25_ranks: dict[int, int] = {}
        for rank, doc_idx in enumerate(bm25_sorted_indices):
            # If doc has 0.0 BM25 score, penalize rank
            if bm25_raw_scores[doc_idx] > 0:
                bm25_ranks[doc_idx] = rank + 1
            else:
                bm25_ranks[doc_idx] = num_docs + 10

        # 2. Dense Vector Similarity Ranking
        query_vector = self.embedder.embed_text(clean_query)
        vector_sims = [
            EmbeddingPipeline.cosine_similarity(query_vector, doc_vec)
            for doc_vec in self._document_vectors
        ]
        vector_sorted_indices = sorted(
            range(num_docs), key=lambda i: vector_sims[i], reverse=True
        )
        vector_ranks: dict[int, int] = {
            doc_idx: rank + 1 for rank, doc_idx in enumerate(vector_sorted_indices)
        }

        # 3. Reciprocal Rank Fusion (RRF with parameter k=60)
        rrf_scores: list[float] = []
        k = self.rrf_k
        for i in range(num_docs):
            r_bm = bm25_ranks.get(i, num_docs + 10)
            r_vec = vector_ranks.get(i, num_docs + 10)
            score = (1.0 / (k + r_bm)) + (1.0 / (k + r_vec))
            rrf_scores.append(score)

        # Max theoretical RRF score with 2 rankers at rank 1 is 2 / (k + 1)
        max_rrf = 2.0 / (k + 1)

        # 4. Filter and Rank Results
        candidate_pool_limit = max(top_k * 3, 10) if rerank else top_k
        ranked_indices = sorted(range(num_docs), key=lambda i: rrf_scores[i], reverse=True)
        results: list[dict[str, Any]] = []

        for idx in ranked_indices:
            doc = self._documents[idx]

            # Apply metadata filters if provided
            if filters:
                if filters.get("regime") and doc.get("combustion_regime") != filters["regime"]:
                    continue
                if filters.get("fuel") and filters["fuel"].lower() not in doc.get("fuel_type", "").lower():
                    continue
                if filters.get("facility") and filters["facility"].lower() not in doc.get("facility", "").lower():
                    continue
                if filters.get("gravity") and filters["gravity"].lower() not in doc.get("gravity_level", "").lower():
                    continue

            norm_rrf = rrf_scores[idx] / max_rrf
            vec_sim = vector_sims[idx]
            bm_val = bm25_raw_scores[idx]

            # Relevance score combining normalized RRF and vector similarity
            relevance = round(float(min(0.96, max(0.05, 0.60 * norm_rrf + 0.40 * vec_sim))), 4)

            entry = dict(doc)
            entry["relevance_score"] = relevance
            entry["rrf_score"] = round(float(rrf_scores[idx]), 6)
            entry["bm25_score"] = round(float(bm_val), 4)
            entry["vector_similarity"] = round(float(vec_sim), 4)
            results.append(entry)

            if len(results) >= candidate_pool_limit:
                break

        # Stage 2: Cross-Encoder Reranking
        if rerank and results:
            return self.reranker.rerank(clean_query, candidates=results, top_k=top_k)

        return results[:top_k]
