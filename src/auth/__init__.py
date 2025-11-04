"""Authentication module for Office 365 OAuth 2.0."""

from .config import DEFAULT_SCOPE, AuthConfig
from .exceptions import AuthenticationError, ConfigurationError, GraphApiError, TokenCacheError
from .graph_client import GraphApiClient
from .manager import AuthenticationManager
from .token_cache import TokenCacheManager

__all__ = [
    "AuthConfig",
    "DEFAULT_SCOPE",
    "AuthenticationError",
    "ConfigurationError",
    "GraphApiClient",
    "GraphApiError",
    "TokenCacheError",
    "AuthenticationManager",
    "TokenCacheManager",
]
