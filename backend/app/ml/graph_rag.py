"""NetworkX Scientific Knowledge Graph & GraphRAG Context Engine for NASA Combustion Research."""

from __future__ import annotations

import logging
from typing import Any

import networkx as nx

from backend.app.services.seed_data import AUTHENTIC_NASA_DATA

logger = logging.getLogger(__name__)


class CombustionKnowledgeGraph:
    """Multidimensional scientific knowledge graph connecting NASA combustion entities."""

    _instance: CombustionKnowledgeGraph | None = None

    def __init__(self):
        self.graph = nx.DiGraph()
        self._build_knowledge_graph()

    @classmethod
    def get_instance(cls) -> CombustionKnowledgeGraph:
        if cls._instance is None:
            cls._instance = CombustionKnowledgeGraph()
        return cls._instance

    def _build_knowledge_graph(self) -> None:
        """Constructs knowledge graph from authentic flight investigations and domain relationships."""
        self.graph.clear()

        # 1. Domain Phenomenon Nodes
        phenomena = [
            ("phenomenon:cool_flames", {"name": "Cool Flames", "type": "Phenomenon", "description": "Low-temperature (600-900 K) quasi-steady combustion supported by peroxy radical branching."}),
            ("phenomenon:radiative_extinction", {"name": "Radiative Extinction", "type": "Phenomenon", "description": "Hot flame quenching driven by high radiative emission from thick spherical soot shells."}),
            ("phenomenon:soot_inception", {"name": "Soot Inception", "type": "Phenomenon", "description": "Polycyclic aromatic hydrocarbon (PAH) condensation into primary soot particles."}),
            ("phenomenon:buoyant_acceleration", {"name": "Buoyant Convection", "type": "Phenomenon", "description": "Density-gradient-induced fluid acceleration absent in microgravity freefall."}),
            ("phenomenon:blowoff_extinction", {"name": "Blowoff Extinction", "type": "Phenomenon", "description": "High-speed convective flow exceeding chemical reaction Damköhler timescale."}),
        ]
        for node_id, attrs in phenomena:
            self.graph.add_node(node_id, **attrs)

        # 2. Standards Nodes
        standards = [
            ("standard:nasa_std_6001b_test1", {"name": "NASA-STD-6001B Test 1", "type": "Standard", "description": "Upward flame propagation test for spacecraft materials."}),
            ("standard:nasa_std_6001b_test7", {"name": "NASA-STD-6001B Test 7", "type": "Standard", "description": "Heat and visible smoke release rate standard."}),
        ]
        for node_id, attrs in standards:
            self.graph.add_node(node_id, **attrs)

        # 3. Flight Investigations and Related Entities from Seed Data
        for inv in AUTHENTIC_NASA_DATA:
            slug = inv["slug"]
            inv_node = f"investigation:{slug}"
            self.graph.add_node(
                inv_node,
                name=inv["title"],
                type="Investigation",
                acronym=inv.get("project_acronym"),
                gravity=inv.get("gravity_level"),
                regime=inv.get("combustion_regime"),
                nasa_url=inv.get("nasa_source_url"),
            )

            # Facility
            facility_name = inv.get("facility")
            if facility_name:
                fac_node = f"facility:{facility_name.lower().replace(' ', '_')}"
                if fac_node not in self.graph:
                    self.graph.add_node(fac_node, name=facility_name, type="Facility")
                self.graph.add_edge(inv_node, fac_node, relationship="CONDUCTED_AT")

            # Fuel
            fuel_name = inv.get("fuel_type")
            if fuel_name:
                fuel_node = f"fuel:{fuel_name.lower().replace(' ', '_').replace('(', '').replace(')', '')}"
                if fuel_node not in self.graph:
                    self.graph.add_node(fuel_node, name=fuel_name, type="Fuel")
                self.graph.add_edge(inv_node, fuel_node, relationship="UTILIZES_FUEL")

                # Connect fuel to phenomena
                if "heptane" in fuel_name.lower() or "decane" in fuel_name.lower():
                    self.graph.add_edge(fuel_node, "phenomenon:cool_flames", relationship="EXHIBITS_CHEMISTRY")
                    self.graph.add_edge(fuel_node, "phenomenon:radiative_extinction", relationship="UNDERGOES")
                if "methane" in fuel_name.lower():
                    self.graph.add_edge(fuel_node, "phenomenon:soot_inception", relationship="PRODUCES_SOOT")
                if "pmma" in fuel_name.lower():
                    self.graph.add_edge(fuel_node, "standard:nasa_std_6001b_test1", relationship="EVALUATED_AGAINST")
                    self.graph.add_edge(fuel_node, "phenomenon:blowoff_extinction", relationship="SUSCEPTIBLE_TO")

            # Combustion Regime
            regime_name = inv.get("combustion_regime")
            if regime_name:
                reg_node = f"regime:{regime_name.lower()}"
                if reg_node not in self.graph:
                    self.graph.add_node(reg_node, name=regime_name.replace('_', ' ').title(), type="CombustionRegime")
                self.graph.add_edge(inv_node, reg_node, relationship="OPERATES_IN_REGIME")

            # Principal Investigators
            for pi in inv.get("principal_investigators", []):
                pi_name = pi.get("name")
                if pi_name:
                    pi_node = f"pi:{pi_name.lower().replace(' ', '_').replace('.', '')}"
                    if pi_node not in self.graph:
                        self.graph.add_node(pi_node, name=pi_name, type="Investigator", affiliation=pi.get("affiliation"))
                    self.graph.add_edge(inv_node, pi_node, relationship="LED_BY")
                    self.graph.add_edge(pi_node, inv_node, relationship="INVESTIGATED")

        logger.info(
            f"Built CombustionKnowledgeGraph: {self.graph.number_of_nodes()} nodes, "
            f"{self.graph.number_of_edges()} edges."
        )

    def get_stats(self) -> dict[str, Any]:
        """Returns topological network statistics and hub entities."""
        n_nodes = self.graph.number_of_nodes()
        n_edges = self.graph.number_of_edges()

        # Degree centrality
        deg_cent = nx.degree_centrality(self.graph)
        top_hubs = sorted(deg_cent.items(), key=lambda x: x[1], reverse=True)[:6]

        hub_details = [
            {
                "id": node_id,
                "name": self.graph.nodes[node_id].get("name", node_id),
                "type": self.graph.nodes[node_id].get("type", "Unknown"),
                "degree_centrality": round(score, 4),
            }
            for node_id, score in top_hubs
        ]

        # Breakdown by node type
        type_counts: dict[str, int] = {}
        for _, attrs in self.graph.nodes(data=True):
            t = attrs.get("type", "Other")
            type_counts[t] = type_counts.get(t, 0) + 1

        return {
            "total_nodes": n_nodes,
            "total_edges": n_edges,
            "graph_density": round(nx.density(self.graph), 4),
            "is_weakly_connected": nx.is_weakly_connected(self.graph),
            "node_type_counts": type_counts,
            "top_hub_entities": hub_details,
        }

    def get_subgraph(self, target_id: str, radius: int = 1) -> dict[str, Any]:
        """Extracts ego-network subgraph around target entity formatted for D3/force-graph."""
        # Find exact or fuzzy matching node ID
        matched_node = None
        target_lower = target_id.strip().lower()

        if target_id in self.graph:
            matched_node = target_id
        else:
            for n, attrs in self.graph.nodes(data=True):
                if target_lower in n.lower() or target_lower in attrs.get("name", "").lower():
                    matched_node = n
                    break

        if not matched_node:
            raise KeyError(f"Entity '{target_id}' not found in scientific knowledge graph.")

        sub_nodes = {matched_node}
        # Expand neighbors up to radius
        current_layer = {matched_node}
        for _ in range(radius):
            next_layer = set()
            for n in current_layer:
                next_layer.update(self.graph.predecessors(n))
                next_layer.update(self.graph.successors(n))
            sub_nodes.update(next_layer)
            current_layer = next_layer

        subgraph = self.graph.subgraph(sub_nodes)

        nodes = []
        for n, attrs in subgraph.nodes(data=True):
            nodes.append({
                "id": n,
                "name": attrs.get("name", n),
                "type": attrs.get("type", "Entity"),
                **{k: v for k, v in attrs.items() if k not in ("name", "type")},
            })

        edges = []
        for u, v, attrs in subgraph.edges(data=True):
            edges.append({
                "source": u,
                "target": v,
                "relationship": attrs.get("relationship", "CONNECTED_TO"),
            })

        return {
            "center_node": matched_node,
            "radius": radius,
            "nodes": nodes,
            "edges": edges,
        }

    def find_shortest_path(self, source_id: str, target_id: str) -> dict[str, Any]:
        """Finds shortest explanatory path between two combustion concepts in the undirected view."""
        # Resolve nodes
        src = self._resolve_node(source_id)
        dst = self._resolve_node(target_id)

        if not src:
            raise KeyError(f"Source entity '{source_id}' not found.")
        if not dst:
            raise KeyError(f"Target entity '{target_id}' not found.")

        undirected = self.graph.to_undirected(as_view=True)
        try:
            path = nx.shortest_path(undirected, source=src, target=dst)
        except nx.NetworkXNoPath:
            return {
                "source": src,
                "target": dst,
                "path_found": False,
                "path_nodes": [],
                "explanation": f"No relational path found between {src} and {dst}.",
            }

        steps = []
        for i in range(len(path) - 1):
            u, v = path[i], path[i + 1]
            # Check edge attributes in either direction
            rel = (
                self.graph.get_edge_data(u, v, {}).get("relationship")
                or self.graph.get_edge_data(v, u, {}).get("relationship")
                or "RELATED_TO"
            )
            u_name = self.graph.nodes[u].get("name", u)
            v_name = self.graph.nodes[v].get("name", v)
            steps.append({
                "from_id": u,
                "from_name": u_name,
                "to_id": v,
                "to_name": v_name,
                "relationship": rel,
            })

        return {
            "source": src,
            "target": dst,
            "path_found": True,
            "path_length": len(path) - 1,
            "path_nodes": [self.graph.nodes[n].get("name", n) for n in path],
            "steps": steps,
        }

    def _resolve_node(self, query: str) -> str | None:
        q = query.strip().lower()
        if q in self.graph:
            return q
        for n, attrs in self.graph.nodes(data=True):
            if q == n.lower() or q in n.lower() or q in attrs.get("name", "").lower():
                return n
        return None

    def enrich_si_context(self, query: str, top_k: int = 3) -> list[str]:
        """Extracts GraphRAG context assertions from connected subgraphs for a query."""
        assertions = []
        q_lower = query.lower()

        for n, attrs in self.graph.nodes(data=True):
            name = attrs.get("name", "").lower()
            if name and name in q_lower:
                # Get outgoing relationships
                for succ in self.graph.successors(n):
                    rel = self.graph[n][succ].get("relationship", "connected to")
                    succ_name = self.graph.nodes[succ].get("name", succ)
                    assertions.append(f"{attrs.get('name')} {rel.lower().replace('_', ' ')} {succ_name}.")

                if len(assertions) >= top_k:
                    break

        return assertions[:top_k]
