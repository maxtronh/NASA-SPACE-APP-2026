"""
Unit and integration tests for Asynchronous Background Ingestion Task Queue (Upgrade 09).
Verifies job enqueuing, stage progression, completion results, and API endpoints.
"""

from __future__ import annotations

import asyncio
import pytest
from starlette.testclient import TestClient

from backend.app.ingestion.async_queue import AsyncIngestionQueue, JobStatus
from backend.app.main import app


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def queue():
    return AsyncIngestionQueue.get_instance()


@pytest.mark.asyncio
async def test_async_ingestion_queue_execution(queue):
    job = queue.submit_job(
        investigation_slug="flex-2-heptane-droplet",
        target_dataset="psi-flex-2-flight",
    )
    assert job.job_id.startswith("job-")
    assert job.status in (JobStatus.PENDING, JobStatus.RUNNING)

    # Wait for completion
    for _ in range(50):
        if job.status == JobStatus.COMPLETED:
            break
        await asyncio.sleep(0.01)

    assert job.status == JobStatus.COMPLETED
    assert job.progress_pct == 100.0
    assert job.result is not None
    assert job.result["null_measurements_preserved"] > 0
    assert job.result["merkle_root_verified"] is True


def test_api_submit_and_query_ingestion_job(client):
    # Submit job
    submit_resp = client.post(
        "/api/v1/ingest/jobs",
        json={
            "investigation_slug": "acme-cld-flame",
            "target_dataset": "psi-acme-cld",
        },
    )
    assert submit_resp.status_code == 200
    data = submit_resp.json()
    job_id = data["job_id"]
    assert data["investigation_slug"] == "acme-cld-flame"

    # Query status
    status_resp = client.get(f"/api/v1/ingest/jobs/{job_id}")
    assert status_resp.status_code == 200
    status_data = status_resp.json()
    assert status_data["job_id"] == job_id
    assert "progress_pct" in status_data

    # List jobs
    list_resp = client.get("/api/v1/ingest/jobs?limit=10")
    assert list_resp.status_code == 200
    jobs = list_resp.json()
    assert any(j["job_id"] == job_id for j in jobs)


def test_api_query_nonexistent_job_returns_404(client):
    resp = client.get("/api/v1/ingest/jobs/nonexistent-job-xyz")
    assert resp.status_code == 404
