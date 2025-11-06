# Email Classifier - Testing Plan

**Version**: 1.0
**Phase**: MVP (Phase 1)
**Status**: Planning
**Last Updated**: 2025-11-05

---

## Overview

This document outlines the comprehensive testing strategy for the Email Classifier MVP. It includes test scenarios, sample data, expected results, and success criteria to ensure the classifier meets accuracy and performance targets.

**Testing Goals**:
- ✅ Verify >90% overall classification accuracy
- ✅ Achieve >95% solicitation detection accuracy
- ✅ Ensure <5% false positive rate (important emails marked as junk)
- ✅ Process 100 emails in <3 minutes
- ✅ Validate all configuration options work correctly

---

## Table of Contents

1. [Test Data Strategy](#test-data-strategy)
2. [Unit Test Scenarios](#unit-test-scenarios)
3. [Integration Test Scenarios](#integration-test-scenarios)
4. [End-to-End Test Scenarios](#end-to-end-test-scenarios)
5. [Performance Test Scenarios](#performance-test-scenarios)
6. [Edge Cases & Error Scenarios](#edge-cases--error-scenarios)
7. [Test Data Samples](#test-data-samples)
8. [Success Criteria](#success-criteria)
9. [Testing Timeline](#testing-timeline)

---

## Test Data Strategy

### Sample Email Dataset

Create a comprehensive test dataset with **at least 100 sample emails** covering all categories and edge cases:

**Category Distribution**:
- Important: 15 emails (15%)
- Solicitation: 30 emails (30%)
- Newsletter: 20 emails (20%)
- Transactional: 20 emails (20%)
- Normal: 15 emails (15%)

**Diversity Requirements**:
- Multiple senders per category
- Various subject line patterns
- Different email lengths (short, medium, long)
- With and without attachments
- With and without unsubscribe links
- Different sender domains
- Multiple languages (primarily English for MVP)
- Thread vs standalone emails

### Test Data Sources

1. **Synthetic Emails**: Create realistic but fake emails for each category
2. **Anonymized Real Emails**: Remove PII from actual emails (optional)
3. **Public Datasets**: Enron email dataset, spam datasets
4. **Edge Cases**: Manually crafted tricky examples

### Data Organization

```
tests/fixtures/sample_emails/
├── important/
│   ├── vip_urgent.json
│   ├── deadline_work.json
│   ├── action_required.json
│   └── ...
├── solicitation/
│   ├── marketing_sale.json
│   ├── cold_outreach.json
│   ├── promotional.json
│   └── ...
├── newsletter/
│   ├── tech_newsletter.json
│   ├── weekly_digest.json
│   └── ...
├── transactional/
│   ├── order_confirmation.json
│   ├── shipping_notice.json
│   └── ...
├── normal/
│   ├── colleague_question.json
│   ├── project_update.json
│   └── ...
└── edge_cases/
    ├── ambiguous_category.json
    ├── multiple_categories.json
    ├── spam_disguised_as_important.json
    └── ...
```

---

## Unit Test Scenarios

### 1. Data Model Tests

```python
class TestDataModels:
    def test_email_input_creation(self):
        """Test EmailInput model creation and validation"""
        # Verify all required fields
        # Test default values
        # Validate datetime handling

    def test_classification_result_serialization(self):
        """Test ClassificationResult to_dict/from_dict"""
        # Round-trip conversion
        # Verify all fields preserved

    def test_confidence_score_validation(self):
        """Test confidence score must be 0.0-1.0"""
        # Test invalid values raise errors
```

### 2. Rule Classifier Tests

```python
class TestRuleClassifier:
    def test_vip_sender_exact_match(self):
        """VIP sender email match → immediate important classification"""
        # Test: boss@company.com → important, confidence=1.0

    def test_vip_domain_match(self):
        """VIP sender domain match → immediate important classification"""
        # Test: anyone@bigclient.com → important, confidence=1.0

    def test_blocked_sender_match(self):
        """Blocked sender → immediate solicitation classification"""
        # Test: spam@example.com → solicitation, confidence=1.0

    def test_keyword_matching_subject(self):
        """Keyword in subject contributes to confidence"""
        # Test: "Limited Time Offer" → solicitation boost

    def test_keyword_matching_body(self):
        """Keyword in body contributes to confidence"""
        # Test: body contains "unsubscribe" → solicitation boost

    def test_sender_pattern_matching(self):
        """Sender pattern matching with wildcards"""
        # Test: *@marketing.company.com matches rule

    def test_multiple_rule_matches(self):
        """Multiple rules combine confidence"""
        # Test: multiple solicitation rules → high confidence

    def test_confidence_capping(self):
        """Combined confidence capped at 1.0"""
        # Test: even if rules sum to >1.0, cap at 1.0

    def test_unsubscribe_link_detection(self):
        """Unsubscribe link boosts solicitation/newsletter"""
        # Test: has_unsubscribe_link=True → confidence boost

    def test_disabled_rule_ignored(self):
        """Disabled rules don't contribute to classification"""
        # Test: rule with enabled=false is skipped

    def test_rule_priority_ordering(self):
        """Higher priority rules checked first"""
        # Test: priority 10 evaluated before priority 5
```

### 3. AI Classifier Tests

```python
class TestAIClassifier:
    def test_prompt_building(self):
        """Test prompt template population"""
        # Verify all email fields included
        # Check few-shot examples included

    def test_ai_response_parsing(self):
        """Test JSON response parsing"""
        # Test valid JSON → ClassificationResult
        # Test malformed JSON → raises error

    def test_ai_response_validation(self):
        """Test AI response has required fields"""
        # Test missing primary_category → error
        # Test invalid confidence → error

    def test_api_timeout_handling(self):
        """Test timeout raises appropriate error"""
        # Mock slow API response
        # Verify timeout exception

    def test_api_retry_logic(self):
        """Test retry on transient errors"""
        # Mock 429 rate limit → retry
        # Mock 500 error → retry
        # Mock success on retry 2 → succeeds
```

### 4. Hybrid Classifier Tests

```python
class TestHybridClassifier:
    def test_cache_hit_returns_cached(self):
        """Cached classification returned immediately"""
        # Setup: email in cache
        # Verify: no rule/AI calls made
        # Verify: cache hit count incremented

    def test_cache_miss_triggers_classification(self):
        """Cache miss triggers full classification"""
        # Setup: email not in cache
        # Verify: classification performed
        # Verify: result cached

    def test_high_confidence_rule_skips_ai(self):
        """Rule confidence >0.9 skips AI call"""
        # Setup: rule returns 0.95 confidence
        # Verify: AI not called
        # Verify: rule result used

    def test_low_confidence_triggers_ai(self):
        """Rule confidence <0.5 triggers AI call"""
        # Setup: rule returns 0.4 confidence
        # Verify: AI called
        # Verify: AI result used if higher confidence

    def test_medium_confidence_enhances_with_ai(self):
        """Rule confidence 0.5-0.9 enhanced by AI"""
        # Setup: rule returns 0.7 confidence
        # Verify: AI called
        # Verify: results combined

    def test_result_combination_takes_higher_confidence(self):
        """Combined result uses higher confidence"""
        # Setup: rule=0.6, AI=0.8
        # Verify: final uses AI result

    def test_thread_signal_boosts_importance(self):
        """User reply to thread boosts importance"""
        # Setup: email.is_reply=True
        # Verify: importance boosted by 0.2

    def test_classification_stored_in_database(self):
        """Classification result stored in database"""
        # Verify: database.store_classification() called
        # Verify: retrievable by email_id
```

### 5. Feedback Handler Tests

```python
class TestFeedbackHandler:
    def test_record_feedback(self):
        """User feedback recorded correctly"""
        # Test: feedback stored in database
        # Verify: all fields captured

    def test_feedback_invalidates_cache(self):
        """Feedback invalidates sender cache"""
        # Setup: sender cached as "solicitation"
        # Action: user corrects to "newsletter"
        # Verify: cache invalidated for sender

    def test_feedback_summary_aggregation(self):
        """Feedback summary provides insights"""
        # Test: get_feedback_summary() returns stats
        # Verify: counts by category, accuracy metrics
```

---

## Integration Test Scenarios

### 1. Full Classification Flow

```python
class TestClassificationFlow:
    def test_vip_email_end_to_end(self):
        """VIP email: input → classification → database → cache"""
        # Input: email from VIP sender
        # Expected: important, confidence=1.0, method=vip
        # Verify: stored in database
        # Verify: cached

    def test_obvious_solicitation_end_to_end(self):
        """Obvious solicitation: rules-only path"""
        # Input: "50% OFF - LIMITED TIME"
        # Expected: solicitation, confidence>0.9, method=rule
        # Verify: AI not called (high confidence)

    def test_ambiguous_email_with_ai(self):
        """Ambiguous email: hybrid classification"""
        # Input: unclear category email
        # Expected: rules + AI combined
        # Verify: both rule and AI confidence tracked

    def test_newsletter_classification(self):
        """Newsletter detection end-to-end"""
        # Input: email from substack.com with "Weekly Digest" subject
        # Expected: newsletter, high confidence

    def test_transactional_order_confirmation(self):
        """Order confirmation classified correctly"""
        # Input: "Your Order #12345 Has Shipped"
        # Expected: transactional, high confidence
```

### 2. Configuration Loading

```python
class TestConfiguration:
    def test_load_vip_senders_yaml(self):
        """VIP senders loaded from YAML correctly"""

    def test_load_category_rules_yaml(self):
        """Category rules loaded and parsed"""

    def test_load_llm_config_yaml(self):
        """LLM config loaded with correct provider"""

    def test_load_classifier_config_yaml(self):
        """Classifier config loaded with defaults"""

    def test_invalid_config_raises_error(self):
        """Invalid configuration raises ConfigurationError"""
```

### 3. Database Operations

```python
class TestDatabaseOperations:
    def test_database_initialization(self):
        """Database tables created on initialization"""

    def test_store_and_retrieve_classification(self):
        """Classification stored and retrieved correctly"""

    def test_cache_expiration(self):
        """Expired cache entries not returned"""

    def test_cache_cleanup(self):
        """Expired cache entries removed by cleanup"""

    def test_feedback_storage(self):
        """User feedback stored in database"""
```

### 4. LLM Provider Integration

```python
class TestLLMIntegration:
    def test_openai_api_classification(self):
        """OpenAI API classifies email correctly"""
        # Requires: OPENAI_API_KEY in environment
        # Test: real API call
        # Verify: valid JSON response

    def test_ollama_local_classification(self):
        """Ollama local LLM classifies email"""
        # Requires: Ollama running locally
        # Test: localhost API call
        # Verify: valid response

    def test_api_error_fallback(self):
        """API error falls back to rules-only"""
        # Mock: API returns 500 error
        # Verify: classification completes with rules
        # Verify: error logged
```

---

## End-to-End Test Scenarios

### Scenario 1: First-Time User Setup

**Steps**:
1. User copies config files from .example
2. User adds 5 VIP senders
3. User runs classifier on 20 emails
4. Classifier uses AI for uncertain emails
5. Results stored in database

**Expected**:
- All config files load successfully
- VIP senders classified as important
- Other emails classified with hybrid approach
- All results in database
- Cache populated for future scans

**Success Criteria**:
- 0 configuration errors
- >85% classification accuracy
- All 20 emails processed in <2 minutes

---

### Scenario 2: Bulk Email Classification

**Steps**:
1. User scans inbox with 100 emails
2. Classifier processes in batches of 50
3. Mix of categories
4. Results cached by sender domain

**Expected**:
- All 100 emails classified
- Cache used for repeat senders
- AI calls minimized through caching
- Performance within targets

**Success Criteria**:
- 100 emails processed in <3 minutes
- Cache hit rate >30% on repeat senders
- <50 AI API calls (due to caching)

---

### Scenario 3: User Feedback Loop

**Steps**:
1. User classifies 20 emails
2. User corrects 3 misclassifications
3. User re-scans same senders
4. Corrected classifications used

**Expected**:
- Feedback stored in database
- Cache invalidated for corrected senders
- Future emails from same sender use corrected category
- Feedback summary shows accuracy improvement

**Success Criteria**:
- All 3 corrections stored
- Cache invalidated for 3 senders
- Re-scan uses corrected classifications

---

### Scenario 4: Mixed Provider Testing

**Steps**:
1. Test with OpenAI (gpt-3.5-turbo)
2. Test with OpenAI (gpt-4)
3. Test with Ollama (llama3.1)
4. Compare classification accuracy

**Expected**:
- All providers work correctly
- GPT-4 has highest accuracy
- Ollama has reasonable accuracy
- All follow same interface

**Success Criteria**:
- 0 provider-specific errors
- GPT-4: >95% accuracy
- GPT-3.5-turbo: >90% accuracy
- Ollama: >80% accuracy

---

## Performance Test Scenarios

### Load Testing

```python
def test_classify_100_emails_under_3_minutes():
    """100 emails classified in <180 seconds"""
    # Load 100 sample emails
    # Start timer
    # Classify all
    # Stop timer
    # Assert: elapsed < 180 seconds

def test_classify_10_emails_under_30_seconds():
    """Small batch processed quickly"""
    # 10 emails in <30 seconds

def test_cache_improves_performance():
    """Cached classifications 10x faster"""
    # First run: measure time
    # Second run (cached): measure time
    # Assert: second run <10% of first run time
```

### Concurrent Processing (Phase 2)

```python
def test_parallel_classification():
    """Parallel processing faster than sequential"""
    # Only when parallel_processing enabled

def test_no_race_conditions():
    """No race conditions with concurrent access"""
    # Test database concurrent writes
    # Test cache concurrent access
```

---

## Edge Cases & Error Scenarios

### Edge Case Tests

```python
class TestEdgeCases:
    def test_empty_email_subject(self):
        """Email with empty subject handled gracefully"""

    def test_very_long_email_body(self):
        """Very long email (>10k chars) handled"""
        # Body truncated to 500 chars for AI

    def test_email_with_no_sender_name(self):
        """Email with only sender email (no name)"""

    def test_non_ascii_characters(self):
        """Email with emoji and unicode characters"""

    def test_html_only_email(self):
        """Email with HTML but no plain text"""

    def test_email_with_50_attachments(self):
        """Email with many attachments"""

    def test_ambiguous_multi_category_email(self):
        """Email that fits multiple categories"""
        # e.g., Important solicitation from VIP

    def test_thread_with_10_replies(self):
        """Long email thread classification"""

    def test_forwarded_email_classification(self):
        """Forwarded email (FWD: prefix)"""
```

### Error Scenario Tests

```python
class TestErrorScenarios:
    def test_database_unavailable(self):
        """Classification continues if database fails"""
        # Mock database error
        # Verify: classification returns result
        # Verify: error logged

    def test_api_rate_limit_exceeded(self):
        """Handle API rate limit (429)"""
        # Mock 429 response
        # Verify: retry with backoff
        # Verify: fallback to rules if retries fail

    def test_api_timeout(self):
        """Handle API timeout"""
        # Mock timeout
        # Verify: fallback to rules

    def test_invalid_json_from_ai(self):
        """Handle malformed AI response"""
        # Mock invalid JSON
        # Verify: error logged
        # Verify: fallback to rules

    def test_cache_corruption(self):
        """Handle corrupted cache data"""
        # Corrupt cache entry
        # Verify: cache miss, re-classify

    def test_missing_config_file(self):
        """Handle missing config files"""
        # Delete config file
        # Verify: defaults used or error raised

    def test_invalid_vip_sender_pattern(self):
        """Handle invalid regex in VIP senders"""
        # Bad pattern in config
        # Verify: validation error raised
```

---

## Test Data Samples

### Important Category Samples

```json
{
  "test_id": "imp_001",
  "category": "important",
  "email": {
    "subject": "Q4 Budget Review - Action Required by Friday",
    "sender": "boss@company.com",
    "sender_name": "Jane Boss",
    "body_preview": "We need to finalize the Q4 budget by end of day Friday. Please review the attached spreadsheet and provide your department's input. This is critical for our planning meeting next week.",
    "has_unsubscribe_link": false,
    "importance": "high"
  },
  "expected": {
    "primary_category": "important",
    "confidence_min": 0.9,
    "method": "vip"
  }
}
```

```json
{
  "test_id": "imp_002",
  "category": "important",
  "email": {
    "subject": "URGENT: Server Down - Immediate Action Needed",
    "sender": "alerts@monitoring.com",
    "body_preview": "Production server is down. All services affected. Need immediate attention to restore services.",
    "importance": "high"
  },
  "expected": {
    "primary_category": "important",
    "confidence_min": 0.8,
    "method": "hybrid"
  }
}
```

### Solicitation Category Samples

```json
{
  "test_id": "sol_001",
  "category": "solicitation",
  "email": {
    "subject": "Limited Time Offer - 50% Off Everything!",
    "sender": "marketing@deals-unlimited.com",
    "body_preview": "Don't miss out! Click here now for amazing savings. This offer expires in 24 hours. Shop now and save big! Unsubscribe anytime.",
    "has_unsubscribe_link": true
  },
  "expected": {
    "primary_category": "solicitation",
    "confidence_min": 0.9,
    "method": "rule"
  }
}
```

```json
{
  "test_id": "sol_002",
  "category": "solicitation",
  "email": {
    "subject": "Quick question about your email workflow",
    "sender": "sales@saas-product.com",
    "body_preview": "Hi, I noticed you might benefit from our email automation tool. Would love to show you a quick demo. Are you available for a 15-minute call this week?",
    "has_unsubscribe_link": false
  },
  "expected": {
    "primary_category": "solicitation",
    "confidence_min": 0.7,
    "method": "ai"
  }
}
```

### Newsletter Category Samples

```json
{
  "test_id": "news_001",
  "category": "newsletter",
  "email": {
    "subject": "The Daily Tech - Issue #247",
    "sender": "newsletter@techblog.com",
    "body_preview": "Welcome to today's edition of The Daily Tech. Here are the top stories: 1) New AI breakthrough announced...",
    "has_unsubscribe_link": true
  },
  "expected": {
    "primary_category": "newsletter",
    "confidence_min": 0.85,
    "method": "rule"
  }
}
```

### Transactional Category Samples

```json
{
  "test_id": "trans_001",
  "category": "transactional",
  "email": {
    "subject": "Your Order #12345 Has Shipped",
    "sender": "noreply@amazon.com",
    "body_preview": "Good news! Your order has shipped. Tracking number: 1Z999AA1234567890. Expected delivery: Tuesday, Nov 7. View order details...",
    "has_unsubscribe_link": false
  },
  "expected": {
    "primary_category": "transactional",
    "confidence_min": 0.9,
    "method": "rule"
  }
}
```

### Normal Category Samples

```json
{
  "test_id": "norm_001",
  "category": "normal",
  "email": {
    "subject": "Re: Project update",
    "sender": "colleague@company.com",
    "body_preview": "Thanks for the update. I reviewed the document and have a few questions about the timeline. Can we discuss in tomorrow's standup?",
    "has_unsubscribe_link": false,
    "is_reply": true
  },
  "expected": {
    "primary_category": "normal",
    "confidence_min": 0.6,
    "method": "hybrid"
  }
}
```

### Edge Cases

```json
{
  "test_id": "edge_001",
  "description": "VIP sender sending promotional content",
  "email": {
    "subject": "Check out this amazing deal!",
    "sender": "boss@company.com",
    "body_preview": "Hey team, thought you'd be interested in this sale. 50% off all software licenses this week only.",
    "has_unsubscribe_link": false
  },
  "expected": {
    "primary_category": "important",
    "secondary_categories": ["solicitation"],
    "notes": "VIP sender overrides solicitation signals"
  }
}
```

---

## Success Criteria

### Accuracy Metrics

| Metric | Target | Minimum Acceptable |
|--------|--------|-------------------|
| Overall Accuracy | >90% | >85% |
| Solicitation Detection | >95% | >90% |
| Important Detection | >90% | >85% |
| Newsletter Detection | >85% | >80% |
| Transactional Detection | >90% | >85% |
| False Positive Rate | <5% | <10% |
| False Negative Rate | <10% | <15% |

### Performance Metrics

| Metric | Target | Maximum Acceptable |
|--------|--------|-------------------|
| 100 emails processing time | <3 min | <5 min |
| Single email (no cache) | <2 sec | <5 sec |
| Single email (cached) | <0.1 sec | <0.5 sec |
| Cache hit rate (repeat senders) | >70% | >50% |
| AI API calls (100 emails) | <60 | <80 |

### Quality Metrics

| Metric | Target |
|--------|--------|
| Test coverage | >80% |
| Unit tests passing | 100% |
| Integration tests passing | 100% |
| Configuration errors | 0 |
| Unhandled exceptions | 0 |

---

## Testing Timeline

### Week 1: Unit Testing (Days 1-2)
- Set up testing infrastructure
- Create test fixtures
- Write data model tests
- Write rule classifier tests
- Target: 50+ unit tests

### Week 1: Integration Testing (Days 3-4)
- Write AI classifier tests
- Write hybrid classifier tests
- Write database tests
- Write configuration tests
- Target: 30+ integration tests

### Week 2: End-to-End Testing (Days 5-6)
- Create 100+ sample emails
- Run full classification flows
- Test all configuration scenarios
- Test with multiple LLM providers
- Target: 10+ E2E scenarios

### Week 2: Performance Testing (Day 7)
- Load testing with 100, 500, 1000 emails
- Cache performance testing
- API rate limit testing
- Measure and optimize

### Week 2: Edge Case Testing (Day 8)
- Test all edge cases
- Error scenario testing
- Boundary condition testing
- Security testing

### Week 2: User Acceptance Testing (Days 9-10)
- Test with real email data
- Gather user feedback
- Refine configurations
- Final accuracy validation

---

## Test Execution Checklist

### Pre-Testing
- [ ] Test environment set up
- [ ] Test database created
- [ ] Sample email dataset created (100+ emails)
- [ ] Configuration files prepared
- [ ] LLM provider configured (OpenAI/Ollama)

### Unit Testing
- [ ] All data model tests passing
- [ ] All rule classifier tests passing
- [ ] All AI classifier tests passing
- [ ] All hybrid classifier tests passing
- [ ] Code coverage >80%

### Integration Testing
- [ ] Configuration loading tests passing
- [ ] Database operations tests passing
- [ ] LLM integration tests passing
- [ ] End-to-end flow tests passing

### Performance Testing
- [ ] 100 emails in <3 minutes
- [ ] Cache performance validated
- [ ] Memory usage acceptable
- [ ] No performance degradation over time

### Accuracy Testing
- [ ] Overall accuracy >90%
- [ ] Solicitation detection >95%
- [ ] False positive rate <5%
- [ ] All categories meeting targets

### Final Validation
- [ ] All tests passing
- [ ] User acceptance testing complete
- [ ] Documentation updated
- [ ] Ready for production use

---

**Document Status**: Complete - Ready for test implementation
**Next Steps**: Create test fixtures, write tests, execute testing plan
