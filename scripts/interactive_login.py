"""Command-line helper to sign in to Microsoft 365 using MSAL."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any

import requests  # type: ignore[import]
from dotenv import load_dotenv  # type: ignore[import]
from msal import (  # type: ignore[import]
    ConfidentialClientApplication,
    PublicClientApplication,
    SerializableTokenCache,
)

try:
    from src.auth.config import AuthConfig
except ImportError:
    # Fallback for running script directly
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from src.auth.config import AuthConfig


def build_client(config: AuthConfig) -> tuple[PublicClientApplication | ConfidentialClientApplication, SerializableTokenCache]:
    if config.cache_path:
        config.cache_path.parent.mkdir(parents=True, exist_ok=True)

    # Create a serializable token cache
    cache = SerializableTokenCache()

    # Load existing cache if available
    if config.cache_path and config.cache_path.exists():
        cache_data = config.cache_path.read_text(encoding="utf-8")
        if cache_data:
            cache.deserialize(cache_data)

    if config.client_secret:
        app = ConfidentialClientApplication(
            client_id=config.client_id,
            client_credential=config.client_secret,
            authority=config.authority,
            token_cache=cache,
        )
    else:
        app = PublicClientApplication(
            client_id=config.client_id,
            authority=config.authority,
            token_cache=cache,
        )

    return app, cache


def persist_cache(cache: SerializableTokenCache, cache_path: Path | None) -> None:
    if cache.has_state_changed and cache_path:
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        cache_data = cache.serialize()
        cache_path.write_text(cache_data, encoding="utf-8")


def acquire_token(app: PublicClientApplication | ConfidentialClientApplication, scopes: tuple[str, ...]) -> dict[str, Any]:
    accounts = app.get_accounts()
    if accounts:
        result = app.acquire_token_silent(scopes=list(scopes), account=accounts[0])
        if result and "access_token" in result:
            return result

    # ConfidentialClientApplication doesn't support device code flow
    if isinstance(app, ConfidentialClientApplication):
        raise RuntimeError(
            "Interactive device code flow requires a public client. "
            "Please remove AZURE_CLIENT_SECRET from .env, or configure your Azure app as a public client: "
            "Azure Portal → App Registrations → Authentication → Allow public client flows = Yes"
        )

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
    load_dotenv()

    try:
        config = AuthConfig.from_env()
    except Exception as exc:  # pragma: no cover - interactive script guard
        print(f"Configuration error: {exc}", file=sys.stderr)
        return 1

    graph_endpoint = os.environ.get("GRAPH_API_ENDPOINT", "https://graph.microsoft.com/v1.0")

    app, cache = build_client(config)
    try:
        result = acquire_token(app, config.scopes)
    except Exception as exc:  # pragma: no cover - interactive script guard
        print(f"Authentication failed: {exc}", file=sys.stderr)
        return 1
    finally:
        persist_cache(cache, config.cache_path)

    if "access_token" not in result:
        print("Failed to obtain access token.", file=sys.stderr)
        print(json.dumps(result, indent=2))
        return 1

    print("Authentication successful. Access token acquired.")
    try:
        profile = call_graph(graph_endpoint, result["access_token"])
    except Exception as exc:  # pragma: no cover - runtime external call
        print(f"Unable to query Microsoft Graph: {exc}", file=sys.stderr)
        return 0

    print("Signed-in user profile:")
    print(json.dumps(profile, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
