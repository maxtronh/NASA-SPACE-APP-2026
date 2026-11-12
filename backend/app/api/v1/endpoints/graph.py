"""API endpoints for NetworkX Scientific Knowledge Graph & GraphRAG."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Query, status

from backend.app.ml.graph_rag import CombustionKnowledgeGraph

router = APIRouter(prefix="/graph", tags=["graph"])


@router.get("/stats")
async def get_graph_stats() -> dict[str, Any]:
    """Returns topological statistics, connectivity, and hub entities of the scientific knowledge graph."""
    kg = CombustionKnowledgeGraph.get_instance()
    return kg.get_stats()


@router.get("/subgraph/{entity_id}")
async def get_subgraph(
    entity_id: str,
    radius: int = Query(default=1, ge=1, le=3, description="Neighbor hop radius for subgraph extraction"),
) -> dict[str, Any]:
    """Extracts an ego-network subgraph centered around the specified entity for D3/force-graph visualization."""
    kg = CombustionKnowledgeGraph.get_instance()
    try:
        return kg.get_subgraph(target_id=entity_id, radius=radius)
    except KeyError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )


@router.get("/path")
async def find_shortest_path(
    source: str = Query(..., min_length=1, description="Source entity ID or name (e.g. 'n-heptane' or 'fuel:n-heptane')"),
    target: str = Query(..., min_length=1, description="Target entity ID or name (e.g. 'cool_flames' or 'phenomenon:cool_flames')"),
) -> dict[str, Any]:
    """Finds the shortest explanatory semantic path between two combustion concepts in the knowledge graph."""
    kg = CombustionKnowledgeGraph.get_instance()
    try:
        return kg.find_shortest_path(source_id=source, target_id=target)
    except KeyError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )


@router.get("/enrich")
async def enrich_context(
    query: str = Query(..., min_length=1, description="Scientific natural language query to enrich with GraphRAG assertions"),
    top_k: int = Query(default=3, ge=1, le=10, description="Maximum number of context assertions"),
) -> dict[str, Any]:
    """Enriches a natural language scientific query with relational assertions from the knowledge graph."""
    kg = CombustionKnowledgeGraph.get_instance()
    assertions = kg.enrich_si_context(query=query, top_k=top_k)
    return {
        "query": query,
        "assertions": assertions,
        "count": len(assertions),
    }
