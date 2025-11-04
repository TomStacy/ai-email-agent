"""Command-line helper to sign in to Microsoft 365 using MSAL."""

from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

import requests  # type: ignore[import]
from dotenv import load_dotenv  # type: ignore[import]
from msal import PublicClientApplication  # type: ignore[import]

CACHE_PATH = Path("data/cache/msal_device_cache.json")


@dataclass(frozen=True, slots=True)
class AuthSettings:
    client_id: str
    authority: str
    scopes: tuple[str, ...]
    graph_endpoint: str


def load_settings() -> AuthSettings:
    load_dotenv()
    required_keys = ["AZURE_CLIENT_ID", "AZURE_TENANT_ID"]
    missing = [key for key in required_keys if not _get_env(key)]
    if missing:
        raise RuntimeError(f"Missing required environment variables: {', '.join(missing)}")

    authority = _get_env("AZURE_AUTHORITY") or (
        f"https://login.microsoftonline.com/{_get_env('AZURE_TENANT_ID')}"
    )
    scopes_raw = _get_env("AZURE_SCOPE") or "User.Read"
    scopes = tuple(scope.strip() for scope in scopes_raw.split() if scope.strip())
    endpoint = _get_env("GRAPH_API_ENDPOINT") or "https://graph.microsoft.com/v1.0"

    return AuthSettings(
        client_id=_get_env("AZURE_CLIENT_ID"),
        authority=authority,
        scopes=scopes,
        graph_endpoint=endpoint,
    )


def _get_env(name: str) -> str:
    value = os.environ.get(name, "").strip()
    return value


def build_client(settings: AuthSettings) -> PublicClientApplication:
    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    cache_state = CACHE_PATH.read_text(encoding="utf-8") if CACHE_PATH.exists() else ""

    app = PublicClientApplication(
        client_id=settings.client_id,
        authority=settings.authority,
    )

    deserialize = getattr(app.token_cache, "deserialize", None)
    if cache_state and callable(deserialize):
        deserialize(cache_state)

    return app


def persist_cache(app: PublicClientApplication) -> None:
    serialize = getattr(app.token_cache, "serialize", None)
    if not callable(serialize):
        return
    cache_state = cast(str, serialize())
    if cache_state:
        CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
        existing_state = CACHE_PATH.read_text(encoding="utf-8") if CACHE_PATH.exists() else ""
        if cache_state != existing_state:
            CACHE_PATH.write_text(cache_state, encoding="utf-8")
    elif CACHE_PATH.exists():
        CACHE_PATH.unlink()


def acquire_token(app: PublicClientApplication, scopes: tuple[str, ...]) -> dict[str, Any]:
    accounts = app.get_accounts()
    if accounts:
        result = app.acquire_token_silent(scopes=list(scopes), account=accounts[0])
        if result and "access_token" in result:
            return result

    flow = app.initiate_device_flow(scopes=list(scopes))
    if "user_code" not in flow:
        raise RuntimeError(f"Device code flow failed to start: {json.dumps(flow, indent=2)}")

    print("To authenticate, visit {verification_uri} and enter the code {user_code}.".format(**flow))
    print()

    return app.acquire_token_by_device_flow(flow)  # blocks until complete


def call_graph(endpoint: str, token: str) -> dict[str, Any]:
    response = requests.get(
        f"{endpoint.rstrip('/')}/me",
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
        },
        timeout=15,
    )
    response.raise_for_status()
    return response.json()


def main() -> int:
    try:
        settings = load_settings()
    except RuntimeError as exc:  # pragma: no cover - interactive script guard
        print(f"Configuration error: {exc}", file=sys.stderr)
        return 1

    app = build_client(settings)
    try:
        result = acquire_token(app, settings.scopes)
    except Exception as exc:  # pragma: no cover - interactive script guard
        print(f"Authentication failed: {exc}", file=sys.stderr)
        return 1
    finally:
        persist_cache(app)

    if "access_token" not in result:
        print("Failed to obtain access token.", file=sys.stderr)
        print(json.dumps(result, indent=2))
        return 1

    print("Authentication successful. Access token acquired.")
    try:
        profile = call_graph(settings.graph_endpoint, result["access_token"])
    except Exception as exc:  # pragma: no cover - runtime external call
        print(f"Unable to query Microsoft Graph: {exc}", file=sys.stderr)
        return 0

    print("Signed-in user profile:")
    print(json.dumps(profile, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
