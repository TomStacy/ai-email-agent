# Setup Guide

## Prerequisites

Before starting, ensure you have:
- Python 3.11 or higher installed
- Git installed
- An Office 365 account
- An OpenAI API account
- Access to Azure Portal (for app registration)

---

## Step 1: Install uv

### Install uv Package Manager

```bash
# Windows (PowerShell)
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Verify installation:
```bash
uv --version
```

---

## Step 2: Clone and Setup Project

### Clone Repository and Setup Environment

```bash
cd E:\Repos\ai-email-agent

# Create virtual environment with uv
uv venv

# Activate virtual environment
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate
```

### Install Dependencies

```bash
# Install production dependencies
uv pip install -r requirements.txt

# Install development dependencies
uv pip install -r requirements-dev.txt

# Or install all at once using pyproject.toml
uv pip install -e ".[dev]"
```

---

## Step 3: Azure App Registration

### Create Azure AD Application

1. **Navigate to Azure Portal**
   - Go to https://portal.azure.com
   - Sign in with your Office 365 account

2. **Register New Application**
   - Go to "Azure Active Directory" > "App registrations"
   - Click "New registration"
   - Name: "AI Email Agent"
   - Supported account types: "Accounts in this organizational directory only"
   - Redirect URI: Leave blank for now (we'll use device code flow)
   - Click "Register"

3. **Note Application Details**
   - Copy the **Application (client) ID**
   - Copy the **Directory (tenant) ID**

4. **Create Client Secret**
   - Go to "Certificates & secrets"
   - Click "New client secret"
   - Description: "AI Email Agent Secret"
   - Expires: Choose duration (recommended: 12-24 months)
   - Click "Add"
   - **IMPORTANT**: Copy the secret value immediately (it won't be shown again)

5. **Configure API Permissions**
   - Go to "API permissions"
   - Click "Add a permission"
   - Select "Microsoft Graph"
   - Select "Delegated permissions"
   - Add the following permissions:
     - `Mail.Read`
     - `Mail.ReadWrite`
     - `User.Read`
   - Click "Add permissions"
   - Click "Grant admin consent" (if you have admin rights)

### Configure Authentication

1. **Enable Public Client Flow**
   - Go to "Authentication"
   - Under "Advanced settings" > "Allow public client flows"
   - Set "Enable the following mobile and desktop flows" to **Yes**
   - Click "Save"

---

## Step 4: OpenAI API Setup

### Get API Key

1. **Create OpenAI Account**
   - Go to https://platform.openai.com
   - Sign up or log in

2. **Generate API Key**
   - Go to "API keys" section
   - Click "Create new secret key"
   - Name: "AI Email Agent"
   - Copy the API key immediately

3. **Add Billing Information** (if not already done)
   - Set up payment method
   - Configure usage limits

---

## Step 5: Environment Configuration

### Create Environment File

Create a `.env` file in the project root:

```bash
# Copy example file
copy .env.example .env  # Windows
# or
cp .env.example .env    # macOS/Linux
```

### Configure Environment Variables

Edit `.env` file with your credentials:

```env
# Microsoft Azure Configuration
AZURE_CLIENT_ID=your_application_client_id_here
AZURE_CLIENT_SECRET=your_client_secret_here
AZURE_TENANT_ID=your_tenant_id_here
AZURE_AUTHORITY=https://login.microsoftonline.com/your_tenant_id_here
AZURE_SCOPE=https://graph.microsoft.com/.default

# Microsoft Graph API
GRAPH_API_ENDPOINT=https://graph.microsoft.com/v1.0

# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4
OPENAI_MAX_TOKENS=1000

# Application Settings
LOG_LEVEL=INFO
MAX_EMAILS_PER_SCAN=100
BATCH_SIZE=50
CACHE_ENABLED=true
CACHE_TTL=3600

# Email Operation Settings
ENABLE_DELETE=false
ENABLE_MOVE=true
DRY_RUN=true
```

### Important Settings

- **DRY_RUN=true**: Start with dry run mode to test without making changes
- **ENABLE_DELETE=false**: Disable delete operations initially for safety
- **LOG_LEVEL=INFO**: Set to DEBUG for detailed logging during setup

---

## Step 6: Project Initialization

### Create Directory Structure

```bash
# Create necessary directories
mkdir data\cache data\logs config tests\fixtures
```

### Initialize Configuration Files

Create `config/settings.yaml`:

```yaml
email:
  folders_to_scan:
    - Inbox
    - Spam
  skip_folders:
    - Deleted Items
    - Archive
  
classification:
  confidence_threshold: 0.7
  enable_ai: true
  enable_rules: true
  categories:
    - solicitation
    - newsletter
    - important
    - personal

operations:
  max_batch_size: 50
  enable_undo: true
  log_operations: true

summarization:
  max_emails_per_summary: 20
  summary_length: short  # short, medium, long
  include_action_items: true
  priority_only: false
```

Create `config/rules.json`:

```json
{
  "solicitation": {
    "keywords": [
      "unsubscribe",
      "promotional",
      "limited time offer",
      "act now",
      "free trial",
      "click here",
      "special offer"
    ],
    "sender_domains": [
      "marketing.company.com",
      "promo.example.com"
    ],
    "exclude_senders": [
      "team@yourcompany.com"
    ]
  },
  "important": {
    "keywords": [
      "urgent",
      "action required",
      "deadline",
      "asap",
      "immediate attention"
    ],
    "vip_senders": [
      "boss@company.com",
      "client@important.com"
    ]
  }
}
```

---

## Step 7: Verify Installation

### Test Python Environment

```bash
# Verify Python version
python --version
# Should show 3.11 or higher

# Verify uv installation
uv --version

# List installed packages
uv pip list
```

### Test Configuration Loading

Create a test script `scripts/test_config.py`:

```python
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Verify Azure configuration
print("Azure Configuration:")
print(f"Client ID: {os.getenv('AZURE_CLIENT_ID')[:8]}...")
print(f"Tenant ID: {os.getenv('AZURE_TENANT_ID')[:8]}...")
print(f"Client Secret: {'Set' if os.getenv('AZURE_CLIENT_SECRET') else 'Not Set'}")

# Verify OpenAI configuration
print("\nOpenAI Configuration:")
print(f"API Key: {os.getenv('OPENAI_API_KEY')[:8]}...")
print(f"Model: {os.getenv('OPENAI_MODEL')}")

print("\nConfiguration loaded successfully!")
```

Run the test:

```bash
uv run python scripts/test_config.py
```

---

## Step 8: First Authentication Test

### Test Azure Authentication

Create a test script `scripts/test_auth.py`:

```python
from msal import PublicClientApplication
import os
from dotenv import load_dotenv

load_dotenv()

# Initialize MSAL client
app = PublicClientApplication(
    client_id=os.getenv('AZURE_CLIENT_ID'),
    authority=os.getenv('AZURE_AUTHORITY')
)

# Request device code
flow = app.initiate_device_flow(scopes=[os.getenv('AZURE_SCOPE')])

if "user_code" not in flow:
    raise ValueError("Failed to create device flow")

print(flow["message"])
print("\nWaiting for authentication...")

# Wait for user to authenticate
result = app.acquire_token_by_device_flow(flow)

if "access_token" in result:
    print("\n✓ Authentication successful!")
    print(f"Token acquired for: {result.get('id_token_claims', {}).get('preferred_username')}")
else:
    print("\n✗ Authentication failed!")
    print(result.get("error"))
    print(result.get("error_description"))
```

Run the authentication test:

```bash
uv run python scripts/test_auth.py
```

Follow the instructions to authenticate via the device code flow.

---

## Step 9: Test Graph API Connection

Create a test script `scripts/test_graph_api.py`:

```python
import requests
from msal import PublicClientApplication
import os
from dotenv import load_dotenv

load_dotenv()

# Authenticate and get token
app = PublicClientApplication(
    client_id=os.getenv('AZURE_CLIENT_ID'),
    authority=os.getenv('AZURE_AUTHORITY')
)

# Try to get cached token or authenticate
accounts = app.get_accounts()
if accounts:
    result = app.acquire_token_silent(
        scopes=[os.getenv('AZURE_SCOPE')],
        account=accounts[0]
    )
else:
    print("No cached token. Please run test_auth.py first.")
    exit(1)

if "access_token" in result:
    token = result["access_token"]
    
    # Test API call - get user profile
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(
        f"{os.getenv('GRAPH_API_ENDPOINT')}/me",
        headers=headers
    )
    
    if response.status_code == 200:
        user = response.json()
        print("✓ Graph API connection successful!")
        print(f"User: {user.get('displayName')}")
        print(f"Email: {user.get('mail') or user.get('userPrincipalName')}")
        
        # Test getting messages
        messages_response = requests.get(
            f"{os.getenv('GRAPH_API_ENDPOINT')}/me/messages?$top=5",
            headers=headers
        )
        
        if messages_response.status_code == 200:
            messages = messages_response.json()
            print(f"\n✓ Successfully retrieved {len(messages.get('value', []))} messages")
            print("\nRecent messages:")
            for msg in messages.get('value', [])[:3]:
                print(f"  - {msg.get('subject')} (from: {msg.get('from', {}).get('emailAddress', {}).get('address')})")
        else:
            print(f"\n✗ Failed to retrieve messages: {messages_response.status_code}")
    else:
        print(f"✗ API call failed: {response.status_code}")
        print(response.text)
else:
    print("✗ Failed to acquire token")
```

Run the Graph API test:

```bash
uv run python scripts/test_graph_api.py
```

---

## Step 10: Test OpenAI Integration

Create a test script `scripts/test_openai.py`:

```python
from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

# Test classification prompt
test_email = {
    "subject": "Limited Time Offer - 50% Off Everything!",
    "from": "marketing@promo-deals.com",
    "body": "Don't miss out! Click here now for amazing savings. Unsubscribe anytime."
}

prompt = f"""Classify the following email as either 'solicitation', 'important', or 'normal'.

Subject: {test_email['subject']}
From: {test_email['from']}
Body: {test_email['body']}

Respond with only the classification and confidence (0-1).
Format: classification|confidence"""

try:
    response = client.chat.completions.create(
        model=os.getenv('OPENAI_MODEL', 'gpt-4'),
        messages=[
            {"role": "system", "content": "You are an email classification assistant."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=50,
        temperature=0.3
    )
    
    result = response.choices[0].message.content.strip()
    print("✓ OpenAI API connection successful!")
    print(f"Test classification result: {result}")
    print(f"Tokens used: {response.usage.total_tokens}")
    
except Exception as e:
    print(f"✗ OpenAI API call failed: {str(e)}")
```

Run the OpenAI test:

```bash
uv run python scripts/test_openai.py
```

---

## Step 11: Initialize Git Repository

```bash
# Initialize git (if not already done)
git init

# Add all files
git add .

# Create initial commit
git commit -m "Initial project setup"

# Create develop branch
git checkout -b develop
```

---

## Troubleshooting

### Issue: Authentication Fails

**Problem**: Device code flow doesn't work
**Solution**:
1. Verify client ID and tenant ID are correct
2. Check that "Allow public client flows" is enabled in Azure
3. Ensure you're using the correct Microsoft account
4. Clear browser cache and try again

### Issue: API Permissions Error

**Problem**: "Insufficient privileges" error
**Solution**:
1. Verify API permissions are configured correctly
2. Grant admin consent if required
3. Wait a few minutes after granting permissions
4. Re-authenticate to get new token with updated permissions

### Issue: OpenAI API Error

**Problem**: "Invalid API key" or rate limit errors
**Solution**:
1. Verify API key is correct (check for extra spaces)
2. Ensure billing is set up on OpenAI account
3. Check usage limits and quotas
4. Try a different model (gpt-3.5-turbo instead of gpt-4)

### Issue: uv Command Not Found

**Problem**: `uv` command not recognized
**Solution**:
1. Ensure uv is installed: Run the installation command again
2. Restart your terminal after installation
3. Check if uv is in your PATH
4. On Windows, you may need to restart PowerShell with admin privileges

### Issue: Import Errors

**Problem**: "ModuleNotFoundError"
**Solution**:
1. Verify virtual environment is activated
2. Reinstall dependencies: `uv pip install -r requirements.txt`
3. Check Python version: `python --version`
4. Try: `uv pip install -e ".[dev]"` to install from pyproject.toml

### Issue: Configuration Not Loading

**Problem**: Environment variables not found
**Solution**:
1. Verify `.env` file exists in project root
2. Check file has no BOM (use UTF-8 encoding)
3. Ensure no quotes around values in .env file
4. Restart terminal/IDE after creating .env


# Add a new package
uv pip install package-name

# Add to dev dependencies
uv pip install --dev package-name

# Update all packages
uv pip install --upgrade -r requirements.txt

# List installed packages
uv pip list
```

### Testing

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=src

# Run specific test file
uv run pytest tests/unit/test_auth.py

# Run tests with specific marker
uv run pytest -m unit
```

### Code Quality

```bash
# Format code with ruff
uv run ruff format src/

# Check code with ruff
uv run ruff check src/

# Fix auto-fixable issues
uv run ruff check --fix src/

# Type check with mypy
uv run mypy src/
```

### Running the Application

```bash
# Run main application
uv run python src/main.py

# Run specific scripts
uv run python scripts/test_config.py
uv run python scripts/test_auth.py
```

---

## Support and Resources

- **uv Documentation**: https://github.com/astral-sh/uv
- **Ruff Documentation**: https://docs.astral.sh/ruff/
- **Microsoft Graph API Docs**: https://docs.microsoft.com/graph
- **MSAL Python Docs**: https://msal-python.readthedocs.io
- **OpenAI API Docs**: https://platform.openai.com/docs
- **Project Issues**: Check project repository for known issues
