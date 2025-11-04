# AI Email Agent

An intelligent Python-based email management tool that connects to Office 365 accounts to automate email organization and provide smart summaries of important communications.

## Features

- 🔐 **Secure Office 365 Integration** - OAuth 2.0 authentication with Microsoft Graph API
- 🤖 **AI-Powered Classification** - Intelligent detection of solicitation and promotional emails
- 📧 **Smart Email Operations** - Move, delete, or archive emails automatically
- 📊 **Email Summarization** - Generate concise summaries of important emails
- ⚙️ **Customizable Rules** - Define your own classification and processing rules
- 🔒 **Privacy First** - All processing happens locally, no email content stored

## Quick Start

### Prerequisites

- Python 3.11+
- [uv](https://github.com/astral-sh/uv) - Fast Python package installer
- Office 365 account
- Azure account (for app registration)
- OpenAI API key

### Installation

1. Clone the repository:

```bash
git clone <repository-url>
cd ai-email-agent
```

1. Install uv (if not already installed):

```bash
# Windows (PowerShell)
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh
```

1. Create the project environment and install dependencies:

```bash
# Create .venv and install runtime dependencies from pyproject.toml
uv sync

# Include development tooling (linting, tests, typing)
uv sync --group dev

# If you need to work from the requirements files instead
uv pip sync requirements.txt
uv pip sync requirements-dev.txt
```

`uv sync` automatically provisions the `.venv` directory and keeps it aligned with the
declared dependencies, as outlined in the [uv documentation](https://docs.astral.sh/uv/uv/#manage-python-projects-with-uv).

1. Activate virtual environment:

```bash
# Windows
.venv\Scripts\activate

# macOS/Linux
source .venv/bin/activate
```

1. Follow the [Setup Guide](docs/SETUP_GUIDE.md) for complete configuration instructions.

## Development

### Running Tests

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=src

# Run specific test file
uv run pytest tests/unit/test_auth.py
```

### Code Quality

```bash
# Format code with ruff
uv run ruff format src/

# Lint code
uv run ruff check src/

# Fix auto-fixable issues
uv run ruff check --fix src/

# Type checking
uv run mypy src/
```

### Running the Application

```bash
# Run main application
uv run python src/main.py

# Run specific scripts
uv run python scripts/test_config.py
```

## Documentation

- [Project Overview](docs/PROJECT_OVERVIEW.md) - High-level project description and goals
- [Technical Requirements](docs/TECHNICAL_REQUIREMENTS.md) - Detailed technical specifications
- [Implementation Plan](docs/IMPLEMENTATION_PLAN.md) - Development roadmap and timeline
- [Project Structure](docs/PROJECT_STRUCTURE.md) - Code organization and architecture
- [Setup Guide](docs/SETUP_GUIDE.md) - Step-by-step setup instructions

## Project Status

🚧 **Currently in Development** - Phase 1: Foundation and Setup

See the [Implementation Plan](docs/IMPLEMENTATION_PLAN.md) for the complete development timeline.

## Technology Stack

- **Python 3.11+** - Core language
- **uv** - Fast package management and task runner
- **Microsoft Graph API** - Office 365 integration
- **OpenAI API** - AI classification and summarization
- **MSAL** - Microsoft authentication
- **pytest** - Testing framework
- **ruff** - Fast Python linter and formatter

## Security

- OAuth 2.0 authentication
- No plain text storage of email content
- Secure credential management
- Audit logging for all operations

See [Technical Requirements](docs/TECHNICAL_REQUIREMENTS.md) for complete security details.

## Contributing

This project is currently in active development. Contribution guidelines will be added soon.

## License

[To be determined]

## Support

For issues and questions, please check the [Setup Guide](docs/SETUP_GUIDE.md) troubleshooting section.
