"""Persistence helpers around ``msal.SerializableTokenCache``."""

from __future__ import annotations

import json
import threading
from pathlib import Path

from msal import SerializableTokenCache  # type: ignore[import]

from .exceptions import TokenCacheError


class TokenCacheManager:
    """Wraps an ``msal.SerializableTokenCache`` with file persistence."""

    def __init__(self, cache_path: Path | None = None) -> None:
        self._cache = SerializableTokenCache()
        self._cache_path = cache_path
        self._lock = threading.Lock()
        if self._cache_path:
            self._cache_path.parent.mkdir(parents=True, exist_ok=True)
            self._load()

    @property
    def cache(self) -> SerializableTokenCache:
        return self._cache

    def _load(self) -> None:
        if not self._cache_path or not self._cache_path.exists():
            return
        try:
            raw_state = self._cache_path.read_text(encoding="utf-8")
            if raw_state:
                self._cache.deserialize(raw_state)
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            raise TokenCacheError(f"Failed to load token cache: {exc}") from exc

    def persist(self) -> None:
        if not self._cache_path or not self._cache.has_state_changed:
            return
        data = self._cache.serialize()
        try:
            with self._lock:
                self._cache_path.write_text(data, encoding="utf-8")
        except OSError as exc:
            raise TokenCacheError(f"Failed to persist token cache: {exc}") from exc

    def clear(self) -> None:
        with self._lock:
            self._cache.clear()
            if self._cache_path and self._cache_path.exists():
                try:
                    self._cache_path.unlink()
                except OSError as exc:
                    raise TokenCacheError(f"Failed to clear token cache: {exc}") from exc
