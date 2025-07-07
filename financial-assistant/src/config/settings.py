"""
Configuration Settings

This module provides configuration management for the Financial Assistant application
using Pydantic settings with environment variable support.
"""

import os
from pathlib import Path
from typing import List, Literal, Optional, Tuple

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing_extensions import Annotated


def find_env_file() -> Optional[str]:
    """
    Find .env file by searching from current file up to project root

    Returns:
        Path to .env file if found, None otherwise
    """
    # Start from the current file's directory
    current_dir = Path(__file__).parent

    # Search up the directory tree for .env file
    for path in [current_dir] + list(current_dir.parents):
        env_file = Path(path, "env", ".env")
        if env_file.exists():
            return str(env_file)

    # Also check current working directory as fallback
    cwd_env = Path.cwd() / ".env"
    if cwd_env.exists():
        return str(cwd_env)

    return None


class Settings(BaseSettings):
    """
    Application settings with environment variable support

    All settings can be configured via environment variables.
    """

    def __init__(self, **data):
        super().__init__(**data)

    # API Keys
    anthropic_api_key: Optional[str] = Field(
        None, description="Anthropic API key for Claude models"
    )
    openai_api_key: Optional[str] = Field(
        None, description="OpenAI API key for GPT models"
    )
    groq_api_key: Optional[str] = Field(
        None, description="Groq API key for Llama models"
    )
    financial_modeling_prep_api_key: Optional[str] = Field(
        None, description="Financial Modeling Prep API key for financial data"
    )

    # LLM Configuration
    default_llm_provider: Annotated[
        str,
        Field(
            "anthropic",
            alias="llm_provider",  # Support both DEFAULT_LLM_PROVIDER and LLM_PROVIDER
            description="Default LLM provider to use (anthropic, openai, or groq)",
        ),
    ]

    # Application Configuration
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = Field(
        "INFO", description="Logging level"
    )
    streamlit_port: int = Field(8501, description="Port for Streamlit application")

    # Financial Data Configuration
    default_income_statement_period: Literal["annual", "quarter"] = Field(
        "annual", description="Default period for income statement data"
    )
    max_historical_periods: int = Field(
        5, description="Maximum number of historical periods to fetch"
    )

    # Cache Configuration
    enable_data_caching: bool = Field(
        True, description="Whether to enable data caching"
    )
    cache_ttl_minutes: int = Field(15, description="Cache time-to-live in minutes")

    # Performance Configuration
    request_timeout_seconds: int = Field(
        30, description="Timeout for API requests in seconds"
    )
    max_concurrent_requests: int = Field(
        5, description="Maximum concurrent API requests"
    )

    # UI Configuration
    app_title: str = Field("Financial Assistant", description="Application title")
    app_icon: str = Field("🏦", description="Application icon")
    max_chat_history: int = Field(
        50, description="Maximum number of chat messages to keep in history"
    )

    # Session Storage Configuration
    storage_db_file: str = Field(
        "tmp/financial_assistant_sessions.db",
        description="SQLite database file for session storage",
    )
    storage_table_name: str = Field(
        "agent_sessions", description="Table name for agent session storage"
    )

    # Session Summary Configuration
    enable_session_summaries: bool = Field(
        True, description="Enable automatic session summary generation"
    )
    session_summary_model_provider: Literal["anthropic", "openai", "groq"] = Field(
        "anthropic", description="LLM provider for session summary generation"
    )
    max_summary_length: int = Field(
        500, description="Maximum length for session summaries in characters"
    )

    # Chat History Configuration
    add_history_to_messages: bool = Field(
        True, description="Add chat history to messages sent to agents"
    )
    num_history_responses: int = Field(
        3, description="Number of previous messages to include in agent context"
    )

    # Session Management
    auto_generate_session_id: bool = Field(
        True, description="Automatically generate session IDs if not provided"
    )
    session_timeout_hours: int = Field(
        24, description="Session timeout in hours for cleanup"
    )

    model_config = SettingsConfigDict(
        env_file=find_env_file(),  # Automatically find .env file
        env_file_encoding="utf-8",
        case_sensitive=False,
        populate_by_name=True,  # Allow field names and aliases
    )

    @field_validator("default_llm_provider")
    @classmethod
    def validate_llm_provider(cls, v, info):
        """Ensure the default LLM provider has a corresponding API key and normalize case"""
        # First normalize the case (handle Groq, groq, GROQ, etc.)
        v = v.lower()

        # Validate that it's a known provider
        valid_providers = ["anthropic", "openai", "groq"]
        if v not in valid_providers:
            raise ValueError(
                f"Invalid LLM provider '{v}'. Must be one of: {', '.join(valid_providers)}"
            )

        if info.data:
            values = info.data
            if v == "anthropic" and not values.get("anthropic_api_key"):
                if values.get("openai_api_key"):
                    return "openai"
                elif values.get("groq_api_key"):
                    return "groq"
            elif v == "openai" and not values.get("openai_api_key"):
                if values.get("anthropic_api_key"):
                    return "anthropic"
                elif values.get("groq_api_key"):
                    return "groq"
            elif v == "groq" and not values.get("groq_api_key"):
                if values.get("anthropic_api_key"):
                    return "anthropic"
                elif values.get("openai_api_key"):
                    return "openai"
        return v

    @property
    def has_llm_provider(self) -> bool:
        """Check if at least one LLM provider is configured"""
        return any([self.anthropic_api_key, self.openai_api_key, self.groq_api_key])

    @property
    def has_financial_data_provider(self) -> bool:
        """Check if financial data provider is configured"""
        return self.financial_modeling_prep_api_key is not None

    @property
    def is_fully_configured(self) -> bool:
        """Check if all required configuration is present"""
        return self.has_llm_provider and self.has_financial_data_provider

    def get_available_llm_providers(self) -> List[str]:
        """Get list of available LLM providers based on configured API keys"""
        providers = []
        if self.anthropic_api_key:
            providers.append("anthropic")
        if self.openai_api_key:
            providers.append("openai")
        if self.groq_api_key:
            providers.append("groq")
        return providers

    def get_llm_model_id(self, provider: str) -> Optional[str]:
        """Get the model ID for a specific provider"""
        model_mapping = {
            "anthropic": "claude-sonnet-4-20250514",
            "openai": "gpt-4o",
            "groq": "llama-3.3-70b-versatile",  # Example Groq model
        }
        return model_mapping.get(provider)


# def get_settings() -> Settings:
#     """
#     Get the global settings instance (singleton pattern)

#     Returns:
#         Settings: The configured settings instance
#     """
#     global _settings
#     if _settings is None:
#         _settings = Settings()
#     return _settings


def reload_settings() -> Settings:
    """
    Reload settings from environment variables

    Returns:
        Settings: The reloaded settings instance
    """
    return Settings()


def validate_configuration(settings: Settings) -> Tuple[bool, List[str]]:
    """
    Validate the current configuration and return any issues

    Returns:
        tuple: (is_valid, list of error messages)
    """
    errors = []

    if not settings.has_llm_provider:
        errors.append(
            "No LLM provider configured. Please set one of: "
            "ANTHROPIC_API_KEY, OPENAI_API_KEY, or GROQ_API_KEY"
        )

    if not settings.has_financial_data_provider:
        errors.append(
            "Financial data provider not configured. "
            "Please set FINANCIAL_MODELING_PREP_API_KEY"
        )

    # Validate port range
    if not (1024 <= settings.streamlit_port <= 65535):
        errors.append(
            f"Invalid Streamlit port {settings.streamlit_port}. "
            "Must be between 1024 and 65535"
        )

    # Validate timeout
    if settings.request_timeout_seconds <= 0:
        errors.append("Request timeout must be positive")

    # Validate cache TTL
    if settings.cache_ttl_minutes <= 0:
        errors.append("Cache TTL must be positive")

    return len(errors) == 0, errors


# Environment variable helpers
def set_env_var(key: str, value: str) -> None:
    """Set an environment variable and reload settings"""
    os.environ[key] = value
    reload_settings()


def get_env_var(key: str, default: Optional[str] = None) -> Optional[str]:
    """Get an environment variable with optional default"""
    return os.getenv(key, default)
