# LangWatch Project Configuration

## How LangWatch Associates Traces with Projects

LangWatch determines which project to associate traces with through multiple mechanisms:

### 1. **Primary: API Key-Based Association**

The **API key is the primary project identifier**:
- Each LangWatch project has a unique API key
- When you call `langwatch.setup(api_key="...")`, all traces go to that project
- Get your API key from: https://app.langwatch.ai → Project Settings

### 2. **Enhanced: Base Attributes for Project Metadata**

Additional project context can be provided via `base_attributes`:

```python
langwatch.setup(
    api_key=self.settings.langwatch_api_key,  # ← Primary project identifier
    endpoint_url=self.settings.langwatch_endpoint,
    base_attributes={
        "project": "financial-assistant",      # Project name/identifier
        "environment": "development",          # Environment (dev/staging/prod)
        "version": "1.0.0",                   # Application version
        "service": "financial-assistant-agno" # Service name
    }
)
```

## Configuration Options

### Environment Variables

Add to your `env/.env` file:

```bash
# Required: LangWatch API Key (get from https://app.langwatch.ai)
LANGWATCH_API_KEY=your_project_api_key_here

# Optional: Custom endpoint (defaults to cloud)
LANGWATCH_ENDPOINT=https://app.langwatch.ai

# Optional: Project metadata
LANGWATCH_PROJECT_NAME=financial-assistant
LANGWATCH_ENVIRONMENT=development  # development|staging|production
```

### Settings Configuration

The `Settings` class now includes:

```python
class Settings:
    # Primary project association
    langwatch_api_key: Optional[str] = Field(None)
    langwatch_endpoint: str = Field("https://app.langwatch.ai")
    
    # Project metadata
    langwatch_project_name: str = Field("financial-assistant") 
    langwatch_environment: str = Field("development")
```

## Project Association Flow

### Step 1: Get LangWatch API Key
1. Sign up at https://app.langwatch.ai
2. Create a new project or use existing project
3. Copy the API key from project settings
4. Note the project name for reference

### Step 2: Configure Environment
```bash
# In env/.env
LANGWATCH_API_KEY="lw_your_actual_api_key_here"
LANGWATCH_PROJECT_NAME="financial-assistant"
LANGWATCH_ENVIRONMENT="development"
```

### Step 3: Workflow Initialization
```python
# In FinancialAssistantWorkflow.__init__()
if self.settings.has_langwatch_configured:
    langwatch.setup(
        api_key=self.settings.langwatch_api_key,     # ← Links to your project
        base_attributes={
            "project": self.settings.langwatch_project_name,
            "environment": self.settings.langwatch_environment,
            "version": "1.0.0",
            "service": "financial-assistant-agno"
        }
    )
```

## Multiple Projects/Environments

### Development vs Production
```bash
# Development environment
LANGWATCH_API_KEY=dev_project_api_key
LANGWATCH_ENVIRONMENT=development

# Production environment  
LANGWATCH_API_KEY=prod_project_api_key
LANGWATCH_ENVIRONMENT=production
```

### Team Setup
- **Shared Development**: Use same API key for development project
- **Individual Testing**: Each developer can have their own LangWatch project
- **Staging/Production**: Use separate API keys for different environments

## Trace Organization in LangWatch

Once configured, traces appear in the LangWatch dashboard organized by:

1. **Project** (determined by API key)
2. **Environment** (from base_attributes)
3. **Service** (from base_attributes)  
4. **Trace Names** (from decorator names)

### Example Trace Hierarchy
```
📁 Financial Assistant Project (API key determines this)
  📁 development (environment)
    📁 financial-assistant-agno (service)
      📄 financial_assistant_workflow (main trace)
        📄 report_flow (span)
          📄 fetch_financial_data (span)
        📄 alone_flow (span)
        📄 chat_flow (span)
```

## Verification

### Test Project Association
```python
# Run this to verify project setup
PYTHONPATH=src uv run python test_official_langwatch.py

# Look for:
# ✅ LangWatch decorators applied successfully
# ✅ Workflow initialized successfully
```

### Check LangWatch Dashboard
1. Go to https://app.langwatch.ai
2. Select your project
3. Run the financial assistant
4. Traces should appear with correct project and metadata

## Troubleshooting

### Wrong Project Showing Traces
- **Cause**: Incorrect API key
- **Fix**: Verify `LANGWATCH_API_KEY` matches your intended project

### Missing Project Metadata  
- **Cause**: `base_attributes` not configured
- **Fix**: Ensure `langwatch_project_name` and `langwatch_environment` are set

### No Traces Appearing
- **Cause**: API key not configured or invalid
- **Fix**: Check API key in LangWatch dashboard and verify environment variable

## Best Practices

1. **Use Different API Keys**: Separate keys for dev/staging/production
2. **Clear Naming**: Use descriptive project and environment names
3. **Version Tracking**: Include application version in base_attributes
4. **Team Coordination**: Share development project API key with team
5. **Security**: Keep production API keys secure and separate

This configuration ensures your traces are properly organized and associated with the correct LangWatch project.