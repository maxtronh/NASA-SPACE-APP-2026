"""Unit and API integration tests for NetworkX Knowledge Graph & GraphRAG."""

from __future__ import annotations

import pytest
from starlette.testclient import TestClient

from backend.app.main import app
from backend.app.ml.graph_rag import CombustionKnowledgeGraph


@pytest.fixture
def kg():
    return CombustionKnowledgeGraph.get_instance()


@pytest.fixture
def client():
    return TestClient(app)


def test_knowledge_graph_construction(kg):
    assert kg.graph.number_of_nodes() > 10
    assert kg.graph.number_of_edges() > 10

    # Ensure key phenomena nodes exist
    assert "phenomenon:cool_flames" in kg.graph
    assert "phenomenon:radiative_extinction" in kg.graph
    assert "standard:nasa_std_6001b_test1" in kg.graph

    # Check investigation node
    flex_node = "investigation:flex-2-heptane-droplet"
    assert flex_node in kg.graph
    attrs = kg.graph.nodes[flex_node]
    assert attrs["type"] == "Investigation"
    assert "Droplet" in attrs["name"]


def test_graph_stats_topological_metrics(kg):
    stats = kg.get_stats()
    assert stats["total_nodes"] == kg.graph.number_of_nodes()
    assert stats["total_edges"] == kg.graph.number_of_edges()
    assert stats["graph_density"] >= 0.0
    assert "node_type_counts" in stats
    assert "Investigation" in stats["node_type_counts"]
    assert "Fuel" in stats["node_type_counts"]
    assert len(stats["top_hub_entities"]) > 0


def test_graph_subgraph_extraction(kg):
    sub = kg.get_subgraph("investigation:flex-2-heptane-droplet", radius=1)
    assert sub["center_node"] == "investigation:flex-2-heptane-droplet"
    assert len(sub["nodes"]) > 1
    assert len(sub["edges"]) > 0

    node_ids = [n["id"] for n in sub["nodes"]]
    assert "investigation:flex-2-heptane-droplet" in node_ids


def test_graph_subgraph_not_found(kg):
    with pytest.raises(KeyError):
        kg.get_subgraph("nonexistent_concept_xyz", radius=1)


def test_shortest_path_reasoning(kg):
    path_info = kg.find_shortest_path("fuel:n-heptane", "phenomenon:cool_flames")
    assert path_info["path_found"] is True
    assert path_info["path_length"] >= 1
    assert len(path_info["steps"]) >= 1
    first_step = path_info["steps"][0]
    assert "from_id" in first_step
    assert "to_id" in first_step
    assert "relationship" in first_step


def test_enrich_si_context(kg):
    assertions = kg.enrich_si_context("What are the characteristics of n-heptane combustion?")
    assert len(assertions) > 0
    assert any("heptane" in a.lower() for a in assertions)


def test_api_graph_stats_endpoint(client):
    response = client.get("/api/v1/graph/stats")
    assert response.status_code == 200
    data = response.json()
    assert data["total_nodes"] > 10
    assert "top_hub_entities" in data


def test_api_graph_subgraph_endpoint(client):
    response = client.get("/api/v1/graph/subgraph/investigation:flex-2-heptane-droplet?radius=1")
    assert response.status_code == 200
    data = response.json()
    assert data["center_node"] == "investigation:flex-2-heptane-droplet"
    assert len(data["nodes"]) >= 2


def test_api_graph_subgraph_not_found_returns_404(client):
    response = client.get("/api/v1/graph/subgraph/nonexistent_unknown_node")
    assert response.status_code == 404


def test_api_graph_path_endpoint(client):
    response = client.get("/api/v1/graph/path", params={"source": "n-heptane", "target": "cool_flames"})
    assert response.status_code == 200
    data = response.json()
    assert data["path_found"] is True
    assert len(data["steps"]) >= 1


def test_api_graph_path_invalid_source_returns_404(client):
    response = client.get("/api/v1/graph/path", params={"source": "unknown_fuel_999", "target": "cool_flames"})
    assert response.status_code == 404


def test_api_graph_enrich_endpoint(client):
    response = client.get("/api/v1/graph/enrich", params={"query": "PMMA flame spread in microgravity"})
    assert response.status_code == 200
    data = response.json()
    assert data["query"] == "PMMA flame spread in microgravity"
    assert isinstance(data["assertions"], list)
