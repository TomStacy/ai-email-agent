"""Configuration helpers for Microsoft identity authentication."""

from __future__ import annotations

import os
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path

from .exceptions import ConfigurationError

# Get the project root directory (two levels up from this file)
_PROJECT_ROOT = Path(__file__).parent.parent.parent

DEFAULT_SCOPE = "https://graph.microsoft.com/.default"
DEFAULT_CACHE_PATH = _PROJECT_ROOT / "data" / "cache" / "msal_device_cache.json"
DEFAULT_AUTHORITY_TEMPLATE = "https://login.microsoftonline.com/{tenant_id}"


@dataclass(frozen=True, slots=True)
class AuthConfig:
    """Typed configuration object for the authentication layer."""

    tenant_id: str
    client_id: str
    client_secret: str | None
    authority: str
    scopes: tuple[str, ...] = field(default_factory=lambda: (DEFAULT_SCOPE,))
    cache_path: Path | None = DEFAULT_CACHE_PATH
    timeout: float = 10.0

    @classmethod
    def from_env(cls, env: Mapping[str, str] | None = None) -> AuthConfig:
        """Create a configuration instance using environment variables."""

        source = env or os.environ
        tenant_id = _get_required(source, "AZURE_TENANT_ID")
        client_id = _get_required(source, "AZURE_CLIENT_ID")
        client_secret = source.get("AZURE_CLIENT_SECRET", "").strip() or None

        authority = source.get("AZURE_AUTHORITY")
        if not authority:
            authority = DEFAULT_AUTHORITY_TEMPLATE.format(tenant_id=tenant_id)

        scopes_raw = source.get("AZURE_SCOPE") or DEFAULT_SCOPE
        scopes = tuple(_normalize_scopes(scopes_raw))
        if not scopes:
            raise ConfigurationError("AZURE_SCOPE cannot be empty")

        cache_path_value = source.get("AZURE_CACHE_PATH")
        cache_path = (
            Path(cache_path_value).expanduser() if cache_path_value else DEFAULT_CACHE_PATH
        )
        if cache_path:
            cache_path = cache_path.resolve()

        timeout_value = source.get("AZURE_HTTP_TIMEOUT")
        timeout = float(timeout_value) if timeout_value else 10.0

        return cls(
            tenant_id=tenant_id,
            client_id=client_id,
            client_secret=client_secret,
            authority=authority,
            scopes=scopes,
            cache_path=cache_path,
            timeout=timeout,
        )

    def with_scopes(self, scopes: Sequence[str]) -> AuthConfig:
        """Return a copy with an updated scope tuple."""

        normalized = tuple(scope.strip() for scope in scopes if scope.strip())
        if not normalized:
            raise ConfigurationError("Scopes cannot be empty")
        return AuthConfig(
            tenant_id=self.tenant_id,
            client_id=self.client_id,
            client_secret=self.client_secret,
            authority=self.authority,
            scopes=normalized,
            cache_path=self.cache_path,
            timeout=self.timeout,
        )


def _get_required(env: Mapping[str, str], key: str) -> str:
    try:
        value = env[key].strip()
    except KeyError as exc:
        raise ConfigurationError(f"Missing required environment variable: {key}") from exc
    if not value:
        raise ConfigurationError(f"Environment variable {key} cannot be blank")
    return value


def _normalize_scopes(scopes: str | Sequence[str]) -> tuple[str, ...]:
    if isinstance(scopes, str):
        separators = [",", " "]
        value = scopes
        for separator in separators:
            value = value.replace(separator, " ")
        parts = [scope.strip() for scope in value.split(" ") if scope.strip()]
    else:
        parts = [scope.strip() for scope in scopes if scope.strip()]
    unique_parts: list[str] = []
    for scope in parts:
        if scope not in unique_parts:
            unique_parts.append(scope)
    return tuple(unique_parts)
