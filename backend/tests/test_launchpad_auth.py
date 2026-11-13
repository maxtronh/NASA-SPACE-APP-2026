"""Unit and API integration tests for NASA Launchpad SSO and OIDC Module."""

from __future__ import annotations

import time
import pytest
from starlette.testclient import TestClient

from backend.app.core.auth_launchpad import (
    MOCK_LAUNCHPAD_USERS,
    LaunchpadTokenManager,
    LaunchpadUserProfile,
)
from backend.app.main import app


@pytest.fixture
def client():
    return TestClient(app)


def test_launchpad_create_and_verify_token():
    profile = MOCK_LAUNCHPAD_USERS["pi_flex@nasa.gov"]
    token = LaunchpadTokenManager.create_token(profile, expires_in_s=3600)

    assert isinstance(token, str)
    assert len(token.split(".")) == 3

    verified = LaunchpadTokenManager.verify_token(token)
    assert verified.sub == profile.sub
    assert verified.email == profile.email
    assert verified.agency == "NASA"
    assert verified.nasa_center == profile.nasa_center


def test_launchpad_tampered_token_raises_401():
    profile = MOCK_LAUNCHPAD_USERS["pi_flex@nasa.gov"]
    token = LaunchpadTokenManager.create_token(profile)
    parts = token.split(".")
    # Tamper with base64 payload
    tampered = f"{parts[0]}.{parts[1][:-4]}AAAA.{parts[2]}"

    with pytest.raises(Exception):
        LaunchpadTokenManager.verify_token(tampered)


def test_api_oidc_discovery(client):
    response = client.get("/api/v1/auth/.well-known/openid-configuration")
    assert response.status_code == 200
    data = response.json()
    assert data["issuer"] == "https://launchpad.nasa.gov"
    assert "userinfo_endpoint" in data
    assert "scopes_supported" in data


def test_api_launchpad_login_and_userinfo(client):
    login_payload = {
        "email": "pi_flex@nasa.gov",
        "nasa_center": "Glenn Research Center (GRC)",
    }
    res_login = client.post("/api/v1/auth/launchpad/login", json=login_payload)
    assert res_login.status_code == 200
    login_data = res_login.json()
    assert "access_token" in login_data
    assert login_data["token_type"] == "Bearer"
    assert login_data["user"]["email"] == "pi_flex@nasa.gov"

    token = login_data["access_token"]

    # Call userinfo with bearer token
    res_userinfo = client.get(
        "/api/v1/auth/launchpad/userinfo",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res_userinfo.status_code == 200
    userinfo = res_userinfo.json()
    assert userinfo["email"] == "pi_flex@nasa.gov"
    assert userinfo["agency"] == "NASA"
    assert userinfo["role"] == "PrincipalInvestigator"


def test_api_userinfo_without_auth_returns_401(client):
    response = client.get("/api/v1/auth/launchpad/userinfo")
    assert response.status_code == 401


def test_api_list_demo_users(client):
    response = client.get("/api/v1/auth/launchpad/demo-users")
    assert response.status_code == 200
    data = response.json()
    assert "demo_accounts" in data
    assert len(data["demo_accounts"]) >= 2
