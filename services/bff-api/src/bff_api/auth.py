"""Authentication and authorization boundary for demo and Entra modes."""

from __future__ import annotations

import importlib
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Callable, Mapping

from fastapi import Request

from .config import Settings
from .contracts import ErrorCode
from .errors import ApiError


READER_ROLES = frozenset(
    {
        "Operator.Read",
        "ProcessEngineer.Contribute",
        "EnergyPlanner.Approve",
        "MaintenanceEngineer.Read",
        "DataScientist.ML",
        "Compliance.Auditor",
        "Platform.Capacity.Manage",
        "Knowledge.Publisher",
    }
)

_PERSONAS = {
    "Operator.Read": "FurnaceOperator",
    "ProcessEngineer.Contribute": "QualityEngineer",
    "EnergyPlanner.Approve": "EnergyManager",
    "MaintenanceEngineer.Read": "MaintenanceReliabilityEngineer",
    "DataScientist.ML": "DataScientist",
    "Compliance.Auditor": "ComplianceAuditor",
    "Platform.Capacity.Manage": "PlatformOperator",
    "Knowledge.Publisher": "KnowledgeEngineer",
}

_ACTIONS = {
    "Operator.Read": {"dashboard.read", "telemetry.read"},
    "ProcessEngineer.Contribute": {
        "dashboard.read",
        "quality.read",
        "quality.whatIf",
    },
    "EnergyPlanner.Approve": {
        "dashboard.read",
        "energy.read",
        "energy.simulate",
        "energy.approve",
    },
    "MaintenanceEngineer.Read": {
        "dashboard.read",
        "furnace.viewForecast",
        "workorder.createSynthetic",
    },
    "Compliance.Auditor": {"audit.read", "sustainability.read"},
    "Platform.Capacity.Manage": {"platform.capacity.manage"},
    "Knowledge.Publisher": {
        "knowledge.read",
        "knowledge.capture",
        "knowledge.publish",
    },
}


@dataclass(frozen=True, slots=True)
class UserContext:
    """Validated identity and server-authoritative authorization scope."""

    user_id: str
    display_name: str
    roles: frozenset[str]
    plant_scope: frozenset[str]
    locale: str = "en-LU"

    @property
    def personas(self) -> list[str]:
        return sorted({_PERSONAS[role] for role in self.roles if role in _PERSONAS})

    @property
    def permitted_actions(self) -> list[str]:
        return sorted(
            {
                action
                for role in self.roles
                for action in _ACTIONS.get(role, set())
            }
        )

    def can_access_site(self, site: str) -> bool:
        return site in self.plant_scope


class EntraJwtValidator:
    """Fail-closed production validation port.

    Signature verification is delegated to an organization-provided, JWKS-aware
    validator module.  This package intentionally does not parse an unverified
    JWT as an authenticated identity.  The adapter must validate signature,
    issuer, audience, expiry, and not-before before returning claims.
    """

    def __init__(self, settings: Settings) -> None:
        self._issuer = settings.jwt_issuer
        self._audience = settings.jwt_audience
        self._validator = self._load_validator(settings.jwt_validator_module)

    @staticmethod
    def _load_validator(
        module_path: str,
    ) -> Callable[[str], Mapping[str, Any]] | None:
        if not module_path:
            return None
        module_name, separator, attr_name = module_path.partition(":")
        if not separator:
            raise ValueError("BFF_JWT_VALIDATOR_MODULE must use module:function syntax.")
        candidate = getattr(importlib.import_module(module_name), attr_name)
        if not callable(candidate):
            raise ValueError("Configured JWT validator is not callable.")
        return candidate

    def validate(self, token: str) -> UserContext:
        if not token or self._validator is None:
            raise ApiError(
                401,
                ErrorCode.INVALID_TOKEN,
                "A production Entra JWT validation adapter is not configured.",
            )
        try:
            claims = dict(self._validator(token))
        except Exception as exc:  # pragma: no cover - adapter controls crypto details
            raise ApiError(401, ErrorCode.INVALID_TOKEN, "The access token is invalid.") from exc
        if self._issuer and claims.get("iss") != self._issuer:
            raise ApiError(401, ErrorCode.INVALID_TOKEN, "The access token issuer is invalid.")
        audience = claims.get("aud")
        audiences = audience if isinstance(audience, list) else [audience]
        if self._audience and self._audience not in audiences:
            raise ApiError(401, ErrorCode.INVALID_TOKEN, "The access token audience is invalid.")
        expires_at = claims.get("exp")
        if expires_at is not None and float(expires_at) <= datetime.now(UTC).timestamp():
            raise ApiError(401, ErrorCode.INVALID_TOKEN, "The access token has expired.")
        return _context_from_claims(claims)


class Authenticator:
    """Uses explicit demo headers locally and a strict JWT port outside demo mode."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._entra = EntraJwtValidator(settings) if not settings.is_demo_mode else None

    def authenticate(self, request: Request) -> UserContext:
        if self._settings.is_demo_mode:
            return self._demo_context(request)
        authorization = request.headers.get("Authorization", "")
        scheme, _, token = authorization.partition(" ")
        if scheme.lower() != "bearer" or not token.strip():
            raise ApiError(401, ErrorCode.INVALID_TOKEN, "A bearer access token is required.")
        assert self._entra is not None
        return self._entra.validate(token.strip())

    @staticmethod
    def _demo_context(request: Request) -> UserContext:
        user_id = request.headers.get("X-Demo-User", "").strip()
        if not user_id:
            raise ApiError(
                401,
                ErrorCode.INVALID_TOKEN,
                "Demo authentication requires the X-Demo-User header.",
            )
        roles = _split_claim(
            request.headers.get("X-Demo-Roles", request.headers.get("X-Demo-Role", ""))
        )
        plants = _split_claim(
            request.headers.get("X-Demo-Plants", request.headers.get("X-Demo-Plant", ""))
        )
        if not roles:
            raise ApiError(
                401,
                ErrorCode.INVALID_TOKEN,
                "Demo authentication requires at least one X-Demo-Roles value.",
            )
        if not plants or any(not plant.startswith("NS-DEMO-") for plant in plants):
            raise ApiError(
                401,
                ErrorCode.INVALID_TOKEN,
                "Demo plant scope must contain NS-DEMO-* values.",
            )
        unknown = set(roles) - READER_ROLES
        if unknown:
            raise ApiError(
                401,
                ErrorCode.INVALID_TOKEN,
                "Demo authentication contains an unknown application role.",
            )
        return UserContext(
            user_id=user_id,
            display_name=request.headers.get("X-Demo-Display-Name", user_id).strip()
            or user_id,
            roles=frozenset(roles),
            plant_scope=frozenset(plants),
            locale=request.headers.get("X-Demo-Locale", "en-LU").strip() or "en-LU",
        )


def _context_from_claims(claims: Mapping[str, Any]) -> UserContext:
    roles = claims.get("roles", [])
    plants = claims.get("plantScope", claims.get("plant_ids", []))
    if isinstance(roles, str):
        roles = [roles]
    if isinstance(plants, str):
        plants = [plants]
    user_id = str(claims.get("oid", claims.get("sub", ""))).strip()
    if not user_id or not isinstance(roles, list) or not isinstance(plants, list):
        raise ApiError(401, ErrorCode.INVALID_TOKEN, "The access token claims are invalid.")
    return UserContext(
        user_id=user_id,
        display_name=str(claims.get("name", user_id)),
        roles=frozenset(str(role) for role in roles),
        plant_scope=frozenset(str(plant) for plant in plants),
        locale=str(claims.get("locale", "en-LU")),
    )


def _split_claim(raw: str) -> set[str]:
    return {value.strip() for value in raw.replace(";", ",").split(",") if value.strip()}


async def current_user(request: Request) -> UserContext:
    """FastAPI dependency resolving the application's configured authenticator."""
    return request.app.state.services.authenticator.authenticate(request)


def require_any_role(user: UserContext, *roles: str) -> None:
    if not user.roles.intersection(roles):
        raise ApiError(
            403,
            ErrorCode.FORBIDDEN_ROLE,
            "You do not have the required application role.",
        )


def require_reader(user: UserContext) -> None:
    require_any_role(user, *READER_ROLES)


def require_site(user: UserContext, site: str) -> None:
    if site != "all" and not user.can_access_site(site):
        raise ApiError(
            403,
            ErrorCode.FORBIDDEN_SCOPE,
            "You do not have access to the requested plant.",
        )
