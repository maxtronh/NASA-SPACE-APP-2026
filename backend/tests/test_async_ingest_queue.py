"""Unit and API integration tests for Asynchronous Background Ingestion Task Pipeline."""

from __future__ import annotations

import asyncio
import time
import pytest
from starlette.testclient import TestClient

from backend.app.ingestion.async_queue import AsyncIngestionQueue, JobStatus
from backend.app.main import app


@pytest.fixture
def client():
    return TestClient(app)


@pytest.mark.asyncio
async def test_async_queue_submit_and_progress():
    queue = AsyncIngestionQueue.get_instance()
    job = queue.submit_job("flex-2-heptane-droplet", "psi-flex-2")
    assert job.job_id.startswith("job-")
    assert job.status in (JobStatus.PENDING, JobStatus.RUNNING)

    # Allow worker to execute all stages
    for _ in range(50):
        completed = queue.get_job(job.job_id)
        if completed and completed.status == JobStatus.COMPLETED:
            break
        await asyncio.sleep(0.01)

    completed = queue.get_job(job.job_id)
    assert completed is not None
    assert completed.status == JobStatus.COMPLETED
    assert completed.progress_pct == 100.0
    assert completed.result is not None
    assert completed.result["merkle_root_verified"] is True


def test_api_submit_ingest_job_and_poll(client):
    payload = {
        "investigation_slug": "flex-2-heptane-droplet",
        "target_dataset": "psi-flex-2",
    }
    res_submit = client.post("/api/v1/ingest/jobs", json=payload)
    assert res_submit.status_code == 200
    job_data = res_submit.json()
    assert "job_id" in job_data
    job_id = job_data["job_id"]

    # Poll status
    res_poll = client.get(f"/api/v1/ingest/jobs/{job_id}")
    assert res_poll.status_code == 200
    poll_data = res_poll.json()
    assert poll_data["job_id"] == job_id
    assert "progress_pct" in poll_data
    assert "status" in poll_data

    # List jobs
    res_list = client.get("/api/v1/ingest/jobs")
    assert res_list.status_code == 200
    jobs = res_list.json()
    assert isinstance(jobs, list)
    assert any(j["job_id"] == job_id for j in jobs)


def test_api_get_job_not_found(client):
    response = client.get("/api/v1/ingest/jobs/nonexistent-job-xyz")
    assert response.status_code == 404
