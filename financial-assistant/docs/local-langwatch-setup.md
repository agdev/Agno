# Local LangWatch Configuration Guide

## Current Configuration for Your Local LangWatch

Your financial assistant is now configured to work with your local LangWatch instance. Here's what's been set up:

### ✅ Configuration Applied

1. **Environment Configuration** (in `env/.env`):

   ```bash
   LANGWATCH_ENDPOINT="http://localhost:3000"
   ```

2. **LangWatch Decorators**: Applied to all workflow methods:
   - `@langwatch_trace(name="financial_assistant_workflow", type="workflow")` - Main workflow
   - `@langwatch_span(name="report_flow", type="flow")` - Report generation flow
   - `@langwatch_span(name="alone_flow", type="flow")` - Single data request flow  
   - `@langwatch_span(name="chat_flow", type="flow")` - Chat interaction flow
   - `@langwatch_span(name="fetch_financial_data", type="data_fetching")` - Data fetching

3. **Local Instance Support**:
   - No API key required for localhost endpoints
   - Automatic detection of local vs cloud instances
   - Graceful fallback if LangWatch is unavailable

### 🚀 Testing the Integration

1. **Start your local LangWatch** (assuming it's running on port 3000)

2. **Run the Financial Assistant**:

   ```bash
   uv run streamlit run src/main.py
   ```

3. **Test with queries**:
   - "What is Apple's stock price?" (alone flow)
   - "Tell me about Microsoft's business" (report flow)  
   - "What is a P/E ratio?" (chat flow)

4. **Monitor traces** in your local LangWatch dashboard at `http://localhost:3000`

### 🔧 Configuration Options

#### Option 1: Local LangWatch (Current Setup)

```bash
# In env/.env
LANGWATCH_ENDPOINT="http://localhost:3000"
# API key is optional for local instances
```

#### Option 2: Local LangWatch with API Key

```bash
# In env/.env
LANGWATCH_API_KEY="your_local_api_key"  
LANGWATCH_ENDPOINT="http://localhost:3000"
```

#### Option 3: Cloud LangWatch (if you switch later)

```bash
# In env/.env
LANGWATCH_API_KEY="your_cloud_api_key"
LANGWATCH_ENDPOINT="https://app.langwatch.ai"
```

### 📊 What You Should See

When the integration is working, you'll see traces for:

1. **Main Workflow Execution**
   - Type: `workflow`
   - Name: `financial_assistant_workflow`
   - Duration: Full request processing time

2. **Flow-Specific Spans**
   - `report_flow`: Multi-step financial report generation
   - `alone_flow`: Single data requests (stock price, income statement, etc.)
   - `chat_flow`: Conversational responses

3. **Data Fetching Operations**
   - `fetch_financial_data`: API calls to Financial Modeling Prep
   - Individual tool usage and response times

### 🔍 Troubleshooting

#### If traces don't appear

1. **Check LangWatch is running**:

   ```bash
   curl http://localhost:3000/health
   ```

2. **Verify configuration**:

   ```bash
   uv run python -c "
   from src.config.settings import Settings
   s = Settings()
   print('LangWatch configured:', s.has_langwatch_configured)
   print('Endpoint:', s.langwatch_endpoint)
   "
   ```

3. **Check logs** in the Streamlit app for LangWatch initialization messages

4. **Test decorator manually**:

   ```bash
   uv run python test_langwatch_integration.py
   ```

### 🎯 Expected Behavior

- **With Local LangWatch**: Traces appear in your local dashboard
- **Without LangWatch**: Application runs normally, decorators are silently skipped
- **Configuration Error**: Graceful fallback, application continues working

### 🔄 Port Configuration

If your local LangWatch runs on a different port, update the endpoint:

```bash
# For port 8080
LANGWATCH_ENDPOINT="http://localhost:8080"

# For custom host/port
LANGWATCH_ENDPOINT="http://your-host:your-port"
```

### ✅ Validation

To confirm everything is working:

1. Start your local LangWatch instance
2. Run: `uv run streamlit run src/main.py`
3. Make a query: "What is Tesla's stock price?"
4. Check your LangWatch dashboard for the trace

You should see a workflow trace with spans showing the complete financial data retrieval process.

---

**The integration is ready! Your financial assistant will now send traces to your local LangWatch instance automatically.** 🎉
