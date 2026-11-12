"""
Unit and integration tests for real-time WebSocket telemetry streaming endpoint.
Verifies protocol handshake, play/pause/seek controls, playback rates, and error conditions.
"""

import json
import pytest
from starlette.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from backend.app.main import app
from backend.app.timeseries import ensure_flight_telemetry_seeded


@pytest.fixture(autouse=True)
def seed_telemetry():
    ensure_flight_telemetry_seeded()


def test_ws_telemetry_handshake_and_step():
    client = TestClient(app)
    with client.websocket_connect("/api/v1/ws/timeseries/FLEX-001") as ws:
        # Initial handshake message
        init_data = ws.receive_json()
        assert init_data["type"] == "init"
        assert init_data["run_identifier"] == "FLEX-001"
        assert init_data["investigation_slug"] == "flex-2-heptane-droplet"
        assert init_data["total_points"] > 0
        assert init_data["status"] == "ready"

        # Step command
        ws.send_text(json.dumps({"command": "step"}))
        step_data = ws.receive_json()
        assert step_data["type"] == "telemetry"
        assert step_data["index"] == 0
        assert "point" in step_data
        assert step_data["point"]["investigation_slug"] == "flex-2-heptane-droplet"


def test_ws_telemetry_controls_play_pause_seek():
    client = TestClient(app)
    with client.websocket_connect("/api/v1/ws/timeseries/FLEX-001") as ws:
        init_data = ws.receive_json()
        assert init_data["type"] == "init"

        # Play command with 5x rate
        ws.send_text(json.dumps({"command": "play", "rate": 5.0}))
        ack_data = ws.receive_json()
        assert ack_data["type"] == "ack"
        assert ack_data["command"] == "play"
        assert ack_data["playback_rate"] == 5.0

        # Receive streamed point
        streamed = ws.receive_json()
        assert streamed["type"] == "telemetry"

        # Pause command
        ws.send_text(json.dumps({"command": "pause"}))
        # Drain in-flight telemetry frames until pause ack arrives
        msg = ws.receive_json()
        retries = 0
        while msg["type"] == "telemetry" and retries < 20:
            msg = ws.receive_json()
            retries += 1
        assert msg["type"] == "ack"
        assert msg["command"] == "pause"

        # Seek command to 5.0 seconds
        ws.send_text(json.dumps({"command": "seek", "time": 5.0}))
        seek_ack = ws.receive_json()
        assert seek_ack["type"] == "ack"
        assert seek_ack["command"] == "seek"
        assert abs(seek_ack["time_seconds"] - 5.0) < 0.2


def test_ws_telemetry_nonexistent_run():
    client = TestClient(app)
    with pytest.raises(WebSocketDisconnect):
        with client.websocket_connect("/api/v1/ws/timeseries/UNKNOWN-NONEXISTENT-RUN-999") as ws:
            err = ws.receive_json()
            assert err["type"] == "error"
            assert err["code"] == "RUN_NOT_FOUND"
            # Next read will raise WebSocketDisconnect
            ws.receive_json()
