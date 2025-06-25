"""
Financial Assistant Streamlit Application

This is the main entry point for the Financial Assistant web application
built with Streamlit and powered by the Agno framework.
"""

import os
from datetime import datetime
from typing import Generator, Optional

import streamlit as st
from dotenv import load_dotenv

# Import our workflow and models
from agno.models.anthropic import Claude
from agno.models.openai import OpenAIChat
from agno.models.groq import Groq
from workflow.financial_assistant import FinancialAssistantWorkflow


# Load environment variables from multiple possible locations
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

# Load environment variables
load_environment_variables()


def initialize_session_state():
    """Initialize Streamlit session state variables"""
    if "workflow" not in st.session_state:
        st.session_state.workflow = None
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "workflow_state" not in st.session_state:
        # Initialize workflow state as a dict - Agno handles session state internally
        st.session_state.workflow_state = {}
    if "api_configured" not in st.session_state:
        st.session_state.api_configured = False


def check_api_configuration() -> bool:
    """Check if required API keys are configured (environment or session state)"""
    # Check environment variables
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    openai_key = os.getenv("OPENAI_API_KEY") 
    groq_key = os.getenv("GROQ_API_KEY")
    fmp_key = os.getenv("FINANCIAL_MODELING_PREP_API_KEY")

    # Check session state for manually entered keys
    session_anthropic = st.session_state.get("anthropic_api_key")
    session_openai = st.session_state.get("openai_api_key")
    session_groq = st.session_state.get("groq_api_key")
    session_fmp = st.session_state.get("fmp_api_key")

    # Need at least one LLM provider and the Financial Modeling Prep API key
    has_llm_provider = any([anthropic_key, openai_key, groq_key, session_anthropic, session_openai, session_groq])
    has_fmp_key = fmp_key is not None or session_fmp is not None

    return has_llm_provider and has_fmp_key


def get_api_key(provider: str) -> Optional[str]:
    """Get API key from environment or session state"""
    env_key = os.getenv(f"{provider.upper()}_API_KEY")
    if env_key:
        return env_key
    return st.session_state.get(f"{provider.lower()}_api_key")

def get_fmp_api_key() -> Optional[str]:
    """Get Financial Modeling Prep API key from environment or session state"""
    env_key = os.getenv("FINANCIAL_MODELING_PREP_API_KEY")
    if env_key:
        return env_key
    return st.session_state.get("fmp_api_key")

def get_llm_model(provider: str = "anthropic") -> Optional[object]:
    """Get configured LLM model based on provider preference"""
    try:
        if provider == "anthropic":
            api_key = get_api_key("anthropic")
            if api_key:
                return Claude(id="claude-sonnet-4-20250514", api_key=api_key)
        elif provider == "openai":
            api_key = get_api_key("openai")
            if api_key:
                return OpenAIChat(id="gpt-4o", api_key=api_key)
        elif provider == "groq":
            api_key = get_api_key("groq")
            if api_key:
                return Groq(id="llama-3.3-70b-versatile", api_key=api_key)

        # Default fallback - try available providers
        for fallback_provider in ["anthropic", "openai", "groq"]:
            api_key = get_api_key(fallback_provider)
            if api_key:
                if fallback_provider == "anthropic":
                    return Claude(id="claude-sonnet-4-20250514", api_key=api_key)
                elif fallback_provider == "openai":
                    return OpenAIChat(id="gpt-4o", api_key=api_key)
                elif fallback_provider == "groq":
                    return Groq(id="llama-3.3-70b-versatile", api_key=api_key)
        
        return None
    except Exception as e:
        st.error(f"Error initializing LLM model: {str(e)}")
        return None


def setup_sidebar():
    """Set up the sidebar with configuration options"""
    with st.sidebar:
        st.title("🏦 Financial Assistant")
        st.markdown("---")

        # API Configuration Section
        st.subheader("🔑 API Configuration")
        
        # Check which keys are available from environment
        env_fmp = bool(os.getenv("FINANCIAL_MODELING_PREP_API_KEY"))
        env_anthropic = bool(os.getenv("ANTHROPIC_API_KEY"))
        env_openai = bool(os.getenv("OPENAI_API_KEY"))
        env_groq = bool(os.getenv("GROQ_API_KEY"))
        
        # Show environment status
        if any([env_fmp, env_anthropic, env_openai, env_groq]):
            st.info("✅ Some API keys loaded from environment")
            if env_fmp:
                st.write("✓ Financial Modeling Prep")
            if env_anthropic:
                st.write("✓ Anthropic (Claude)")
            if env_openai:
                st.write("✓ OpenAI (GPT)")
            if env_groq:
                st.write("✓ Groq (Llama)")
        else:
            st.warning("No environment variables found - manual input required")

        # Manual API Key Input Section
        st.markdown("### Manual API Keys")
        st.markdown("*Enter keys only if not set in environment*")
        
        # Financial Modeling Prep API Key (Required)
        if not env_fmp:
            fmp_key = st.text_input(
                "Financial Modeling Prep API Key *",
                type="password",
                value=st.session_state.get("fmp_api_key", ""),
                help="Required for financial data. Get it at financialmodelingprep.com",
                key="fmp_key_input"
            )
            if fmp_key:
                st.session_state["fmp_api_key"] = fmp_key
        
        # LLM Provider Selection (Always show all providers)
        st.markdown("### LLM Provider")
        selected_provider = st.selectbox(
            "Choose LLM Provider",
            ["anthropic", "openai", "groq"],
            index=0,
            help="Select your preferred language model provider"
        )
        
        # Provider-specific API key input (if not in environment)
        provider_configured = False
        
        if selected_provider == "anthropic":
            if not env_anthropic:
                anthropic_key = st.text_input(
                    "Anthropic API Key *",
                    type="password",
                    value=st.session_state.get("anthropic_api_key", ""),
                    help="Get your Claude API key from console.anthropic.com",
                    key="anthropic_key_input"
                )
                if anthropic_key:
                    st.session_state["anthropic_api_key"] = anthropic_key
                    provider_configured = True
            else:
                provider_configured = True
                
        elif selected_provider == "openai":
            if not env_openai:
                openai_key = st.text_input(
                    "OpenAI API Key *",
                    type="password", 
                    value=st.session_state.get("openai_api_key", ""),
                    help="Get your OpenAI API key from platform.openai.com",
                    key="openai_key_input"
                )
                if openai_key:
                    st.session_state["openai_api_key"] = openai_key
                    provider_configured = True
            else:
                provider_configured = True
                
        elif selected_provider == "groq":
            if not env_groq:
                groq_key = st.text_input(
                    "Groq API Key *",
                    type="password",
                    value=st.session_state.get("groq_api_key", ""),
                    help="Get your Groq API key from console.groq.com",
                    key="groq_key_input"
                )
                if groq_key:
                    st.session_state["groq_api_key"] = groq_key
                    provider_configured = True
            else:
                provider_configured = True

        # Configuration Status
        api_configured = check_api_configuration()
        fmp_configured = get_fmp_api_key() is not None
        
        if api_configured:
            st.success("✅ Configuration complete!")
            st.session_state.api_configured = True
            
            # Initialize workflow if provider changed or not initialized
            if (st.session_state.workflow is None or 
                getattr(st.session_state, "current_provider", None) != selected_provider):
                with st.spinner(f"Initializing {selected_provider.title()}..."):
                    llm_model = get_llm_model(selected_provider)
                    if llm_model:
                        # Initialize workflow with the LLM model
                        # The workflow will automatically pick up FMP API key from session state
                        st.session_state.workflow = FinancialAssistantWorkflow(llm=llm_model)
                        st.session_state.current_provider = selected_provider
                        st.success(f"✅ Using {selected_provider.title()}")
                    else:
                        st.error(f"❌ Failed to initialize {selected_provider}")
                        st.session_state.api_configured = False
        else:
            st.session_state.api_configured = False
            st.error("❌ Missing required API keys")
            
            missing_items = []
            if not fmp_configured:
                missing_items.append("Financial Modeling Prep API key")
            if not provider_configured:
                missing_items.append(f"{selected_provider.title()} API key")
            
            if missing_items:
                st.write("Missing:")
                for item in missing_items:
                    st.write(f"• {item}")

        st.markdown("---")

        # Usage Examples
        st.subheader("💡 Example Queries")
        st.markdown("""
        **Specific Data:**
        - "What is Apple's stock price?"
        - "Show Tesla's income statement"
        - "Get Microsoft's financial ratios"
        
        **Comprehensive Reports:**
        - "Tell me about Apple's business"
        - "Analyze Amazon's financials"
        - "Generate a report on Google"
        
        **General Questions:**
        - "What is a P/E ratio?"
        - "Explain revenue vs profit"
        - "How do I analyze stocks?"
        """)

        # Clear conversation
        if st.button("🗑️ Clear Conversation", type="secondary"):
            st.session_state.messages = []
            st.session_state.workflow_state = {}
            st.rerun()


def display_message(role: str, content: str):
    """Display a chat message with appropriate styling"""
    with st.chat_message(role):
        if role == "assistant" and content.startswith("# "):
            # Render markdown for reports
            st.markdown(content)
        else:
            st.write(content)


def process_user_input(user_input: str) -> Generator[str, None, None]:
    """Process user input through the workflow and yield responses"""
    if not st.session_state.workflow:
        yield "❌ Workflow not initialized. Please check your API configuration."
        return

    try:
        # Update workflow state - store as dict for Streamlit compatibility
        st.session_state.workflow_state["request"] = user_input
        st.session_state.workflow_state["updated_at"] = str(datetime.now())

        # Process through workflow - Agno workflows return Iterator[RunResponse]
        responses = st.session_state.workflow.run(message=user_input)

        for response in responses:
            if hasattr(response, "content") and response.content:
                yield str(response.content)
            else:
                yield str(response)

    except Exception as e:
        yield f"❌ Error processing request: {str(e)}\n\nPlease check your API keys and try again."


def main():
    """Main application entry point"""
    st.set_page_config(
        page_title="Financial Assistant",
        page_icon="🏦",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    # Initialize session state
    initialize_session_state()

    # Setup sidebar
    setup_sidebar()

    # Main content area
    st.title("🏦 Financial Assistant")
    st.markdown("Get instant access to financial data and analysis powered by AI")

    if not st.session_state.api_configured:
        st.warning("⚠️ Please configure your API keys in the sidebar to get started.")
        st.info("""
        This application requires:
        1. **Financial Modeling Prep API Key** - for real-time financial data
        2. **LLM Provider API Key** - for AI-powered analysis (Anthropic, OpenAI, or Groq)
        
        Set these as environment variables or in a `.env` file.
        """)
        return

    if not st.session_state.workflow:
        st.info(
            "🔄 Initializing AI workflow... Please select an LLM provider in the sidebar."
        )
        return

    # Display chat history
    for message in st.session_state.messages:
        display_message(message["role"], message["content"])

    # Chat input
    if prompt := st.chat_input(
        "Ask me about any publicly traded company or financial concept..."
    ):
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        display_message("user", prompt)

        # Process the request and stream the response
        with st.chat_message("assistant"):
            with st.spinner("Analyzing your request..."):
                response_placeholder = st.empty()
                full_response = ""

                try:
                    for response_chunk in process_user_input(prompt):
                        full_response = response_chunk  # For workflow responses, we get the complete response
                        response_placeholder.markdown(full_response)
                except Exception as e:
                    error_message = f"❌ An error occurred: {str(e)}"
                    response_placeholder.error(error_message)
                    full_response = error_message

        # Add assistant response to chat history
        if full_response:
            st.session_state.messages.append(
                {"role": "assistant", "content": full_response}
            )


if __name__ == "__main__":
    main()
