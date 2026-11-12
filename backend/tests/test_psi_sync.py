"""Unit and integration tests for NASA PSI S3 Sync and Catalog API."""

from __future__ import annotations

import pytest
from starlette.testclient import TestClient

from backend.app.ingestion.psi_sync import (
    AUTHENTIC_PSI_DATASETS,
    PSIS3FileRecord,
    PSIS3SyncClient,
)
from backend.app.main import app


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def sync_client():
    return PSIS3SyncClient(enable_network=False)


def test_psi_sync_client_list_datasets(sync_client):
    datasets = sync_client.list_datasets()
    assert len(datasets) >= 3
    dataset_ids = [d.dataset_id for d in datasets]
    assert "psi-flex-2" in dataset_ids
    assert "psi-bass-ii" in dataset_ids

    # Check FLEX-2 attributes
    flex = next(d for d in datasets if d.dataset_id == "psi-flex-2")
    assert flex.acronym == "FLEX-2"
    assert flex.combustion_regime == "droplet_combustion"
    assert flex.primary_fuel == "n-heptane"
    assert flex.file_count >= 2
    assert flex.total_bytes > 0


def test_psi_sync_client_get_dataset(sync_client):
    ds = sync_client.get_dataset("psi-flex-2")
    assert ds is not None
    assert ds.dataset_id == "psi-flex-2"
    assert ds.facility == "Combustion Integrated Rack (CIR)"

    # Fuzzy match
    ds_fuzzy = sync_client.get_dataset("bass-ii")
    assert ds_fuzzy is not None
    assert ds_fuzzy.dataset_id == "psi-bass-ii"


def test_psi_sync_client_get_nonexistent(sync_client):
    ds = sync_client.get_dataset("nonexistent-dataset-xyz")
    assert ds is None


def test_psi_parse_s3_xml_listing(sync_client):
    sample_xml = """<?xml version="1.0" encoding="UTF-8"?>
    <ListBucketResult xmlns="http://s3.amazonaws.com/doc/2006-03-01/">
        <Name>nasa-psi</Name>
        <Prefix>combustion/flex-2/</Prefix>
        <Contents>
            <Key>combustion/flex-2/test_01.csv</Key>
            <LastModified>2023-01-15T12:00:00.000Z</LastModified>
            <ETag>"abc123etag"</ETag>
            <Size>12345</Size>
            <StorageClass>STANDARD</StorageClass>
        </Contents>
    </ListBucketResult>
    """
    records = sync_client.parse_s3_xml_listing(sample_xml)
    assert len(records) == 1
    rec = records[0]
    assert rec.key == "combustion/flex-2/test_01.csv"
    assert rec.size_bytes == 12345
    assert rec.etag == "abc123etag"


def test_api_list_psi_datasets(client):
    response = client.get("/api/v1/ingest/psi/datasets")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 3
    slugs = [d["dataset_id"] for d in data]
    assert "psi-flex-2" in slugs


def test_api_get_psi_dataset_details(client):
    response = client.get("/api/v1/ingest/psi/datasets/psi-flex-2")
    assert response.status_code == 200
    data = response.json()
    assert data["dataset_id"] == "psi-flex-2"
    assert data["primary_fuel"] == "n-heptane"
    assert len(data["files"]) >= 2
    assert any("parquet" in f["key"].lower() for f in data["files"])


def test_api_get_psi_dataset_not_found(client):
    response = client.get("/api/v1/ingest/psi/datasets/invalid-id-999")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_api_list_psi_files(client):
    response = client.get("/api/v1/ingest/psi/files", params={"prefix": "combustion/flex-2/"})
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert all("combustion/flex-2/" in f["key"] for f in data)
