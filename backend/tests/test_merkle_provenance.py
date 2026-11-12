"""Tests for Merkle Tree Cryptographic Provenance and Audit Verification Engine."""

import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.provenance.merkle import MerkleTree, _hash_leaf, _hash_pair
from backend.app.services.merkle_service import FlightArchiveMerkleRegistry


@pytest.fixture
def client():
    return TestClient(app)


def test_merkle_leaf_and_pair_domain_separation():
    h_leaf = _hash_leaf("test_data")
    h_pair = _hash_pair(h_leaf, h_leaf)
    assert len(h_leaf) == 64
    assert len(h_pair) == 64
    assert h_leaf != h_pair


def test_merkle_tree_construction_and_root():
    items = [
        {"slug": "rec-1", "value": 10},
        {"slug": "rec-2", "value": 20},
        {"slug": "rec-3", "value": 30},
    ]
    tree = MerkleTree(items)
    root = tree.root_hash
    assert len(root) == 64
    assert len(tree.levels) == 3  # 3 leaves -> 2 nodes -> 1 root


def test_merkle_tree_inclusion_proof_and_verification():
    items = [
        {"slug": "alpha", "val": 1},
        {"slug": "beta", "val": 2},
        {"slug": "gamma", "val": 3},
        {"slug": "delta", "val": 4},
    ]
    tree = MerkleTree(items)
    root = tree.root_hash

    for item in items:
        slug = item["slug"]
        idx = tree.id_to_leaf_index[slug]
        leaf_hash = tree.leaf_hashes[idx]
        proof = tree.get_proof(slug)

        assert len(proof) == 2  # depth for 4 leaves is log2(4) = 2
        assert MerkleTree.verify_proof(leaf_hash, proof, root) is True


def test_merkle_tree_tamper_detection():
    items = [
        {"slug": "flex", "burn_rate": 0.74},
        {"slug": "bass", "spread_rate": 0.85},
    ]
    tree = MerkleTree(items)
    root = tree.root_hash

    proof = tree.get_proof("flex")
    valid_leaf = tree.leaf_hashes[tree.id_to_leaf_index["flex"]]
    assert MerkleTree.verify_proof(valid_leaf, proof, root) is True

    # Tampered leaf: someone forged burn_rate to 0.99
    tampered_item = {"slug": "flex", "burn_rate": 0.99}
    tampered_leaf = MerkleTree.hash_item(tampered_item)

    assert tampered_leaf != valid_leaf
    # Tampered proof verification must fail
    assert MerkleTree.verify_proof(tampered_leaf, proof, root) is False


def test_api_merkle_root_endpoint(client: TestClient):
    res = client.get("/api/v1/provenance/merkle-root")
    assert res.status_code == 200
    data = res.json()
    assert "merkle_root" in data
    assert len(data["merkle_root"]) == 64
    assert data["total_leaves"] >= 5
    assert data["algorithm"] == "RFC-6962 / SHA-256"


def test_api_inclusion_proof_and_verification_endpoints(client: TestClient):
    # 1. Fetch proof for authentic FLEX record
    proof_res = client.get("/api/v1/provenance/proof/flex-2-heptane-droplet")
    assert proof_res.status_code == 200
    proof_data = proof_res.json()

    assert proof_data["identifier"] == "flex-2-heptane-droplet"
    assert "leaf_hash" in proof_data
    assert "merkle_root" in proof_data
    assert "proof" in proof_data
    assert proof_data["verified"] is True

    # 2. Verify proof via POST endpoint
    verify_payload = {
        "leaf_hash": proof_data["leaf_hash"],
        "proof": proof_data["proof"],
        "expected_root": proof_data["merkle_root"],
    }
    verify_res = client.post("/api/v1/provenance/verify-proof", json=verify_payload)
    assert verify_res.status_code == 200
    verify_data = verify_res.json()
    assert verify_data["valid"] is True
    assert "successfully verified" in verify_data["detail"]

    # 3. Forged root verification should fail
    forged_payload = {
        "leaf_hash": proof_data["leaf_hash"],
        "proof": proof_data["proof"],
        "expected_root": "0" * 64,
    }
    forged_res = client.post("/api/v1/provenance/verify-proof", json=forged_payload)
    assert forged_res.status_code == 200
    assert forged_res.json()["valid"] is False


def test_api_proof_404_for_nonexistent_record(client: TestClient):
    res = client.get("/api/v1/provenance/proof/nonexistent-slug-xyz")
    assert res.status_code == 404
