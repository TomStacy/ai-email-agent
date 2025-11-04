from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any
from unittest.mock import MagicMock

import pytest  # type: ignore[import]

from src.auth.exceptions import GraphApiError
from src.auth.graph_client import GraphApiClient


@dataclass
class DummyResponse:
    status_code: int
    payload: Any = None
    reason: str = ""

    def __post_init__(self) -> None:
        if self.reason:
            return
        if 200 <= self.status_code < 300:
            self.reason = "OK"
        else:
            self.reason = "Error"

    @property
    def ok(self) -> bool:
        return 200 <= self.status_code < 300

    @property
    def content(self) -> bytes:
        if self.payload is None:
            return b""
        return json.dumps(self.payload).encode("utf-8")

    @property
    def text(self) -> str:
        if self.payload is None:
            return ""
        return json.dumps(self.payload)

    def json(self) -> Any:
        if self.payload is None:
            raise json.JSONDecodeError("no payload", "", 0)
        return self.payload


def test_request_returns_payload() -> None:
    auth_manager = MagicMock()
    auth_manager.config.timeout = 10
    auth_manager.get_access_token.return_value = "token"
    session = MagicMock()
    session.request.return_value = DummyResponse(200, {"value": []})

    client = GraphApiClient(auth_manager, session=session)

    payload = client.request("GET", "/me/messages")

    assert payload == {"value": []}
    session.request.assert_called_once()


def test_request_refreshes_after_unauthorized() -> None:
    auth_manager = MagicMock()
    auth_manager.config.timeout = 10
    auth_manager.get_access_token.side_effect = ["expired", "fresh"]
    session = MagicMock()
    session.request.side_effect = iter([
        DummyResponse(401, {"error": {"code": "InvalidAuthenticationToken"}}),
        DummyResponse(200, {"id": "123"}),
    ])

    client = GraphApiClient(auth_manager, session=session)

    payload = client.request("GET", "/me")

    assert payload == {"id": "123"}
    assert auth_manager.get_access_token.call_count == 2


def test_request_raises_graph_api_error() -> None:
    auth_manager = MagicMock()
    auth_manager.config.timeout = 10
    auth_manager.get_access_token.return_value = "token"
    session = MagicMock()
    session.request.return_value = DummyResponse(
        429,
        {"error": {"code": "TooManyRequests", "message": "Retry later", "retry-after": 5}},
    )

    client = GraphApiClient(auth_manager, session=session)

    with pytest.raises(GraphApiError) as exc:
        client.request("GET", "/me")

    assert exc.value.status_code == 429
    assert exc.value.error == "TooManyRequests"
    assert exc.value.details == {"retry-after": 5}


def test_fetch_messages_parses_value_list() -> None:
    auth_manager = MagicMock()
    auth_manager.config.timeout = 10
    auth_manager.get_access_token.return_value = "token"
    session = MagicMock()
    session.request.return_value = DummyResponse(200, {"value": [{"id": "1"}, {"id": "2"}]})

    client = GraphApiClient(auth_manager, session=session)

    messages = client.fetch_messages(top=5, select=["id"])

    assert [message["id"] for message in messages] == ["1", "2"]
    session.request.assert_called_with(
        "GET",
        "https://graph.microsoft.com/v1.0/me/messages",
        params={"$top": 5, "$select": "id"},
        json=None,
        headers={
            "Authorization": "Bearer token",
            "Accept": "application/json",
        },
        timeout=10,
    )
