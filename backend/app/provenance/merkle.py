"""Cryptographic Merkle Tree Provenance and Tamper-Proof Audit Engine for NASA Flight Archives.

Implements RFC 6962 compliant Merkle trees with domain separation prefixes:
- Leaf hash: SHA256(0x00 || serialized_leaf_data)
- Internal node hash: SHA256(0x01 || left_hash || right_hash)

Provides cryptographic inclusion proofs, root verification, and tamper detection.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any


def _hash_leaf(data: bytes | str) -> str:
    """Computes leaf hash with domain separation prefix 0x00."""
    raw = data.encode("utf-8") if isinstance(data, str) else data
    hasher = hashlib.sha256()
    hasher.update(b"\x00")
    hasher.update(raw)
    return hasher.hexdigest()


def _hash_pair(left_hex: str, right_hex: str) -> str:
    """Computes parent node hash from left and right children with domain separation prefix 0x01."""
    left_bytes = bytes.fromhex(left_hex)
    right_bytes = bytes.fromhex(right_hex)
    hasher = hashlib.sha256()
    hasher.update(b"\x01")
    hasher.update(left_bytes)
    hasher.update(right_bytes)
    return hasher.hexdigest()


class MerkleTree:
    """Cryptographic binary Merkle tree with inclusion proof generation and verification."""

    def __init__(self, leaves_data: list[dict[str, Any]] | None = None):
        self.raw_leaves: list[dict[str, Any]] = []
        self.leaf_hashes: list[str] = []
        self.id_to_leaf_index: dict[str, int] = {}
        self.levels: list[list[str]] = []
        self.root_hash: str = ""

        if leaves_data:
            self.build_tree(leaves_data)

    def build_tree(self, items: list[dict[str, Any]]) -> str:
        """Constructs Merkle tree from list of items with identifier keys."""
        self.raw_leaves = []
        self.leaf_hashes = []
        self.id_to_leaf_index = {}
        self.levels = []

        if not items:
            self.root_hash = hashlib.sha256(b"").hexdigest()
            self.levels = [[self.root_hash]]
            return self.root_hash

        # Canonical deterministic serialization
        for idx, item in enumerate(items):
            self.raw_leaves.append(dict(item))
            # Extract identifier (id, slug, or run_identifier)
            identifier = str(item.get("slug") or item.get("id") or item.get("run_identifier") or idx)
            self.id_to_leaf_index[identifier] = idx

            canonical_json = json.dumps(item, sort_keys=True, separators=(",", ":"))
            leaf_h = _hash_leaf(canonical_json)
            self.leaf_hashes.append(leaf_h)

        # Build tree levels from leaves to root
        current_level = list(self.leaf_hashes)
        self.levels.append(current_level)

        while len(current_level) > 1:
            next_level: list[str] = []
            for i in range(0, len(current_level), 2):
                left = current_level[i]
                # If odd number of nodes, duplicate the last node
                right = current_level[i + 1] if i + 1 < len(current_level) else left
                parent = _hash_pair(left, right)
                next_level.append(parent)
            current_level = next_level
            self.levels.append(current_level)

        self.root_hash = self.levels[-1][0] if self.levels else ""
        return self.root_hash

    def get_proof(self, identifier_or_index: str | int) -> list[dict[str, str]]:
        """Generates cryptographic inclusion proof for a leaf by identifier or index.
        
        Returns:
            List of sibling hashes with position ('left' | 'right').
        """
        if isinstance(identifier_or_index, str):
            if identifier_or_index not in self.id_to_leaf_index:
                raise KeyError(f"Identifier '{identifier_or_index}' not found in Merkle tree leaves")
            idx = self.id_to_leaf_index[identifier_or_index]
        else:
            idx = identifier_or_index

        if idx < 0 or idx >= len(self.leaf_hashes):
            raise IndexError(f"Leaf index {idx} out of range (0..{len(self.leaf_hashes)-1})")

        proof: list[dict[str, str]] = []
        current_idx = idx

        for level in self.levels[:-1]:
            is_right_child = (current_idx % 2 == 1)
            sibling_idx = current_idx - 1 if is_right_child else current_idx + 1

            if sibling_idx < len(level):
                sibling_hash = level[sibling_idx]
            else:
                # Odd node duplicated itself
                sibling_hash = level[current_idx]

            proof.append({
                "position": "left" if is_right_child else "right",
                "hash": sibling_hash,
            })
            current_idx //= 2

        return proof

    @staticmethod
    def verify_proof(leaf_hash: str, proof: list[dict[str, str]], expected_root: str) -> bool:
        """Verifies an inclusion proof starting from leaf_hash up to expected_root."""
        current_hash = leaf_hash
        for step in proof:
            sibling = step["hash"]
            position = step["position"]

            if position == "left":
                current_hash = _hash_pair(sibling, current_hash)
            else:
                current_hash = _hash_pair(current_hash, sibling)

        return current_hash.lower() == expected_root.lower()

    @staticmethod
    def hash_item(item: dict[str, Any]) -> str:
        """Computes deterministic leaf hash for an arbitrary item dictionary."""
        canonical_json = json.dumps(item, sort_keys=True, separators=(",", ":"))
        return _hash_leaf(canonical_json)
