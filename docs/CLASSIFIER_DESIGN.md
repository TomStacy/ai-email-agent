# Email Classification System - Design Document

**Status**: Planning
**Phase**: Feature Design
**Last Updated**: 2025-11-05

---

## Overview

This document outlines the design and strategy for the Email Classification module, a core component that will enable intelligent email categorization, prioritization, and automation in the AI Email Agent.

---

## Classification Strategies

### 1. Multi-Tier Classification Approach

A layered approach provides the best balance of speed, cost, and accuracy:

**Tier 1: Fast Rule-Based Pre-filtering** (runs first, cheapest)
- Whitelist/VIP senders → instant "important" classification
- Known spam domains → instant "junk"
- Obvious patterns (unsubscribe links, marketing keywords)
- Sender domain matching

**Tier 2: AI Classification** (runs on uncertain emails)
- More nuanced understanding
- Context-aware categorization
- Handles edge cases and new patterns
- Can detect tone, urgency, intent

**Tier 3: User Feedback Loop** (optional future enhancement)
- Learn from user corrections
- Adjust confidence thresholds
- Build personalized rules over time

---

## Category Taxonomy

### Priority-Based Categories

- `critical` - VIP senders, urgent matters, time-sensitive
- `important` - Needs attention but not urgent
- `normal` - Regular correspondence
- `low_priority` - FYI, newsletters, updates

### Content-Based Categories

- `finance` - Banking, investments, bills, receipts
- `work` - Job-related, professional correspondence
- `job_notifications` - LinkedIn, job boards, recruiter emails
- `tech` - GitHub, dev tools, tech newsletters
- `social` - Social media notifications
- `shopping` - Order confirmations, shipping, deals
- `travel` - Bookings, confirmations, itineraries
- `health` - Medical, fitness, wellness

### Action-Based Categories

- `solicitation` - Marketing, promotions, cold outreach
- `newsletter` - Subscribed content, digests
- `transactional` - Receipts, confirmations, automated messages
- `personal` - Friends, family, personal contacts
- `automated` - System notifications, no-reply emails

### Design Decision: Hierarchical vs Flat

**Question**: Should we use hierarchical categories (e.g., `solicitation.cold_outreach` vs `solicitation.newsletter`) or flat categories with tags?

**Considerations**:
- Hierarchical: More organized, allows category inheritance, complex to configure
- Flat with tags: Simpler, more flexible, allows multiple categories per email
- Hybrid: Primary category + secondary tags

---

## Configuration-Driven Design

### Important Senders List

```
Priority Levels:

VIP (always important, never auto-delete)
  - Boss, key clients, family
  - Domains: company.com, important-client.com
  - Actions: Always notify, never filter, highest priority

Trusted (generally important)
  - Colleagues, regular contacts
  - Domains: partner-companies
  - Actions: High priority, rarely filter

Monitored (watch for patterns)
  - New contacts, potential leads
  - Actions: Normal processing, watch for patterns
```

### Category Rules Configuration

Each category could have:
- **Keywords** (subject, body, sender)
- **Sender patterns** (domains, email formats)
- **Header checks** (reply-to, list-unsubscribe)
- **Attachment patterns** (has PDF, has invoice)
- **Time-based rules** (sent during business hours)
- **Confidence threshold** (how sure to be before applying)

Example:
```yaml
categories:
  finance:
    keywords:
      subject: ["invoice", "payment", "statement", "receipt", "billing"]
      body: ["account balance", "transaction", "due date"]
    sender_patterns:
      - "*@bank.com"
      - "*@paypal.com"
    confidence_threshold: 0.7

  solicitation:
    keywords:
      subject: ["limited time", "act now", "free trial", "unsubscribe"]
      body: ["click here", "special offer", "promotional"]
    headers:
      - has_unsubscribe_link: true
    confidence_threshold: 0.8
```

---

## Hybrid Classification Logic

### Decision Flow

1. **Check VIP list first**
   - If sender is VIP → classify as important, skip AI
   - If sender is blocked → classify as junk, skip AI

2. **Run fast rule checks**
   - Known patterns (has "unsubscribe" → likely newsletter)
   - Transactional patterns (order #, tracking #)
   - Automated sender patterns (noreply@, no-reply@)

3. **Confidence scoring**
   - If rule confidence > 90% → use rule result, skip AI
   - If rule confidence 50-90% → enhance with AI
   - If rule confidence < 50% → rely on AI

4. **AI classification**
   - Use GPT for nuanced understanding
   - Provide context: sender history, email thread, previous classifications
   - Ask AI for category + confidence + reasoning

5. **Combine results**
   - Weight rule-based and AI scores
   - Use AI reasoning to override rules if strongly confident
   - Flag conflicts for user review

### Classification Workflow Pseudocode

```
function classify_email(email):
    # Tier 1: VIP/Blocklist check
    if email.sender in vip_list:
        return Classification(category="important", confidence=1.0, method="vip")
    if email.sender in blocklist:
        return Classification(category="junk", confidence=1.0, method="blocked")

    # Tier 2: Rule-based classification
    rule_result = apply_rules(email)

    if rule_result.confidence >= 0.9:
        return rule_result

    # Tier 3: AI classification (if enabled and needed)
    if ai_enabled and rule_result.confidence < 0.9:
        ai_result = classify_with_ai(email)

        # Combine results
        if ai_result.confidence > rule_result.confidence:
            return ai_result
        else:
            return hybrid_result(rule_result, ai_result)

    return rule_result
```

---

## Performance & Cost Considerations

### Token Optimization

**Challenge**: Sending full emails to AI is expensive

**Solutions**:
- Don't send full email body to AI (too expensive)
- Send: subject + first 500 chars of body + sender + basic metadata
- Cache classifications by sender domain
- Batch classify similar emails

**Example**:
```
Instead of 5000 token email → send 300 token summary
Cost reduction: ~94%
Accuracy tradeoff: Minimal (most classification signals in first paragraph)
```

### Caching Strategy

**Domain-level caching**:
- "All emails from newsletter@company.com are newsletters"
- User confirms once → cache for future
- TTL on cache (30 days? 90 days?)
- Invalidate on user correction

**Sender pattern caching**:
- Learn that "noreply@*.com" is typically automated
- Cache common patterns
- Reduce AI calls by 60-80%

### Rate Limiting

**API Call Management**:
- Limit AI calls per scan (e.g., max 50 per session)
- Process rules-based first
- Queue uncertain emails for AI processing
- Option to process in batches during off-peak times
- Fallback to rule-based if quota exceeded

**Cost Controls**:
- Track OpenAI API usage
- Set daily/monthly limits
- Warn user when approaching limits
- Graceful degradation to rules-only mode

---

## User Customization Options

### What Should Users Be Able to Configure?

#### VIP/Important Senders
- Email addresses (exact match)
- Domains (pattern match)
- Name patterns (regex support)
- Per-sender custom categories

#### Category Preferences
- Which categories to use
- Custom category definitions
- Category-specific keywords
- Enable/disable specific categories

#### Classification Behavior
- **Aggressiveness** (conservative vs aggressive filtering)
- **Confidence thresholds** (per category)
- **AI usage** (always, never, hybrid)
- **Which categories get AI** vs just rules
- **Auto-apply actions** based on category

#### Blocked/Junk Criteria
- Sender blacklist
- Domain blacklist
- Keyword blacklist
- Pattern matching rules

### Configuration Levels

**Level 1: Beginner (Minimal Setup)**
- Just VIP sender list
- Use default categories and rules
- AI enabled by default

**Level 2: Intermediate**
- Custom category keywords
- Adjust confidence thresholds
- Basic sender rules

**Level 3: Advanced (Power User)**
- Full rules engine
- Custom categories
- Complex pattern matching
- Conditional logic

---

## Classification Metadata

### Data to Track for Each Classification

```python
ClassificationResult:
    email_id: str
    primary_category: str
    secondary_categories: List[str]  # tags
    confidence_score: float  # 0-1
    classification_method: str  # rule_based, ai, hybrid, user_override, vip
    timestamp: datetime
    matched_rule: Optional[str]  # which rule triggered
    ai_reasoning: Optional[str]  # AI explanation
    user_feedback: Optional[str]  # if user corrected
    processing_time_ms: int
```

### Why Track This?

- **Debugging**: Understand why email was classified
- **Improvement**: Identify low-confidence classifications
- **User feedback**: Learn from corrections
- **Analytics**: Track classification accuracy over time
- **Audit trail**: For compliance/review

---

## Special Cases to Handle

### Email Threads

**Challenge**: Should all emails in a thread have same category?

**Approaches**:
1. **Thread inheritance**: First email sets category for entire thread
2. **Individual classification**: Each email classified separately
3. **Thread evolution**: Allow category to change as thread progresses

**Recommendation**: Start with individual classification, add thread-aware option later

**Edge case**: "Important" work thread that degenerates into spam/marketing

### Automated Emails

**Challenge**: Distinguish legitimate automated emails from spam

**Indicators of legitimate automated**:
- Receipts vs marketing dressed as receipts
- Legitimate notifications vs notification spam
- Transactional emails from known services

**Detection strategies**:
- Check sender domain reputation
- Look for transaction IDs, order numbers
- Verify "from" matches "reply-to"
- Check for personalization (has your name, order details)

### Newsletters

**Challenge**: Subscribed newsletters (wanted) vs cold email lists (unwanted)

**Distinction criteria**:
- Has unsubscribe link that works
- User has opened previous emails from sender
- Consistent sending schedule
- Content quality (newsletter vs pure marketing)

**Approach**:
- Allow user to mark specific newsletters as "wanted"
- Build whitelist of trusted newsletter domains
- AI can detect content quality difference

### Multi-lingual Emails

**Challenge**: Does AI handle non-English well enough?

**Considerations**:
- GPT-4 handles major languages well
- Rule-based keywords need translation
- Some languages might need language-specific rules

**Approach**:
- Start with English
- Add language detection
- Use AI for non-English (better than translated rules)
- Allow users to add language-specific keywords

---

## AI Prompt Strategy

### Information to Provide to AI

Optimized payload to minimize tokens while maximizing signal:

```
- Subject line (full)
- Sender email address
- Sender display name
- First 500 characters of body
- Has unsubscribe link? (boolean)
- Has attachments? What types?
- Is part of thread? Thread subject?
- Sender domain
- Recipient (to/cc/bcc info)
```

### Prompt Structure Options

#### Option A: Single Category (Simplest)
```
"Classify this email into exactly one category from this list:
[important, solicitation, newsletter, transactional, normal]

Email:
Subject: {subject}
From: {sender}
Body: {body_excerpt}

Respond with just the category name."
```

**Pros**: Fastest, cheapest, clearest
**Cons**: Loses nuance, can't handle multi-faceted emails

#### Option B: Multi-tag (Flexible)
```
"Tag this email with all applicable categories from this list:
[list of all categories]

Email: [details]

Respond with comma-separated categories."
```

**Pros**: Captures complexity, allows multiple dimensions
**Cons**: Harder to use for automation, need primary category

#### Option C: Structured Response (Comprehensive)
```
"Analyze this email and provide:
1. Primary category: [one of: list]
2. Secondary tags: [any of: list]
3. Priority level: [1-5]
4. Is solicitation: [yes/no]
5. Confidence: [0.0-1.0]
6. Brief reasoning: [one sentence]

Email: [details]

Respond in JSON format."
```

**Pros**: Rich information, clear reasoning, confidence scores
**Cons**: More tokens, requires JSON parsing, slower

**Recommendation**: Start with Option C for MVP to gather data, optimize to Option A/B based on findings

### Few-Shot Examples

**Strategy**: Provide 3-5 examples of each category in the prompt

**Example structure**:
```
Here are examples of correctly classified emails:

[IMPORTANT]
Subject: "Q4 Budget Review - Action Required"
From: boss@company.com
Body: "We need to finalize the budget by Friday..."
→ Category: important, Priority: 5, Reasoning: "From VIP sender, action required, deadline"

[SOLICITATION]
Subject: "Limited Time Offer - 50% Off!"
From: marketing@deals.com
Body: "Don't miss out! Click here for amazing savings..."
→ Category: solicitation, Priority: 1, Reasoning: "Marketing language, promotional offer, unsubscribe link"

[Continue with more examples...]

Now classify this email: [actual email]
```

**Dynamic examples**: Update based on user corrections, domain-specific needs

---

## Implementation Phases

### Phase 1: MVP (Weeks 3-4)

**Core Categories**:
- `important`
- `solicitation`
- `newsletter`
- `transactional`
- `normal`

**Features**:
- Simple VIP sender list (config file)
- Basic rule-based classification (keywords + sender patterns)
- AI classification for uncertain cases (confidence < 0.9)
- Confidence scoring
- Clear logging of classification decisions

**Configuration**:
- YAML file for VIP senders
- JSON file for category rules
- Enable/disable AI via env variable

**Deliverable**: Working classifier that can categorize emails with >85% accuracy

### Phase 2: Enhancement (Week 5-6)

**Additional Categories**:
- `finance`
- `work`
- `tech`
- `personal`

**Features**:
- User feedback mechanism
- Classification result caching
- Sender domain caching
- Advanced keyword matching (regex support)
- Multi-tag support

**Improvements**:
- Optimize AI prompts based on Phase 1 learnings
- Reduce token usage
- Improve confidence scoring algorithm

### Phase 3: Advanced Features (Future)

**Features**:
- Machine learning from user feedback
- Automatic rule generation from patterns
- Thread-aware classification
- Sender reputation scoring
- Time-based patterns (newsletters on Mondays, etc.)
- Custom user-defined categories
- Classification analytics dashboard

---

## Open Questions for Decision

1. **Scope**: Start with just solicitation detection (original plan) and expand later? Or build full classification system (5 categories) now?

2. **Category Set**: Small focused set (5-7 categories) or comprehensive (15-20)?

3. **User Experience**: How much configuration expected? Simple (just VIP list) or power-user (full rules engine)?

4. **AI Dependency**: Should system work fully without AI (rules-only mode) or is AI required?

5. **Privacy**: Some users won't want to send email data to OpenAI. Should rule-based be a full alternative?

6. **Learning**: Want system to learn from user feedback and auto-generate rules, or keep it static/manual configuration?

7. **Multi-category**: Support multiple categories per email (tags) or force single category?

8. **Thread handling**: Classify emails individually or consider thread context?

---

## Success Metrics

### Accuracy Targets

- **Overall accuracy**: >90% (matches user's expected category)
- **Solicitation detection**: >95% (critical for main use case)
- **False positive rate**: <5% (important emails marked as junk)
- **False negative rate**: <10% (junk marked as important)

### Performance Targets

- **Classification time**: <2 seconds per email (including AI)
- **Batch processing**: 100 emails in <30 seconds
- **Cache hit rate**: >70% (reduce AI calls)
- **Token usage**: <500 tokens average per AI classification

### Cost Targets

- **AI cost**: <$0.01 per email classification
- **Monthly cost**: <$10 for typical user (1000 emails/month)
- **Rules-only mode**: $0 (no AI calls)

### User Experience

- **Setup time**: <10 minutes to configure VIP list
- **Accuracy improvement**: User corrections reduce errors by 50% within 1 week
- **Configuration clarity**: 90% of users understand category meanings

---

## Next Steps

1. **Review and approve** this design document
2. **Choose MVP scope** (answer open questions)
3. **Create detailed technical specification** for chosen approach
4. **Design configuration file formats** (YAML/JSON schemas)
5. **Write AI prompt templates**
6. **Plan testing strategy** (test datasets, accuracy measurement)
7. **Begin implementation** following approved design

---

## References

- Original requirement: IMPLEMENTATION_PLAN.md (Phase 2, Weeks 3-4)
- Target accuracy: >85% for solicitation detection (TECHNICAL_REQUIREMENTS.md)
- Related modules: `src/classifiers/` (PROJECT_STRUCTURE.md)

---

**Document Status**: Draft for review
**Next Review**: After stakeholder feedback
**Implementation Start**: TBD based on approved scope
