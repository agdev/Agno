"""
Financial Assistant Streamlit Application

This is the main entry point for the Financial Assistant web application
built with Streamlit and powered by the Agno framework.
"""

import uuid
from datetime import datetime
from typing import Generator, Optional

# import langwatch  # Removed - handled in workflow initialization
import streamlit as st

# Import our workflow and models
from agno.models.anthropic import Claude
from agno.models.groq import Groq
from agno.models.openai import OpenAIChat
from agno.storage.sqlite import SqliteStorage
from config.settings import Settings
from workflow.financial_assistant import FinancialAssistantWorkflow

# LangWatch setup is now handled in the workflow initialization
# No need for global setup here


# Initialize settings
def get_app_settings() -> Settings:
    """Get application settings instance"""
    return Settings()


def initialize_session_state():
    """Initialize Streamlit session state variables"""
    if "workflow" not in st.session_state:
        st.session_state.workflow = None
    if "storage" not in st.session_state:
        st.session_state.storage = None
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "workflow_state" not in st.session_state:
        # Initialize workflow state as a dict - Agno handles session state internally
        st.session_state.workflow_state = {}
    if "api_configured" not in st.session_state:
        st.session_state.api_configured = False

    # Session management for conversation persistence
    if "user_id" not in st.session_state:
        # Generate a persistent user ID for this browser session
        st.session_state.user_id = str(uuid.uuid4())
    if "session_id" not in st.session_state:
        # Generate a new session ID for this conversation
        st.session_state.session_id = str(uuid.uuid4())
    if "conversation_summary" not in st.session_state:
        st.session_state.conversation_summary = ""
    if "available_sessions" not in st.session_state:
        st.session_state.available_sessions = []


def check_api_configuration(settings: Settings) -> bool:
    """Check if required API keys are configured (settings or session state)"""
    # Check session state for manually entered keys
    session_anthropic = st.session_state.get("anthropic_api_key")
    session_openai = st.session_state.get("openai_api_key")
    session_groq = st.session_state.get("groq_api_key")
    session_fmp = st.session_state.get("fmp_api_key")

    # Need at least one LLM provider and the Financial Modeling Prep API key
    has_llm_provider = any(
        [
            settings.anthropic_api_key,
            settings.openai_api_key,
            settings.groq_api_key,
            session_anthropic,
            session_openai,
            session_groq,
        ]
    )
    has_fmp_key = (
        settings.financial_modeling_prep_api_key is not None or session_fmp is not None
    )

    return has_llm_provider and has_fmp_key


def get_api_key(provider: str, settings: Settings) -> Optional[str]:
    """Get API key from settings or session state"""
    # Check settings first
    if provider == "anthropic" and settings.anthropic_api_key:
        return settings.anthropic_api_key
    elif provider == "openai" and settings.openai_api_key:
        return settings.openai_api_key
    elif provider == "groq" and settings.groq_api_key:
        return settings.groq_api_key

    # Fall back to session state
    return st.session_state.get(f"{provider.lower()}_api_key")


def get_fmp_api_key(settings: Settings) -> Optional[str]:
    """Get Financial Modeling Prep API key from settings or session state"""
    if settings.financial_modeling_prep_api_key:
        return settings.financial_modeling_prep_api_key
    return st.session_state.get("fmp_api_key")


def initialize_storage(settings: Settings) -> SqliteStorage:
    """Initialize storage for session persistence"""
    if st.session_state.storage is None:
        # Ensure the tmp directory exists
        import os

        os.makedirs(os.path.dirname(settings.storage_db_file), exist_ok=True)

        storage = SqliteStorage(
            table_name=settings.storage_table_name, db_file=settings.storage_db_file
        )
        st.session_state.storage = storage

    return st.session_state.storage


def get_llm_model(provider: str, settings: Settings) -> Optional[object]:
    """Get configured LLM model based on provider preference"""
    try:
        if provider == "anthropic":
            api_key = get_api_key("anthropic", settings)
            if api_key:
                model_id = (
                    settings.get_llm_model_id("anthropic") or "claude-sonnet-4-20250514"
                )
                return Claude(id=model_id, api_key=api_key)
        elif provider == "openai":
            api_key = get_api_key("openai", settings)
            if api_key:
                model_id = settings.get_llm_model_id("openai") or "gpt-4o"
                return OpenAIChat(id=model_id, api_key=api_key)
        elif provider == "groq":
            api_key = get_api_key("groq", settings)
            if api_key:
                model_id = (
                    settings.get_llm_model_id("groq") or "llama-3.3-70b-versatile"
                )
                return Groq(id=model_id, api_key=api_key)

        # Default fallback - try available providers based on settings
        available_providers = settings.get_available_llm_providers()
        for fallback_provider in available_providers:
            api_key = get_api_key(fallback_provider, settings)
            if api_key:
                model_id = settings.get_llm_model_id(fallback_provider)
                if fallback_provider == "anthropic":
                    fallback_model_id = model_id or "claude-sonnet-4-20250514"
                    return Claude(id=fallback_model_id, api_key=api_key)
                elif fallback_provider == "openai":
                    fallback_model_id = model_id or "gpt-4o"
                    return OpenAIChat(id=fallback_model_id, api_key=api_key)
                elif fallback_provider == "groq":
                    fallback_model_id = model_id or "llama-3.3-70b-versatile"
                    return Groq(id=fallback_model_id, api_key=api_key)

        return None
    except Exception as e:
        st.error(f"Error initializing LLM model: {str(e)}")
        return None


def setup_sidebar(settings: Settings):
    """Set up the sidebar with configuration options"""
    with st.sidebar:
        st.title(settings.app_title)
        st.markdown("---")

        # API Configuration Section
        st.subheader("🔑 API Configuration")

        # Check which keys are available from settings
        env_fmp = bool(settings.financial_modeling_prep_api_key)
        env_anthropic = bool(settings.anthropic_api_key)
        env_openai = bool(settings.openai_api_key)
        env_groq = bool(settings.groq_api_key)

        # LLM Provider Selection (Show all supported providers) - Move this first
        st.markdown("### LLM Provider")
        all_providers = [
            "anthropic",
            "openai",
            "groq",
        ]  # Always show all supported providers
        available_providers = (
            settings.get_available_llm_providers()
        )  # Providers with API keys

        # Show default provider if it's supported, otherwise default to first
        default_index = 0
        if settings.default_llm_provider in all_providers:
            default_index = all_providers.index(settings.default_llm_provider)

        selected_provider = st.selectbox(
            "Choose LLM Provider",
            all_providers,  # Show all providers, not just configured ones
            index=default_index,
            help="Select your preferred language model provider",
        )

        # Show status for selected provider only
        selected_provider_has_key = selected_provider in available_providers
        if selected_provider_has_key:
            st.success(f"✅ **{selected_provider.title()}**: Configured and ready!")
        else:
            st.warning(
                f"🔑 **{selected_provider.title()}**: API key required (enter below)"
            )

        # Show environment status for relevant keys only
        st.markdown("### Environment Status")
        env_keys_found = []
        if env_fmp:
            env_keys_found.append("Financial Modeling Prep")

        # Only show selected provider's environment status
        if selected_provider == "anthropic" and env_anthropic:
            env_keys_found.append("Anthropic (Claude)")
        elif selected_provider == "openai" and env_openai:
            env_keys_found.append("OpenAI (GPT)")
        elif selected_provider == "groq" and env_groq:
            env_keys_found.append("Groq (Llama)")

        if env_keys_found:
            st.info("✅ Keys loaded from environment:")
            for key in env_keys_found:
                st.write(f"✓ {key}")
        else:
            st.info("🔑 Manual API key entry required")

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
                key="fmp_key_input",
            )
            if fmp_key:
                st.session_state["fmp_api_key"] = fmp_key

        # Provider-specific API key input (only for selected provider if needed)
        provider_configured = selected_provider in available_providers

        # Selected provider API key input (only if not in environment)
        if selected_provider == "anthropic" and not env_anthropic:
            anthropic_key = st.text_input(
                "Anthropic API Key *",
                type="password",
                value=st.session_state.get("anthropic_api_key", ""),
                help="Get your Claude API key from console.anthropic.com",
                key="anthropic_key_input",
            )
            if anthropic_key:
                st.session_state["anthropic_api_key"] = anthropic_key
                provider_configured = True

        elif selected_provider == "openai" and not env_openai:
            openai_key = st.text_input(
                "OpenAI API Key *",
                type="password",
                value=st.session_state.get("openai_api_key", ""),
                help="Get your OpenAI API key from platform.openai.com",
                key="openai_key_input",
            )
            if openai_key:
                st.session_state["openai_api_key"] = openai_key
                provider_configured = True

        elif selected_provider == "groq" and not env_groq:
            groq_key = st.text_input(
                "Groq API Key *",
                type="password",
                value=st.session_state.get("groq_api_key", ""),
                help="Get your Groq API key from console.groq.com",
                key="groq_key_input",
            )
            if groq_key:
                st.session_state["groq_api_key"] = groq_key
                provider_configured = True

        # Configuration Status
        api_configured = check_api_configuration(settings)
        fmp_configured = get_fmp_api_key(settings) is not None

        if api_configured:
            st.success("✅ Configuration complete!")
            st.session_state.api_configured = True

            # Check if streaming settings changed
            current_stream = st.session_state.get("streaming_enabled", False)
            current_intermediate = st.session_state.get(
                "stream_intermediate_steps", False
            )
            last_stream = getattr(st.session_state, "last_streaming_enabled", None)
            last_intermediate = getattr(
                st.session_state, "last_stream_intermediate_steps", None
            )

            # Initialize workflow if provider changed, streaming settings changed, or not initialized
            if (
                st.session_state.workflow is None
                or getattr(st.session_state, "current_provider", None)
                != selected_provider
                or last_stream != current_stream
                or last_intermediate != current_intermediate
            ):
                with st.spinner(f"Initializing {selected_provider.title()}..."):
                    llm_model = get_llm_model(selected_provider, settings)
                    if llm_model:
                        # Initialize storage first
                        storage = initialize_storage(settings)

                        # Create composite session_id for user isolation
                        composite_session_id = (
                            f"{st.session_state.user_id}_{st.session_state.session_id}"
                        )

                        # Initialize workflow with the LLM model, settings, storage, composite session_id, and streaming settings
                        st.session_state.workflow = FinancialAssistantWorkflow(
                            llm=llm_model,
                            settings=settings,
                            storage=storage,
                            session_id=composite_session_id,
                            stream=st.session_state.get("streaming_enabled", False),
                            stream_intermediate_steps=st.session_state.get(
                                "stream_intermediate_steps", False
                            ),
                        )
                        st.session_state.current_provider = selected_provider
                        st.session_state.settings = (
                            settings  # Store settings in session
                        )
                        # Track streaming settings to detect changes
                        st.session_state.last_streaming_enabled = current_stream
                        st.session_state.last_stream_intermediate_steps = (
                            current_intermediate
                        )

                        streaming_status = (
                            "with streaming" if current_stream else "without streaming"
                        )
                        st.success(
                            f"✅ Using {selected_provider.title()} {streaming_status}"
                        )
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

        # Streaming Configuration
        st.subheader("⚡ Streaming Settings")
        streaming_enabled = st.checkbox(
            "Enable Response Streaming",
            value=st.session_state.get("streaming_enabled", True),
            help="Stream responses as they are generated for faster feedback",
            key="streaming_toggle",
        )
        st.session_state.streaming_enabled = streaming_enabled

        if streaming_enabled:
            stream_intermediate = st.checkbox(
                "Show Intermediate Steps",
                value=st.session_state.get("stream_intermediate_steps", False),
                help="Display agent reasoning steps during streaming",
                key="intermediate_toggle",
            )
            st.session_state.stream_intermediate_steps = stream_intermediate
        else:
            st.session_state.stream_intermediate_steps = False

        st.markdown("---")

        # Session Management
        st.subheader("💬 Session Management")

        # Display current session info
        current_session_short = st.session_state.session_id[:8] + "..."
        st.write(f"**Current Session:** `{current_session_short}`")

        # Session summary display
        if st.session_state.conversation_summary:
            with st.expander("📋 Conversation Summary", expanded=False):
                st.write(st.session_state.conversation_summary)
        else:
            st.info("No conversation summary yet")

        # Session actions
        col1, col2 = st.columns(2)

        with col1:
            if st.button("🆕 New Session", type="secondary"):
                # Start a new session
                st.session_state.session_id = str(uuid.uuid4())
                st.session_state.messages = []
                st.session_state.conversation_summary = ""
                st.session_state.workflow_state = {}
                st.rerun()

        with col2:
            if st.button("📥 Export Chat", type="secondary"):
                if st.session_state.messages:
                    # Create markdown export
                    export_content = "# Financial Assistant Conversation\n"
                    export_content += f"**Session ID:** {st.session_state.session_id}\n"
                    export_content += (
                        f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                    )

                    for msg in st.session_state.messages:
                        role = (
                            "**User:**" if msg["role"] == "user" else "**Assistant:**"
                        )
                        export_content += f"{role}\n{msg['content']}\n\n---\n\n"

                    st.download_button(
                        label="📄 Download Markdown",
                        data=export_content,
                        file_name=f"financial_chat_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                        mime="text/markdown",
                    )
                else:
                    st.warning("No conversation to export")

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

        if responses is None:
            yield "❌ DEBUG: Workflow returned None instead of iterator"
            return

        for response in responses:
            if hasattr(response, "content") and response.content:
                yield str(response.content)
            else:
                yield str(response)

    except Exception as e:
        yield f"❌ Error processing request: {str(e)}\n\nPlease check your API keys and try again."


def main():
    """Main application entry point"""
    # Initialize settings
    settings = get_app_settings()

    st.set_page_config(
        page_title=settings.app_title,
        page_icon=settings.app_icon,
        layout="wide",
        initial_sidebar_state="expanded",
    )

    # Initialize session state
    initialize_session_state()

    # Setup sidebar with settings
    setup_sidebar(settings)

    # Main content area
    st.title(f"{settings.app_icon} {settings.app_title}")
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
                    chunk_count = 0
                    for response_chunk in process_user_input(prompt):
                        chunk_count += 1
                        # For streaming, each chunk should be displayed as it arrives
                        full_response = (
                            response_chunk  # Each chunk is the complete response so far
                        )
                        response_placeholder.markdown(full_response)

                    # Debug: Show chunk count if streaming is enabled
                    if (
                        st.session_state.get("streaming_enabled", True)
                        and chunk_count > 1
                    ):
                        st.caption(f"🔄 Streamed in {chunk_count} chunks")
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
