from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest  # type: ignore[import]

from src.auth.exceptions import TokenCacheError
from src.auth.token_cache import TokenCacheManager


def test_persist_writes_when_cache_changed(tmp_path: Path) -> None:
    cache_file = tmp_path / "cache.json"
    manager = TokenCacheManager(cache_file)
    manager._cache = MagicMock()  # type: ignore[attr-defined]  # pragma: no cover - test helper
    manager._cache.has_state_changed = True
    manager._cache.serialize.return_value = "{}"

    manager.persist()

    assert cache_file.read_text(encoding="utf-8") == "{}"


def test_load_invalid_state_raises(tmp_path: Path) -> None:
    cache_file = tmp_path / "cache.json"
    cache_file.write_text("not-json", encoding="utf-8")

    with pytest.raises(TokenCacheError):
        TokenCacheManager(cache_file)
