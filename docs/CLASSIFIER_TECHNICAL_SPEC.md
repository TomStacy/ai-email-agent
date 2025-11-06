# Email Classifier - Technical Specification

**Version**: 1.0
**Phase**: MVP (Phase 1 - Weeks 3-4)
**Status**: Planning
**Last Updated**: 2025-11-05

---

## Overview

This document provides detailed technical specifications for implementing the Email Classification module. It covers data models, database schemas, configuration formats, API contracts, and AI prompt templates needed for MVP development.

**Related Documents**:
- Design Document: `CLASSIFIER_DESIGN.md`
- Implementation Plan: `IMPLEMENTATION_PLAN.md`
- Project Structure: `PROJECT_STRUCTURE.md`

---

## Table of Contents

1. [Data Models](#data-models)
2. [Database Schema](#database-schema)
3. [Configuration Files](#configuration-files)
4. [AI Prompt Templates](#ai-prompt-templates)
5. [Module Interfaces](#module-interfaces)
6. [Error Handling](#error-handling)
7. [Logging Strategy](#logging-strategy)
8. [Testing Strategy](#testing-strategy)

---

## Data Models

### Core Classification Models

#### Email Input Model

```python
@dataclass
class EmailInput:
    """Email data to be classified"""
    email_id: str                    # Microsoft Graph message ID
    sender: str                      # Email address
    sender_name: str                 # Display name
    sender_domain: str               # Extracted domain
    subject: str                     # Email subject
    body_preview: str                # First 500 chars of body
    received_datetime: datetime      # When email was received

    # Metadata
    has_attachments: bool
    attachment_types: list[str]      # ["pdf", "docx", etc.]
    importance: str                  # "low", "normal", "high"
    is_read: bool

    # Thread information
    conversation_id: str
    is_reply: bool                   # User is in To/CC/BCC
    user_is_sender: bool             # User sent this email

    # Headers
    has_unsubscribe_link: bool
    reply_to: str | None
```

#### Classification Result Model

```python
@dataclass
class ClassificationResult:
    """Result of email classification"""
    email_id: str
    primary_category: str            # One of: important, solicitation, newsletter, transactional, normal
    secondary_categories: list[str]   # Additional tags
    confidence: float                # 0.0 - 1.0
    classification_method: str       # "vip", "blocked", "rule", "ai", "hybrid"

    # Details
    matched_rule: str | None         # Which rule matched (if rule-based)
    ai_reasoning: str | None         # AI explanation (if AI-based)
    processing_time_ms: int          # Time taken to classify
    timestamp: datetime              # When classified

    # Rule/AI scores (for hybrid)
    rule_confidence: float | None
    ai_confidence: float | None

    def to_dict(self) -> dict:
        """Convert to dictionary for storage"""
        ...

    @classmethod
    def from_dict(cls, data: dict) -> 'ClassificationResult':
        """Load from dictionary"""
        ...
```

#### User Feedback Model

```python
@dataclass
class UserFeedback:
    """User correction to classification"""
    feedback_id: str                 # UUID
    email_id: str
    sender: str
    sender_domain: str

    # Original classification
    original_primary: str
    original_secondary: list[str]
    original_confidence: float
    original_method: str

    # User correction
    corrected_primary: str
    corrected_secondary: list[str] | None

    # Metadata
    timestamp: datetime
    user_comment: str | None         # Optional user notes
```

#### VIP Sender Model

```python
@dataclass
class VIPSender:
    """VIP sender configuration"""
    identifier: str                  # Email or domain
    identifier_type: str             # "email", "domain", "pattern"
    priority_level: str              # "vip", "trusted", "monitored"
    custom_category: str | None      # Override category if specified
    never_auto_delete: bool          # Safety flag
    notes: str | None                # User notes
```

#### Category Rule Model

```python
@dataclass
class CategoryRule:
    """Rule for category classification"""
    rule_id: str
    category: str
    confidence_threshold: float      # Minimum confidence to apply

    # Matching criteria
    keywords_subject: list[str]      # Keywords in subject
    keywords_body: list[str]         # Keywords in body
    sender_patterns: list[str]       # Sender email/domain patterns

    # Boolean conditions
    has_unsubscribe_link: bool | None
    has_attachments: bool | None
    attachment_types: list[str] | None

    # Metadata
    enabled: bool
    priority: int                    # Higher priority rules checked first
```

#### Cached Classification Model

```python
@dataclass
class CachedClassification:
    """Cached classification for sender"""
    cache_key: str                   # sender_domain or sender_email
    primary_category: str
    secondary_categories: list[str]
    confidence: float
    method: str

    # Cache metadata
    cached_at: datetime
    expires_at: datetime             # cached_at + 90 days
    hit_count: int                   # How many times used
    last_used: datetime
```

---

## Database Schema

### SQLite Database: `classifications.db`

#### Table: classifications

```sql
CREATE TABLE classifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email_id TEXT NOT NULL UNIQUE,
    sender TEXT NOT NULL,
    sender_domain TEXT NOT NULL,
    subject TEXT,

    -- Classification results
    primary_category TEXT NOT NULL,
    secondary_categories TEXT,        -- JSON array
    confidence REAL NOT NULL,
    classification_method TEXT NOT NULL,

    -- Details
    matched_rule TEXT,
    ai_reasoning TEXT,
    rule_confidence REAL,
    ai_confidence REAL,
    processing_time_ms INTEGER,

    -- Metadata
    classified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Indexes
    INDEX idx_sender (sender),
    INDEX idx_sender_domain (sender_domain),
    INDEX idx_primary_category (primary_category),
    INDEX idx_classified_at (classified_at)
);
```

#### Table: user_feedback

```sql
CREATE TABLE user_feedback (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    feedback_id TEXT NOT NULL UNIQUE,
    email_id TEXT NOT NULL,
    sender TEXT NOT NULL,
    sender_domain TEXT NOT NULL,

    -- Original classification
    original_primary TEXT NOT NULL,
    original_secondary TEXT,          -- JSON array
    original_confidence REAL,
    original_method TEXT,

    -- User correction
    corrected_primary TEXT NOT NULL,
    corrected_secondary TEXT,         -- JSON array
    user_comment TEXT,

    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Indexes
    INDEX idx_sender_domain (sender_domain),
    INDEX idx_corrected_primary (corrected_primary),
    INDEX idx_created_at (created_at),

    -- Foreign key
    FOREIGN KEY (email_id) REFERENCES classifications(email_id)
);
```

#### Table: classification_cache

```sql
CREATE TABLE classification_cache (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cache_key TEXT NOT NULL UNIQUE,   -- sender_domain or sender_email
    key_type TEXT NOT NULL,           -- "domain" or "email"

    -- Cached classification
    primary_category TEXT NOT NULL,
    secondary_categories TEXT,         -- JSON array
    confidence REAL NOT NULL,
    method TEXT NOT NULL,

    -- Cache metadata
    cached_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL,
    hit_count INTEGER DEFAULT 0,
    last_used TIMESTAMP,

    -- Indexes
    INDEX idx_cache_key (cache_key),
    INDEX idx_expires_at (expires_at)
);
```

#### Table: vip_senders

```sql
CREATE TABLE vip_senders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    identifier TEXT NOT NULL UNIQUE,   -- Email or domain
    identifier_type TEXT NOT NULL,     -- "email", "domain", "pattern"
    priority_level TEXT NOT NULL,      -- "vip", "trusted", "monitored"
    custom_category TEXT,              -- Optional category override
    never_auto_delete BOOLEAN DEFAULT 1,
    notes TEXT,

    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_identifier (identifier),
    INDEX idx_priority_level (priority_level)
);
```

#### Table: category_rules

```sql
CREATE TABLE category_rules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    rule_id TEXT NOT NULL UNIQUE,
    category TEXT NOT NULL,
    confidence_threshold REAL DEFAULT 0.7,

    -- Matching criteria (stored as JSON)
    keywords_subject TEXT,             -- JSON array
    keywords_body TEXT,                -- JSON array
    sender_patterns TEXT,              -- JSON array

    -- Boolean conditions
    has_unsubscribe_link BOOLEAN,
    has_attachments BOOLEAN,
    attachment_types TEXT,             -- JSON array

    -- Metadata
    enabled BOOLEAN DEFAULT 1,
    priority INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_category (category),
    INDEX idx_enabled_priority (enabled, priority DESC)
);
```

### Database Initialization

```python
# src/classifiers/database.py

class ClassificationDatabase:
    """Manages SQLite database for classifications"""

    def __init__(self, db_path: str = "data/classifications.db"):
        self.db_path = db_path
        self.connection: sqlite3.Connection | None = None

    def initialize(self) -> None:
        """Create tables if they don't exist"""
        ...

    def store_classification(self, result: ClassificationResult) -> None:
        """Store classification result"""
        ...

    def get_classification(self, email_id: str) -> ClassificationResult | None:
        """Retrieve classification by email ID"""
        ...

    def store_feedback(self, feedback: UserFeedback) -> None:
        """Store user feedback"""
        ...

    def get_cached_classification(self, cache_key: str) -> CachedClassification | None:
        """Get cached classification by sender/domain"""
        ...

    def update_cache_hit(self, cache_key: str) -> None:
        """Increment hit count for cache entry"""
        ...

    def clean_expired_cache(self) -> int:
        """Remove expired cache entries, return count removed"""
        ...
```

---

## Configuration Files

### 1. VIP Senders Configuration

**File**: `config/vip_senders.yaml`

```yaml
# VIP Senders Configuration
# Priority levels: vip, trusted, monitored

vip_senders:
  # VIP - Highest priority, never auto-delete
  - identifier: "boss@company.com"
    type: email
    priority: vip
    custom_category: important
    notes: "Direct manager"

  - identifier: "bigclient.com"
    type: domain
    priority: vip
    custom_category: important
    notes: "Major client - all emails important"

  # Trusted - Generally important
  - identifier: "*@partner-company.com"
    type: pattern
    priority: trusted
    notes: "Business partner emails"

  # Monitored - Watch for patterns
  - identifier: "recruiter@headhunter.com"
    type: email
    priority: monitored
    notes: "Potential opportunities"

# Blocked senders (auto-classify as junk)
blocked_senders:
  - identifier: "spam@example.com"
    type: email
    notes: "Known spammer"

  - identifier: "marketing-spam.com"
    type: domain
    notes: "Spam domain"
```

### 2. Category Rules Configuration

**File**: `config/category_rules.yaml`

```yaml
# Category Classification Rules
# Each rule contributes to confidence scoring

categories:
  solicitation:
    confidence_threshold: 0.8
    rules:
      - rule_id: "sol_001"
        name: "Marketing keywords"
        keywords_subject:
          - "limited time"
          - "act now"
          - "free trial"
          - "special offer"
          - "50% off"
        keywords_body:
          - "click here"
          - "unsubscribe"
          - "promotional"
        has_unsubscribe_link: true
        confidence_boost: 0.3
        priority: 10

      - rule_id: "sol_002"
        name: "Marketing domains"
        sender_patterns:
          - "*@marketing.*"
          - "*@promo.*"
          - "*@deals.*"
        confidence_boost: 0.4
        priority: 9

  newsletter:
    confidence_threshold: 0.7
    rules:
      - rule_id: "news_001"
        name: "Newsletter patterns"
        keywords_subject:
          - "newsletter"
          - "weekly digest"
          - "monthly update"
        sender_patterns:
          - "*@newsletter.*"
          - "*@substack.com"
          - "*@medium.com"
        has_unsubscribe_link: true
        confidence_boost: 0.4
        priority: 8

  transactional:
    confidence_threshold: 0.75
    rules:
      - rule_id: "trans_001"
        name: "Order confirmations"
        keywords_subject:
          - "order confirmation"
          - "receipt"
          - "invoice"
          - "payment received"
          - "shipping confirmation"
        keywords_body:
          - "order number"
          - "tracking number"
          - "invoice #"
        confidence_boost: 0.5
        priority: 9

      - rule_id: "trans_002"
        name: "Automated notifications"
        sender_patterns:
          - "noreply@*"
          - "no-reply@*"
          - "notifications@*"
        confidence_boost: 0.3
        priority: 7

  important:
    confidence_threshold: 0.7
    rules:
      - rule_id: "imp_001"
        name: "Urgent keywords"
        keywords_subject:
          - "urgent"
          - "action required"
          - "deadline"
          - "asap"
          - "immediate attention"
        confidence_boost: 0.4
        priority: 10
```

### 3. LLM Configuration

**File**: `config/llm_config.yaml`

```yaml
# LLM Configuration for Classification

# Primary LLM provider
llm:
  provider: "openai"                 # openai, ollama, azure-openai
  base_url: "https://api.openai.com/v1"
  model: "gpt-4"                     # or gpt-3.5-turbo, llama3.1, mistral, etc.
  api_key_env: "OPENAI_API_KEY"      # Environment variable name

  # Request parameters
  temperature: 0.3                   # Lower = more deterministic
  max_tokens: 500                    # Response size limit
  timeout_seconds: 30                # API timeout

  # Retry configuration
  max_retries: 3
  retry_delay_seconds: 1

# Ollama configuration (if provider = "ollama")
ollama:
  base_url: "http://localhost:11434/v1"
  model: "llama3.1"
  # api_key not needed for local Ollama

# Azure OpenAI configuration (if provider = "azure-openai")
azure_openai:
  base_url: "https://YOUR-RESOURCE.openai.azure.com/openai/deployments/YOUR-DEPLOYMENT"
  api_version: "2024-02-01"
  model: "gpt-4"
  api_key_env: "AZURE_OPENAI_KEY"

# Cost tracking
cost_limits:
  daily_max_usd: 5.0
  monthly_max_usd: 50.0
  warn_at_percent: 80
```

### 4. Classifier Configuration

**File**: `config/classifier_config.yaml`

```yaml
# Email Classifier Configuration

# General settings
classifier:
  enabled: true
  mode: "hybrid"                     # "rules-only", "ai-only", "hybrid"

  # Confidence thresholds
  high_confidence_threshold: 0.9     # Skip AI if rule confidence > this
  low_confidence_threshold: 0.5      # Use AI if rule confidence < this

  # Categories
  default_category: "normal"
  enabled_categories:
    - important
    - solicitation
    - newsletter
    - transactional
    - normal

  # Classification behavior
  require_primary_category: true     # Always assign primary
  max_secondary_categories: 3        # Limit tags

  # Thread awareness
  thread_signals_enabled: true
  user_reply_boost: 0.2              # Boost importance if user replied

  # Cache settings
  cache_enabled: true
  cache_ttl_days: 90
  cache_on_sender_domain: true       # Cache by domain
  cache_on_sender_email: true        # Cache by exact email

  # Performance
  batch_size: 50                     # Emails to classify at once
  parallel_processing: false         # Enable in Phase 2
  max_processing_time_seconds: 300   # 5 minutes timeout

# Logging
logging:
  level: "INFO"                      # DEBUG, INFO, WARNING, ERROR
  log_classifications: true
  log_ai_reasoning: true
  log_rule_matches: true
  log_file: "data/logs/classifier.log"
```

---

## AI Prompt Templates

### Classification Prompt Template

```python
# src/classifiers/prompts.py

CLASSIFICATION_SYSTEM_PROMPT = """You are an email classification assistant. Your task is to analyze emails and classify them into categories based on their content, sender, and context.

Categories:
- important: Emails requiring immediate attention, from VIPs, or time-sensitive
- solicitation: Marketing, promotions, cold outreach, sales emails
- newsletter: Subscribed content, digests, regular updates
- transactional: Order confirmations, receipts, automated notifications
- normal: Regular correspondence that doesn't fit other categories

Analyze each email carefully and provide a structured classification with reasoning."""

CLASSIFICATION_USER_PROMPT_TEMPLATE = """Classify the following email:

**Subject**: {subject}
**From**: {sender_name} <{sender}>
**Domain**: {sender_domain}
**Received**: {received_datetime}

**Body Preview** (first 500 characters):
{body_preview}

**Metadata**:
- Has attachments: {has_attachments}
- Attachment types: {attachment_types}
- Has unsubscribe link: {has_unsubscribe_link}
- Importance flag: {importance}
- User replied to this thread: {user_replied}

**Provide your classification in this exact JSON format**:
{{
  "primary_category": "one of: important, solicitation, newsletter, transactional, normal",
  "secondary_categories": ["optional", "tags"],
  "confidence": 0.85,
  "reasoning": "Brief explanation of why this category was chosen (one sentence)"
}}

**Important**:
- Choose the MOST SPECIFIC category that applies
- Confidence should be 0.0-1.0 (be honest about uncertainty)
- Reasoning should explain the key signals that led to this classification
- Secondary categories are optional but helpful for multi-faceted emails"""

# Few-shot examples for better accuracy
FEW_SHOT_EXAMPLES = [
    {
        "subject": "Q4 Budget Review - Action Required by Friday",
        "sender": "boss@company.com",
        "body_preview": "We need to finalize the Q4 budget by end of day Friday. Please review the attached spreadsheet and provide your input...",
        "response": {
            "primary_category": "important",
            "secondary_categories": ["work"],
            "confidence": 0.95,
            "reasoning": "From manager with deadline and action required in subject"
        }
    },
    {
        "subject": "Limited Time Offer - 50% Off Everything!",
        "sender": "marketing@deals-unlimited.com",
        "body_preview": "Don't miss out! Click here now for amazing savings. This offer expires in 24 hours. Unsubscribe anytime...",
        "response": {
            "primary_category": "solicitation",
            "secondary_categories": [],
            "confidence": 0.98,
            "reasoning": "Marketing language, time pressure, unsubscribe link, promotional offer"
        }
    },
    {
        "subject": "Your Order #12345 Has Shipped",
        "sender": "noreply@amazon.com",
        "body_preview": "Good news! Your order has shipped. Tracking number: 1Z999AA1234567890. Expected delivery: Tuesday, Nov 7...",
        "response": {
            "primary_category": "transactional",
            "secondary_categories": ["shopping"],
            "confidence": 0.92,
            "reasoning": "Order confirmation with tracking number from automated sender"
        }
    }
]
```

### Prompt Builder

```python
class PromptBuilder:
    """Builds AI prompts for classification"""

    def __init__(self, include_few_shot: bool = True):
        self.include_few_shot = include_few_shot

    def build_classification_prompt(self, email: EmailInput) -> tuple[str, str]:
        """Build system and user prompts for classification

        Returns:
            (system_prompt, user_prompt)
        """
        system_prompt = CLASSIFICATION_SYSTEM_PROMPT

        if self.include_few_shot:
            system_prompt += "\n\n**Example Classifications**:\n"
            for example in FEW_SHOT_EXAMPLES:
                system_prompt += f"\nSubject: {example['subject']}\n"
                system_prompt += f"→ {example['response']}\n"

        user_prompt = CLASSIFICATION_USER_PROMPT_TEMPLATE.format(
            subject=email.subject,
            sender_name=email.sender_name,
            sender=email.sender,
            sender_domain=email.sender_domain,
            received_datetime=email.received_datetime.isoformat(),
            body_preview=email.body_preview,
            has_attachments=email.has_attachments,
            attachment_types=", ".join(email.attachment_types) if email.attachment_types else "None",
            has_unsubscribe_link=email.has_unsubscribe_link,
            importance=email.importance,
            user_replied=email.is_reply
        )

        return system_prompt, user_prompt
```

---

## Module Interfaces

### 1. Rule-Based Classifier

```python
# src/classifiers/rule_classifier.py

class RuleClassifier:
    """Rule-based email classification"""

    def __init__(self, rules: list[CategoryRule], vip_senders: list[VIPSender]):
        self.rules = rules
        self.vip_senders = vip_senders

    def classify(self, email: EmailInput) -> ClassificationResult:
        """Classify email using rules

        Returns classification with confidence score
        """
        ...

    def check_vip(self, email: EmailInput) -> VIPSender | None:
        """Check if sender is VIP/blocked"""
        ...

    def apply_rules(self, email: EmailInput, category: str) -> float:
        """Apply category rules and return confidence score (0-1)"""
        ...

    def match_keyword_rule(self, text: str, keywords: list[str]) -> bool:
        """Check if any keywords match (case-insensitive)"""
        ...
```

### 2. AI Classifier

```python
# src/classifiers/ai_classifier.py

class AIClassifier:
    """AI-based email classification using LLM"""

    def __init__(self, llm_client: OpenAI, prompt_builder: PromptBuilder):
        self.llm_client = llm_client
        self.prompt_builder = prompt_builder

    def classify(self, email: EmailInput) -> ClassificationResult:
        """Classify email using AI

        Returns classification with AI reasoning
        """
        ...

    def parse_ai_response(self, response: str) -> dict:
        """Parse JSON response from AI"""
        ...

    def validate_classification(self, classification: dict) -> bool:
        """Validate AI response has required fields"""
        ...
```

### 3. Hybrid Classifier (Main Entry Point)

```python
# src/classifiers/hybrid_classifier.py

class HybridClassifier:
    """Combines rule-based and AI classification"""

    def __init__(
        self,
        rule_classifier: RuleClassifier,
        ai_classifier: AIClassifier,
        database: ClassificationDatabase,
        config: ClassifierConfig
    ):
        self.rule_classifier = rule_classifier
        self.ai_classifier = ai_classifier
        self.database = database
        self.config = config

    def classify_email(self, email: EmailInput) -> ClassificationResult:
        """Main classification method

        Flow:
        1. Check cache
        2. Check VIP/blocked
        3. Apply rules
        4. Use AI if needed (low confidence)
        5. Combine results
        6. Store in database
        7. Update cache
        """
        ...

    def check_cache(self, email: EmailInput) -> ClassificationResult | None:
        """Check if classification is cached"""
        ...

    def combine_results(
        self,
        rule_result: ClassificationResult,
        ai_result: ClassificationResult | None
    ) -> ClassificationResult:
        """Combine rule and AI results into final classification"""
        ...

    def update_cache(self, email: EmailInput, result: ClassificationResult) -> None:
        """Update classification cache"""
        ...
```

### 4. User Feedback Handler

```python
# src/classifiers/feedback_handler.py

class FeedbackHandler:
    """Handles user corrections to classifications"""

    def __init__(self, database: ClassificationDatabase):
        self.database = database

    def record_feedback(
        self,
        email_id: str,
        corrected_category: str,
        corrected_tags: list[str] | None = None,
        comment: str | None = None
    ) -> UserFeedback:
        """Record user correction"""
        ...

    def invalidate_cache(self, sender_key: str) -> None:
        """Invalidate cache for sender after correction"""
        ...

    def get_feedback_summary(self, days: int = 30) -> dict:
        """Get summary of recent feedback for analysis"""
        ...
```

---

## Error Handling

### Exception Hierarchy

```python
# src/classifiers/exceptions.py

class ClassifierError(Exception):
    """Base exception for classifier module"""
    pass

class ClassificationError(ClassifierError):
    """Error during classification process"""
    pass

class AIClassificationError(ClassificationError):
    """Error calling AI service"""
    def __init__(self, message: str, status_code: int | None = None):
        self.status_code = status_code
        super().__init__(message)

class RuleValidationError(ClassifierError):
    """Invalid rule configuration"""
    pass

class CacheError(ClassifierError):
    """Error accessing classification cache"""
    pass

class DatabaseError(ClassifierError):
    """Error accessing classification database"""
    pass

class ConfigurationError(ClassifierError):
    """Invalid configuration"""
    pass
```

### Error Handling Strategy

```python
class HybridClassifier:
    def classify_email(self, email: EmailInput) -> ClassificationResult:
        try:
            # Try classification
            result = self._classify_internal(email)
            return result

        except AIClassificationError as e:
            # AI failed - fallback to rules only
            logger.warning(f"AI classification failed: {e}, falling back to rules")
            return self.rule_classifier.classify(email)

        except CacheError as e:
            # Cache failed - continue without cache
            logger.warning(f"Cache access failed: {e}, continuing without cache")
            # Continue classification without cache

        except DatabaseError as e:
            # Database failed - classify but don't store
            logger.error(f"Database error: {e}, classification not persisted")
            # Return result but warn user

        except Exception as e:
            # Unknown error - return default classification
            logger.error(f"Unexpected classification error: {e}")
            return self._create_default_classification(email)

    def _create_default_classification(self, email: EmailInput) -> ClassificationResult:
        """Create safe default classification on error"""
        return ClassificationResult(
            email_id=email.email_id,
            primary_category="normal",
            secondary_categories=[],
            confidence=0.5,
            classification_method="fallback",
            matched_rule=None,
            ai_reasoning="Classification failed, using default category",
            processing_time_ms=0,
            timestamp=datetime.now()
        )
```

---

## Logging Strategy

### Log Levels and Content

```python
# src/classifiers/logger.py

import logging
from datetime import datetime

class ClassifierLogger:
    """Structured logging for classification"""

    def __init__(self, log_file: str = "data/logs/classifier.log"):
        self.logger = logging.getLogger("classifier")
        # Setup handlers, formatters, etc.

    def log_classification(self, email: EmailInput, result: ClassificationResult):
        """Log successful classification"""
        self.logger.info(
            f"Classified email {email.email_id} | "
            f"From: {email.sender} | "
            f"Category: {result.primary_category} | "
            f"Confidence: {result.confidence:.2f} | "
            f"Method: {result.classification_method} | "
            f"Time: {result.processing_time_ms}ms"
        )

        if result.ai_reasoning:
            self.logger.debug(f"AI Reasoning: {result.ai_reasoning}")

    def log_cache_hit(self, cache_key: str, category: str):
        """Log cache hit"""
        self.logger.debug(f"Cache HIT: {cache_key} → {category}")

    def log_cache_miss(self, cache_key: str):
        """Log cache miss"""
        self.logger.debug(f"Cache MISS: {cache_key}")

    def log_feedback(self, feedback: UserFeedback):
        """Log user feedback"""
        self.logger.info(
            f"User feedback | Email: {feedback.email_id} | "
            f"Original: {feedback.original_primary} → "
            f"Corrected: {feedback.corrected_primary}"
        )

    def log_error(self, error: Exception, context: dict):
        """Log error with context"""
        self.logger.error(
            f"Classification error: {str(error)} | "
            f"Context: {context}",
            exc_info=True
        )
```

---

## Testing Strategy

### Unit Tests

```python
# tests/unit/classifiers/test_rule_classifier.py

def test_vip_sender_classification():
    """Test VIP sender gets immediate important classification"""
    ...

def test_keyword_matching():
    """Test keyword matching in subject and body"""
    ...

def test_confidence_scoring():
    """Test confidence calculation from multiple rules"""
    ...

def test_sender_pattern_matching():
    """Test domain and email pattern matching"""
    ...


# tests/unit/classifiers/test_ai_classifier.py

def test_ai_classification_parsing():
    """Test JSON response parsing"""
    ...

def test_ai_fallback_on_error():
    """Test fallback when AI fails"""
    ...

def test_prompt_building():
    """Test prompt template population"""
    ...


# tests/unit/classifiers/test_hybrid_classifier.py

def test_cache_hit():
    """Test cached classification retrieval"""
    ...

def test_high_confidence_rule_skips_ai():
    """Test rule with >90% confidence doesn't call AI"""
    ...

def test_low_confidence_triggers_ai():
    """Test rule with <50% confidence triggers AI"""
    ...

def test_result_combination():
    """Test combining rule and AI results"""
    ...
```

### Integration Tests

```python
# tests/integration/test_classification_flow.py

def test_end_to_end_classification():
    """Test full classification flow from email input to database storage"""
    ...

def test_feedback_invalidates_cache():
    """Test user feedback invalidates cache entry"""
    ...

def test_database_persistence():
    """Test classification is stored and retrievable"""
    ...

def test_concurrent_classification():
    """Test multiple emails classified in parallel (Phase 2)"""
    ...
```

### Test Data

```python
# tests/fixtures/sample_emails.py

SAMPLE_VIP_EMAIL = EmailInput(
    email_id="vip_001",
    sender="boss@company.com",
    sender_name="Jane Boss",
    sender_domain="company.com",
    subject="Q4 Budget Review - Action Required",
    body_preview="We need to finalize the budget by Friday...",
    # ... other fields
)

SAMPLE_SOLICITATION_EMAIL = EmailInput(
    email_id="sol_001",
    sender="marketing@deals.com",
    sender_name="Best Deals",
    sender_domain="deals.com",
    subject="Limited Time Offer - 50% Off!",
    body_preview="Don't miss out! Click here for amazing savings...",
    has_unsubscribe_link=True,
    # ... other fields
)

# Add 20+ sample emails covering all categories
```

---

## Implementation Checklist

### Phase 1: Core Infrastructure (Days 1-2)

- [ ] Create data models (dataclasses)
- [ ] Set up SQLite database with schema
- [ ] Implement database access layer
- [ ] Create configuration file loaders
- [ ] Set up logging infrastructure
- [ ] Write unit tests for models

### Phase 2: Rule-Based Classification (Days 3-4)

- [ ] Implement RuleClassifier
- [ ] Load and parse category rules
- [ ] Implement VIP/blocked sender checking
- [ ] Implement keyword matching
- [ ] Implement pattern matching
- [ ] Calculate confidence scores
- [ ] Write unit tests for rules

### Phase 3: AI Classification (Days 5-6)

- [ ] Set up OpenAI client with configurable endpoint
- [ ] Implement PromptBuilder
- [ ] Implement AIClassifier
- [ ] Add JSON response parsing
- [ ] Add error handling and retries
- [ ] Test with Ollama and OpenAI
- [ ] Write unit tests for AI classifier

### Phase 4: Hybrid System (Days 7-8)

- [ ] Implement HybridClassifier
- [ ] Implement caching logic
- [ ] Implement result combination
- [ ] Add thread signal boosting
- [ ] Implement FeedbackHandler
- [ ] Write integration tests
- [ ] Performance testing

### Phase 5: Integration & Testing (Days 9-10)

- [ ] Integrate with email_client module
- [ ] End-to-end testing with real emails
- [ ] Performance optimization
- [ ] Documentation updates
- [ ] User guide for configuration
- [ ] Deploy and validate

---

## Configuration Examples

### Minimal MVP Configuration

```yaml
# Absolute minimum to get started

# vip_senders.yaml
vip_senders:
  - identifier: "boss@company.com"
    type: email
    priority: vip

# llm_config.yaml
llm:
  provider: "openai"
  model: "gpt-3.5-turbo"
  api_key_env: "OPENAI_API_KEY"

# classifier_config.yaml
classifier:
  enabled: true
  mode: "hybrid"
  default_category: "normal"
```

### Full Production Configuration

See detailed examples in sections above.

---

## Next Steps

After completing this technical specification:

1. **Review and validate** data models with stakeholders
2. **Create sample configuration files** in `config/` directory
3. **Set up development environment** with test database
4. **Begin implementation** following the checklist above
5. **Iterative testing** with real email data

---

**Document Status**: Complete - Ready for implementation
**Next Review**: After Phase 1 completion
**Related**: See CLASSIFIER_DESIGN.md for strategic decisions
