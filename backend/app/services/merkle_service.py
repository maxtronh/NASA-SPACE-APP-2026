"""Merkle Tree Provenance Service for NASA Microgravity Combustion Archives."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from backend.app.provenance.merkle import MerkleTree
from backend.app.services.seed_data import AUTHENTIC_NASA_DATA

logger = logging.getLogger(__name__)


class FlightArchiveMerkleRegistry:
    """Registry maintaining cryptographic Merkle tree over all authentic flight investigations."""

    _instance: FlightArchiveMerkleRegistry | None = None

    def __init__(self):
        self.tree: MerkleTree = MerkleTree()
        self.created_at: str = datetime.now(timezone.utc).isoformat()
        self._rebuild_tree()

    @classmethod
    def get_instance(cls) -> FlightArchiveMerkleRegistry:
        if cls._instance is None:
            cls._instance = FlightArchiveMerkleRegistry()
        return cls._instance

    def _rebuild_tree(self) -> None:
        """Constructs Merkle tree over authenticated flight records."""
        leaves = []
        for doc in AUTHENTIC_NASA_DATA:
            leaf_payload = {
                "slug": doc.get("slug"),
                "title": doc.get("title"),
                "project_acronym": doc.get("project_acronym"),
                "gravity_level": doc.get("gravity_level"),
                "combustion_regime": doc.get("combustion_regime"),
                "fuel_type": doc.get("fuel_type"),
                "nasa_source_url": doc.get("nasa_source_url"),
                "measurements": doc.get("measurements", {}),
            }
            leaves.append(leaf_payload)

        self.tree.build_tree(leaves)
        self.created_at = datetime.now(timezone.utc).isoformat()
        logger.info(
            f"Built Merkle tree: root={self.tree.root_hash[:16]}... "
            f"leaves={len(self.tree.leaf_hashes)} levels={len(self.tree.levels)}"
        )

    def get_root_info(self) -> dict[str, Any]:
        """Returns root status metadata."""
        return {
            "merkle_root": self.tree.root_hash,
            "total_leaves": len(self.tree.leaf_hashes),
            "tree_depth": len(self.tree.levels),
            "created_at": self.created_at,
            "algorithm": "RFC-6962 / SHA-256",
            "audit_standard": "NASA Provenance Checksum Protocol v1",
        }

    def get_proof(self, identifier: str) -> dict[str, Any]:
        """Generates audit inclusion proof for a flight record."""
        if identifier not in self.tree.id_to_leaf_index:
            raise KeyError(f"Investigation '{identifier}' not registered in Merkle archive")

        idx = self.tree.id_to_leaf_index[identifier]
        leaf_hash = self.tree.leaf_hashes[idx]
        proof = self.tree.get_proof(identifier)
        raw_doc = self.tree.raw_leaves[idx]

        return {
            "identifier": identifier,
            "leaf_index": idx,
            "leaf_hash": leaf_hash,
            "merkle_root": self.tree.root_hash,
            "proof": proof,
            "record_title": raw_doc.get("title"),
            "verified": MerkleTree.verify_proof(leaf_hash, proof, self.tree.root_hash),
        }

    def verify_proof(
        self,
        leaf_hash: str,
        proof: list[dict[str, str]],
        expected_root: str | None = None,
    ) -> bool:
        """Verifies proof against given or active root."""
        root = expected_root or self.tree.root_hash
        return MerkleTree.verify_proof(leaf_hash, proof, root)
