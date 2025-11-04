from __future__ import annotations

import os
from pathlib import Path

import pytest  # type: ignore[import]

from src.auth.config import DEFAULT_CACHE_PATH, AuthConfig
from src.auth.exceptions import ConfigurationError


def test_from_env_parses_defaults(tmp_path: Path) -> None:
    cache_path = tmp_path / "cache.json"
    env = {
        "MSAL_TENANT_ID": "contoso.onmicrosoft.com",
        "MSAL_CLIENT_ID": "client-id",
        "MSAL_CLIENT_SECRET": "top-secret",
        "MSAL_SCOPES": "Mail.Read,Mail.Send",
        "MSAL_CACHE_PATH": str(cache_path),
        "MSAL_HTTP_TIMEOUT": "15",
    }

    config = AuthConfig.from_env(env)

    assert config.tenant_id == "contoso.onmicrosoft.com"
    assert config.client_id == "client-id"
    assert config.client_secret == "top-secret"
    assert config.authority.endswith("contoso.onmicrosoft.com")
    assert config.scopes == ("Mail.Read", "Mail.Send")
    assert config.cache_path == cache_path.resolve()
    assert config.timeout == pytest.approx(15.0)


def test_from_env_uses_defaults_when_not_overridden(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MSAL_TENANT_ID", "contoso")
    monkeypatch.setenv("MSAL_CLIENT_ID", "client")
    monkeypatch.setenv("MSAL_CLIENT_SECRET", "secret")

    config = AuthConfig.from_env(os.environ)

    assert config.scopes == ("https://graph.microsoft.com/.default",)
    assert config.cache_path == DEFAULT_CACHE_PATH.resolve()
    assert config.timeout == pytest.approx(10.0)


def test_from_env_missing_variable_raises() -> None:
    env = {"MSAL_CLIENT_ID": "client"}

    with pytest.raises(ConfigurationError):
        AuthConfig.from_env(env)


def test_with_scopes_replaces_values(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MSAL_TENANT_ID", "contoso")
    monkeypatch.setenv("MSAL_CLIENT_ID", "client")
    monkeypatch.setenv("MSAL_CLIENT_SECRET", "secret")
    config = AuthConfig.from_env(os.environ)

    replacement = config.with_scopes(["Mail.Read", "Mail.Send"])

    assert replacement.scopes == ("Mail.Read", "Mail.Send")
    assert replacement.cache_path == config.cache_path
