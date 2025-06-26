"""
Financial Assistant Workflow Implementation

This module implements the main FinancialAssistantWorkflow class that orchestrates
the entire financial assistant application using Agno's Level 5 Agentic Workflow pattern.
"""

from typing import Iterator, Any, Optional
from agno.agent import Agent, RunResponse
from agno.workflow import Workflow
from agno.models.anthropic import Claude
from agno.models.openai import OpenAIChat
from agno.models.groq import Groq
from agno.storage.sqlite import SqliteStorage

# Import tools, models, and configuration
from tools.financial_modeling_prep import FinancialModelingPrepTools
from config.settings import Settings


class FinancialAssistantWorkflow(Workflow):
    """
    Level 5 Agentic Workflow implementing the financial assistant
    with deterministic flow control for two distinct patterns:
    - Single Information Flow (alone path)
    - Comprehensive Report Flow (report path)
    - Chat Flow (conversational interaction)
    """
    
    def __init__(self, llm=None, settings: Optional[Settings] = None, storage: Optional[SqliteStorage] = None):
        """
        Initialize the Financial Assistant Workflow
        
        Args:
            llm: The language model to use for all agents. 
                 Defaults to Claude Sonnet 4 if not provided.
            settings: Configuration settings. If not provided, will create new Settings instance.
            storage: Storage instance for session persistence. If not provided, will create based on settings.
        """
        super().__init__()
        
        # Initialize settings
        self.settings = settings or Settings()
        
        # Initialize storage for session management
        if storage:
            self.storage = storage
        else:
            self.storage = SqliteStorage(
                table_name=self.settings.storage_table_name,
                db_file=self.settings.storage_db_file
            )
        
        # Use provided LLM or create default based on settings
        if llm:
            self.llm = llm
        else:
            # Use settings to determine default model
            model_id = self.settings.get_llm_model_id(self.settings.default_llm_provider)
            if model_id:
                self.llm = Claude(id=model_id)
            else:
                self.llm = Claude(id="claude-sonnet-4-20250514")  # Fallback
        
        self._initialize_agents()
    
    def _initialize_agents(self):
        """Initialize all workflow agents with the provided LLM"""
        
        # Get FMP API key from settings or session state
        fmp_api_key = self.settings.financial_modeling_prep_api_key
        if not fmp_api_key:
            try:
                import streamlit as st
                fmp_api_key = st.session_state.get("fmp_api_key")
            except ImportError:
                pass  # Streamlit not available, that's OK
        
        # Initialize Financial Modeling Prep Tools with settings
        self.fmp_tools = FinancialModelingPrepTools(
            api_key=fmp_api_key, 
            settings=self.settings
        )
        
        # Router Agent - Categorizes user requests with conversation context
        self.router_agent = Agent(
            name="Router Agent",
            role="Categorize user requests for appropriate workflow path using conversation context",
            model=self.llm,
            storage=self.storage,
            enable_session_summaries=self.settings.enable_session_summaries,
            add_history_to_messages=self.settings.add_history_to_messages,
            num_history_responses=self.settings.num_history_responses,
            instructions=[
                "Categorize user requests into: income_statement, company_financials, stock_price, report, or chat",
                "IMPORTANT: Use conversation context and summary to better categorize requests",
                "Consider previous topics and companies mentioned in the conversation",
                "Follow-up questions like 'What about Tesla?' should use context to determine the data type needed",
                "If conversation context mentions specific companies, consider that for ambiguous requests",
                "Return only the category name",
                "Examples:",
                "- 'What is Apple's stock price?' -> stock_price",
                "- 'Show Tesla's income statement' -> income_statement", 
                "- 'Tell me about Apple' -> report",
                "- 'What about Tesla?' (with previous financial context) -> same category as previous request",
                "- 'What is a P/E ratio?' -> chat"
            ]
        )
        
        # Symbol Extraction Agent - Extracts stock symbols with conversation context
        self.symbol_extraction_agent = Agent(
            name="Symbol Extraction Agent", 
            role="Extract stock symbols from natural language queries using conversation context",
            model=self.llm,
            tools=[self.fmp_tools],
            storage=self.storage,
            enable_session_summaries=self.settings.enable_session_summaries,
            add_history_to_messages=self.settings.add_history_to_messages,
            num_history_responses=self.settings.num_history_responses,
            instructions=[
                "Extract stock ticker symbols from user queries using conversation context",
                "IMPORTANT: Use conversation history to resolve ambiguous symbol references",
                "Handle pronouns and references like 'it', 'that company', 'the stock' by checking conversation context",
                "If previous messages mention specific companies, prioritize those for ambiguous references",
                "Handle company names and convert to proper symbols using the search_symbol tool",
                "Examples: 'Apple' -> 'AAPL', 'Tesla' -> 'TSLA', 'Microsoft' -> 'MSFT'",
                "Context examples: 'it' after discussing Apple -> 'AAPL', 'that company' -> refer to last mentioned company",
                "Use the search_symbol tool to validate and find correct symbols",
                "Return 'UNKNOWN' if no valid symbol can be extracted even with context",
                "Always return symbols in uppercase"
            ]
        )
        
        # Data Retrieval Agents with conversation history
        self.income_statement_agent = Agent(
            name="Income Statement Agent",
            role="Retrieve and format income statement data",
            model=self.llm,
            tools=[self.fmp_tools],
            storage=self.storage,
            add_history_to_messages=self.settings.add_history_to_messages,
            num_history_responses=self.settings.num_history_responses,
            instructions=[
                "Use the get_income_statement tool to fetch income statement for given symbol", 
                "Format as structured markdown with clear sections",
                "Include revenue, expenses, profit margins, and key metrics",
                "Present data in a professional, easy-to-read format",
                "Show revenue, gross profit, operating income, net income, and key ratios",
                "Include period information and growth trends if available",
                "Use conversation history to provide relevant context and comparisons"
            ]
        )
        
        self.company_financials_agent = Agent(
            name="Company Financials Agent", 
            role="Retrieve and format company financial metrics",
            model=self.llm,
            tools=[self.fmp_tools],
            storage=self.storage,
            add_history_to_messages=self.settings.add_history_to_messages,
            num_history_responses=self.settings.num_history_responses,
            instructions=[
                "Use the get_company_financials tool to fetch company financials for given symbol", 
                "Format key metrics clearly in structured markdown",
                "Include financial ratios, valuation metrics, and profitability indicators",
                "Highlight important financial health indicators",
                "Show P/E ratio, debt-to-equity, ROE, ROA, margins, and growth metrics",
                "Provide context and interpretation of the financial metrics",
                "Use conversation history to provide relevant comparisons and context"
            ]
        )
        
        self.stock_price_agent = Agent(
            name="Stock Price Agent",
            role="Retrieve and format current stock price data", 
            model=self.llm,
            tools=[self.fmp_tools],
            storage=self.storage,
            add_history_to_messages=self.settings.add_history_to_messages,
            num_history_responses=self.settings.num_history_responses,
            instructions=[
                "Use the get_stock_price tool to fetch current stock price data", 
                "Include price movement and basic analytics",
                "Show current price, change, percentage change, volume",
                "Add context about recent performance and trading activity",
                "Include 52-week high/low, market cap, and trading volume analysis",
                "Format as clear, easy-to-read markdown with key metrics highlighted",
                "Use conversation history to provide relevant context and comparisons"
            ]
        )
        
        # Report Generation Agent - Combines multiple data sources
        self.report_generation_agent = Agent(
            name="Report Generation Agent",
            role="Create comprehensive financial reports from aggregated data",
            model=self.llm,
            storage=self.storage,
            add_history_to_messages=self.settings.add_history_to_messages,
            num_history_responses=self.settings.num_history_responses,
            instructions=[
                "Combine income statement, company financials, and stock price data",
                "Generate structured markdown report with clear sections",
                "Include analysis and key insights based on conversation context",
                "Ensure professional formatting and consistent style",
                "Create executive summary at the top with key findings",
                "Highlight strengths, weaknesses, and opportunities",
                "Reference previous analyses and comparisons from conversation history",
                "Provide relevant context from past discussions about the company"
            ],
            markdown=True
        )
        
        # Chat Agent - Handles conversational interactions
        self.chat_agent = Agent(
            name="Chat Agent",
            role="Handle conversational interactions and general queries",
            model=self.llm,
            storage=self.storage,
            add_history_to_messages=self.settings.add_history_to_messages,
            num_history_responses=self.settings.num_history_responses,
            instructions=[
                "Provide conversational responses about finance using conversation context",
                "Offer educational content when appropriate based on user's knowledge level",
                "Keep responses informative but concise and contextually relevant",
                "Use friendly, professional tone consistent with conversation history",
                "Explain financial concepts clearly, building on previous explanations",
                "Ask clarifying questions when needed, considering past interactions",
                "Reference previous topics and companies discussed in the conversation",
                "Adapt explanations based on user's demonstrated understanding level"
            ]
        )
    
    def get_session_summary(self, session_id: Optional[str] = None) -> Optional[str]:
        """
        Retrieve the current session summary for context
        
        Args:
            session_id: Optional session ID. If not provided, uses current session.
            
        Returns:
            Session summary string or None if not available
        """
        try:
            # If using session summaries, the Agent itself will have access to summaries
            # through the enable_session_summaries feature. For now, let's return None
            # and rely on Agno's built-in session summary functionality within agents.
            
            # TODO: Research the correct API for accessing session summaries from Agno storage
            # The session summaries are likely handled internally by the Agent when
            # enable_session_summaries=True is set
            
            pass
                    
        except Exception as e:
            # Log error but don't fail - graceful degradation
            print(f"Warning: Could not retrieve session summary: {e}")
            
        return None
    
    def get_conversation_context(self, session_id: Optional[str] = None) -> str:
        """
        Get formatted conversation context for agents
        
        Args:
            session_id: Optional session ID for context retrieval
            
        Returns:
            Formatted context string for agent consumption
        """
        # Try to get session summary from Agno's built-in functionality first
        summary = self.get_session_summary(session_id)
        
        if summary:
            return f"Conversation summary: {summary}"
        
        # Fallback to session state if available
        try:
            import streamlit as st
            fallback_summary = st.session_state.get('conversation_summary', '')
            if fallback_summary:
                return f"Conversation summary: {fallback_summary}"
        except ImportError:
            pass
        
        # If no summary available, rely on Agno's built-in history via add_history_to_messages
        # The agents are configured with add_history_to_messages=True so they'll have context
        return "Previous conversation history available through agent memory."
    
    def run(self, **kwargs: Any) -> Iterator[RunResponse]:  # type: ignore[override]
        """
        Main workflow execution implementing the three flow patterns:
        1. Single Information Flow (alone path) 
        2. Comprehensive Report Flow (report path)
        3. Chat Flow
        
        Args:
            **kwargs: Keyword arguments including 'message' for user input
            
        Yields:
            RunResponse: Stream of responses from the workflow execution
        """
        
        # Extract message from kwargs
        message = kwargs.get('message', '')
        if not message:
            yield RunResponse(run_id=self.run_id, content="No message provided")
            return
        
        # Step 1: Route the request with conversation context
        conversation_context = self.get_conversation_context()
        category_response = self.router_agent.run(
            f"User request: {message}\n{conversation_context}"
        )
        
        # Handle potential None content
        category_content = category_response.content if category_response.content else "chat"
        category = category_content.strip().lower()
        self.session_state['category'] = category
        
        # Step 2: Conditional flow based on category
        if category == 'report':
            yield from self._run_report_flow(message)
        elif category == 'chat':
            yield from self._run_chat_flow(message)
        else:  # income_statement, company_financials, stock_price
            yield from self._run_alone_flow(message, category)
    
    def _run_report_flow(self, message: str) -> Iterator[RunResponse]:
        """
        Comprehensive Report Flow - Parallel data collection + aggregation
        
        This flow is triggered for comprehensive business analysis requests.
        It collects income statement, company financials, and stock price data
        in parallel, then generates a comprehensive report.
        
        Args:
            message: User's original request message
            
        Yields:
            RunResponse: Final comprehensive report
        """
        
        # Extract symbol with conversation context
        conversation_context = self.get_conversation_context()
        symbol_response = self.symbol_extraction_agent.run(
            f"Extract symbol from: {message}\n{conversation_context}"
        )
        symbol_content = symbol_response.content if symbol_response.content else "UNKNOWN"
        symbol = symbol_content.strip()
        
        if symbol == 'UNKNOWN':
            yield RunResponse(
                run_id=self.run_id, 
                content="Could not extract a valid stock symbol from your request. Please specify a company name or ticker symbol."
            )
            return
            
        self.session_state['symbol'] = symbol
        
        # Parallel data collection
        # Note: In current implementation, these run sequentially.
        # In Phase 2 with tools, these could run in parallel for better performance.
        income_response = self.income_statement_agent.run(f"Get income statement for {symbol}")
        financials_response = self.company_financials_agent.run(f"Get company financials for {symbol}")
        price_response = self.stock_price_agent.run(f"Get stock price for {symbol}")
        
        # Aggregate data for report generation
        report_data = f"""
        Income Statement Data: {income_response.content}
        
        Company Financials Data: {financials_response.content}
        
        Stock Price Data: {price_response.content}
        """
        
        # Generate comprehensive report
        report_response = self.report_generation_agent.run(
            f"Generate a comprehensive financial report for {symbol} using this data: {report_data}"
        )
        
        # Cache and yield final result
        self.session_state['last_symbol'] = symbol
        self.session_state['workflow_path'] = 'report'
        yield RunResponse(run_id=self.run_id, content=report_response.content)
    
    def _run_alone_flow(self, message: str, category: str) -> Iterator[RunResponse]:
        """
        Single Information Flow - Direct path to specific data
        
        This flow is triggered for specific data requests that only need
        one type of financial information.
        
        Args:
            message: User's original request message
            category: The specific data category (income_statement, company_financials, stock_price)
            
        Yields:
            RunResponse: Specific financial data response
        """
        
        # Extract symbol with conversation context
        conversation_context = self.get_conversation_context()
        symbol_response = self.symbol_extraction_agent.run(
            f"Extract symbol from: {message}\n{conversation_context}"
        )
        symbol_content = symbol_response.content if symbol_response.content else "UNKNOWN"
        symbol = symbol_content.strip()
        
        if symbol == 'UNKNOWN':
            yield RunResponse(
                run_id=self.run_id, 
                content="Could not extract a valid stock symbol from your request. Please specify a company name or ticker symbol."
            )
            return
            
        self.session_state['symbol'] = symbol
        
        # Route to specific data agent based on category
        if category == 'income_statement':
            response = self.income_statement_agent.run(f"Get income statement for {symbol}")
        elif category == 'company_financials':
            response = self.company_financials_agent.run(f"Get company financials for {symbol}")
        elif category == 'stock_price':
            response = self.stock_price_agent.run(f"Get stock price for {symbol}")
        else:
            yield RunResponse(
                run_id=self.run_id, 
                content="Invalid category for data request. Please specify income statement, company financials, or stock price."
            )
            return
        
        # Cache and yield result
        self.session_state['last_symbol'] = symbol
        self.session_state['workflow_path'] = 'alone'
        self.session_state['data_category'] = category
        yield RunResponse(run_id=self.run_id, content=response.content)
    
    def _run_chat_flow(self, message: str) -> Iterator[RunResponse]:
        """
        Chat Flow - Direct conversational response
        
        This flow handles general financial questions, educational content,
        and conversational interactions that don't require data fetching.
        
        Args:
            message: User's conversational message
            
        Yields:
            RunResponse: Conversational response from chat agent
        """
        self.session_state['workflow_path'] = 'chat'
        response = self.chat_agent.run(message)
        yield RunResponse(run_id=self.run_id, content=response.content)


# Convenience function for easy workflow instantiation
def create_financial_assistant_workflow(
    llm=None, 
    settings: Optional[Settings] = None
) -> FinancialAssistantWorkflow:
    """
    Create and return a configured FinancialAssistantWorkflow instance.
    
    Args:
        llm: Optional language model to use. Defaults to Claude Sonnet 4.
        settings: Optional settings instance. If not provided, creates new Settings.
        
    Returns:
        FinancialAssistantWorkflow: Configured workflow instance
    """
    return FinancialAssistantWorkflow(llm=llm, settings=settings)