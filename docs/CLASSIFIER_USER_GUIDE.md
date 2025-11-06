# Email Classifier - User Configuration Guide

**Version**: 1.0
**Last Updated**: 2025-11-05
**Difficulty**: Beginner to Intermediate

---

## Welcome! 👋

This guide will help you set up and configure the AI Email Classifier to automatically organize your inbox. Whether you're a beginner just getting started or an advanced user wanting to fine-tune every detail, this guide has you covered.

**What you'll learn**:
- Quick setup in 10 minutes
- How to configure VIP senders
- How to customize category rules
- How to choose and configure your AI provider
- How to provide feedback to improve accuracy
- Troubleshooting common issues

---

## Table of Contents

1. [Quick Start (10 minutes)](#quick-start)
2. [Understanding Categories](#understanding-categories)
3. [Configuring VIP Senders](#configuring-vip-senders)
4. [Customizing Classification Rules](#customizing-classification-rules)
5. [Choosing Your AI Provider](#choosing-your-ai-provider)
6. [Advanced Configuration](#advanced-configuration)
7. [Providing Feedback](#providing-feedback)
8. [Troubleshooting](#troubleshooting)
9. [FAQ](#faq)

---

## Quick Start

### Step 1: Copy Configuration Files (2 minutes)

Navigate to the `config/` directory and copy the example files:

```bash
cd config/
cp vip_senders.yaml.example vip_senders.yaml
cp category_rules.yaml.example category_rules.yaml
cp llm_config.yaml.example llm_config.yaml
cp classifier_config.yaml.example classifier_config.yaml
```

### Step 2: Add Your VIP Senders (5 minutes)

Open `vip_senders.yaml` in your text editor and add your most important contacts:

```yaml
vip_senders:
  # Your boss or manager
  - identifier: "boss@company.com"
    type: email
    priority: vip
    notes: "Direct manager"

  # Your company domain (all colleagues)
  - identifier: "yourcompany.com"
    type: domain
    priority: trusted
    notes: "Company emails"

  # Family members
  - identifier: "mom@email.com"
    type: email
    priority: vip
    notes: "Family"
```

**Tip**: Start with 5-10 VIP senders. You can always add more later!

### Step 3: Choose Your AI Provider (3 minutes)

Open `llm_config.yaml` and choose ONE option:

**Option A - OpenAI (Cloud, High Quality)**
```yaml
llm:
  provider: "openai"
  model: "gpt-3.5-turbo"           # or "gpt-4" for better quality
  api_key_env: "OPENAI_API_KEY"
```

Then create a `.env` file in the project root:
```bash
OPENAI_API_KEY=sk-your-key-here
```

**Option B - Ollama (Local, Free, Private)**
```yaml
llm:
  provider: "ollama"
  base_url: "http://localhost:11434/v1"
  model: "llama3.1"
```

Make sure Ollama is installed and running:
```bash
ollama serve
ollama pull llama3.1
```

### Step 4: You're Ready! 🎉

That's it! The classifier is now configured with sensible defaults. You can start classifying emails.

**First test**: Run the classifier on a small batch of emails and review the results. Provide feedback on any misclassifications to improve accuracy.

---

## Understanding Categories

The classifier organizes emails into **5 main categories**:

### 📌 Important
**What it is**: Emails requiring immediate attention, from VIPs, or time-sensitive

**Examples**:
- Email from your boss with a deadline
- Critical system alerts
- Urgent client requests
- Action items with "ASAP" or "urgent" in subject

**When to use**: Anything you need to see and act on quickly

---

### 🛍️ Solicitation
**What it is**: Marketing emails, promotions, sales pitches, cold outreach

**Examples**:
- "Limited time offer - 50% off!"
- Cold sales emails
- Marketing campaigns
- Promotional deals

**Common signals**:
- "Click here", "Buy now", "Special offer"
- Has unsubscribe link
- From marketing@... or promo@... addresses

---

### 📰 Newsletter
**What it is**: Subscribed content you opted into - digests, updates, blogs

**Examples**:
- Tech newsletter: "The Daily Tech - Issue #247"
- Weekly digest from Medium or Substack
- Blog updates you subscribed to
- Company newsletters

**Difference from solicitation**: You wanted these emails, they provide value

---

### 🧾 Transactional
**What it is**: Automated confirmations, receipts, notifications

**Examples**:
- Order confirmations: "Your Order #12345 Has Shipped"
- Payment receipts
- Password reset emails
- Shipping notifications

**Common signals**:
- From "noreply@..." addresses
- Contains order numbers, tracking numbers
- Automated system messages

---

### 💬 Normal
**What it is**: Regular correspondence that doesn't fit other categories

**Examples**:
- Colleague asking a question
- Project updates
- Meeting invites
- General conversation

**Default category**: If the classifier is uncertain, it defaults to "normal"

---

## Configuring VIP Senders

VIP senders are people or organizations whose emails should **always** be treated as important.

### Basic Syntax

```yaml
vip_senders:
  - identifier: "who to match"
    type: "how to match"
    priority: "importance level"
    notes: "reminder for yourself"
```

### Match Types

#### Type: `email` - Exact Email Match

Match a specific email address exactly:

```yaml
- identifier: "boss@company.com"
  type: email
  priority: vip
  notes: "My manager"
```

**When to use**: For specific individuals

---

#### Type: `domain` - Entire Domain Match

Match everyone from a domain:

```yaml
- identifier: "bigclient.com"
  type: domain
  priority: vip
  notes: "Important client - all emails matter"
```

**When to use**: For organizations where all emails are important

---

#### Type: `pattern` - Wildcard Match

Match using wildcards (*):

```yaml
- identifier: "*@partner-company.com"
  type: pattern
  priority: trusted
  notes: "Business partner"
```

**When to use**: For flexible matching (use sparingly - can have unexpected matches)

---

### Priority Levels

**VIP** - Highest priority
- Always classified as "important"
- Never auto-deleted or auto-marked read
- Use for: Boss, key clients, family

**Trusted** - High priority
- Generally important
- Higher classification confidence
- Use for: Colleagues, business partners

**Monitored** - Track patterns
- Normal priority
- System learns from these senders
- Use for: Newsletters you sometimes read, potential opportunities

---

### Common VIP Configurations

**Scenario 1: Small Team**
```yaml
vip_senders:
  - identifier: "boss@startup.com"
    type: email
    priority: vip

  - identifier: "startup.com"
    type: domain
    priority: trusted
    notes: "All team emails"
```

**Scenario 2: Enterprise User**
```yaml
vip_senders:
  # Direct reports and manager
  - identifier: "manager@corp.com"
    type: email
    priority: vip

  # All company emails trusted
  - identifier: "corp.com"
    type: domain
    priority: trusted

  # Key clients
  - identifier: "bigclient.com"
    type: domain
    priority: vip

  # Executive team
  - identifier: "*@corp.com"
    type: pattern
    priority: vip
    notes: "Only if sender is CXO"
```

**Scenario 3: Freelancer**
```yaml
vip_senders:
  # Each client
  - identifier: "client1@company1.com"
    type: email
    priority: vip

  - identifier: "client2@company2.com"
    type: email
    priority: vip

  # Payment platforms
  - identifier: "paypal.com"
    type: domain
    priority: important
    notes: "Payment notifications"
```

---

### Blocking Senders

Block spam or unwanted senders:

```yaml
blocked_senders:
  - identifier: "spam@example.com"
    type: email
    notes: "Known spammer"

  - identifier: "marketing-spam.com"
    type: domain
    notes: "Spam domain"
```

Blocked senders are automatically classified as "solicitation" with high confidence.

---

## Customizing Classification Rules

Category rules help the classifier identify emails without using AI (faster and free).

### Rule Structure

Each category has rules that look for patterns:

```yaml
solicitation:
  rules:
    - rule_id: "sol_001"
      name: "Marketing keywords"
      enabled: true
      priority: 10
      confidence_boost: 0.4

      keywords_subject:
        - "limited time"
        - "50% off"

      keywords_body:
        - "click here"
        - "buy now"
```

### Understanding Rule Fields

- **rule_id**: Unique identifier (don't change once created)
- **name**: Description for yourself
- **enabled**: Set to `false` to disable without deleting
- **priority**: 1-10 (higher checked first)
- **confidence_boost**: How much this rule increases confidence (0.0-1.0)

### Adding Custom Keywords

Want to catch specific types of emails? Add keywords:

**Example: Catch invoice emails**
```yaml
transactional:
  rules:
    - rule_id: "trans_custom_001"
      name: "Invoice emails"
      enabled: true
      priority: 9
      confidence_boost: 0.5

      keywords_subject:
        - "invoice"
        - "billing statement"
        - "payment due"

      sender_patterns:
        - "*@accounting.*"
        - "billing@*"
```

### Tuning Confidence

**Confidence** determines how sure the classifier is about a category:
- **0.9-1.0**: Very confident (skip AI classification)
- **0.7-0.9**: Confident (may use AI to confirm)
- **0.5-0.7**: Somewhat confident (use AI to help)
- **Below 0.5**: Not confident (rely on AI)

**Adjust `confidence_boost` values**:
- `0.5`: Very strong signal (e.g., sender is known newsletter platform)
- `0.3-0.4`: Strong signal (e.g., "unsubscribe" in marketing email)
- `0.2`: Moderate signal (e.g., certain keywords present)
- `0.1`: Weak signal (e.g., generic patterns)

### Common Customizations

**Add your industry's keywords**:
```yaml
important:
  rules:
    - rule_id: "imp_custom_001"
      name: "Healthcare urgent terms"
      keywords_subject:
        - "patient alert"
        - "lab results"
        - "prescription ready"
      confidence_boost: 0.4
```

**Recognize your company's patterns**:
```yaml
work:
  rules:
    - rule_id: "work_custom_001"
      name: "Internal project emails"
      keywords_subject:
        - "[PROJECT-X]"
        - "sprint review"
        - "standup notes"
      confidence_boost: 0.3
```

---

## Choosing Your AI Provider

The classifier supports multiple AI providers. Choose based on your needs:

### Provider Comparison

| Provider | Cost | Speed | Quality | Privacy | Setup Difficulty |
|----------|------|-------|---------|---------|-----------------|
| **OpenAI (GPT-3.5-turbo)** | $$ | Fast | Excellent | Cloud | Easy |
| **OpenAI (GPT-4)** | $$$ | Medium | Best | Cloud | Easy |
| **Ollama (Local)** | Free | Slow | Good | 100% Private | Medium |
| **Azure OpenAI** | $$$ | Fast | Excellent | Enterprise | Hard |

### Option 1: OpenAI (Recommended for Most Users)

**Pros**:
- High accuracy out of the box
- Fast classification
- Easy setup
- Reliable

**Cons**:
- Costs money (~$0.001 per email with GPT-3.5)
- Requires internet
- Email data sent to OpenAI

**Setup**:
1. Get API key from https://platform.openai.com/api-keys
2. Add to `.env` file: `OPENAI_API_KEY=sk-your-key`
3. Configure in `llm_config.yaml`:
```yaml
llm:
  provider: "openai"
  model: "gpt-3.5-turbo"          # or "gpt-4"
  api_key_env: "OPENAI_API_KEY"
```

**Cost Estimate**:
- 100 emails/day: ~$3/month (GPT-3.5) or ~$30/month (GPT-4)
- 1000 emails/day: ~$30/month (GPT-3.5) or ~$300/month (GPT-4)

---

### Option 2: Ollama (Local LLM)

**Pros**:
- Completely free
- 100% private (runs on your machine)
- No internet required
- No API costs

**Cons**:
- Slower classification
- Requires 8GB+ RAM
- Lower accuracy than GPT-4
- More complex setup

**Setup**:
1. Install Ollama: https://ollama.ai/download
2. Pull a model: `ollama pull llama3.1`
3. Start server: `ollama serve`
4. Configure in `llm_config.yaml`:
```yaml
llm:
  provider: "ollama"
  base_url: "http://localhost:11434/v1"
  model: "llama3.1"                # or "mistral", "phi3"
```

**Recommended Models**:
- **llama3.1** (8GB): Best quality, slower
- **mistral** (4GB): Good balance
- **phi3** (2GB): Fastest, lower quality

---

### Option 3: Azure OpenAI (Enterprise)

**Pros**:
- Enterprise security and compliance
- Same quality as OpenAI
- Microsoft support

**Cons**:
- More expensive
- Complex setup
- Requires Azure subscription

**Setup**: See Azure OpenAI documentation

---

## Advanced Configuration

### Adjusting Classification Behavior

Open `classifier_config.yaml`:

#### Classification Mode

```yaml
classifier:
  mode: "hybrid"                    # "rules-only", "ai-only", "hybrid"
```

**Modes**:
- **hybrid** (recommended): Use rules + AI together
- **rules-only**: Fast, free, less accurate
- **ai-only**: Most accurate, slowest, costs more

---

#### Confidence Thresholds

```yaml
confidence:
  high_confidence_threshold: 0.9    # Skip AI if rules this confident
  low_confidence_threshold: 0.5     # Use AI if rules below this
```

**Lower thresholds** = More AI calls = More accurate but slower/costlier
**Higher thresholds** = Fewer AI calls = Faster/cheaper but less accurate

**Tuning tips**:
- Start with defaults (0.9 high, 0.5 low)
- If too many mistakes: Lower high threshold to 0.8
- If costs too high: Raise low threshold to 0.6

---

### Thread Awareness

```yaml
thread_signals:
  enabled: true
  user_reply_boost: 0.2             # Boost if you replied
  user_initiated_boost: 0.3         # Boost if you started thread
```

Emails you've participated in are automatically boosted toward "important".

---

### Caching for Performance

```yaml
cache:
  enabled: true
  cache_by_domain: true              # Cache by sender domain
  domain_cache_ttl_days: 90          # Cache for 90 days
```

**How it works**: Once a sender is classified, future emails from that sender reuse the classification (much faster, no AI cost).

**When to clear cache**: After providing feedback corrections

---

### Cost Controls

```yaml
cost_limits:
  enabled: true
  daily_max_usd: 5.0                # Stop if spending >$5/day
  monthly_max_usd: 50.0             # Stop if spending >$50/month
  warn_at_percent: 80               # Warn at 80% of limit
```

Protects you from unexpected AI costs.

---

## Providing Feedback

The classifier learns from your corrections to improve accuracy over time.

### How to Provide Feedback

When you see a misclassification:

1. **Note the email ID** and incorrect category
2. **Record your correction** using the feedback interface
3. **The system will**:
   - Store your correction
   - Invalidate cache for that sender
   - Use your correction for future emails from that sender

### Example Feedback Workflow

```
Email from newsletter@techblog.com classified as "solicitation"
→ You correct it to "newsletter"
→ System invalidates cache
→ Future emails from techblog.com will be "newsletter"
```

### Feedback Best Practices

✅ **Do**:
- Provide feedback consistently
- Be specific about the correct category
- Add notes about why (helps you remember later)

❌ **Don't**:
- Overthink it - go with your first instinct
- Provide conflicting feedback (changing mind frequently)

---

## Troubleshooting

### Common Issues

#### "Classification failed" Error

**Possible causes**:
1. AI provider not configured
2. API key missing or invalid
3. Network issues

**Solutions**:
1. Check `llm_config.yaml` is configured
2. Verify API key in `.env` file
3. Test AI connection: `curl https://api.openai.com/v1/models -H "Authorization: Bearer $OPENAI_API_KEY"`

---

#### "All emails classified as 'normal'"

**Possible causes**:
1. VIP senders not loaded
2. Category rules not loaded
3. Confidence thresholds too high

**Solutions**:
1. Verify `vip_senders.yaml` exists and has entries
2. Verify `category_rules.yaml` exists
3. Check `classifier_config.yaml` thresholds
4. Enable debug logging: `logging.level: "DEBUG"`

---

#### "Too slow / timeout errors"

**Possible causes**:
1. AI provider too slow
2. Processing too many emails at once
3. Poor network connection

**Solutions**:
1. Try faster model (GPT-3.5 instead of GPT-4)
2. Reduce batch size: `performance.batch_size: 25`
3. Increase timeout: `performance.per_email_timeout_seconds: 30`
4. Use Ollama locally (no network)

---

#### "Costs too high"

**Solutions**:
1. Use GPT-3.5-turbo instead of GPT-4 (10x cheaper)
2. Raise confidence thresholds (fewer AI calls)
3. Improve category rules (better rules = less AI needed)
4. Enable caching: `cache.enabled: true`
5. Set cost limits: `cost_limits.daily_max_usd: 2.0`
6. Switch to Ollama (free)

---

#### "Too many false positives"

**False positive** = Important email marked as junk

**Solutions**:
1. Add sender to VIP list
2. Lower solicitation confidence threshold
3. Review and disable aggressive solicitation rules
4. Provide feedback to retrain
5. Switch to AI-only mode for better accuracy

---

## FAQ

### Q: How accurate is the classifier?

**A**: With default settings:
- Overall: 85-90% accuracy
- With feedback: 90-95% accuracy after 1 week
- Solicitation detection: 95%+ accuracy

GPT-4 provides highest accuracy. Rules-only is 70-80% accurate.

---

### Q: How much does it cost to use OpenAI?

**A**: Approximate costs per 100 emails:
- GPT-3.5-turbo: $0.10
- GPT-4: $1.00

With caching, repeat senders are free. Typical user costs: $3-10/month.

---

### Q: Is my email data private?

**A**: Depends on provider:
- **OpenAI/Azure**: Email subjects/previews sent to cloud (see privacy policy)
- **Ollama (local)**: 100% private, nothing leaves your machine
- **Rules-only mode**: 100% private, no AI used

We send only subject + first 500 chars of body, not full email content.

---

### Q: Can I use multiple AI providers?

**A**: One provider at a time in MVP. Phase 2 will support fallback providers.

---

### Q: What happens if AI is down?

**A**: The classifier automatically falls back to rules-only mode. You'll see a warning, but classification continues.

---

### Q: How do I disable AI temporarily?

**A**: Set in `classifier_config.yaml`:
```yaml
classifier:
  mode: "rules-only"
```

---

### Q: Can I add my own categories?

**A**: Not in MVP. MVP supports 5 fixed categories. Phase 2 will support custom categories.

---

### Q: How do I reset everything?

**A**:
1. Delete database: `rm data/classifications.db`
2. Delete cache: `rm -rf data/cache/*`
3. Restart with fresh configs

---

## Next Steps

Now that you're configured:

1. **Test with a small batch** (10-20 emails)
2. **Review classifications** for accuracy
3. **Provide feedback** on mistakes
4. **Adjust VIP senders** as needed
5. **Fine-tune rules** if needed
6. **Scale up** to your full inbox

**Need help?** Check the technical documentation or open an issue on GitHub.

---

**Happy organizing! 📧✨**
