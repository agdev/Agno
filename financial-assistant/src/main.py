"""
Financial Assistant Streamlit Application

This is the main entry point for the Financial Assistant web application
built with Streamlit and powered by the Agno framework.
"""

import os
import streamlit as st
from dotenv import load_dotenv
from typing import Optional, Generator

# Load environment variables
load_dotenv()

# Import our workflow and models
from workflow.financial_assistant import FinancialAssistantWorkflow, create_financial_assistant_workflow
from models.schemas import WorkflowState
from agno.models.anthropic import Claude
from agno.models.openai import OpenAIChat


def initialize_session_state():
    """Initialize Streamlit session state variables"""
    if "workflow" not in st.session_state:
        st.session_state.workflow = None
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "workflow_state" not in st.session_state:
        st.session_state.workflow_state = WorkflowState()
    if "api_configured" not in st.session_state:
        st.session_state.api_configured = False


def check_api_configuration() -> bool:
    """Check if required API keys are configured"""
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    openai_key = os.getenv("OPENAI_API_KEY")
    groq_key = os.getenv("GROQ_API_KEY")
    fmp_key = os.getenv("FINANCIAL_MODELING_PREP_API_KEY")
    
    # Need at least one LLM provider and the Financial Modeling Prep API key
    has_llm_provider = any([anthropic_key, openai_key, groq_key])
    
    return has_llm_provider and fmp_key is not None


def get_llm_model(provider: str = "anthropic"):
    """Get configured LLM model based on provider preference"""
    try:
        if provider == "anthropic" and os.getenv("ANTHROPIC_API_KEY"):
            return Claude(id="claude-sonnet-4-20250514")
        elif provider == "openai" and os.getenv("OPENAI_API_KEY"):
            return OpenAIChat(id="gpt-4o")
        elif provider == "groq" and os.getenv("GROQ_API_KEY"):
            # Note: Groq integration would need to be added to agno
            # For now, fallback to Claude or OpenAI
            if os.getenv("ANTHROPIC_API_KEY"):
                return Claude(id="claude-sonnet-4-20250514")
            elif os.getenv("OPENAI_API_KEY"):
                return OpenAIChat(id="gpt-4o")
        
        # Default fallback
        if os.getenv("ANTHROPIC_API_KEY"):
            return Claude(id="claude-sonnet-4-20250514")
        elif os.getenv("OPENAI_API_KEY"):
            return OpenAIChat(id="gpt-4o")
        else:
            return None
    except Exception as e:
        st.error(f"Error initializing LLM model: {str(e)}")
        return None


def setup_sidebar():
    """Set up the sidebar with configuration options"""
    with st.sidebar:
        st.title("🏦 Financial Assistant")
        st.markdown("---")
        
        # API Configuration Status
        st.subheader("📊 Configuration")
        
        if check_api_configuration():
            st.success("✅ API keys configured")
            st.session_state.api_configured = True
        else:
            st.error("❌ Missing API keys")
            st.session_state.api_configured = False
            
            st.markdown("""
            **Required Environment Variables:**
            - `FINANCIAL_MODELING_PREP_API_KEY` (required)
            - At least one LLM provider:
              - `ANTHROPIC_API_KEY` (recommended)
              - `OPENAI_API_KEY`
              - `GROQ_API_KEY`
            """)
        
        # LLM Provider Selection
        if st.session_state.api_configured:
            st.subheader("🤖 Model Settings")
            
            available_providers = []
            if os.getenv("ANTHROPIC_API_KEY"):
                available_providers.append("anthropic")
            if os.getenv("OPENAI_API_KEY"):
                available_providers.append("openai")
            if os.getenv("GROQ_API_KEY"):
                available_providers.append("groq")
            
            if available_providers:
                selected_provider = st.selectbox(
                    "LLM Provider",
                    available_providers,
                    index=0,
                    help="Choose your preferred language model provider"
                )
                
                # Initialize workflow if not already done or if provider changed
                if (st.session_state.workflow is None or 
                    getattr(st.session_state, 'current_provider', None) != selected_provider):
                    
                    with st.spinner("Initializing workflow..."):
                        llm_model = get_llm_model(selected_provider)
                        if llm_model:
                            st.session_state.workflow = create_financial_assistant_workflow(llm_model)
                            st.session_state.current_provider = selected_provider
                            st.success(f"✅ Using {selected_provider.title()}")
                        else:
                            st.error(f"Failed to initialize {selected_provider} model")
        
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
            st.session_state.workflow_state = WorkflowState()
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
        # Update workflow state
        st.session_state.workflow_state.request = user_input
        st.session_state.workflow_state.update_timestamp()
        
        # Process through workflow
        responses = st.session_state.workflow.run(user_input)
        
        for response in responses:
            if hasattr(response, 'content'):
                yield response.content
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
        initial_sidebar_state="expanded"
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
        st.info("🔄 Initializing AI workflow... Please select an LLM provider in the sidebar.")
        return
    
    # Display chat history
    for message in st.session_state.messages:
        display_message(message["role"], message["content"])
    
    # Chat input
    if prompt := st.chat_input("Ask me about any publicly traded company or financial concept..."):
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
            st.session_state.messages.append({"role": "assistant", "content": full_response})


if __name__ == "__main__":
    main()