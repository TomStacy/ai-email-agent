from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest  # type: ignore[import]

from src.auth.config import AuthConfig
from src.auth.exceptions import AuthenticationError
from src.auth.manager import AuthenticationManager
from src.auth.token_cache import TokenCacheManager


@pytest.fixture
def auth_config(tmp_path: Path) -> AuthConfig:
    cache_path = tmp_path / "cache.json"
    return AuthConfig(
        tenant_id="contoso",
        client_id="client",
        client_secret="secret",
        authority="https://login.microsoftonline.com/contoso",
        scopes=("Scope.Read",),
        cache_path=cache_path,
        timeout=5.0,
    )


def test_get_access_token_uses_cache(auth_config: AuthConfig) -> None:
    cache_manager = TokenCacheManager(auth_config.cache_path)
    mock_client = MagicMock()
    mock_client.acquire_token_silent.return_value = {"access_token": "cached-token"}

    manager = AuthenticationManager(auth_config, cache_manager=cache_manager, client=mock_client)

    token = manager.get_access_token()

    assert token == "cached-token"
    mock_client.acquire_token_silent.assert_called_once()
    mock_client.acquire_token_for_client.assert_not_called()


def test_get_access_token_refreshes_when_needed(auth_config: AuthConfig) -> None:
    cache_manager = TokenCacheManager(auth_config.cache_path)
    cache_manager.persist = MagicMock()  # type: ignore[assignment]  # pragma: no cover - test helper
    mock_client = MagicMock()
    mock_client.acquire_token_silent.return_value = None
    mock_client.acquire_token_for_client.return_value = {"access_token": "new-token"}

    manager = AuthenticationManager(auth_config, cache_manager=cache_manager, client=mock_client)

    token = manager.get_access_token(force_refresh=True)

    assert token == "new-token"
    mock_client.acquire_token_for_client.assert_called_once_with(
        scopes=["Scope.Read"],
        force_refresh=True,
    )
    cache_manager.persist.assert_called()  # type: ignore[attr-defined]


def test_get_access_token_raises_when_not_available(auth_config: AuthConfig) -> None:
    cache_manager = TokenCacheManager(auth_config.cache_path)
    mock_client = MagicMock()
    mock_client.acquire_token_silent.return_value = None
    mock_client.acquire_token_for_client.return_value = {"error": "invalid_client"}

    manager = AuthenticationManager(auth_config, cache_manager=cache_manager, client=mock_client)

    with pytest.raises(AuthenticationError):
        manager.get_access_token()
