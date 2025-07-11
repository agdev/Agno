# Financial Assistant - Agno Framework

A modern financial assistant application built with the [Agno](https://agno.ai) framework, providing intelligent financial data retrieval, analysis, and reporting capabilities through a natural language interface.

## Overview

This application has been migrated from LangGraph/LangChain to the Agno framework to leverage improved performance, simplified architecture, and built-in capabilities. It provides three distinct workflow patterns:

1. **Single Information Flow**: Direct path for specific data requests (e.g., "What is Apple's stock price?")
2. **Comprehensive Report Flow**: Parallel data collection for complete business analysis (e.g., "Tell me about Apple's business")
3. **Chat Flow**: Conversational responses for general financial discussions

## Features

- **Intelligent Request Routing**: Automatically categorizes user queries
- **Symbol Extraction**: LLM-powered extraction of stock symbols from natural language
- **Financial Data Retrieval**: Integration with Financial Modeling Prep API for real-time data
- **Comprehensive Reports**: Professional markdown reports combining multiple data sources
- **Multi-Provider LLM Support**: OpenAI, Anthropic, and Groq integration
- **Streamlit Interface**: Clean, intuitive web interface

## Architecture

The application uses Agno's Level 5 Agentic Workflow pattern with:
- **5 Specialized Agents**: Router, Symbol Extraction, Financial Data (3x), Report Generation, and Chat
- **Deterministic Flow Control**: Two distinct workflow patterns with conditional routing
- **Session State Management**: Built-in state persistence and memory management
- **Parallel Processing**: Coordinated parallel execution for report generation

## Installation

### Prerequisites

- Python 3.11+
- [uv](https://github.com/astral-sh/uv) tool for dependency management

### Setup

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd financial-assistant
   ```

2. **Install dependencies**:
   ```bash
   # Install uv if not already installed
   pipx install uv
   
   # Install project dependencies
   uv sync
   ```

3. **Configure environment variables**:
   ```bash
   # Copy the example environment file
   cp .env.example .env
   
   # Edit .env with your API keys
   ```

   Required environment variables:
   ```bash
   # Required API Keys
   FINANCIAL_MODELING_PREP_API_KEY=your_fmp_key_here
   ANTHROPIC_API_KEY=your_anthropic_key_here  # OR
   OPENAI_API_KEY=your_openai_key_here        # OR
   GROQ_API_KEY=your_groq_key_here            # At least one LLM provider
   
   # Optional Configuration
   DEFAULT_LLM_PROVIDER=anthropic
   LOG_LEVEL=INFO
   ```

### API Keys

1. **Financial Modeling Prep API** (Required):
   - Sign up at [financialmodelingprep.com](https://financialmodelingprep.com)
   - Get your free API key from the dashboard

2. **LLM Provider** (At least one required):
   - **Anthropic Claude**: Get API key from [console.anthropic.com](https://console.anthropic.com)
   - **OpenAI**: Get API key from [platform.openai.com](https://platform.openai.com/api-keys)
   - **Groq**: Get API key from [console.groq.com](https://console.groq.com)

## Usage

### Running the Application

```bash
# Activate the virtual environment
source .venv/bin/activate  # Linux/macOS
# or .venv\Scripts\activate  # Windows

# Run the Streamlit application
uv run streamlit run src/main.py

# Or using the application launcher
python run.py
```

The application will be available at `http://localhost:8501`.

### Example Queries

**Specific Data Requests**:
- "What is Apple's stock price?"
- "Show Tesla's income statement"
- "Get Microsoft's financial ratios"

**Comprehensive Reports**:
- "Tell me about Apple's business"
- "Analyze Amazon's financials"
- "Generate a report on Google"

**General Questions**:
- "What is a P/E ratio?"
- "Explain revenue vs profit"
- "How do I analyze stocks?"

## Development

### Running Tests

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=src

# Run specific test file
uv run pytest tests/test_workflow.py -v
```

### Project Structure

```
financial-assistant/
   src/
      workflow/
         financial_assistant.py    # Main workflow implementation
      agents/                       # Individual agent implementations (future)
      tools/
         financial_modeling_prep.py # Financial data tools
      models/
         schemas.py                # Pydantic data models
      config/
         settings.py               # Configuration management
      main.py                       # Streamlit application
   tests/
      test_workflow.py              # Unit tests
   docs/                             # Project documentation
   .env.example                      # Environment variables template
   pyproject.toml                    # Project configuration
   README.md                         # This file
```

### Development Commands

```bash
# Install development dependencies
uv add --dev <package>

# Add production dependencies
uv add <package>

# Update dependencies
uv sync

# Build distribution
uv build
```

## Performance

Expected performance improvements over LangGraph implementation:
- **Response Time**: 30-50% improvement
- **Memory Usage**: 90%+ reduction (~32.5KiB for 5-agent team vs ~50-100MB)
- **Concurrent Users**: 5-10x improvement in capacity
- **Error Rate**: <1% during normal operation

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Run the test suite: `uv run pytest`
6. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For issues and questions:
1. Check the [documentation](docs/)
2. Search existing [issues](../../issues)
3. Create a new issue with detailed information

## Acknowledgments

- Built with [Agno](https://agno.ai) framework
- Financial data provided by [Financial Modeling Prep](https://financialmodelingprep.com)
- UI powered by [Streamlit](https://streamlit.io)