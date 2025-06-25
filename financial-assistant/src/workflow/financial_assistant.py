"""
Financial Assistant Workflow Implementation

This module implements the main FinancialAssistantWorkflow class that orchestrates
the entire financial assistant application using Agno's Level 5 Agentic Workflow pattern.
"""

from typing import Iterator, Optional
from agno.agent import Agent, RunResponse
from agno.workflow import Workflow
from agno.models.anthropic import Claude
from agno.models.openai import OpenAIChat

# Import tools and models
from tools.financial_modeling_prep import FinancialModelingPrepTools
from models.schemas import RouterResult


class FinancialAssistantWorkflow(Workflow):
    """
    Level 5 Agentic Workflow implementing the financial assistant
    with deterministic flow control for two distinct patterns:
    - Single Information Flow (alone path)
    - Comprehensive Report Flow (report path)
    - Chat Flow (conversational interaction)
    """
    
    def __init__(self, llm=None):
        """
        Initialize the Financial Assistant Workflow
        
        Args:
            llm: The language model to use for all agents. 
                 Defaults to Claude Sonnet 4 if not provided.
        """
        super().__init__()
        self.llm = llm or Claude(id="claude-sonnet-4-20250514")
        self._initialize_agents()
    
    def _initialize_agents(self):
        """Initialize all workflow agents with the provided LLM"""
        
        # Initialize Financial Modeling Prep Tools
        self.fmp_tools = FinancialModelingPrepTools()
        
        # Router Agent - Categorizes user requests
        self.router_agent = Agent(
            name="Router Agent",
            role="Categorize user requests for appropriate workflow path",
            model=self.llm,
            instructions=[
                "Categorize user requests into: income_statement, company_financials, stock_price, report, or chat",
                "Use conversation context from session for better categorization",
                "Return only the category name",
                "Examples:",
                "- 'What is Apple's stock price?' -> stock_price",
                "- 'Show Tesla's income statement' -> income_statement", 
                "- 'Tell me about Apple' -> report",
                "- 'What is a P/E ratio?' -> chat"
            ]
        )
        
        # Symbol Extraction Agent - Extracts stock symbols from natural language
        self.symbol_extraction_agent = Agent(
            name="Symbol Extraction Agent", 
            role="Extract stock symbols from natural language queries",
            model=self.llm,
            tools=[self.fmp_tools],
            instructions=[
                "Extract stock ticker symbols from user queries",
                "Handle company names and convert to proper symbols using the search_symbol tool",
                "Examples: 'Apple' -> 'AAPL', 'Tesla' -> 'TSLA', 'Microsoft' -> 'MSFT'",
                "Use the search_symbol tool to validate and find correct symbols",
                "Return 'UNKNOWN' if no valid symbol can be extracted",
                "Always return symbols in uppercase"
            ]
        )
        
        # Data Retrieval Agents
        self.income_statement_agent = Agent(
            name="Income Statement Agent",
            role="Retrieve and format income statement data",
            model=self.llm,
            tools=[self.fmp_tools],
            instructions=[
                "Use the get_income_statement tool to fetch income statement for given symbol", 
                "Format as structured markdown with clear sections",
                "Include revenue, expenses, profit margins, and key metrics",
                "Present data in a professional, easy-to-read format",
                "Show revenue, gross profit, operating income, net income, and key ratios",
                "Include period information and growth trends if available"
            ]
        )
        
        self.company_financials_agent = Agent(
            name="Company Financials Agent", 
            role="Retrieve and format company financial metrics",
            model=self.llm,
            tools=[self.fmp_tools],
            instructions=[
                "Use the get_company_financials tool to fetch company financials for given symbol", 
                "Format key metrics clearly in structured markdown",
                "Include financial ratios, valuation metrics, and profitability indicators",
                "Highlight important financial health indicators",
                "Show P/E ratio, debt-to-equity, ROE, ROA, margins, and growth metrics",
                "Provide context and interpretation of the financial metrics"
            ]
        )
        
        self.stock_price_agent = Agent(
            name="Stock Price Agent",
            role="Retrieve and format current stock price data", 
            model=self.llm,
            tools=[self.fmp_tools],
            instructions=[
                "Use the get_stock_price tool to fetch current stock price data", 
                "Include price movement and basic analytics",
                "Show current price, change, percentage change, volume",
                "Add context about recent performance and trading activity",
                "Include 52-week high/low, market cap, and trading volume analysis",
                "Format as clear, easy-to-read markdown with key metrics highlighted"
            ]
        )
        
        # Report Generation Agent - Combines multiple data sources
        self.report_generation_agent = Agent(
            name="Report Generation Agent",
            role="Create comprehensive financial reports from aggregated data",
            model=self.llm,
            instructions=[
                "Combine income statement, company financials, and stock price data",
                "Generate structured markdown report with clear sections",
                "Include analysis and key insights",
                "Ensure professional formatting",
                "Create executive summary at the top",
                "Highlight strengths, weaknesses, and opportunities"
            ],
            markdown=True
        )
        
        # Chat Agent - Handles conversational interactions
        self.chat_agent = Agent(
            name="Chat Agent",
            role="Handle conversational interactions and general queries",
            model=self.llm,
            instructions=[
                "Provide conversational responses about finance",
                "Offer educational content when appropriate",
                "Keep responses informative but concise",
                "Use friendly, professional tone",
                "Explain financial concepts clearly",
                "Ask clarifying questions when needed"
            ]
        )
    
    def run(self, message: str) -> Iterator[RunResponse]:
        """
        Main workflow execution implementing the three flow patterns:
        1. Single Information Flow (alone path) 
        2. Comprehensive Report Flow (report path)
        3. Chat Flow
        
        Args:
            message: User's input message/query
            
        Yields:
            RunResponse: Stream of responses from the workflow execution
        """
        
        # Step 1: Route the request
        conversation_summary = self.session_state.get('conversation_summary', '')
        category_response = self.router_agent.run(
            f"User request: {message}\nConversation summary: {conversation_summary}"
        )
        category = category_response.content.strip().lower()
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
        
        # Extract symbol
        symbol_response = self.symbol_extraction_agent.run(message)
        symbol = symbol_response.content.strip()
        
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
        
        # Extract symbol
        symbol_response = self.symbol_extraction_agent.run(message)
        symbol = symbol_response.content.strip()
        
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
def create_financial_assistant_workflow(llm=None) -> FinancialAssistantWorkflow:
    """
    Create and return a configured FinancialAssistantWorkflow instance.
    
    Args:
        llm: Optional language model to use. Defaults to Claude Sonnet 4.
        
    Returns:
        FinancialAssistantWorkflow: Configured workflow instance
    """
    return FinancialAssistantWorkflow(llm=llm)