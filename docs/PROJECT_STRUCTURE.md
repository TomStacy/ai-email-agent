# Project Structure

## Directory Organization

```
ai-email-agent/
│
├── src/
│   ├── __init__.py
│   │
│   ├── auth/
│   │   ├── __init__.py
│   │   ├── authenticator.py          # OAuth 2.0 authentication
│   │   ├── token_manager.py          # Token caching and refresh
│   │   └── credentials.py            # Credential management
│   │
│   ├── email_client/
│   │   ├── __init__.py
│   │   ├── graph_client.py           # Microsoft Graph API client
│   │   ├── email_scanner.py          # Inbox scanning logic
│   │   ├── email_fetcher.py          # Email retrieval
│   │   └── models.py                 # Email data models
│   │
│   ├── classifiers/
│   │   ├── __init__.py
│   │   ├── ai_classifier.py          # AI-based classification
│   │   ├── rule_classifier.py        # Rule-based classification
│   │   ├── solicitation_detector.py  # Solicitation detection
│   │   └── prompts.py                # AI prompt templates
│   │
│   ├── operations/
│   │   ├── __init__.py
│   │   ├── email_mover.py            # Move email operations
│   │   ├── email_deleter.py          # Delete email operations
│   │   ├── folder_manager.py         # Folder management
│   │   ├── batch_processor.py        # Batch processing
│   │   └── operation_logger.py       # Operation logging
│   │
│   ├── summarization/
│   │   ├── __init__.py
│   │   ├── summarizer.py             # Email summarization
│   │   ├── digest_generator.py       # Daily digest creation
│   │   ├── priority_detector.py      # Priority email detection
│   │   └── action_extractor.py       # Action item extraction
│   │
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── config.py                 # Configuration management
│   │   ├── logger.py                 # Logging setup
│   │   ├── cache.py                  # Caching utilities
│   │   ├── rate_limiter.py           # API rate limiting
│   │   └── helpers.py                # Helper functions
│   │
│   └── main.py                       # Main application entry
│
├── tests/
│   ├── __init__.py
│   ├── conftest.py                   # Pytest configuration
│   │
│   ├── unit/
│   │   ├── test_auth.py
│   │   ├── test_email_client.py
│   │   ├── test_classifiers.py
│   │   ├── test_operations.py
│   │   └── test_summarization.py
│   │
│   ├── integration/
│   │   ├── test_graph_api.py
│   │   ├── test_openai_api.py
│   │   └── test_workflows.py
│   │
│   └── fixtures/
│       ├── sample_emails.json
│       └── mock_responses.json
│
├── config/
│   ├── settings.yaml                 # Application settings
│   ├── rules.json                    # Classification rules
│   └── logging.yaml                  # Logging configuration
│
├── docs/
│   ├── PROJECT_OVERVIEW.md
│   ├── TECHNICAL_REQUIREMENTS.md
│   ├── IMPLEMENTATION_PLAN.md
│   ├── PROJECT_STRUCTURE.md
│   ├── API_DOCUMENTATION.md
│   ├── USER_GUIDE.md
│   ├── SETUP_GUIDE.md
│   └── architecture/
│       ├── system_design.md
│       └── diagrams/
│
├── data/
│   ├── cache/                        # Cached data
│   ├── logs/                         # Log files
│   └── .gitkeep
│
├── scripts/
│   ├── setup.py                      # Setup script
│   ├── run_scanner.py                # Run email scanner
│   ├── run_cleanup.py                # Run cleanup operations
│   └── generate_summary.py           # Generate email summary
│
├── .env.example                      # Example environment variables
├── .gitignore                        # Git ignore file
├── requirements.txt                  # Python dependencies
├── requirements-dev.txt              # Development dependencies
├── pytest.ini                        # Pytest configuration
├── setup.py                          # Package setup
└── README.md                         # Project README
```

---

## Module Descriptions

### Authentication Module (`src/auth/`)

**authenticator.py**
- Implements OAuth 2.0 flow for Microsoft Graph API
- Handles device code flow and authorization code flow
- Manages user authentication state

**token_manager.py**
- Handles token storage and retrieval
- Implements token refresh logic
- Manages token expiration

**credentials.py**
- Secure credential storage
- Environment variable management
- Credential validation

---

### Email Client Module (`src/email_client/`)

**graph_client.py**
- Base client for Microsoft Graph API
- HTTP request handling with retries
- Error handling and logging
- Rate limiting implementation

**email_scanner.py**
- Scans inbox and folders
- Implements pagination
- Filters emails by criteria
- Manages scan state

**email_fetcher.py**
- Fetches individual emails
- Retrieves email metadata
- Extracts email body and attachments
- Handles different email formats

**models.py**
- Email data models (Pydantic or dataclasses)
- Folder models
- Classification result models
- Operation result models

---

### Classifiers Module (`src/classifiers/`)

**ai_classifier.py**
- OpenAI API integration
- AI-based email classification
- Prompt management
- Response parsing

**rule_classifier.py**
- Rule-based classification logic
- Keyword matching
- Sender domain analysis
- Pattern recognition

**solicitation_detector.py**
- Combines AI and rule-based detection
- Implements classification pipeline
- Confidence scoring
- Result caching

**prompts.py**
- AI prompt templates
- Prompt versioning
- Few-shot examples
- Prompt optimization utilities

---

### Operations Module (`src/operations/`)

**email_mover.py**
- Move emails between folders
- Batch move operations
- Undo functionality
- Error recovery

**email_deleter.py**
- Soft delete (move to deleted items)
- Permanent delete
- Batch delete
- Safety checks

**folder_manager.py**
- List and search folders
- Create new folders
- Manage folder hierarchy
- Folder operations

**batch_processor.py**
- Batch processing engine
- Progress tracking
- Resumable operations
- Parallel processing support

**operation_logger.py**
- Log all operations
- Transaction history
- Audit trail
- Operation replay

---

### Summarization Module (`src/summarization/`)

**summarizer.py**
- Single email summarization
- Batch summarization
- Summary caching
- Multiple summary formats

**digest_generator.py**
- Daily digest creation
- Weekly summaries
- Custom time range summaries
- Template rendering

**priority_detector.py**
- Importance scoring
- Urgency detection
- Priority rules
- VIP sender detection

**action_extractor.py**
- Extract action items
- Deadline detection
- Task categorization
- Action item formatting

---

### Utilities Module (`src/utils/`)

**config.py**
- Configuration loading
- Settings validation
- Environment variable handling
- Configuration merging

**logger.py**
- Logging setup
- Log formatting
- Log rotation
- Contextual logging

**cache.py**
- Local caching implementation
- Cache invalidation
- Cache statistics
- Memory management

**rate_limiter.py**
- API rate limit tracking
- Request throttling
- Backoff strategies
- Rate limit reporting

**helpers.py**
- Common utility functions
- Data parsing helpers
- String manipulation
- Date/time utilities

---

## Configuration Files

### `.env.example`
Template for environment variables including:
- Azure credentials
- OpenAI API key
- Application settings
- Feature flags

### `config/settings.yaml`
Application settings including:
- Email processing preferences
- Folder mappings
- Automation schedules
- User preferences

### `config/rules.json`
Classification rules including:
- Keyword lists
- Domain patterns
- Custom rules
- Priority definitions

### `pyproject.toml`
Project configuration including:
- Project metadata and dependencies
- Ruff configuration (linting and formatting)
- MyPy type checking settings
- Pytest configuration (test discovery, coverage, markers)

---

## Key Design Patterns

### Authentication
- **Singleton Pattern**: Single authenticator instance
- **Token Caching**: Persistent token storage
- **Auto-refresh**: Automatic token renewal

### Email Client
- **Repository Pattern**: Abstract data access
- **Retry Logic**: Exponential backoff
- **Pagination**: Efficient large dataset handling

### Classification
- **Strategy Pattern**: Pluggable classifiers
- **Pipeline Pattern**: Sequential processing
- **Factory Pattern**: Classifier creation

### Operations
- **Command Pattern**: Operation encapsulation
- **Transaction Pattern**: Rollback support
- **Observer Pattern**: Operation monitoring

### Summarization
- **Template Method**: Customizable summaries
- **Cache Aside**: Result caching
- **Factory Pattern**: Summary format creation

---

## Development Workflow

1. **Feature Development**
   - Create feature branch
   - Implement functionality
   - Write unit tests
   - Update documentation

2. **Code Review**
   - Format code: `uv run ruff format src/`
   - Lint code: `uv run ruff check --fix src/`
   - Type check: `uv run mypy src/`
   - Review test coverage
   - Check documentation
   - Merge to main

3. **Testing**
   - Run unit tests: `uv run pytest tests/unit/`
   - Run integration tests: `uv run pytest tests/integration/`
   - Run all tests: `uv run pytest`
   - Check coverage: `uv run pytest --cov=src`
   - Manual testing
   - Performance testing

4. **Deployment**
   - Update version
   - Create release notes
   - Tag release
   - Deploy to production
