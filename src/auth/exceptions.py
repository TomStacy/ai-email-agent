"""Custom exceptions for the authentication subsystem."""

from __future__ import annotations

from dataclasses import dataclass


class ConfigurationError(ValueError):
    """Raised when authentication settings are missing or invalid."""


class AuthenticationError(RuntimeError):
    """Raised when the Microsoft identity platform cannot issue a token."""


class TokenCacheError(RuntimeError):
    """Raised when a token cache cannot be loaded or persisted."""


@dataclass(slots=True)
class GraphApiError(RuntimeError):
    """Represents an error returned by the Microsoft Graph API."""

    status_code: int
    message: str
    error: str | None = None
    details: dict[str, object] | None = None

    def __str__(self) -> str:  # pragma: no cover - trivial formatting
        parts = [f"Graph API request failed ({self.status_code})"]
        if self.error:
            parts.append(f"error={self.error}")
        parts.append(f"message={self.message}")
        if self.details:
            parts.append(f"details={self.details}")
        return " | ".join(parts)
