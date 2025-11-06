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

✅ **DECISION**: Should use Hybrid
     - Rationale: provides the most value
     - Date: 2025-11-05
     - Status: Approved
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

### Decision Flow - This is good

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

6. **Category Folders**
    - Create category folders using the graph API to move emails to appropriate folder

7. **Mark as read**
    - applies to certain categories

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

## LLM selection

- Should be configurable using the OpenAI Python library
- Local models leveraging Olama should be a phase 1 MVP feature, assume Olama is installed and configured
- Perhpas fine tuning somewhare down the road

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
- LLM (primary and secondary)

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

### Use SQLite for data storage initially

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
- Add language detection (Future)
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
   ✅ **DECISION**: Build full classification system (5 categories)
     - Rationale: More user value, better testing
     - Date: 2025-11-05
     - Status: Approved

2. **Category Set**: Small focused set (5-7 categories) or comprehensive (15-20)?
  ✅ **DECISION**: Start with 5, expand to 10 in Phase 2
     - Rationale: Balance of simplicity and functionality
     - Date: 2025-11-05
     - Status: Approved

3. **User Experience**: How much configuration expected? Simple (just VIP list) or power-user (full rules engine)?
  ✅ **DECISION**: Start VIP list, but architect to expand to power user
     - Rationale: The VIP list might be enough, and it's not clear what additional would be needed for a power-user
     - Date: 2025-11-05
     - Status: Approved

4. **AI Dependency**: Should system work fully without AI (rules-only mode) or is AI required?
  ✅ **DECISION**: AI is required but should be coupled with the rules engine. LLM models should be configurable using the OpenAI library
     - Rationale: AI provides that value that existing rull based systems can't match
     - Date: 2025-11-05
     - Status: Approved

5. **Privacy**: Some users won't want to send email data to OpenAI. Should rule-based be a full alternative?
  ✅ **DECISION**: A rules based engine or an LLM running locally should be options. For the MVP, let's require AI 
     - Rationale: AI provides that value that existing rull based systems can't match
     - Date: 2025-11-05
     - Status: Approved

6. **Learning**: Want system to learn from user feedback and auto-generate rules, or keep it static/manual configuration?
  ✅ **DECISION**: The system should learn from user feedback and auto-generate rules 
     - Rationale: This is a core value prop
     - Date: 2025-11-05
     - Status: Approved

7. **Multi-category**: Support multiple categories per email (tags) or force single category?
  ✅ **DECISION**: The system should support multiple categories 
     - Rationale: Increased flesibility
     - Date: 2025-11-05
     - Status: Approved

8. **Thread handling**: Classify emails individually or consider thread context?
  ✅ **DECISION**: Thread context should be considered 
     - Rationale: If a user replies to an email, that should increase the importance of the email
     - Date: 2025-11-05
     - Status: Approved

---

## Implementation Questions

**Status**: Pending Review
**Purpose**: Clarifications needed before implementation begins

The decisions above provide strategic direction, but several implementation details need clarification to ensure a successful MVP.

### A. MVP Scope Clarification

#### 1. Local LLM Support (Ollama)

**Issue**: Decision #5 says "For the MVP, let's require AI" but the LLM section says "Local models (perhaps leveraging Ollama) should be an MVP feature"

**Question**: Is Ollama (local LLM) support part of MVP or deferred to Phase 2? 

**Answer**: Assume Ollama is installed and configure, Olama provides an OpenAPI compatable API, it should be part of Phase 1

**Considerations**:
- Option A: OpenAI only (simpler, faster to implement, ~2-3 days)
- Option B: OpenAI + Ollama support (more privacy, more complexity, ~5-7 days)
- Ollama requires additional dependencies and testing
- Local models may have lower accuracy than GPT-4

**Impact on Timeline**: Adding Ollama to MVP could extend Weeks 3-4 timeline

**Recommendation**:

- 11/5/2025 - Any OPENAI API compatable LLM should be available via configuration of a URL and model name
- ~~MVP: OpenAI API only (configurable model: GPT-3.5-turbo, GPT-4)~~
- ~~Phase 2: Add Ollama support for privacy-focused users~~

---

#### 2. Auto-Generated Rules from Feedback

**Issue**: Decision #6 says "system should learn from user feedback and auto-generate rules" - this is quite ambitious for MVP

**Question**: Is auto-rule generation part of MVP (Weeks 3-4) or Phase 2?

**Answer**: Move to Phase 2

**Complexity Levels**:
- **Simple** (MVP candidate): "User always marks emails from sender@example.com as junk → add to blocklist"
- **Moderate** (Phase 2): "Pattern detected: emails with subject containing 'newsletter' from domain *.substack.com → auto-categorize as newsletter"
- **Complex** (Phase 3): ML-based pattern recognition and rule synthesis

**Related Questions**:
- Should users approve auto-generated rules before they apply?
- What's the confidence threshold for auto-generated rules?
- How many user corrections needed before generating a rule? (3? 5? 10?)

**Recommendation**:
- MVP: Manual user corrections update cached classifications only (no rule generation)
- Phase 2: Simple sender-based auto-rules (requires approval)
- Phase 3: Pattern-based rule generation with ML

---

#### 3. Category Folders - Auto-Creation

**Issue**: Decision flow step #6 mentions "Create category folders using the graph API to move emails to appropriate folder"

**Question**: Should MVP create category folders automatically, or just classify emails in place?

**Answer**: For MVP, just classify emails in place

**Detailed Specifications Needed**:

**Folder Structure**: What layout?
```
Option A - Flat under Inbox:
Inbox/
  AI-Important/
  AI-Solicitation/
  AI-Newsletter/
  ...

Option B - Nested hierarchy:
Inbox/
  AI-Agent/
    Important/
    Solicitation/
    Newsletter/
    Finance/
    ...

Option C - Configurable root:
{USER_CONFIGURED_ROOT}/
  Important/
  Solicitation/
  ...
```

**Folder Naming**:
- Prefix with "AI-Agent" or emoji? (e.g., "📧 Solicitation")
- Allow user customization of folder names?

**Creation Timing**:
- On first classification of that category?
- On app startup (create all category folders)?
- User-triggered setup command?

**Multi-Category Handling**:
- If email has primary=`important` + secondary=`finance`, which folder?
- Always use primary category for folder placement?

**Existing Folders**:
- Check if folder exists before creating?
- What if user has existing folder with same name?

**User Control**:
- Should users be able to disable auto-folder creation?
- Option to classify-only without moving emails?

**Recommendation for MVP**:
- Classify emails but DO NOT auto-move (classify-only mode)
- Provide classification results and let user decide on actions
- Phase 2: Add optional auto-folder creation with configuration

---

#### 4. Auto-Mark as Read

**Issue**: Decision flow step #7 says "Mark as read applies to certain categories"

**Question**: Which categories should auto-mark as read? What are the rules?

**Answer**: Let's move this to Phase 2

**Detailed Specifications Needed**:

**Which Categories**:
- `solicitation` only?
- `solicitation` + `newsletter`?
- `low_priority` + `solicitation` + `newsletter`?
- User configurable per category?

**Safety Constraints**:
- Confidence threshold: Only mark if confidence >95%?
- VIP exceptions: Never mark VIP senders as read?
- Important exceptions: Never mark anything tagged as `important`?

**User Control**:
- Global enable/disable toggle?
- Per-category configuration?
- Preview mode: Show what will be marked before applying?

**Recommendation for MVP**:
- DO NOT auto-mark as read in MVP (too risky)
- Show classification results only
- Phase 2: Add optional auto-mark with strict safeguards (opt-in, high confidence only)

---

### B. Technical Specifications

#### 5. Classification History Storage

**Issue**: Decisions require learning from feedback, but no storage format defined

**Question**: What database/storage format for classification history and user feedback?

**Answer**:  Use SQLite for MVP

**Options**:
- **JSON files** (simple, no dependencies, good for MVP)
- **SQLite** (structured, queryable, lightweight)
- **PostgreSQL** (overkill for MVP, better for production)
- **Vector DB** (ChromaDB, Pinecone - for similarity search, Phase 3)

**Data to Store**:
```python
{
  "email_id": "AAMkAGI...",
  "sender": "newsletter@example.com",
  "sender_domain": "example.com",
  "subject": "Weekly Newsletter #42",
  "classification": {
    "primary_category": "newsletter",
    "secondary_categories": ["tech"],
    "confidence": 0.87,
    "method": "ai",
    "ai_reasoning": "Regular newsletter format with unsubscribe link"
  },
  "user_feedback": {
    "corrected_to": "solicitation",
    "timestamp": "2025-11-05T10:30:00Z"
  },
  "timestamp": "2025-11-05T10:25:00Z"
}
```

**Retention**:
- How long to keep classification history?
- Privacy: Store email content or just metadata?

**Recommendation for MVP**:
- SQLite for classification history (structured, easy to query)
- JSON for user feedback log (simple append-only)
- Vector DB deferred to Phase 3

---

#### 6. Thread Context - Implementation Details

**Issue**: Decision #8 requires thread context consideration, but implementation unclear

**Question**: How much thread context to fetch and analyze?

**Graph API Considerations**:
- Fetching full thread = multiple API calls per email
- 100 emails could become 300+ API calls (performance impact)
- Rate limiting concerns

**Implementation Options**:

**Option A - Minimal Metadata** (Recommended for MVP):
```
Fetch from email metadata:
- conversationId (free, included in email object)
- isRead status
- hasAttachments
- importance flag
- user is in To/CC/BCC

Derive signals:
- User replied to thread = boost importance
- Thread has >3 messages = likely conversation
```

**Option B - Thread Summary**:
```
Additional API call to get thread:
- Participant count
- Message count in thread
- User participation (how many times user replied)

Use signals to adjust classification:
- User replied 2+ times = important
- Only received, never replied = normal
```

**Option C - Full Thread Analysis**:
```
Fetch all messages in thread
Analyze conversation flow
Classify based on thread content

Too expensive for MVP
```

**Thread Signals for Classification**:
- User replied to email → boost importance score by +0.2
- User is original sender → always important
- Thread has >5 participants → likely work-related
- Thread age >30 days with no user replies → decrease importance

**Edge Cases**:
- What if user replies to spam? (Don't auto-mark spam as important)
- Should require 2+ signals before boosting importance

**Recommendation for MVP**:
- Use minimal metadata approach (Option A)
- Add simple thread signals (user replied = boost importance)
- Defer full thread analysis to Phase 2

---

#### 7. Multi-Category Behavior

**Issue**: Decision #7 enables multi-category, but automation rules unclear

**Question**: How to handle folder moves and actions with multi-category emails?

**Scenarios**:
```
Email classified as:
- Primary: important
- Secondary: [finance, work]

Actions to take:
- Move to which folder? → Follow primary category
- Mark as read? → Never (important)
- Apply which rules? → Primary category rules only
```

**Hierarchy Definition**:
```
1. VIP sender rules (highest priority, always apply)
2. Primary category (drives folder location, read status)
3. Secondary categories (tags only, for filtering/search)
4. Default behavior (fallback if no match)
```

**Recommendation**:
- Primary category drives all automatic actions
- Secondary categories are metadata/tags only
- Document clear hierarchy in user guide

---

### C. Configuration & User Experience

#### 8. Folder Naming Convention

**Question**: If we implement auto-folder creation (Phase 2), what naming convention?

**Options**:
- `AI-Agent/{category}` (clear prefix, organized)
- `AI/{category}` (shorter)
- `📧 {category}` (emoji prefix, visual)
- `{category}` (clean but could conflict)
- User configurable template

**Recommendation**:
- Default: `AI-Agent/{category}`
- Allow customization via config file
- Check for conflicts before creating

---

#### 9. Per-Sender LLM Configuration

**Issue**: VIP/Important Senders section mentions "LLM (primary and secondary)"

**Question**: What's the use case for per-sender LLM configuration?

**Possible Scenarios**:
- Use GPT-4 for VIP senders, GPT-3.5-turbo for others? (cost optimization)
- Use local LLM for privacy-sensitive senders?

**Complexity Assessment**:
- Adds significant configuration complexity
- Marginal benefit for most users
- Better to have global LLM config with quality tiers

**Recommendation**:
- Defer per-sender LLM to Phase 3
- MVP: Single global LLM configuration
- Phase 2: Consider LLM tiers (high/medium/low priority use different models)

---

### D. Performance & Scalability

#### 10. Classification Latency with Thread Context

**Question**: What's acceptable latency for thread-aware classification?

**Benchmarks**:
- Current (no thread): ~1-2 seconds per email
- With thread metadata: ~1.5-2.5 seconds per email
- With full thread analysis: ~3-5 seconds per email

**Batch Processing**:
- 100 emails with minimal thread context: ~2-3 minutes
- 100 emails with full thread analysis: ~5-8 minutes

**Target**: Keep under 3 minutes for 100 emails in MVP

**Recommendation**:
- Use minimal thread metadata (adds <0.5s per email)
- Implement parallel processing for batch classification
- Add progress indicators for user feedback

---

#### 11. Classification Cache TTL

**Question**: Should classification results be cached indefinitely or have TTL?

**Considerations**:
- Sender behavior changes over time
- Rules get updated
- User preferences evolve

**Options**:
- No TTL (cache forever, invalidate on user correction)
- 30-day TTL (re-classify monthly)
- 90-day TTL (re-classify quarterly)
- Configurable TTL

**Recommendation for MVP**:
- Cache sender-based classifications for 90 days
- Invalidate immediately on user correction
- Allow manual cache clearing

---

### E. MVP Feature Set Recommendation

To keep MVP focused and achievable in Weeks 3-4:

**✅ Include in MVP:**
- 5 core categories (important, solicitation, newsletter, transactional, normal)
- Hybrid approach (primary category + secondary tags)
- VIP sender list (YAML config)
- Basic rule-based classification (keyword matching, sender patterns)
- Any OPENAI API compatable LLM should be available via configuration of a URL and model name
- Structured AI prompts (Option C: JSON response with reasoning)
- SQLite for classification history
- JSON file for user feedback logging
- Basic thread metadata (conversationId, user replied signal)
- Classify-only mode (no auto-move, no auto-mark-read)
- Confidence scoring and logging
- Classification metadata tracking

**⏸️ Defer to Phase 2:**
- Ollama/local LLM support
- Auto-rule generation from feedback
- Category folder auto-creation
- Auto-mark emails as read
- Advanced thread analysis (full thread content)
- Sender domain caching with TTL
- Additional categories (finance, work, tech, personal)
- Multi-tag UI/reporting

**⏸️ Defer to Phase 3:**
- Vector DB for similarity search
- Per-sender LLM configuration
- ML-based pattern recognition
- Advanced rule synthesis
- Classification analytics dashboard
- A/B testing different prompts

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
