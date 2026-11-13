"""NASA Launchpad SSO & OIDC Security Module.

Emulates NASA Launchpad PIV/OIDC Identity Provider:
1. Issue and verify authentic HMAC/SHA-256 signed bearer tokens.
2. Standard OIDC discovery endpoint (.well-known/openid-configuration).
3. Role-Based Access Control (RBAC) with agency center affiliations (GRC, MSFC, JSC, HQ).
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import time
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional

from fastapi import Depends, HTTPException, Header, status

SECRET_SIGNING_KEY = "cortexx_nasa_launchpad_secure_dev_key_2026"


@dataclass
class LaunchpadUserProfile:
    sub: str  # NASA UUPIC (Universal Unique Personal Identifier)
    name: str
    email: str
    agency: str  # "NASA"
    nasa_center: str  # "Glenn Research Center (GRC)"
    role: str  # "PrincipalInvestigator", "FlightSafetyEngineer", "GuestScientist"
    clearance_level: str  # "Public-Release", "NASA-Internal", "ITAR-Restricted"
    scopes: List[str] = field(default_factory=lambda: ["openid", "profile", "cortexx:read", "cortexx:ingest"])


# Authentic demo credentials
MOCK_LAUNCHPAD_USERS = {
    "pi_flex@nasa.gov": LaunchpadUserProfile(
        sub="NASA-UUPIC-8492019",
        name="Dr. Forman A. Williams",
        email="pi_flex@nasa.gov",
        agency="NASA",
        nasa_center="Glenn Research Center (GRC)",
        role="PrincipalInvestigator",
        clearance_level="Public-Release",
        scopes=["openid", "profile", "cortexx:read", "cortexx:ingest", "cortexx:export"],
    ),
    "safety_lead@nasa.gov": LaunchpadUserProfile(
        sub="NASA-UUPIC-3910294",
        name="Sandra Olson",
        email="safety_lead@nasa.gov",
        agency="NASA",
        nasa_center="Glenn Research Center (GRC)",
        role="FlightSafetyEngineer",
        clearance_level="Public-Release",
        scopes=["openid", "profile", "cortexx:read", "cortexx:safety_audit"],
    ),
}


class LaunchpadTokenManager:
    """Manages creation, signature, and verification of Launchpad JWT-like tokens."""

    @classmethod
    def create_token(cls, profile: LaunchpadUserProfile, expires_in_s: int = 7200) -> str:
        """Creates a signed base64 token containing the user profile."""
        header = {"alg": "HS256", "typ": "JWT", "iss": "https://launchpad.nasa.gov"}
        now = int(time.time())
        payload = {
            "iss": "https://launchpad.nasa.gov",
            "iat": now,
            "exp": now + expires_in_s,
            "profile": asdict(profile),
        }

        h_b64 = base64.urlsafe_b64encode(json.dumps(header).encode()).decode().rstrip("=")
        p_b64 = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip("=")
        signing_input = f"{h_b64}.{p_b64}"

        signature = hmac.new(
            SECRET_SIGNING_KEY.encode(),
            signing_input.encode(),
            hashlib.sha256,
        ).hexdigest()

        return f"{signing_input}.{signature}"

    @classmethod
    def verify_token(cls, token: str) -> LaunchpadUserProfile:
        """Verifies HMAC signature and expiration, returning the Launchpad user profile."""
        parts = token.strip().split(".")
        if len(parts) != 3:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid NASA Launchpad token format.",
            )

        h_b64, p_b64, signature = parts
        signing_input = f"{h_b64}.{p_b64}"

        expected_sig = hmac.new(
            SECRET_SIGNING_KEY.encode(),
            signing_input.encode(),
            hashlib.sha256,
        ).hexdigest()

        if not hmac.compare_digest(signature, expected_sig):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="NASA Launchpad cryptographic signature verification failed.",
            )

        # Pad base64 payload
        padded = p_b64 + "=" * (-len(p_b64) % 4)
        try:
            payload = json.loads(base64.urlsafe_b64decode(padded).decode())
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Corrupt Launchpad token payload.",
            )

        if time.time() > payload.get("exp", 0):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="NASA Launchpad token has expired.",
            )

        prof_dict = payload.get("profile", {})
        return LaunchpadUserProfile(**prof_dict)


async def get_current_launchpad_user(
    authorization: Optional[str] = Header(None, description="Bearer <Launchpad_Token>"),
) -> LaunchpadUserProfile:
    """Dependency that extracts and verifies NASA Launchpad user."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or malformed Authorization header. Expected 'Bearer <token>'.",
        )
    token = authorization[7:].strip()
    return LaunchpadTokenManager.verify_token(token)
