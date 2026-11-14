"""Unit and integration tests for Multimodal Schlieren & Video Frame RAG (Upgrade E-07)."""

import math
import uuid
import numpy as np
import pytest
from fastapi.testclient import TestClient

from backend.app.ml.multimodal_rag import (
    KeyframeExtractor,
    MultimodalEmbedder,
    SootPyrometryProcessor,
)


def test_keyframe_extractor_sample_indices():
    # 30 FPS native, 10 Hz target -> sample every 3 frames: [0, 3, 6, 9, 12, 15, 18, 21, 24, 27]
    indices = KeyframeExtractor.sample_indices(total_frames=30, native_fps=30.0, target_hz=10.0)
    assert len(indices) == 10
    assert indices[0] == 0
    assert indices[1] == 3
    assert indices[-1] == 27

    # Edge cases
    assert KeyframeExtractor.sample_indices(total_frames=0, native_fps=30.0) == []
    assert KeyframeExtractor.sample_indices(total_frames=10, native_fps=-5.0) == []


def test_keyframe_extractor_synthetic_stream():
    stream = KeyframeExtractor.generate_synthetic_stream(
        total_duration_s=2.0,
        native_fps=30.0,
        regime="microgravity",
    )
    assert len(stream) == 20  # 2.0 s * 10 Hz
    first = stream[0]
    assert first["frame_index"] == 0
    assert first["timestamp_s"] == 0.0
    assert first["width_px"] == 256
    assert first["height_px"] == 256
    assert "mean_intensity" in first
    assert "peak_intensity" in first
    assert "is_flame_present" in first
    assert len(first["frame_matrix"]) == 256
    assert len(first["frame_matrix"][0]) == 256


def test_soot_pyrometry_processor_spherical_microgravity():
    stream = KeyframeExtractor.generate_synthetic_stream(
        total_duration_s=1.0,
        native_fps=30.0,
        regime="microgravity",
    )
    # Steady burning frame
    mat = np.array(stream[5]["frame_matrix"])
    res = SootPyrometryProcessor.analyze_frame(
        frame_matrix=mat,
        wavelength_1_nm=650.0,
        wavelength_2_nm=530.0,
        droplet_radius_px=10.0,
    )

    assert res["peak_temperature_k"] is not None
    assert 800.0 <= res["peak_temperature_k"] <= 2400.0
    assert res["mean_temperature_k"] is not None
    assert 800.0 <= res["mean_temperature_k"] <= 2400.0
    assert res["equivalent_diameter_px"] is not None
    assert res["equivalent_diameter_px"] > 20.0
    # Spherical flame in microgravity has high sphericity index
    assert res["sphericity_index"] is not None
    assert res["sphericity_index"] >= 0.70

    # SSOR is calculated when droplet_radius_px is provided
    assert res["soot_standoff_ratio"] is not None
    expected_ssor = (res["equivalent_diameter_px"] / 2.0) / 10.0
    assert pytest.approx(res["soot_standoff_ratio"], abs=0.01) == expected_ssor


def test_soot_pyrometry_strict_null_preservation():
    stream = KeyframeExtractor.generate_synthetic_stream(
        total_duration_s=1.0,
        native_fps=30.0,
        regime="microgravity",
    )
    mat = np.array(stream[5]["frame_matrix"])

    # When droplet_radius_px is None -> soot_standoff_ratio MUST be None (not 0.0)
    res_none = SootPyrometryProcessor.analyze_frame(frame_matrix=mat, droplet_radius_px=None)
    assert res_none["soot_standoff_ratio"] is None
    assert res_none["soot_standoff_ratio"] is not 0.0

    # When no flame present (black frame)
    black = np.zeros((100, 100))
    res_black = SootPyrometryProcessor.analyze_frame(frame_matrix=black)
    assert res_black["peak_temperature_k"] is None
    assert res_black["equivalent_diameter_px"] is None
    assert res_black["soot_standoff_ratio"] is None


def test_multimodal_embedder_dimensions_and_normalization():
    mat = np.random.uniform(0.0, 1.0, (64, 64))
    emb_img = MultimodalEmbedder.generate_image_embedding(mat, modality="schlieren", regime="microgravity")
    assert len(emb_img) == 512
    norm_img = math.sqrt(sum(x ** 2 for x in emb_img))
    assert pytest.approx(norm_img, abs=1e-3) == 1.0

    emb_text = MultimodalEmbedder.generate_text_embedding("Spherical soot shell in microgravity")
    assert len(emb_text) == 512
    norm_text = math.sqrt(sum(x ** 2 for x in emb_text))
    assert pytest.approx(norm_text, abs=1e-3) == 1.0


def test_api_extract_keyframes_endpoint(client: TestClient):
    payload = {
        "video_id": "flex2_test_vid_01",
        "fps": 30.0,
        "target_hz": 10.0,
        "duration_s": 2.0,
        "simulate_synthetic": True,
        "regime": "microgravity",
    }
    res = client.post("/api/v1/multimodal/extract-keyframes", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["video_id"] == "flex2_test_vid_01"
    assert data["target_hz"] == 10.0
    assert data["stride_frames"] == 3
    assert data["total_frames_sampled"] == 20
    assert len(data["keyframes"]) == 20
    assert data["keyframes"][0]["frame_index"] == 0


def test_api_pyrometry_endpoint_with_null_preservation(client: TestClient):
    # Case 1: Without droplet_radius_px -> soot_standoff_ratio is None
    res1 = client.post("/api/v1/multimodal/pyrometry", json={})
    assert res1.status_code == 200
    data1 = res1.json()
    assert data1["peak_temperature_k"] is not None
    assert 800.0 <= data1["peak_temperature_k"] <= 2400.0
    assert data1["soot_standoff_ratio"] is None

    # Case 2: With droplet_radius_px -> soot_standoff_ratio is computed
    res2 = client.post("/api/v1/multimodal/pyrometry", json={"droplet_radius_px": 12.5})
    assert res2.status_code == 200
    data2 = res2.json()
    assert data2["soot_standoff_ratio"] is not None
    assert data2["soot_standoff_ratio"] > 0.0


def test_api_index_and_search_and_get_frame(client: TestClient):
    frame_uid = f"frame_test_{uuid.uuid4().hex[:8]}"

    # Index frame
    unique_caption = f"Unique Schlieren thermal boundary layer {frame_uid}"
    idx_payload = {
        "frame_identifier": frame_uid,
        "timestamp_s": 1.25,
        "optical_modality": "schlieren",
        "regime": "microgravity",
        "peak_temperature_k": 1850.5,
        "mean_temperature_k": 1520.0,
        "equivalent_diameter_px": 84.2,
        "sphericity_index": 0.94,
        "soot_standoff_ratio": None,  # strict null preservation
        "caption_text": unique_caption,
        "metadata": {"investigation": "FLEX-2", "fuel": "n-heptane"},
    }
    idx_res = client.post("/api/v1/multimodal/index-frame", json=idx_payload)
    assert idx_res.status_code == 201
    idx_data = idx_res.json()
    assert idx_data["status"] == "indexed"
    assert idx_data["vector_dimension"] == 512
    created_id = idx_data["frame_id"]

    # Search frame
    search_payload = {
        "query_text": unique_caption,
        "optical_modality": "schlieren",
        "top_k": 5,
    }
    s_res = client.post("/api/v1/multimodal/search", json=search_payload)
    assert s_res.status_code == 200
    s_data = s_res.json()
    assert s_data["total_matches"] >= 1
    found = any(item["frame_identifier"] == frame_uid for item in s_data["results"])
    assert found

    # Retrieve frame details
    get_res = client.get(f"/api/v1/multimodal/frames/{created_id}")
    assert get_res.status_code == 200
    get_data = get_res.json()
    assert get_data["frame_identifier"] == frame_uid
    assert get_data["peak_temperature_k"] == 1850.5
    assert get_data["soot_standoff_ratio"] is None  # Strict NULL preservation confirmed!


def test_api_get_frame_not_found(client: TestClient):
    random_id = str(uuid.uuid4())
    res = client.get(f"/api/v1/multimodal/frames/{random_id}")
    assert res.status_code == 404


def test_api_pyrometry_rejects_empty_matrix(client: TestClient):
    res = client.post("/api/v1/multimodal/pyrometry", json={"frame_matrix": []})
    assert res.status_code == 422
    assert "frame_matrix must be a non-empty 2D rectangular matrix" in res.json()["detail"]


def test_api_pyrometry_rejects_jagged_matrix(client: TestClient):
    res = client.post("/api/v1/multimodal/pyrometry", json={"frame_matrix": [[0.5, 0.5], [0.5]]})
    assert res.status_code == 422
    assert "Invalid frame_matrix structure" in res.json()["detail"]


def test_soot_pyrometry_processor_empty_or_degenerate_matrix():
    # 0-length matrix
    res_empty = SootPyrometryProcessor.analyze_frame(frame_matrix=[])
    assert res_empty["peak_temperature_k"] is None
    assert res_empty["flame_area_px2"] == 0.0
    assert res_empty["centroid_x_px"] == 0.0
    assert res_empty["centroid_y_px"] == 0.0

    # 1D matrix
    res_1d = SootPyrometryProcessor.analyze_frame(frame_matrix=[0.5, 0.6])
    assert res_1d["peak_temperature_k"] is None
    assert res_1d["flame_area_px2"] == 0.0

