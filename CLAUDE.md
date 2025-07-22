# Financial Assistant - Agno Framework Migration


## Project Overview

This project is a comprehensive financial assistant application that is being migrated from LangGraph/LangChain to the Agno framework. The application provides intelligent financial data retrieval, analysis, and reporting capabilities through a natural language interface.

## Architecture Summary

**Current State**: Legacy implementation using LangGraph/LangChain with complex graph-based workflows  
**Target State**: Modern Agno Level 5 Agentic Workflow implementation with improved performance and simplified architecture

### Core Capabilities

1. **Intelligent Request Routing**: Categorizes user queries into specific financial data types or comprehensive reports
2. **Symbol Extraction**: LLM-powered extraction of stock symbols from natural language
3. **Financial Data Retrieval**: Integration with Financial Modeling Prep API for:
   - Income statements
   - Company financials  
   - Stock price data
4. **Report Generation**: Comprehensive financial reports combining multiple data sources
5. **Conversational Interface**: Natural language chat for financial education and general queries

### Three Workflow Patterns

1. **Single Information Flow (Alone Path)**: Direct path for specific data requests (e.g., "What is Apple's stock price?")
2. **Comprehensive Report Flow (Report Path)**: Parallel data collection for complete business analysis (e.g., "Tell me about Apple's business")
3. **Chat Flow**: Conversational responses for general financial discussions

## Technology Stack

### Framework & Infrastructure
- **Primary Framework**: [Agno](https://agno.ai) - Modern AI agent framework
- **Web Interface**: Streamlit for user interaction
- **Project Management**: uv for Python package and environment management
- **Testing**: pytest with pytest-mock for comprehensive testing

### AI & Language Models
- **Multi-Provider Support**: OpenAI (GPT), Anthropic (Claude), Groq (Llama)
- **Primary Model**: Claude Sonnet 4 for main workflow operations
- **Structured Output**: Built-in Agno structured output capabilities
- **Memory Management**: Native Agno memory and storage systems

### Data Sources & APIs
- **Financial Data**: Financial Modeling Prep API
- **API Management**: Environment-based configuration with automatic provider detection
- **Data Processing**: Pydantic models for type safety and validation

### Development Tools
- **Environment**: Python 3.11+ with uv virtual environment management
- **Code Quality**: Type hints, comprehensive docstrings, >90% test coverage target
- **Documentation**: Markdown-based docs with detailed implementation plans

## Project Structure

```
financial-assistant/
├── src/
│   ├── __init__.py
│   ├── main.py                     # Entry point and Streamlit app
│   ├── workflow/
│   │   ├── __init__.py
│   │   └── financial_assistant.py  # FinancialAssistantWorkflow class
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── router.py              # Router agent
│   │   ├── symbol_extraction.py   # Symbol extraction agent
│   │   ├── financial_data.py      # Financial data agents
│   │   ├── report_generation.py   # Report generation agent
│   │   └── chat.py               # Chat agent
│   ├── tools/
│   │   ├── __init__.py
│   │   └── financial_modeling_prep.py  # FinancialModelingPrepTools
│   ├── models/
│   │   ├── __init__.py
│   │   └── schemas.py            # Pydantic models for structured data
│   └── config/
│       ├── __init__.py
│       └── settings.py           # Configuration management
├── tests/
│   ├── __init__.py
│   ├── test_workflow.py          # Workflow tests
│   ├── test_agents.py            # Agent tests
│   └── test_tools.py             # Tool tests
├── docs/
│   ├── financial-assistant-analysis.md    # Current system analysis
│   ├── financial-assistant-plan.md        # Migration implementation plan
│   └── implementation-todo.md             # Detailed task tracking
├── requirements.txt              # Dependencies managed by uv
├── pyproject.toml               # Project configuration
├── .env.example                 # Environment variables template
├── .gitignore
├── CLAUDE.md                    # This file - project context for Claude Code
└── README.md
```

## Development Workflow

### Environment Setup (Using uv)
```bash
# Install uv tool
pipx install uv

# Initialize project with Python 3.11
uv init financial-assistant --python 3.11
cd financial-assistant

# Create virtual environment with Python 3.11
uv venv --python 3.11

# Add core dependencies
uv add agno streamlit python-dotenv pydantic

# Add development dependencies  
uv add --dev pytest pytest-mock ipykernel

# Run the application
uv run streamlit run src/main.py

# Run tests
uv run pytest

# Activate virtual environment (if needed)
source .venv/bin/activate  # Linux/macOS
# or .venv\Scripts\activate  # Windows
```

### Key Development Commands
- `uv run <command>`: Execute commands in project environment
- `uv add <package>`: Add new dependency
- `uv sync`: Synchronize environment with lockfile  
- `uv lock`: Update dependency lockfile
- `uv build`: Build distribution packages

## Key Implementation Details

### Agno Workflow Architecture
The application uses Agno's Level 5 Agentic Workflow pattern with:
- **Deterministic Flow Control**: Two distinct workflow patterns with conditional routing
- **Specialized Agents**: 5 focused agents handling specific responsibilities
- **Session State Management**: Built-in state persistence and memory management
- **Parallel Processing**: Coordinated parallel execution for report generation

### Agent Responsibilities
1. **RouterAgent**: Categorizes user requests (income_statement|company_financials|stock_price|report|chat)
2. **SymbolExtractionAgent**: Extracts stock symbols from natural language using Financial Modeling Prep tools
3. **FinancialDataAgents**: Three specialized agents for different data types (income, financials, stock price)
4. **ReportGenerationAgent**: Aggregates multiple data sources into comprehensive markdown reports
5. **ChatAgent**: Handles conversational interactions and financial education

### Performance Targets
- **Response Time**: 30-50% improvement over current LangGraph implementation
- **Memory Usage**: 90%+ reduction (target ~32.5KiB for 5-agent team vs ~50-100MB current)
- **Concurrent Users**: 5-10x improvement in capacity
- **Error Rate**: <1% during normal operation

## Environment Variables

Create a `.env` file based on `.env.example`:

```bash
# Required API Keys
ANTHROPIC_API_KEY=your_anthropic_key_here
OPENAI_API_KEY=your_openai_key_here  # Optional
GROQ_API_KEY=your_groq_key_here      # Optional
FINANCIAL_MODELING_PREP_API_KEY=your_fmp_key_here

# Optional Configuration
DEFAULT_LLM_PROVIDER=anthropic        # anthropic|openai|groq
LOG_LEVEL=INFO                        # DEBUG|INFO|WARNING|ERROR
STREAMLIT_PORT=8501
```

## Testing Strategy

### Test Coverage Goals
- **Unit Tests**: >90% code coverage for all components
- **Integration Tests**: Complete workflow execution testing
- **Performance Tests**: Response time and memory usage validation
- **API Tests**: Financial Modeling Prep API integration testing

### Test Categories
- `test_workflow.py`: Core workflow logic and flow control
- `test_agents.py`: Individual agent behavior and responses
- `test_tools.py`: Financial data tools and API integration
- Performance benchmarks against current LangGraph implementation

## Migration Progress Tracking

Detailed progress is tracked in `docs/implementation-todo.md` with:
- **6 Implementation Phases**: From core migration to deployment
- **Priority-based Tasks**: High/Medium/Low priority classification
- **Success Criteria**: Measurable performance and feature parity goals
- **Validation Checklist**: Comprehensive testing and quality assurance

## Key Migration Milestones

1. **Phase 1**: Core framework migration (Agents + Workflow)
2. **Phase 2**: Tools and API integration (FinancialModelingPrepTools)
3. **Phase 3**: UI integration (Streamlit interface)
4. **Phase 4**: Testing and quality assurance
5. **Phase 5**: Performance optimization
6. **Phase 6**: Documentation and deployment

## Code Quality Standards

- **Type Hints**: Comprehensive type annotations throughout
- **Documentation**: Detailed docstrings for all classes and methods
- **Error Handling**: Graceful degradation and user-friendly error messages
- **Security**: Secure API key handling and input validation
- **Performance**: Memory-efficient patterns and response time optimization

## Related Documentation

- **Current System Analysis**: `docs/financial-assistant-analysis.md`
- **Implementation Plan**: `docs/financial-assistant-plan.md`
- **Task Tracking**: `docs/implementation-todo.md`
- **Code Standards**: `docs/rules/python-best-practices.md`
- **Architecture Guidelines**: `docs/rules/architecture-guidelines.md`
- **Original LangGraph Implementation**: `/home/yoda/Library/Projects/Portfolio/Langgraph/FinancialAssistant/`

## Development Rules and Standards

This project follows strict development standards documented in the `docs/rules/` directory:

- **`docs/rules/python-best-practices.md`**: Comprehensive Python coding standards including:
  - **NO GLOBAL VARIABLES**: Never use global variables - use dependency injection and configuration objects
  - Type hints, error handling, async patterns, testing standards
  - Security guidelines, performance optimization, documentation standards
  - Modern Python 3.11+ features and best practices
- **`docs/rules/architecture-guidelines.md`**: System architecture and design patterns

**IMPORTANT**: All code must follow these rules. Pay special attention to avoiding global variables and using proper dependency injection patterns.

## Notes for Claude Code Assistant

- This project prioritizes defensive security and proper API key management
- The migration preserves all existing functionality while improving performance
- Use uv for all Python environment and dependency management
- Follow the existing code patterns and architecture decisions
- Refer to the detailed implementation plan and task list for guidance
- Test thoroughly against the current LangGraph implementation for feature parity

## Memories and Development Notes

- place your test files in @financial-assistant/src/tests/ folder