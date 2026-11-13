"""Unit and API integration tests for Multi-Agent Consensus Evaluation Suite."""

from __future__ import annotations

import pytest
from starlette.testclient import TestClient

from backend.app.main import app
from backend.app.ml.consensus_evaluator import (
    ConsensusEvaluationReport,
    MultiAgentConsensusEvaluator,
)


@pytest.fixture
def client():
    return TestClient(app)


def test_consensus_evaluator_valid_grounded_response():
    report = MultiAgentConsensusEvaluator.evaluate(
        query="What is the droplet burning rate in microgravity for n-heptane?",
        response_text="In microgravity (FLEX-2), isolated n-heptane droplets exhibit spherical symmetry and quasi-steady d^2 burning with radiative and diffusive extinction.",
        citations=[
            {
                "investigation_id": "flex-2-heptane-droplet",
                "title": "FLEX-2 Droplet Combustion",
                "nasa_source_url": "https://ntrs.nasa.gov/citations/20150023456",
            }
        ],
        abstention_flag=False,
        si_measurements={"burning_rate_m2_s": 0.58e-6, "chamber_pressure_pa": 101325.0},
    )

    assert isinstance(report, ConsensusEvaluationReport)
    assert report.total_evaluators == 5
    assert report.overall_status == "VERIFIED_CONSENSUS"
    assert report.consensus_score >= 0.9
    assert report.zero_fabrication_adherence_pct == 100.0
    assert report.null_preservation_adherence_pct == 100.0


def test_consensus_evaluator_out_of_domain_abstention():
    report = MultiAgentConsensusEvaluator.evaluate(
        query="What is the price of bitcoin cryptocurrency on Mars?",
        response_text="I can only answer questions related to NASA microgravity combustion research.",
        citations=[],
        abstention_flag=True,
    )

    assert report.overall_status == "VERIFIED_CONSENSUS"
    zf_verdict = next(v for v in report.verdicts if v.agent_persona == "Zero-Fabrication Verifier")
    assert zf_verdict.passed is True
    assert zf_verdict.score == 1.0


def test_consensus_evaluator_catches_coerced_zero():
    # Coerced 0.0 in missing sensor metric
    report = MultiAgentConsensusEvaluator.evaluate(
        query="Explain PMMA flame spread velocity in BASS-II.",
        response_text="BASS-II flame spread is governed by airflow velocity.",
        citations=[{"nasa_source_url": "https://ntrs.nasa.gov/citations/20210011385"}],
        abstention_flag=False,
        si_measurements={"unmeasured_radiometer_flux": 0.0},
    )

    assert report.overall_status == "REJECTED_CONSENSUS"
    data_verdict = next(v for v in report.verdicts if v.agent_persona == "Data Integrity Inspector")
    assert data_verdict.passed is False
    assert report.null_preservation_adherence_pct == 0.0


def test_api_consensus_eval_endpoint(client):
    payload = {
        "query": "How does cool flame transition occur in n-heptane?",
        "response_text": "In microgravity, cool flames transition following radiative extinction at low temperatures.",
        "citations": [
            {
                "investigation_id": "flex-2",
                "nasa_source_url": "https://ntrs.nasa.gov/citations/20150023456",
            }
        ],
        "abstention_flag": False,
    }
    response = client.post("/api/v1/analytics/consensus-eval", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["total_evaluators"] == 5
    assert "consensus_score" in data
    assert len(data["verdicts"]) == 5
