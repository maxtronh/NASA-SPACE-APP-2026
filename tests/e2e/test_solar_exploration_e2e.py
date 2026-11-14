"""
Solar System Exploration & 25-Faces E2E Test Suite — Milestone M9
Comprehensive end-to-end verification covering:
1. FastAPI exploration REST endpoints (/api/v1/exploration/...)
2. Standalone HTML5 simulation app structure, DOM badges, zero CDN dependencies
3. Keplerian ephemeris math & translunar injection physics
4. Qwen AI copilot inference and fallback engine
"""

import os
import re
from html.parser import HTMLParser
import pytest
from fastapi.testclient import TestClient

from backend.app.main import app

WORKSPACE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
STANDALONE_DIR = os.path.join(WORKSPACE_DIR, "nasa exploration")


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


class SimpleDomParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.elements_by_id = {}
        self.buttons = []
        self.scripts = []
        self.links = []
        self.canvases = []

    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)
        elem_id = attrs_dict.get("id")
        if elem_id:
            self.elements_by_id[elem_id] = {"tag": tag, "attrs": attrs_dict}

        if tag == "button":
            self.buttons.append(attrs_dict)
        elif tag == "script":
            self.scripts.append(attrs_dict)
        elif tag == "link":
            self.links.append(attrs_dict)
        elif tag == "canvas":
            self.canvases.append(attrs_dict)


class TestExplorationApiEndpoints:
    def test_get_25_faces_matrix(self, client):
        """Verify GET /api/v1/exploration/faces-25 returns all 25 scientific faces."""
        response = client.get("/api/v1/exploration/faces-25")
        assert response.status_code == 200
        data = response.json()
        assert data["total_faces"] == 25
        assert len(data["faces"]) == 25

        # Check required schema fields
        for face in data["faces"]:
            assert "id" in face and 1 <= face["id"] <= 25
            assert "face_id" in face
            assert "tier" in face and 1 <= face["tier"] <= 5
            assert "tier_name" in face
            assert "name" in face and len(face["name"]) > 0
            assert "formulation" in face and len(face["formulation"]) > 0
            assert "key_constant" in face and len(face["key_constant"]) > 0
            assert "flight_application" in face and len(face["flight_application"]) > 0
            assert "telemetry_channel" in face
            assert face.get("unmeasured_null") is None

    def test_get_single_face_detail(self, client):
        """Verify GET /api/v1/exploration/faces-25/{face_id} for Face 16 (Qwen LoRA)."""
        response = client.get("/api/v1/exploration/faces-25/16")
        assert response.status_code == 200
        face = response.json()
        assert face["id"] == 16
        assert face["face_id"] == "Face 16"
        assert "Qwen" in face["name"]
        assert face["tier"] == 4
        assert face["tier_name"] == "Qwen AI Intelligence"

    def test_get_face_404_not_found(self, client):
        """Verify 404 on out-of-range face ID."""
        response = client.get("/api/v1/exploration/faces-25/99")
        assert response.status_code == 404

    def test_get_planetary_ephemeris(self, client):
        """Verify GET /api/v1/exploration/planets calculates valid Keplerian state vectors."""
        response = client.get("/api/v1/exploration/planets?epoch_seconds=0")
        assert response.status_code == 200
        data = response.json()
        assert data["total_bodies"] >= 9
        assert len(data["planets"]) >= 9

        names = [p["name"] for p in data["planets"]]
        for req_body in ["Mercury", "Venus", "Earth", "Mars", "Jupiter", "Saturn", "Uranus", "Neptune", "Pluto"]:
            assert req_body in names

        # Verify Earth's coordinates at epoch 0
        earth = next(p for p in data["planets"] if p["name"] == "Earth")
        assert 0.98 <= earth["position"]["distance_sun_au"] <= 1.02
        assert 28.0 <= earth["position"]["speed_km_s"] <= 31.0
        assert 0.99 <= earth["kepler_law_ratio"] <= 1.01

    def test_calculate_trajectory_earth_to_mars(self, client):
        """Verify POST /api/v1/exploration/trajectory/calculate for Earth -> Mars."""
        payload = {"origin_body": "Earth", "target_body": "Mars"}
        response = client.post("/api/v1/exploration/trajectory/calculate", json=payload)
        assert response.status_code == 200
        res = response.json()
        assert res["transfer_type"] == "heliocentric_interplanetary"
        assert 5.4 <= res["delta_v_total_km_s"] <= 5.8
        assert 240 <= res["transit_duration_days"] <= 280
        assert "Mars" in res["scientific_summary"]

    def test_calculate_trajectory_earth_to_moon_tli(self, client):
        """Verify POST /api/v1/exploration/trajectory/calculate for Earth -> Moon (translunar injection)."""
        payload = {"origin_body": "Earth", "target_body": "Moon"}
        response = client.post("/api/v1/exploration/trajectory/calculate", json=payload)
        assert response.status_code == 200
        res = response.json()
        assert res["transfer_type"] == "geocentric_translunar"
        assert 3.10 <= res["delta_v_departure_km_s"] <= 3.25
        assert 3.80 <= res["delta_v_total_km_s"] <= 4.20
        assert 2.8 <= res["transit_duration_days"] <= 3.8
        assert "Translunar" in res["scientific_summary"] or "TLI" in res["scientific_summary"]

    def test_copilot_chat_endpoint(self, client):
        """Verify POST /api/v1/exploration/copilot/chat executes Qwen AI copilot reasoning."""
        payload = {
            "query": "Calculate Earth to Mars delta-V",
            "active_face_id": 25,
            "departure_body": "Earth",
            "target_body": "Mars",
        }
        response = client.post("/api/v1/exploration/copilot/chat", json=payload)
        assert response.status_code == 200
        res = response.json()
        assert "5.59" in res["response"] or "5.6" in res["response"]
        assert res["model_name"] == "Qwen/Qwen2.5-0.5B-Instruct+LoRA"
        assert "<|im_start|>" in res["chatml_prompt"]
        assert res["trajectory_context"] is not None

    def test_model_metadata_endpoint(self, client):
        """Verify GET /api/v1/exploration/model/metadata reports extracted LoRA config."""
        response = client.get("/api/v1/exploration/model/metadata")
        assert response.status_code == 200
        meta = response.json()
        assert meta["base_model"] == "Qwen/Qwen2.5-0.5B-Instruct"
        assert meta["lora_rank"] == 16
        assert meta["lora_alpha"] == 32
        assert meta["status"] == "READY"


class TestStandaloneSimulationPackage:
    def test_standalone_directory_exists(self):
        """Assert the directory 'c:/dev/NASA-SPACE-APP-2026/nasa exploration' exists."""
        assert os.path.isdir(STANDALONE_DIR)

    def test_required_standalone_files_present(self):
        """Assert all required standalone files are present on disk."""
        req_files = [
            "index.html",
            "styles.css",
            "simulation.js",
            "qwen_copilot.js",
            "run_simulation.py",
            "run_simulation.bat",
        ]
        for f in req_files:
            p = os.path.join(STANDALONE_DIR, f)
            assert os.path.isfile(p), f"Missing standalone file: {p}"
            assert os.path.getsize(p) > 0, f"File {f} is empty"

    def test_zero_external_cdn_dependencies(self):
        """
        Verify that index.html contains ZERO external CDN scripts/styles (100% offline).
        """
        html_path = os.path.join(STANDALONE_DIR, "index.html")
        with open(html_path, "r", encoding="utf-8") as f:
            content = f.read()

        parser = SimpleDomParser()
        parser.feed(content)

        # Check script tags
        for s in parser.scripts:
            src = s.get("src")
            if src:
                assert not src.startswith("http://") and not src.startswith("https://"), (
                    f"Forbidden external CDN script detected: {src}"
                )

        # Check link stylesheet tags
        for link in parser.links:
            href = link.get("href")
            if href:
                assert not href.startswith("http://") and not href.startswith("https://"), (
                    f"Forbidden external CDN stylesheet detected: {href}"
                )

    def test_standalone_dom_elements_structure(self):
        """
        Verify that index.html contains all 4 tabs, canvas, and all 25 faces cards.
        """
        html_path = os.path.join(STANDALONE_DIR, "index.html")
        with open(html_path, "r", encoding="utf-8") as f:
            content = f.read()

        parser = SimpleDomParser()
        parser.feed(content)

        # Tabs
        assert "tab-btn-faces" in parser.elements_by_id
        assert "tab-btn-orbit" in parser.elements_by_id
        assert "tab-btn-qwen" in parser.elements_by_id
        assert "tab-btn-trajectory" in parser.elements_by_id

        # Orbit canvas
        assert "orbitCanvas" in parser.elements_by_id

        # Chat inputs
        assert "chat-input" in parser.elements_by_id
        assert "chat-messages" in parser.elements_by_id

        # Trajectory controls
        assert "dep-body" in parser.elements_by_id
        assert "arr-body" in parser.elements_by_id
        assert "res-deltav" in parser.elements_by_id

        # Face buttons: should contain 25 face card buttons
        face_buttons = [
            b for b in parser.buttons if "face-card-btn" in b.get("class", "")
        ]
        assert len(face_buttons) == 25, f"Expected 25 face buttons in DOM, found {len(face_buttons)}"


class TestFrontendComponentIntegration:
    def test_milky_way_experience_has_three_tabs(self):
        """Assert MilkyWayExperience.tsx includes the 3-way toggle."""
        component_path = os.path.join(WORKSPACE_DIR, "frontend", "src", "components", "MilkyWayExperience.tsx")
        with open(component_path, "r", encoding="utf-8") as f:
            code = f.read()

        assert 'id="faces-lab-tab"' in code
        assert 'id="milky-way-tab"' in code
        assert 'id="solar-system-tab"' in code
        assert "SolarSystem25FacesHUD" in code

    def test_solar_system_hud_component_exists(self):
        """Assert SolarSystem25FacesHUD.tsx exists and implements vanilla Three.js."""
        hud_path = os.path.join(WORKSPACE_DIR, "frontend", "src", "components", "SolarSystem25FacesHUD.tsx")
        assert os.path.isfile(hud_path)
        with open(hud_path, "r", encoding="utf-8") as f:
            code = f.read()

        assert "THREE.WebGLRenderer" in code
        assert "OrbitControls" in code
        assert "STATIC_25_FACES" in code
        assert "Qwen 2.5" in code
