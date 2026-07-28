"""Configuration boundary for the BFF foundation."""

from __future__ import annotations

import os
from dataclasses import dataclass
from enum import StrEnum
from urllib.parse import urlparse

from .capacity import SCALABLE_SKUS


class DemoMode(StrEnum):
    """The only demo mode accepted by the foundation."""

    LOCAL = "local"
    OFF = "off"


class ConfigurationError(ValueError):
    """Raised when a startup configuration would violate a safety invariant."""


def _split_origins(raw_origins: str) -> tuple[str, ...]:
    origins = tuple(
        origin.strip().rstrip("/")
        for origin in raw_origins.replace(";", ",").split(",")
        if origin.strip()
    )
    if not origins:
        raise ConfigurationError("BFF_CORS_ORIGINS must contain at least one origin.")

    for origin in origins:
        parsed = urlparse(origin)
        if (
            parsed.scheme not in {"http", "https"}
            or not parsed.netloc
            or parsed.path not in {"", "/"}
            or parsed.params
            or parsed.query
            or parsed.fragment
        ):
            raise ConfigurationError(f"Invalid CORS origin: {origin!r}")
    return origins


def _env_bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    value = raw.strip().lower()
    if value in {"1", "true", "yes", "on"}:
        return True
    if value in {"0", "false", "no", "off"}:
        return False
    raise ConfigurationError(f"{name} must be a boolean value.")


@dataclass(frozen=True, slots=True)
class Settings:
    """Runtime settings with local fixtures and explicit cloud trust boundaries."""

    service_name: str
    api_version: str
    environment: str
    demo_mode: DemoMode
    data_namespace: str
    cors_origins: tuple[str, ...]
    auth_mode: str
    demo_data_directory: str = ""
    jwt_validator_module: str = ""
    jwt_issuer: str = ""
    jwt_audience: str = ""
    capacity_mode: str = "local"
    capacity_allowlist: tuple[str, ...] = ("cap-novasteel-demo-sc",)
    capacity_sku_allowlist: tuple[str, ...] = ("F2", "F4", "F8")
    demo_clock_rebase: bool = True

    @property
    def is_demo_mode(self) -> bool:
        return self.demo_mode is DemoMode.LOCAL

    def __post_init__(self) -> None:
        """Keep direct test/host construction subject to the same safety rules."""
        if self.is_demo_mode and not self.data_namespace.startswith("NS-DEMO-"):
            raise ConfigurationError(
                "DEMO_MODE=local requires BFF_DATA_NAMESPACE to start with 'NS-DEMO-'."
            )
        if self.auth_mode not in {"demo", "entra", "entra-pending"}:
            raise ConfigurationError("BFF_AUTH_MODE is invalid.")
        if not self.is_demo_mode and self.auth_mode == "demo":
            raise ConfigurationError("BFF_AUTH_MODE=demo is permitted only when DEMO_MODE=local.")
        if self.capacity_mode not in {"local", "arm"}:
            raise ConfigurationError("BFF_CAPACITY_MODE must be 'local' or 'arm'.")
        if not self.capacity_allowlist:
            raise ConfigurationError("BFF_CAPACITY_ALLOWLIST must contain at least one capacity.")
        if not self.capacity_sku_allowlist:
            raise ConfigurationError("BFF_CAPACITY_SKU_ALLOWLIST must contain at least one SKU.")
        invalid = [s for s in self.capacity_sku_allowlist if s not in SCALABLE_SKUS]
        if invalid:
            raise ConfigurationError(
                f"BFF_CAPACITY_SKU_ALLOWLIST contains invalid SKUs: {invalid}. "
                f"Permitted: {list(SCALABLE_SKUS)}."
            )

    @classmethod
    def from_environment(cls) -> Settings:
        raw_demo_mode = os.getenv("DEMO_MODE", DemoMode.LOCAL.value).strip().lower()
        try:
            demo_mode = DemoMode(raw_demo_mode)
        except ValueError as error:
            allowed = ", ".join(mode.value for mode in DemoMode)
            raise ConfigurationError(
                f"DEMO_MODE must be one of: {allowed}; got {raw_demo_mode!r}."
            ) from error

        environment = os.getenv(
            "BFF_ENVIRONMENT", "demo" if demo_mode is DemoMode.LOCAL else "dev"
        ).strip()
        data_namespace = os.getenv(
            "BFF_DATA_NAMESPACE",
            "NS-DEMO-LUX-01" if demo_mode is DemoMode.LOCAL else "NS-DEV-LUX-01",
        ).strip()
        if demo_mode is DemoMode.LOCAL and not data_namespace.startswith("NS-DEMO-"):
            raise ConfigurationError(
                "DEMO_MODE=local requires BFF_DATA_NAMESPACE to start with 'NS-DEMO-'."
            )

        auth_mode = os.getenv(
            "BFF_AUTH_MODE",
            "demo" if demo_mode is DemoMode.LOCAL else "entra-pending",
        ).strip()
        if auth_mode not in {"demo", "entra", "entra-pending"}:
            raise ConfigurationError(
                "BFF_AUTH_MODE must be 'demo', 'entra', or 'entra-pending'."
            )
        if demo_mode is DemoMode.OFF and auth_mode == "demo":
            raise ConfigurationError(
                "BFF_AUTH_MODE=demo is permitted only when DEMO_MODE=local."
            )

        capacity_mode = os.getenv(
            "BFF_CAPACITY_MODE", "local" if demo_mode is DemoMode.LOCAL else "arm"
        ).strip().lower()
        if capacity_mode not in {"local", "arm"}:
            raise ConfigurationError("BFF_CAPACITY_MODE must be 'local' or 'arm'.")

        return cls(
            service_name=os.getenv("BFF_SERVICE_NAME", "novasteel-bff-api").strip(),
            api_version="v1",
            environment=environment,
            demo_mode=demo_mode,
            data_namespace=data_namespace,
            cors_origins=_split_origins(
                os.getenv(
                    "BFF_CORS_ORIGINS",
                    "http://localhost:5266,https://localhost:7075,"
                    "http://localhost:5000,http://localhost:5173",
                )
            ),
            auth_mode=auth_mode,
            demo_data_directory=os.getenv("BFF_DEMO_DATA_DIRECTORY", "").strip(),
            jwt_validator_module=os.getenv("BFF_JWT_VALIDATOR_MODULE", "").strip(),
            jwt_issuer=os.getenv("BFF_JWT_ISSUER", "").strip(),
            jwt_audience=os.getenv("BFF_JWT_AUDIENCE", "").strip(),
            capacity_mode=capacity_mode,
            capacity_allowlist=tuple(
                value.strip()
                for value in os.getenv(
                    "BFF_CAPACITY_ALLOWLIST", "cap-novasteel-demo-sc"
                ).split(",")
                if value.strip()
            ),
            capacity_sku_allowlist=tuple(
                value.strip().upper()
                for value in os.getenv(
                    "BFF_CAPACITY_SKU_ALLOWLIST", "F2,F4,F8"
                ).split(",")
                if value.strip()
            ),
            demo_clock_rebase=_env_bool("DEMO_CLOCK_REBASE", True),
        )
