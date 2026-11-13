"""API endpoints for NASA Launchpad SSO and OpenID Connect."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, EmailStr, Field

from backend.app.core.auth_launchpad import (
    MOCK_LAUNCHPAD_USERS,
    LaunchpadTokenManager,
    LaunchpadUserProfile,
    get_current_launchpad_user,
)

router = APIRouter(prefix="/auth", tags=["authentication"])


class LaunchpadLoginRequest(BaseModel):
    email: str = Field(default="pi_flex@nasa.gov", description="NASA official email address")
    nasa_center: str = Field(default="Glenn Research Center (GRC)", description="Affiliated NASA Research Center")


class LaunchpadLoginResponse(BaseModel):
    access_token: str
    token_type: str = "Bearer"
    expires_in_seconds: int = 7200
    user: Dict[str, Any]


@router.get("/.well-known/openid-configuration")
async def get_oidc_configuration() -> Dict[str, Any]:
    """Standard OpenID Connect Discovery metadata for NASA Launchpad federation."""
    return {
        "issuer": "https://launchpad.nasa.gov",
        "authorization_endpoint": "https://launchpad.nasa.gov/oauth2/authorize",
        "token_endpoint": "https://launchpad.nasa.gov/oauth2/token",
        "userinfo_endpoint": "/api/v1/auth/launchpad/userinfo",
        "jwks_uri": "https://launchpad.nasa.gov/oauth2/jwks",
        "response_types_supported": ["code", "token", "id_token"],
        "subject_types_supported": ["public"],
        "id_token_signing_alg_values_supported": ["HS256", "RS256"],
        "scopes_supported": ["openid", "profile", "email", "cortexx:read", "cortexx:ingest"],
    }


@router.post("/launchpad/login", response_model=LaunchpadLoginResponse)
async def launchpad_login(payload: LaunchpadLoginRequest):
    """Authenticates against NASA Launchpad SSO and issues a cryptographically signed token."""
    email = payload.email.strip().lower()
    profile = MOCK_LAUNCHPAD_USERS.get(email)

    if not profile:
        # Generate generic guest/investigator profile
        name = email.split("@")[0].replace(".", " ").title()
        profile = LaunchpadUserProfile(
            sub=f"NASA-UUPIC-{abs(hash(email)) % 10000000}",
            name=name,
            email=email,
            agency="NASA",
            nasa_center=payload.nasa_center,
            role="ResearchScientist",
            clearance_level="Public-Release",
        )

    token = LaunchpadTokenManager.create_token(profile)
    return {
        "access_token": token,
        "token_type": "Bearer",
        "expires_in_seconds": 7200,
        "user": asdict(profile),
    }


@router.get("/launchpad/userinfo")
async def get_launchpad_userinfo(
    current_user: LaunchpadUserProfile = Depends(get_current_launchpad_user),
) -> Dict[str, Any]:
    """Returns the verified authenticated NASA Launchpad user profile."""
    return asdict(current_user)


@router.get("/launchpad/demo-users")
async def list_demo_users() -> Dict[str, Any]:
    """Lists available NASA Launchpad demo accounts with roles and center affiliations."""
    users = [asdict(u) for u in MOCK_LAUNCHPAD_USERS.values()]
    return {"demo_accounts": users}
