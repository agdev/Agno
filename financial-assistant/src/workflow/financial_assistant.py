"""
Financial Assistant Workflow Implementation

This module implements the main FinancialAssistantWorkflow class that orchestrates
the entire financial assistant application using Agno's Level 5 Agentic Workflow pattern.
"""

from datetime import datetime
from typing import Any, Iterator, Optional

from agno.agent import Agent
from agno.models.anthropic import Claude
from agno.run.response import RunResponse
from agno.storage.sqlite import SqliteStorage
from agno.workflow import Workflow
from config.settings import Settings
from models.schemas import Extraction, RouterResult, ConversationMessage, WorkflowSummary, ChatResponse

# Import tools, models, and configuration
from tools.financial_modeling_prep import FinancialModelingPrepTools


class FinancialAssistantWorkflow(Workflow):
    """
    Level 5 Agentic Workflow implementing the financial assistant
    with deterministic flow control for two distinct patterns:
    - Single Information Flow (alone path)
    - Comprehensive Report Flow (report path)
    - Chat Flow (conversational interaction)
    """

    def __init__(
        self,
        llm=None,
        settings: Optional[Settings] = None,
        storage: Optional[SqliteStorage] = None,
        session_id: Optional[str] = None,
    ):
        """
        Initialize the Financial Assistant Workflow

        Args:
            llm: The language model to use for all agents.
                 Defaults to Claude Sonnet 4 if not provided.
            settings: Configuration settings. If not provided, will create new Settings instance.
            storage: Storage instance for session persistence. If not provided, will create based on settings.
            session_id: Composite session ID for user isolation (format: user_id_session_id).
        """
        # Pass session_id to Workflow parent class
        super().__init__(session_id=session_id)

        # Initialize settings
        self.settings = settings or Settings()

        # Initialize session state structure for conversation management
        if not hasattr(self, 'session_state') or not self.session_state:
            self.session_state = {
                # Persistent conversation data
                'messages': [],  # List[ConversationMessage] - Full conversation history
                'conversation_summary': None,  # WorkflowSummary - Current summary
                'last_summary_message_count': 0,  # int - Track when summary was generated
                
                # User context
                'user_preferences': {},  # Dict - User settings and preferences
                'companies_discussed': [],  # List[str] - Companies mentioned in conversation
                
                # Transient workflow state (not critical for persistence)
                'current_category': None,
                'current_symbol': None,
                'workflow_path': None,
            }

        # Initialize storage for session management
        if storage:
            self.storage = storage
        else:
            self.storage = SqliteStorage(
                table_name=self.settings.storage_table_name,
                db_file=self.settings.storage_db_file,
            )

        # Use provided LLM or create default based on settings
        if llm:
            self.llm = llm
        else:
            # Use settings to determine default model
            model_id = self.settings.get_llm_model_id(
                self.settings.default_llm_provider
            )
            if model_id:
                self.llm = Claude(id=model_id)
            else:
                self.llm = Claude(id="claude-sonnet-4-20250514")  # Fallback

        self._initialize_agents()

    def _initialize_agents(self):
        """Initialize all workflow agents with the provided LLM"""

        # Get FMP API key from settings or session state
        fmp_api_key = self.settings.financial_modeling_prep_api_key
        # Initialize Financial Modeling Prep Tools with settings
        self.fmp_tools = FinancialModelingPrepTools(
            api_key=fmp_api_key, settings=self.settings
        )

        # Router Agent - Categorizes user requests with conversation context
        self.router_agent = Agent(
            name="Router Agent",
            role="Categorize user requests for appropriate workflow path using conversation context",
            model=self.llm,
            # Note: Removed storage from agents to avoid storage mode conflicts
            # The workflow itself will handle storage
            enable_session_summaries=self.settings.enable_session_summaries,
            # add_history_to_messages=self.settings.add_history_to_messages,
            # num_history_responses=self.settings.num_history_responses,
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
                "- 'What is a P/E ratio?' -> chat",
            ],
            response_model=RouterResult,
        )

        # Symbol Extraction Agent - Extracts stock symbols with conversation context
        self.symbol_extraction_agent = Agent(
            name="Symbol Extraction Agent",
            role="Extract stock symbols from natural language queries using conversation context",
            model=self.llm,
            tools=[self.fmp_tools],
            # Note: Removed storage from agents to avoid storage mode conflicts
            # enable_session_summaries=self.settings.enable_session_summaries,
            # add_history_to_messages=self.settings.add_history_to_messages,
            # num_history_responses=self.settings.num_history_responses,
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
                "Always return symbols in uppercase",
            ],
            response_model=Extraction,
        )

        # Note: Removed individual data retrieval agents - replaced with direct tool calls for better performance

        # Note: Removed Report Generation Agent - using manual composition for better performance and reliability

        # Chat Agent - Handles conversational interactions
        self.chat_agent = Agent(
            name="Chat Agent",
            role="Handle conversational interactions and general queries",
            model=self.llm,
            # Note: Removed storage from agents to avoid storage mode conflicts
            # add_history_to_messages=self.settings.add_history_to_messages,
            # num_history_responses=self.settings.num_history_responses,
            response_model=ChatResponse,  # Structured response
            instructions=[
                "Provide conversational responses about finance using conversation context",
                "Structure responses with main content and educational context",
                "Suggest relevant follow-up questions when appropriate",
                "Include confidence scores for complex explanations",
                "Offer educational content when appropriate based on user's knowledge level",
                "Keep responses informative but concise and contextually relevant",
                "Use friendly, professional tone consistent with conversation history",
                "Explain financial concepts clearly, building on previous explanations",
                "Ask clarifying questions when needed, considering past interactions",
                "Reference previous topics and companies discussed in the conversation",
                "Adapt explanations based on user's demonstrated understanding level",
            ],
        )

        # Summary Agent - Generates and updates conversation summaries
        self.summary_agent = Agent(
            name="Summary Agent",
            role="Generate and update conversation summaries from message history",
            model=self.llm,
            response_model=WorkflowSummary,
            instructions=[
                "Generate conversation summaries from message history",
                "Update existing summaries with new messages efficiently",
                "Track key topics, companies mentioned, and important insights",
                "Keep summaries concise but comprehensive",
                "Maintain context for financial discussions and data requests",
                "Focus on user interests and recurring topics",
                "Identify patterns in user questions and preferences",
                "Preserve important context for future conversations",
            ],
        )

    def _get_conversation_context(self) -> str:
        """
        Generate conversation context from workflow state

        Returns:
            Formatted context string for agent consumption
        """
        
        # Get current summary
        summary = self.session_state.get('conversation_summary')
        summary_text = summary.summary if summary else "No previous conversation"
        
        # Get recent messages (last 3-5)
        recent_messages = self.session_state.get('messages', [])[-5:]
        recent_context = []
        
        for msg in recent_messages:
            if isinstance(msg, dict):
                # Handle dict format
                role_prefix = "User" if msg.get('role') == "user" else f"Agent ({msg.get('agent_name', 'Unknown')})"
                recent_context.append(f"{role_prefix}: {msg.get('content', '')}")
            else:
                # Handle ConversationMessage object
                role_prefix = "User" if msg.role == "user" else f"Agent ({msg.agent_name})"
                recent_context.append(f"{role_prefix}: {msg.content}")
        
        context = f"""
Conversation Summary: {summary_text}

Recent Messages:
{chr(10).join(recent_context)}

Companies Previously Discussed: {', '.join(self.session_state.get('companies_discussed', []))}
"""
        
        return context.strip()

    def _update_conversation_summary(self) -> Optional[WorkflowSummary]:
        """
        Generate or update conversation summary when needed
        
        Returns:
            Updated WorkflowSummary or None if no update needed
        """
        message_count = len(self.session_state.get('messages', []))
        last_count = self.session_state.get('last_summary_message_count', 0)
        
        # Generate summary every 5-10 messages
        if message_count - last_count >= 5:
            new_messages = self.session_state['messages'][last_count:]
            existing_summary = self.session_state.get('conversation_summary')
            
            # Prepare context for summary agent
            summary_context_parts = []
            
            if existing_summary:
                if isinstance(existing_summary, dict):
                    summary_context_parts.append(f"Previous summary: {existing_summary.get('summary', '')}")
                else:
                    summary_context_parts.append(f"Previous summary: {existing_summary.summary}")
            
            summary_context_parts.append("\nNew messages to summarize:")
            for msg in new_messages:
                if isinstance(msg, dict):
                    role = msg.get('role', 'unknown')
                    content = msg.get('content', '')
                    agent_name = msg.get('agent_name', 'Unknown') if role == 'agent' else ''
                    summary_context_parts.append(f"- {role.title()}{f' ({agent_name})' if agent_name else ''}: {content}")
                else:
                    role = getattr(msg, 'role', 'unknown')
                    content = getattr(msg, 'content', '')
                    agent_name = getattr(msg, 'agent_name', 'Unknown') if role == 'agent' else ''
                    summary_context_parts.append(f"- {role.title()}{f' ({agent_name})' if agent_name else ''}: {content}")
            
            summary_context_parts.append(f"\nTotal messages in conversation: {message_count}")
            
            summary_context = "\n".join(summary_context_parts)
            
            try:
                # Generate updated summary
                summary_response = self.summary_agent.run(summary_context)
                
                # Extract the actual WorkflowSummary from the response
                if hasattr(summary_response, 'content') and hasattr(summary_response.content, 'summary'):
                    # Response contains WorkflowSummary in content
                    updated_summary = summary_response.content
                    self.session_state['conversation_summary'] = updated_summary
                    self.session_state['last_summary_message_count'] = message_count
                    return updated_summary
                elif hasattr(summary_response, 'content'):
                    # Simple string response, create WorkflowSummary wrapper
                    updated_summary = WorkflowSummary(
                        summary=str(summary_response.content),
                        message_count_at_generation=message_count
                    )
                    self.session_state['conversation_summary'] = updated_summary
                    self.session_state['last_summary_message_count'] = message_count
                    return updated_summary
                else:
                    return None
                
            except Exception as e:
                print(f"Warning: Could not generate conversation summary: {e}")
                return None
        
        return self.session_state.get('conversation_summary')

    def get_conversation_context(self, session_id: Optional[str] = None) -> str:
        """
        Get formatted conversation context for agents

        Args:
            session_id: Optional session ID for context retrieval (deprecated - uses workflow state)

        Returns:
            Formatted context string for agent consumption
        """
        # Use the new workflow-level context generation
        return self._get_conversation_context()

    def _compose_financial_report(
        self, 
        symbol: str,
        income_data,  # IncomeStatementData
        financials_data,  # CompanyFinancialsData
        price_data  # StockPriceData
    ) -> str:
        """
        Manually compose financial report from structured data
        
        Args:
            symbol: Stock symbol
            income_data: Income statement data from API
            financials_data: Company financials data from API  
            price_data: Stock price data from API
            
        Returns:
            Formatted markdown report
        """
        
        # Auto-generate insights based on data
        key_insights = self._generate_key_insights(income_data, financials_data, price_data)
        
        # Get company name from data
        company_name = (
            getattr(financials_data, 'company_name', None) or 
            getattr(price_data, 'name', None) or 
            symbol
        )
        
        # Calculate quality scores
        data_quality_score = self._calculate_data_quality(income_data, financials_data, price_data)
        completeness_score = self._calculate_completeness(income_data, financials_data, price_data)
        
        # Compose the report
        report = f"""# Financial Report - {symbol} ({company_name})

## Executive Summary
Comprehensive financial analysis of {company_name} ({symbol}) based on latest available data including income statement, financial ratios, and current market performance.

**Data Quality Score**: {data_quality_score:.1%}  
**Data Completeness**: {completeness_score:.1%}

## Key Insights
{chr(10).join(f'• {insight}' for insight in key_insights)}

## Financial Data

### Income Statement
{self._format_income_statement(income_data, symbol)}

### Company Financials & Ratios  
{self._format_company_financials(financials_data, symbol)}

### Stock Price & Market Data
{self._format_stock_price(price_data, symbol)}

## Analysis Summary

**Strengths:**
{chr(10).join(f'• {strength}' for strength in self._identify_strengths(income_data, financials_data, price_data))}

**Areas of Attention:**
{chr(10).join(f'• {concern}' for concern in self._identify_concerns(income_data, financials_data, price_data))}

---
*Report generated at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} UTC*
"""
        
        return report

    def _generate_key_insights(self, income_data, financials_data, price_data) -> list[str]:
        """Generate key insights from financial data"""
        insights = []
        
        # Revenue analysis
        revenue = getattr(income_data, 'revenue', 0)
        if revenue > 0:
            insights.append(f"Revenue: ${revenue:,.0f}")
        
        # Profitability analysis
        net_income_ratio = getattr(income_data, 'net_income_ratio', 0)
        if net_income_ratio > 0:
            insights.append(f"Net margin: {net_income_ratio:.1%}")
        
        # Valuation analysis
        pe_ratio = getattr(financials_data, 'pe_ratio', 0) or getattr(price_data, 'pe_ratio', 0)
        if pe_ratio and pe_ratio > 0:
            insights.append(f"P/E ratio: {pe_ratio:.2f}")
        
        # Performance analysis
        change_percent = getattr(price_data, 'change_percent', 0)
        if change_percent != 0:
            direction = "up" if change_percent > 0 else "down"
            insights.append(f"Stock {direction} {abs(change_percent):.2f}% today")
        
        # Market cap
        market_cap = getattr(financials_data, 'market_cap', 0) or getattr(price_data, 'market_cap', 0)
        if market_cap > 0:
            if market_cap > 200_000_000_000:
                insights.append("Large-cap company (>$200B)")
            elif market_cap > 10_000_000_000:
                insights.append("Mid-cap company ($10B-$200B)")
            else:
                insights.append("Small-cap company (<$10B)")
        
        return insights if insights else ["Financial data analysis in progress"]

    def _identify_strengths(self, income_data, financials_data, price_data) -> list[str]:
        """Identify company strengths from financial data"""
        strengths = []
        
        # High profitability
        net_margin = getattr(income_data, 'net_income_ratio', 0)
        if net_margin > 0.15:
            strengths.append(f"Strong profitability with {net_margin:.1%} net margin")
        
        # Good ROE
        roe = getattr(financials_data, 'roe', 0)
        if roe > 0.15:
            strengths.append(f"Excellent return on equity at {roe:.1%}")
        
        # Low debt
        debt_to_equity = getattr(financials_data, 'debt_to_equity', 0)
        if 0 < debt_to_equity < 0.3:
            strengths.append("Conservative debt levels")
        
        # Strong growth (if available)
        revenue_growth = getattr(financials_data, 'revenue_growth', 0)
        if revenue_growth > 0.1:
            strengths.append(f"Strong revenue growth at {revenue_growth:.1%}")
        
        return strengths if strengths else ["Detailed analysis requires additional data"]

    def _identify_concerns(self, income_data, financials_data, price_data) -> list[str]:
        """Identify potential areas of concern"""
        concerns = []
        
        # Low profitability
        net_margin = getattr(income_data, 'net_income_ratio', 0)
        if net_margin < 0:
            concerns.append("Company is currently unprofitable")
        elif net_margin < 0.05:
            concerns.append("Low profit margins")
        
        # High debt
        debt_to_equity = getattr(financials_data, 'debt_to_equity', 0)
        if debt_to_equity > 1.0:
            concerns.append("High debt levels relative to equity")
        
        # Poor ROE
        roe = getattr(financials_data, 'roe', 0)
        if 0 < roe < 0.05:
            concerns.append("Low return on equity")
        
        # High valuation
        pe_ratio = getattr(financials_data, 'pe_ratio', 0) or getattr(price_data, 'pe_ratio', 0)
        if pe_ratio and pe_ratio > 30:
            concerns.append(f"High P/E ratio at {pe_ratio:.1f} may indicate overvaluation")
        
        return concerns if concerns else ["No significant concerns identified"]

    def _calculate_data_quality(self, income_data, financials_data, price_data) -> float:
        """Calculate data quality score based on available information"""
        total_fields = 0
        filled_fields = 0
        
        # Check income statement data
        income_fields = ["revenue", "net_income", "eps", "net_income_ratio"]
        for field in income_fields:
            total_fields += 1
            if getattr(income_data, field, None) is not None and getattr(income_data, field, 0) != 0:
                filled_fields += 1
        
        # Check financials data
        financial_fields = ["pe_ratio", "market_cap", "roe", "debt_to_equity"]
        for field in financial_fields:
            total_fields += 1
            if getattr(financials_data, field, None) is not None and getattr(financials_data, field, 0) != 0:
                filled_fields += 1
        
        # Check price data
        price_fields = ["price", "change", "volume"]
        for field in price_fields:
            total_fields += 1
            if getattr(price_data, field, None) is not None and getattr(price_data, field, 0) != 0:
                filled_fields += 1
        
        return filled_fields / total_fields if total_fields > 0 else 0.0

    def _calculate_completeness(self, income_data, financials_data, price_data) -> float:
        """Calculate completeness score based on data sections available"""
        sections_available = 0
        total_sections = 3
        
        if income_data and any(getattr(income_data, field, 0) for field in ["revenue", "net_income"]):
            sections_available += 1
        
        if financials_data and any(getattr(financials_data, field, 0) for field in ["pe_ratio", "market_cap"]):
            sections_available += 1
            
        if price_data and any(getattr(price_data, field, 0) for field in ["price", "change"]):
            sections_available += 1
        
        return sections_available / total_sections

    def _format_financial_data(self, data, data_type: str, symbol: str) -> str:
        """Format financial data into readable markdown

        Args:
            data: Pydantic model with financial data
            data_type: Type of data (income_statement, company_financials, stock_price)
            symbol: Stock symbol for context

        Returns:
            Formatted markdown string
        """
        if not data:
            return f"No {data_type.replace('_', ' ')} data available for {symbol}"

        if data_type == "income_statement":
            return self._format_income_statement(data, symbol)
        elif data_type == "company_financials":
            return self._format_company_financials(data, symbol)
        elif data_type == "stock_price":
            return self._format_stock_price(data, symbol)
        else:
            return f"Unknown data type: {data_type}"

    def _format_income_statement(self, data, symbol: str) -> str:
        """Format income statement data"""
        return f"""# Income Statement - {symbol}

## Revenue
- Total Revenue: {getattr(data, 'revenue', 'N/A')}
- Gross Profit: {getattr(data, 'gross_profit', 'N/A')}

## Expenses & Income
- Operating Income: {getattr(data, 'operating_income', 'N/A')}
- Net Income: {getattr(data, 'net_income', 'N/A')}

## Key Metrics
- EPS: {getattr(data, 'eps', 'N/A')}
- Operating Margin: {getattr(data, 'operating_income_ratio', 'N/A')}

*Data period: {getattr(data, 'date', 'N/A')}*
"""

    def _format_company_financials(self, data, symbol: str) -> str:
        """Format company financials data"""
        return f"""# Company Financials - {symbol}

## Valuation Metrics
- P/E Ratio: {getattr(data, 'pe_ratio', 'N/A')}
- Market Cap: {getattr(data, 'market_cap', 'N/A')}
- Enterprise Value: {getattr(data, 'enterprise_value', 'N/A')}

## Financial Ratios
- ROE: {getattr(data, 'roe', 'N/A')}
- ROA: {getattr(data, 'roa', 'N/A')}
- Debt to Equity: {getattr(data, 'debt_to_equity', 'N/A')}

## Profitability
- Gross Margin: {getattr(data, 'gross_margin', 'N/A')}
- Operating Margin: {getattr(data, 'operating_margin', 'N/A')}
- Net Margin: {getattr(data, 'net_margin', 'N/A')}
"""

    def _format_stock_price(self, data, symbol: str) -> str:
        """Format stock price data"""
        return f"""# Stock Price - {symbol}

## Current Price
- Price: ${getattr(data, 'price', 'N/A')}
- Change: {getattr(data, 'change', 'N/A')} ({getattr(data, 'change_percent', 'N/A')}%)

## Trading Data
- Volume: {getattr(data, 'volume', 'N/A')}
- Market Cap: {getattr(data, 'market_cap', 'N/A')}

## 52-Week Range
- High: ${getattr(data, 'fifty_two_week_high', 'N/A')}
- Low: ${getattr(data, 'fifty_two_week_low', 'N/A')}

*Last updated: {getattr(data, 'timestamp', 'N/A')}*
"""

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

        # Extract and validate message
        message = kwargs.get("message", "")
        if not message:
            yield RunResponse(run_id=self.run_id, content="No message provided")
            return

        # Track user input
        user_message = ConversationMessage(
            role="user",
            content=message,
            timestamp=datetime.now()
        )
        
        # Ensure messages list exists
        if 'messages' not in self.session_state:
            self.session_state['messages'] = []
        
        self.session_state['messages'].append(user_message.dict())
        
        # Update conversation summary if needed
        self._update_conversation_summary()
        
        # Get conversation context for agents
        conversation_context = self._get_conversation_context()

        # Step 1: Route the request with conversation context
        category_response = self.router_agent.run(
            f"User request: {message}\n{conversation_context}"
        )
        
        # Track router agent response
        router_content = category_response.content if category_response.content else "chat"
        router_message = ConversationMessage(
            role="agent",
            content=router_content,
            agent_name="Router Agent",
            structured_data={"category": router_content}
        )
        self.session_state['messages'].append(router_message.dict())

        # Handle potential None content
        category_content = (
            category_response.content if category_response.content else "chat"
        )
        category = category_content.strip().lower()
        self.session_state["category"] = category

        # Step 2: Conditional flow based on category
        if category == "report":
            yield from self._run_report_flow(message)
        elif category == "chat":
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
        symbol_content = (
            symbol_response.content if symbol_response.content else "UNKNOWN"
        )
        symbol = symbol_content.strip()

        # Track symbol extraction response
        symbol_message = ConversationMessage(
            role="agent",
            content=f"Extracted symbol: {symbol}",
            agent_name="Symbol Extraction Agent",
            structured_data={"symbol": symbol, "extraction_successful": symbol != "UNKNOWN"}
        )
        self.session_state['messages'].append(symbol_message.dict())

        if symbol == "UNKNOWN":
            error_message = "Could not extract a valid stock symbol from your request. Please specify a company name or ticker symbol."
            
            # Track error response
            error_response_message = ConversationMessage(
                role="agent",
                content=error_message,
                agent_name="Workflow System",
                structured_data={"error_type": "symbol_extraction_failed"}
            )
            self.session_state['messages'].append(error_response_message.dict())
            
            yield RunResponse(
                run_id=self.run_id,
                content=error_message,
            )
            return

        self.session_state["symbol"] = symbol

        # Direct tool calls for data collection (much faster than individual agents)
        try:
            income_data = self.fmp_tools.get_income_statement(symbol)
            financials_data = self.fmp_tools.get_company_financials(symbol)
            price_data = self.fmp_tools.get_stock_price(symbol)
        except Exception as e:
            yield RunResponse(
                run_id=self.run_id,
                content=f"Error retrieving financial data for {symbol}: {str(e)}",
            )
            return

        # Generate comprehensive report using manual composition
        comprehensive_report = self._compose_financial_report(
            symbol=symbol,
            income_data=income_data,
            financials_data=financials_data,
            price_data=price_data
        )

        # Track report generation response
        report_message = ConversationMessage(
            role="agent",
            content=comprehensive_report,
            agent_name="Financial Report Composer",
            structured_data={
                "symbol": symbol,
                "data_sources": ["income_statement", "company_financials", "stock_price"],
                "report_type": "comprehensive",
                "composition_method": "manual"
            }
        )
        self.session_state['messages'].append(report_message.dict())

        # Cache and yield final result
        self.session_state["last_symbol"] = symbol
        self.session_state["workflow_path"] = "report"
        yield RunResponse(run_id=self.run_id, content=comprehensive_report)

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
        symbol_content = (
            symbol_response.content if symbol_response.content else "UNKNOWN"
        )
        symbol = symbol_content.strip()

        # Track symbol extraction response
        symbol_message = ConversationMessage(
            role="agent",
            content=f"Extracted symbol: {symbol}",
            agent_name="Symbol Extraction Agent",
            structured_data={"symbol": symbol, "extraction_successful": symbol != "UNKNOWN"}
        )
        self.session_state['messages'].append(symbol_message.dict())

        if symbol == "UNKNOWN":
            error_message = "Could not extract a valid stock symbol from your request. Please specify a company name or ticker symbol."
            
            # Track error response
            error_response_message = ConversationMessage(
                role="agent",
                content=error_message,
                agent_name="Workflow System",
                structured_data={"error_type": "symbol_extraction_failed"}
            )
            self.session_state['messages'].append(error_response_message.dict())
            
            yield RunResponse(
                run_id=self.run_id,
                content=error_message,
            )
            return

        self.session_state["symbol"] = symbol

        # Direct tool call based on category (much faster than agent)
        try:
            if category == "income_statement":
                raw_data = self.fmp_tools.get_income_statement(symbol)
            elif category == "company_financials":
                raw_data = self.fmp_tools.get_company_financials(symbol)
            elif category == "stock_price":
                raw_data = self.fmp_tools.get_stock_price(symbol)
            else:
                yield RunResponse(
                    run_id=self.run_id,
                    content="Invalid category for data request. Please specify income statement, company financials, or stock price.",
                )
                return
        except Exception as e:
            yield RunResponse(
                run_id=self.run_id,
                content=f"Error retrieving {category.replace('_', ' ')} data for {symbol}: {str(e)}",
            )
            return

        # Format the raw data into readable markdown
        formatted_content = self._format_financial_data(raw_data, category, symbol)

        # Track financial data response
        data_message = ConversationMessage(
            role="agent",
            content=formatted_content,
            agent_name="Financial Data Agent",
            structured_data={
                "symbol": symbol,
                "data_type": category,
                "data_source": "Financial Modeling Prep",
                "raw_data": raw_data if isinstance(raw_data, dict) else None
            }
        )
        self.session_state['messages'].append(data_message.dict())

        # Cache and yield result
        self.session_state["last_symbol"] = symbol
        self.session_state["workflow_path"] = "alone"
        self.session_state["data_category"] = category
        yield RunResponse(run_id=self.run_id, content=formatted_content)

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
        self.session_state["workflow_path"] = "chat"
        
        # Get conversation context for chat agent
        conversation_context = self._get_conversation_context()
        
        # Run chat agent with context
        response = self.chat_agent.run(f"{message}\n\nContext:\n{conversation_context}")
        
        # Track chat agent response
        response_content = response.content if hasattr(response, 'content') and response.content else str(response)
        chat_message = ConversationMessage(
            role="agent",
            content=response_content,
            agent_name="Chat Agent",
            structured_data={
                "response_type": "conversational",
                "context_used": True,
                "structured_response": response.__dict__ if hasattr(response, '__dict__') else None
            }
        )
        self.session_state['messages'].append(chat_message.dict())
        
        yield RunResponse(run_id=self.run_id, content=response.content if hasattr(response, 'content') else str(response))


# Convenience function for easy workflow instantiation
def create_financial_assistant_workflow(
    llm=None, settings: Optional[Settings] = None, session_id: Optional[str] = None
) -> FinancialAssistantWorkflow:
    """
    Create and return a configured FinancialAssistantWorkflow instance.

    Args:
        llm: Optional language model to use. Defaults to Claude Sonnet 4.
        settings: Optional settings instance. If not provided, creates new Settings.
        session_id: Optional composite session ID for user isolation.

    Returns:
        FinancialAssistantWorkflow: Configured workflow instance
    """
    return FinancialAssistantWorkflow(llm=llm, settings=settings, session_id=session_id)
