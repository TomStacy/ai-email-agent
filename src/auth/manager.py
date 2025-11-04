"""Core authentication manager built on top of MSAL."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from msal import ConfidentialClientApplication  # type: ignore[import]

from .config import AuthConfig
from .exceptions import AuthenticationError
from .token_cache import TokenCacheManager


class AuthenticationManager:
    """Central orchestrator for OAuth 2.0 flows with the Microsoft identity platform."""

    def __init__(
        self,
        config: AuthConfig,
        cache_manager: TokenCacheManager | None = None,
        client: ConfidentialClientApplication | None = None,
    ) -> None:
        self._config = config
        self._cache_manager = cache_manager or TokenCacheManager(config.cache_path)
        self._client = client or ConfidentialClientApplication(
            client_id=config.client_id,
            client_credential=config.client_secret,
            authority=config.authority,
            token_cache=self._cache_manager.cache,
        )

    @property
    def config(self) -> AuthConfig:
        return self._config

    def get_authorization_request_url(
        self,
        scopes: Sequence[str] | None = None,
        redirect_uri: str | None = None,
        state: str | None = None,
        **kwargs: Any,
    ) -> str:
        """Create an authorization URL for the auth-code flow."""

        target_scopes = list(scopes or self._config.scopes)
        return self._client.get_authorization_request_url(
            scopes=target_scopes,
            redirect_uri=redirect_uri,
            state=state,
            **kwargs,
        )

    def acquire_token_by_authorization_code(
        self,
        code: str,
        scopes: Sequence[str] | None = None,
        redirect_uri: str | None = None,
    ) -> Mapping[str, Any]:
        """Exchange an authorization code for tokens."""

        target_scopes = list(scopes or self._config.scopes)
        result = self._client.acquire_token_by_authorization_code(
            code=code,
            scopes=target_scopes,
            redirect_uri=redirect_uri,
        )
        self._cache_manager.persist()
        return result

    def initiate_auth_code_flow(
        self,
        scopes: Sequence[str] | None = None,
        redirect_uri: str | None = None,
        **kwargs: Any,
    ) -> Mapping[str, Any]:
        """Kick off an authorization code flow and return the flow parameters."""

        target_scopes = list(scopes or self._config.scopes)
        return self._client.initiate_auth_code_flow(
            scopes=target_scopes,
            redirect_uri=redirect_uri,
            **kwargs,
        )

    def get_access_token(
        self,
        scopes: Sequence[str] | None = None,
        force_refresh: bool = False,
    ) -> str:
        """Acquire an access token, using the cache when possible."""

        target_scopes = list(scopes or self._config.scopes)
        result: Mapping[str, Any] | None = None
        if not force_refresh:
            result = self._client.acquire_token_silent(
                scopes=target_scopes,
                account=None,
            )
        if not result:
            result = self._client.acquire_token_for_client(
                scopes=target_scopes,
                force_refresh=force_refresh,
            )
        if not result or "access_token" not in result:
            error = result.get("error") if isinstance(result, Mapping) else None
            description = result.get("error_description") if isinstance(result, Mapping) else None
            raise AuthenticationError(
                "Failed to acquire access token"
                + (f": {error} - {description}" if error or description else "")
            )
        self._cache_manager.persist()
        return str(result["access_token"])

    def clear_cache(self) -> None:
        self._cache_manager.clear()

    def acquire_on_behalf_of(
        self,
        user_assertion: str,
        scopes: Sequence[str],
    ) -> Mapping[str, Any]:
        """Acquire a token using the on-behalf-of flow."""

        result = self._client.acquire_token_on_behalf_of(
            user_assertion=user_assertion,
            scopes=list(scopes),
        )
        if "access_token" not in result:
            raise AuthenticationError(
                "Failed to acquire on-behalf-of token: "
                f"{result.get('error')}: {result.get('error_description')}"
            )
        self._cache_manager.persist()
        return result
