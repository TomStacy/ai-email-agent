"""HTTP client for Microsoft Graph built on ``requests``."""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from typing import Any
from urllib.parse import urljoin

import requests  # type: ignore[import]
from requests import Response  # type: ignore[import]
from requests.adapters import HTTPAdapter  # type: ignore[import]
from urllib3.util.retry import Retry  # type: ignore[import]

from .exceptions import GraphApiError
from .manager import AuthenticationManager

DEFAULT_GRAPH_BASE_URL = "https://graph.microsoft.com/v1.0/"
_DEFAULT_ALLOWED_METHODS = frozenset({"GET", "POST", "PATCH", "DELETE", "PUT"})


class GraphApiClient:
    """Typed wrapper around Microsoft Graph requests."""

    def __init__(
        self,
        auth_manager: AuthenticationManager,
        base_url: str = DEFAULT_GRAPH_BASE_URL,
        timeout: float | None = None,
        session: requests.Session | None = None,
    ) -> None:
        self._auth_manager = auth_manager
        self._base_url = base_url if base_url.endswith("/") else f"{base_url}/"
        self._timeout = timeout or auth_manager.config.timeout
        self._session = session or self._build_session()

    def _build_session(self) -> requests.Session:
        session = requests.Session()
        retry = Retry(
            total=5,
            backoff_factor=0.3,
            status_forcelist=(429, 500, 502, 503, 504),
            allowed_methods=_DEFAULT_ALLOWED_METHODS,
        )
        adapter = HTTPAdapter(max_retries=retry)
        session.mount("https://", adapter)
        session.mount("http://", adapter)
        return session

    def request(
        self,
        method: str,
        path: str,
        *,
        params: Mapping[str, Any] | None = None,
        json_body: Mapping[str, Any] | Sequence[Any] | None = None,
        headers: Mapping[str, str] | None = None,
        scopes: Sequence[str] | None = None,
        timeout: float | None = None,
    ) -> Any:
        url = self._build_url(path)
        token = self._auth_manager.get_access_token(scopes=scopes)
        request_headers = self._prepare_headers(headers, token)
        response = self._send_request(
            method,
            url,
            params=params,
            json_body=json_body,
            headers=request_headers,
            timeout=timeout,
        )
        if response.status_code == 401:
            # Token may be expired; retry once with a fresh token.
            token = self._auth_manager.get_access_token(scopes=scopes, force_refresh=True)
            request_headers = self._prepare_headers(headers, token)
            response = self._send_request(
                method,
                url,
                params=params,
                json_body=json_body,
                headers=request_headers,
                timeout=timeout,
            )
        return self._handle_response(response)

    def fetch_messages(
        self,
        user_id: str | None = None,
        *,
        folder: str | None = None,
        top: int | None = 25,
        select: Sequence[str] | None = None,
        filters: Mapping[str, Any] | None = None,
        scopes: Sequence[str] | None = None,
    ) -> list[Mapping[str, Any]]:
        mailbox_segment = "me" if not user_id else f"users/{user_id}"
        if folder:
            path = f"{mailbox_segment}/mailFolders/{folder}/messages"
        else:
            path = f"{mailbox_segment}/messages"
        params: dict[str, Any] = {}
        if top:
            params["$top"] = top
        if select:
            params["$select"] = ",".join(select)
        if filters:
            params.update(filters)
        result = self.request(
            "GET",
            path,
            params=params,
            scopes=scopes,
        )
        value = result.get("value") if isinstance(result, Mapping) else None
        if isinstance(value, list):
            return [item for item in value if isinstance(item, Mapping)]
        return []

    def _send_request(
        self,
        method: str,
        url: str,
        *,
        params: Mapping[str, Any] | None,
        json_body: Mapping[str, Any] | Sequence[Any] | None,
        headers: Mapping[str, str],
        timeout: float | None,
    ) -> Response:
        return self._session.request(
            method,
            url,
            params=params,
            json=json_body,
            headers=dict(headers),
            timeout=timeout or self._timeout,
        )

    def _handle_response(self, response: Response) -> Any:
        if response.ok:
            return self._parse_json(response)
        message = response.reason or "Unexpected response"
        payload = self._parse_json(response)
        error = None
        details = None
        if isinstance(payload, Mapping):
            error_body = payload.get("error")
            if isinstance(error_body, Mapping):
                error = str(error_body.get("code")) if error_body.get("code") else None
                message = str(error_body.get("message", message))
                details = {
                    key: value
                    for key, value in error_body.items()
                    if key not in {"code", "message"}
                }
        raise GraphApiError(
            status_code=response.status_code,
            message=message,
            error=error,
            details=details,
        )

    @staticmethod
    def _prepare_headers(headers: Mapping[str, str] | None, token: str) -> Mapping[str, str]:
        merged = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
        }
        if headers:
            merged.update(headers)
        return merged

    def _build_url(self, path: str) -> str:
        trimmed = path.lstrip("/")
        return urljoin(self._base_url, trimmed)

    @staticmethod
    def _parse_json(response: Response) -> Any:
        try:
            if not response.content:
                return None
            return response.json()
        except json.JSONDecodeError:
            return response.text
