# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

AI Email Agent is a Python-based email management tool that connects to Office 365 accounts to automate email organization using AI. It uses Microsoft Graph API for email operations and OpenAI API for intelligent classification and summarization.

**Current Status**: Early development phase - authentication module implemented, other modules (classifiers, operations, summarization) are placeholders.

## Development Commands

### Environment Setup
```bash
# Install all dependencies (creates .venv automatically)
uv sync

# Install with development dependencies
uv sync --group dev

# Activate virtual environment
source .venv/bin/activate  # macOS/Linux
.venv\Scripts\activate     # Windows
```

### Testing
```bash
# Run all tests with coverage
uv run pytest

# Run specific test file
uv run pytest tests/unit/auth/test_manager.py

# Run tests by marker
uv run pytest -m unit
uv run pytest -m integration

# Run without coverage checks (faster iteration)
uv run pytest --no-cov
```

**Coverage requirement**: 80% minimum (configured in pyproject.toml and pytest.ini)

### Code Quality
```bash
# Format code (run before commits)
uv run ruff format src/

# Lint with auto-fix
uv run ruff check --fix src/

# Type checking (strict mode enabled)
uv run mypy src/
```

**Important**: MyPy is configured with strict settings including `disallow_untyped_defs`. All new functions must have type annotations.

### Running the Application
```bash
# Main application entry point
uv run python main.py

# Interactive login script (authenticate to Microsoft 365)
uv run python scripts/interactive_login.py

# Test inbox scanning functionality (requires authentication first)
uv run python scripts/test_inbox_scanner.py
```

## Architecture

### Module Structure

**src/auth/** - OAuth 2.0 authentication (IMPLEMENTED)
- `manager.py`: Core `AuthenticationManager` class - orchestrates MSAL flows (auth code, client credentials, on-behalf-of)
- `graph_client.py`: `GraphApiClient` - HTTP client for Microsoft Graph with automatic token refresh and retry logic
- `token_cache.py`: Persistent token storage using MSAL's SerializableTokenCache
- `config.py`: Authentication configuration management
- `exceptions.py`: Custom exceptions (`AuthenticationError`, `GraphApiError`)

**src/email_client/** - Microsoft Graph email operations (IMPLEMENTED)
- `models.py`: Data models for Email, Folder, EmailAddress, EmailBody, ScanResult
- `folder_manager.py`: `FolderManager` - List and manage mailbox folders with caching
- `email_fetcher.py`: `EmailFetcher` - Fetch individual emails and attachments metadata
- `email_scanner.py`: `EmailScanner` - Scan inbox/folders with pagination, filtering, and progress tracking

**src/classifiers/** - AI and rule-based email classification (PLACEHOLDER)
- Future: OpenAI integration for solicitation detection

**src/operations/** - Email operations: move, delete, batch processing (PLACEHOLDER)

**src/summarization/** - AI-powered email summarization (PLACEHOLDER)

**src/utils/** - Shared utilities (PLACEHOLDER)

### Key Design Patterns

**Authentication Flow**:
1. `AuthenticationManager` wraps MSAL's `ConfidentialClientApplication`
2. Supports multiple flows: authorization code (interactive), client credentials (app-only), on-behalf-of
3. Token caching via `TokenCacheManager` for performance
4. `GraphApiClient` automatically handles 401 responses by refreshing tokens

**API Retry Strategy**:
- Configured in `GraphApiClient._build_session()` using `urllib3.Retry`
- Retries 5 times with exponential backoff (0.3s factor)
- Retries on: 429 (rate limit), 500, 502, 503, 504

**Email Scanning Flow**:
1. `FolderManager` lists and caches folder structure for quick lookup
2. `EmailScanner` uses generator pattern (`_fetch_email_pages`) for memory-efficient pagination
3. Uses OData `$select` to minimize payload size during scanning
4. Progress tracking with tqdm, configurable limits via environment variables
5. `EmailFetcher` retrieves full details on-demand (lazy loading pattern)

### Configuration

**Environment Variables** (see .env.example):
- `AZURE_CLIENT_ID`, `AZURE_CLIENT_SECRET`, `AZURE_TENANT_ID` - Azure app registration
- `AZURE_AUTHORITY` - Auth endpoint (default: https://login.microsoftonline.com/{tenant_id})
- `AZURE_SCOPE` - Graph API scopes (default: https://graph.microsoft.com/.default)
- `OPENAI_API_KEY`, `OPENAI_MODEL` - AI configuration
- `LOG_LEVEL`, `MAX_EMAILS_PER_SCAN`, `BATCH_SIZE` - Application settings
- `SCAN_BATCH_SIZE=50` - Number of emails to fetch per API page (default: 50)
- `INCLUDE_BODY_IN_SCAN=false` - Whether to fetch full email body during scanning (default: false)
- `DRY_RUN=true` - Safety flag for testing without making actual changes

**Microsoft Graph Permissions Required**:
- Mail.Read, Mail.ReadWrite, User.Read

## Testing Strategy

**Test Organization**:
- `tests/unit/auth/` - Authentication module tests (mocked MSAL and requests)
- `tests/unit/email_client/` - Email client module tests (mocked GraphApiClient)
- `tests/integration/` - End-to-end API tests (future)
- `tests/fixtures/` - Sample data (future)
- `scripts/test_inbox_scanner.py` - Manual integration test for inbox scanning

**Markers** (use with `pytest -m <marker>`):
- `unit` - Fast, isolated unit tests
- `integration` - Tests requiring external services
- `auth` - Authentication-related tests
- `api` - API integration tests
- `slow` - Long-running tests

**Mocking**:
- Use `pytest-mock` for dependency injection
- Mock MSAL's `ConfidentialClientApplication` in auth tests
- Mock `requests.Session` in graph_client tests

## Common Patterns

### Adding New Microsoft Graph API Methods
When extending `GraphApiClient`:
1. Use the existing `request()` method for HTTP calls
2. Handle pagination for list endpoints (see `fetch_messages()` example)
3. Include `scopes` parameter for custom permission requirements
4. Return typed data (not raw Response objects)

### Scanning Emails
When using `EmailScanner`:
1. Always use `show_progress=False` in tests to avoid tqdm output
2. Prefer `scan_inbox()` over `scan_folder()` when possible (uses cached folder lookup)
3. Use `scan_with_filter()` for OData queries (e.g., `"isRead eq false"`, `"importance eq 'high'"`)
4. Set `INCLUDE_BODY_IN_SCAN=false` for initial scans (fetch bodies on-demand with `EmailFetcher`)
5. Handle `ScanResult.has_more` flag when implementing pagination resumption

### Error Handling
- Raise `AuthenticationError` for auth failures
- Raise `GraphApiError` for API failures (includes status_code, message, error code, details)
- Log errors before raising for debugging

### Type Annotations
- Use `from __future__ import annotations` for forward references
- Use `collections.abc` types (Mapping, Sequence) instead of dict, list in signatures
- Use `str | None` syntax (not `Optional[str]`)
- Import types from `typing` only when needed (Any, TYPE_CHECKING)

## Important Notes

- **Security**: Never commit .env files. Use .env.example as template.
- **Rate Limiting**: Microsoft Graph API has rate limits. The retry adapter handles 429 responses automatically.
- **Token Management**: Tokens are cached in `data/token_cache.json` by default. Clear with `AuthenticationManager.clear_cache()`.
- **Package Management**: Use `uv add <package>` to add dependencies (automatically updates pyproject.toml and uv.lock).
- **Ruff Configuration**: Line length is 100 characters. Double quotes for strings. Spaces for indentation (4 spaces).

## Documentation References

- Setup instructions: docs/SETUP_GUIDE.md
- Architecture details: docs/PROJECT_STRUCTURE.md
- Technical requirements: docs/TECHNICAL_REQUIREMENTS.md
- Implementation roadmap: docs/IMPLEMENTATION_PLAN.md
