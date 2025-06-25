# Provider Configuration Plan - Agno Financial Assistant

## Problem Analysis

The current Agno implementation has issues with provider configuration functionality:

1. **Environment Variable Loading**: The `.env` file is located in `financial-assistant/env/.env` but the application is looking for it in the root directory
2. **Missing User Interface**: Unlike the LangGraph version, users cannot manually enter API keys through the UI
3. **Limited Provider Selection**: The provider selection UI exists but doesn't properly integrate with configuration management
4. **Configuration Persistence**: No session-based API key storage for user-entered values

## LangGraph Implementation Analysis

The original LangGraph implementation has a robust provider configuration system:

### Key Features to Preserve
1. **Multi-location .env file loading** with priority order
2. **Dynamic provider selection** with real-time switching  
3. **Manual API key input** as fallback when environment variables aren't available
4. **Session-based secure storage** using Pydantic SecretStr
5. **Automatic provider detection** based on available API keys
6. **Clean workflow reinitialization** when provider changes

### Provider Flow Pattern
```
Environment Variable Loading (Priority 1)
    ↓ (if fails)
Manual API Key Input UI (Priority 2)
    ↓ (both store in)
Session State Configuration
    ↓ (triggers)
Workflow Reinitialization with New Provider
```

## Implementation Strategy

### Phase 1: Fix Environment Variable Loading

**Current Issue:**
```python
# In src/main.py - line 16
load_dotenv()  # Only looks in current directory
```

**Solution:**
```python
# Enhanced multi-location loading
def load_environment_variables():
    """Load environment variables from multiple possible locations"""
    possible_env_paths = [
        os.path.join(os.path.dirname(__file__), "..", "env", ".env"),  # ../env/.env  
        os.path.join(os.path.dirname(__file__), "..", ".env"),         # ../.env
        os.path.join(os.getcwd(), "env", ".env"),                     # ./env/.env
        os.path.join(os.getcwd(), ".env"),                            # ./.env
        ".env"                                                        # Current directory
    ]
    
    for env_path in possible_env_paths:
        if os.path.exists(env_path):
            load_dotenv(env_path)
            print(f"✅ Loaded environment variables from {env_path}")
            return True
    
    print("⚠️ No .env file found in expected locations")
    return False
```

### Phase 2: Implement Manual API Key Input UI

**Add to Sidebar Configuration:**
```python
def configure_api_keys_ui():
    """Provide UI for manual API key configuration when env vars aren't available"""
    
    # Check if we have env-based config
    settings = Settings()
    if settings.is_fully_configured:
        st.success("✅ API keys loaded from environment variables")
        return settings
    
    # Show manual input UI
    st.subheader("🔑 API Configuration")
    st.markdown("""
    **API keys are stored only in session state and are not persisted.**
    
    Required:
    - Financial Modeling Prep API key ([Get it here](https://financialmodelingprep.com/developer/docs/))
    - At least one LLM provider API key
    """)
    
    # Provider selection
    available_providers = []
    if os.getenv("ANTHROPIC_API_KEY") or "anthropic_key" in st.session_state:
        available_providers.append("anthropic")
    if os.getenv("OPENAI_API_KEY") or "openai_key" in st.session_state:
        available_providers.append("openai") 
    if os.getenv("GROQ_API_KEY") or "groq_key" in st.session_state:
        available_providers.append("groq")
    
    # If no env keys, show manual input
    if not available_providers:
        selected_provider = st.selectbox(
            "Select LLM Provider",
            ["anthropic", "openai", "groq"],
            help="Choose your preferred language model provider"
        )
        
        # Provider-specific API key input
        llm_key = st.text_input(
            f"{selected_provider.title()} API Key",
            type="password",
            key=f"{selected_provider}_key_input"
        )
        
        # Financial Modeling Prep API key
        fmp_key = st.text_input(
            "Financial Modeling Prep API Key",
            type="password", 
            key="fmp_key_input"
        )
        
        # Save button
        if st.button("💾 Save API Keys", type="primary"):
            if llm_key and fmp_key:
                # Store in session state
                st.session_state[f"{selected_provider}_key"] = llm_key
                st.session_state["fmp_key"] = fmp_key
                st.session_state["selected_provider"] = selected_provider
                
                # Force workflow reinitialization
                if "workflow" in st.session_state:
                    del st.session_state.workflow
                
                st.success("✅ API keys saved successfully!")
                st.rerun()
            else:
                st.error("❌ Please enter both API keys")
    
    return None
```

### Phase 3: Enhanced Configuration Management

**Update Settings Class:**
```python
# In src/config/settings.py
class Settings(BaseSettings):
    # ... existing fields ...
    
    def __init__(self, session_state=None, **data):
        """Initialize settings with optional session state override"""
        super().__init__(**data)
        
        # Override with session state values if available
        if session_state:
            if "anthropic_key" in session_state:
                self.anthropic_api_key = session_state["anthropic_key"]
            if "openai_key" in session_state:
                self.openai_api_key = session_state["openai_key"]
            if "groq_key" in session_state:
                self.groq_api_key = session_state["groq_key"]
            if "fmp_key" in session_state:
                self.financial_modeling_prep_api_key = session_state["fmp_key"]
    
    @classmethod
    def from_session(cls, session_state) -> "Settings":
        """Create settings instance with session state override"""
        return cls(session_state=session_state)
```

### Phase 4: Dynamic Provider Switching

**Enhanced Provider Management:**
```python
def get_llm_model_dynamic(provider: str = None, session_state=None) -> Optional[object]:
    """Get LLM model with dynamic provider selection and session state support"""
    
    # Create settings with session state override
    if session_state:
        settings = Settings.from_session(session_state)
    else:
        settings = Settings()
    
    # Determine provider priority
    if provider:
        providers_to_try = [provider]
    else:
        providers_to_try = settings.get_available_llm_providers()
    
    # Try each provider in order
    for prov in providers_to_try:
        try:
            if prov == "anthropic" and settings.anthropic_api_key:
                return Claude(
                    id="claude-sonnet-4-20250514",
                    api_key=settings.anthropic_api_key
                )
            elif prov == "openai" and settings.openai_api_key:
                return OpenAIChat(
                    id="gpt-4o",
                    api_key=settings.openai_api_key
                )
            elif prov == "groq" and settings.groq_api_key:
                # Note: When Groq support is added to Agno
                # return GroqChat(id="llama-3-70b-8192", api_key=settings.groq_api_key)
                # For now, fallback to other providers
                continue
        except Exception as e:
            st.warning(f"Failed to initialize {prov}: {str(e)}")
            continue
    
    return None
```

### Phase 5: UI Integration Updates

**Enhanced Sidebar Setup:**
```python
def setup_sidebar_enhanced():
    """Enhanced sidebar with proper provider configuration"""
    with st.sidebar:
        st.title("🏦 Financial Assistant")
        st.markdown("---")
        
        # Load environment variables first
        env_loaded = load_environment_variables()
        
        # Configuration section
        st.subheader("📊 Configuration")
        
        # Try to get settings (env + session state)
        settings = Settings.from_session(st.session_state) if hasattr(st, 'session_state') else Settings()
        
        if settings.is_fully_configured:
            st.success("✅ All API keys configured")
            
            # Provider selection
            available_providers = settings.get_available_llm_providers()
            if available_providers:
                selected_provider = st.selectbox(
                    "🤖 LLM Provider",
                    available_providers,
                    index=0,
                    help="Choose your preferred language model provider"
                )
                
                # Show current provider info
                if env_loaded:
                    st.info(f"📝 Using environment variables")
                else:
                    st.info(f"🔐 Using session-stored keys")
                
                # Initialize workflow with selected provider
                provider_changed = (
                    "current_provider" not in st.session_state or 
                    st.session_state.current_provider != selected_provider
                )
                
                if st.session_state.get("workflow") is None or provider_changed:
                    with st.spinner(f"Initializing {selected_provider.title()}..."):
                        llm_model = get_llm_model_dynamic(selected_provider, st.session_state)
                        if llm_model:
                            st.session_state.workflow = FinancialAssistantWorkflow(llm=llm_model)
                            st.session_state.current_provider = selected_provider
                            st.success(f"✅ Using {selected_provider.title()}")
                        else:
                            st.error(f"❌ Failed to initialize {selected_provider}")
            
        else:
            # Show configuration UI
            configure_api_keys_ui()
            
        st.markdown("---")
        
        # Rest of sidebar content...
```

## Implementation Checklist

### ✅ **High Priority - Core Fixes**
- [ ] Fix environment variable loading to check `env/.env` directory
- [ ] Add multi-location .env file search functionality  
- [ ] Update `load_dotenv()` call in `src/main.py`
- [ ] Test environment variable loading from `financial-assistant/env/.env`

### 🟡 **Medium Priority - Manual Input UI**  
- [ ] Implement `configure_api_keys_ui()` function
- [ ] Add manual API key input forms with password fields
- [ ] Implement session-based API key storage with SecretStr
- [ ] Add "Save API Keys" button with validation
- [ ] Add provider selection for manual input mode

### 🟢 **Low Priority - Enhanced Features**
- [ ] Add configuration validation and error messages
- [ ] Implement automatic provider fallback logic
- [ ] Add configuration export/import functionality
- [ ] Add API key testing/validation before saving
- [ ] Implement configuration reset functionality

### 🧪 **Testing Requirements**
- [ ] Test .env loading from multiple locations
- [ ] Test manual API key input and storage
- [ ] Test provider switching with workflow reinitialization
- [ ] Test session state persistence across page reloads
- [ ] Test error handling for invalid API keys

## File Structure Changes

```
financial-assistant/
├── env/
│   └── .env                    # ✅ Already exists
├── src/
│   ├── config/
│   │   ├── __init__.py
│   │   ├── settings.py         # 🔄 Update Settings class
│   │   └── env_loader.py       # ➕ New: Multi-location env loading
│   ├── ui/
│   │   ├── __init__.py         # ➕ New: UI components module
│   │   ├── sidebar.py          # ➕ New: Enhanced sidebar
│   │   └── api_config.py       # ➕ New: API configuration UI
│   └── main.py                 # 🔄 Update to use enhanced config
└── .env.example                # ➕ New: Template for users
```

## Expected Benefits

### ✅ **Immediate Fixes**
1. **Environment Variable Loading**: Properly loads from `env/.env` directory
2. **Provider Selection**: Works correctly with available API keys
3. **Configuration Status**: Shows correct status based on actual configuration

### 🚀 **Enhanced User Experience**
1. **Flexible Configuration**: Environment variables OR manual input
2. **Dynamic Provider Switching**: Real-time provider changes without restart
3. **Secure Key Storage**: Session-only storage with no persistence
4. **Fallback Support**: Graceful handling when environment variables are missing

### 📈 **Feature Parity**
1. **LangGraph Compatibility**: Same user experience as original implementation
2. **Multi-Provider Support**: Full support for Anthropic, OpenAI, and Groq
3. **Configuration Priority**: Environment variables take precedence over manual input
4. **Session Management**: Proper cleanup and reinitialization on provider changes

## Security Considerations

### ✅ **Secure Practices**
- API keys stored only in session state (not persisted to disk)
- Password-type input fields for sensitive data
- Clear user messaging about security practices
- No logging of API keys or sensitive information

### ⚠️ **Security Notes**
- Session state is cleared when browser session ends
- API keys are not transmitted outside the application
- Environment variables are loaded only from expected locations
- No API key validation calls that could expose keys in logs

## Migration Path

1. **Quick Fix (30 minutes)**: Update environment variable loading in `main.py`
2. **UI Enhancement (2 hours)**: Add manual API key input interface
3. **Integration (1 hour)**: Integrate manual input with workflow initialization
4. **Testing (1 hour)**: Test all configuration scenarios
5. **Documentation (30 minutes)**: Update user documentation

This plan provides a comprehensive solution that maintains the user-friendly configuration experience from the LangGraph version while adapting it to the Agno framework architecture.