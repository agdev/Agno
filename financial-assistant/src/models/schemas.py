"""
Pydantic Models for Financial Data

This module defines Pydantic models for structured data representation
throughout the financial assistant application.
"""

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional, Union

from pydantic import BaseModel, Field, field_validator


class RouterResult(BaseModel):
    """Result from the router agent categorizing user requests"""

    category: Literal[
        "income_statement", "company_financials", "stock_price", "report", "chat"
    ]
    confidence: Optional[float] = Field(
        None, ge=0, le=1, description="Confidence score for routing decision"
    )
    reasoning: Optional[str] = Field(
        None, description="Brief explanation of routing decision"
    )


class Extraction(BaseModel):
    symbol: str = Field(description="The symbol of the company")


class SymbolSearchResult(BaseModel):
    """Result from symbol search/extraction"""

    symbol: str = Field(..., description="Stock ticker symbol")
    company_name: Optional[str] = Field(None, description="Full company name")
    exchange: Optional[str] = Field(None, description="Stock exchange")
    found: bool = Field(..., description="Whether symbol was successfully found")
    error: Optional[str] = Field(None, description="Error message if search failed")


class IncomeStatementData(BaseModel):
    """Income statement financial data"""

    symbol: str
    date: str
    period: str  # 'annual' or 'quarter'
    revenue: float = Field(0, description="Total revenue")
    gross_profit: float = Field(0, description="Gross profit")
    operating_income: float = Field(0, description="Operating income")
    net_income: float = Field(0, description="Net income")
    eps: float = Field(0, description="Earnings per share")
    gross_profit_ratio: float = Field(0, description="Gross profit margin")
    operating_income_ratio: float = Field(0, description="Operating margin")
    net_income_ratio: float = Field(0, description="Net profit margin")
    research_and_development: float = Field(0, description="R&D expenses")
    total_operating_expenses: float = Field(0, description="Total operating expenses")
    success: bool = Field(True, description="Whether data fetch was successful")
    error: Optional[str] = Field(None, description="Error message if fetch failed")

    @field_validator(
        "revenue", "gross_profit", "operating_income", "net_income", mode="before"
    )
    @classmethod
    def convert_to_float(cls, v):
        """Convert numeric values to float, handling None values"""
        if v is None:
            return 0.0
        return float(v)


class CompanyFinancialsData(BaseModel):
    """Company financial metrics and ratios"""

    symbol: str
    company_name: str = Field("Unknown", description="Company name")
    market_cap: float = Field(0, description="Market capitalization")
    beta: float = Field(0, description="Beta coefficient")
    pe_ratio: float = Field(0, description="Price-to-earnings ratio")
    price_to_book: float = Field(0, description="Price-to-book ratio")
    price_to_sales: float = Field(0, description="Price-to-sales ratio")
    debt_to_equity: float = Field(0, description="Debt-to-equity ratio")
    current_ratio: float = Field(0, description="Current ratio")
    quick_ratio: float = Field(0, description="Quick ratio")
    roe: float = Field(0, description="Return on equity")
    roa: float = Field(0, description="Return on assets")
    revenue_growth: float = Field(0, description="Revenue growth rate")
    gross_margin: float = Field(0, description="Gross profit margin")
    operating_margin: float = Field(0, description="Operating profit margin")
    net_margin: float = Field(0, description="Net profit margin")
    enterprise_value: float = Field(0, description="Enterprise value")
    working_capital: float = Field(0, description="Working capital")
    date: str = Field("Unknown", description="Date of data")
    success: bool = Field(True, description="Whether data fetch was successful")
    error: Optional[str] = Field(None, description="Error message if fetch failed")

    @field_validator("market_cap", "enterprise_value", "working_capital", mode="before")
    @classmethod
    def convert_large_numbers(cls, v):
        """Convert large numbers to float, handling None values"""
        if v is None:
            return 0.0
        return float(v)


class StockPriceData(BaseModel):
    """Current stock price and trading data"""

    symbol: str
    name: str = Field("Unknown", description="Company name")
    price: float = Field(0, description="Current stock price")
    change: float = Field(0, description="Price change from previous close")
    change_percent: float = Field(
        0, description="Percentage change from previous close"
    )
    previous_close: float = Field(0, description="Previous closing price")
    open: float = Field(0, description="Opening price")
    high: float = Field(0, description="Day's high")
    low: float = Field(0, description="Day's low")
    volume: int = Field(0, description="Trading volume")
    avg_volume: int = Field(0, description="Average volume")
    market_cap: float = Field(0, description="Market capitalization")
    pe_ratio: float = Field(0, description="Price-to-earnings ratio")
    eps: float = Field(0, description="Earnings per share")
    fifty_two_week_high: float = Field(0, description="52-week high")
    fifty_two_week_low: float = Field(0, description="52-week low")
    exchange: str = Field("Unknown", description="Stock exchange")
    timestamp: int = Field(0, description="Data timestamp")
    success: bool = Field(True, description="Whether data fetch was successful")
    error: Optional[str] = Field(None, description="Error message if fetch failed")

    @field_validator(
        "price", "change", "previous_close", "open", "high", "low", mode="before"
    )
    @classmethod
    def convert_prices(cls, v):
        """Convert price values to float, handling None values"""
        if v is None:
            return 0.0
        return float(v)

    @field_validator("volume", "avg_volume", mode="before")
    @classmethod
    def convert_volumes(cls, v):
        """Convert volume values to int, handling None values"""
        if v is None:
            return 0
        return int(v)


class CompanyProfileData(BaseModel):
    """Basic company profile information"""

    symbol: str
    company_name: str = Field("Unknown", description="Company name")
    description: str = Field(
        "No description available", description="Company description"
    )
    industry: str = Field("Unknown", description="Industry")
    sector: str = Field("Unknown", description="Sector")
    website: str = Field("", description="Company website")
    ceo: str = Field("Unknown", description="CEO name")
    employees: int = Field(0, description="Number of full-time employees")
    country: str = Field("Unknown", description="Country")
    exchange: str = Field("Unknown", description="Stock exchange")
    currency: str = Field("USD", description="Trading currency")
    success: bool = Field(True, description="Whether data fetch was successful")
    error: Optional[str] = Field(None, description="Error message if fetch failed")


class FinancialReport(BaseModel):
    """Comprehensive financial report combining multiple data sources"""

    symbol: str
    company_name: str
    generated_at: datetime = Field(default_factory=datetime.now)

    # Core financial data
    income_statement: Optional[IncomeStatementData] = None
    company_financials: Optional[CompanyFinancialsData] = None
    stock_price: Optional[StockPriceData] = None
    company_profile: Optional[CompanyProfileData] = None

    # Report content
    executive_summary: str = Field("", description="Executive summary of the report")
    key_insights: List[str] = Field(
        default_factory=list, description="Key insights and findings"
    )
    strengths: List[str] = Field(default_factory=list, description="Company strengths")
    weaknesses: List[str] = Field(default_factory=list, description="Areas of concern")
    opportunities: List[str] = Field(
        default_factory=list, description="Growth opportunities"
    )

    # Report metadata
    data_quality_score: float = Field(
        1.0, ge=0, le=1, description="Quality score of underlying data"
    )
    completeness_score: float = Field(
        1.0, ge=0, le=1, description="Completeness of available data"
    )
    report_markdown: str = Field("", description="Full report in markdown format")

    @field_validator("data_quality_score", "completeness_score")
    @classmethod
    def validate_scores(cls, v):
        """Ensure scores are between 0 and 1"""
        return max(0.0, min(1.0, v))


class WorkflowState(BaseModel):
    """State management for the financial assistant workflow"""

    request: str = Field("", description="Original user request")
    category: Optional[str] = Field(None, description="Request category from router")
    symbol: Optional[str] = Field(None, description="Extracted stock symbol")
    workflow_path: Optional[str] = Field(
        None, description="Workflow path taken (alone/report/chat)"
    )
    data_category: Optional[str] = Field(
        None, description="Specific data category for alone path"
    )

    # Conversation context
    conversation_summary: str = Field("", description="Summary of conversation history")
    last_symbol: Optional[str] = Field(None, description="Last used stock symbol")
    user_preferences: Dict[str, Any] = Field(
        default_factory=dict, description="User preferences"
    )

    # Data cache
    cached_data: Dict[str, Any] = Field(
        default_factory=dict, description="Cached financial data"
    )

    # Workflow control
    parallel_complete: bool = Field(
        False, description="Whether parallel data collection is complete"
    )
    error_count: int = Field(0, description="Number of errors encountered")
    retry_count: int = Field(0, description="Number of retries attempted")

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    def update_timestamp(self):
        """Update the updated_at timestamp"""
        self.updated_at = datetime.now()


class AgentResponse(BaseModel):
    """Standard response format for individual agents"""

    agent_name: str = Field(..., description="Name of the responding agent")
    content: str = Field(..., description="Agent response content")
    data: Optional[Dict[str, Any]] = Field(
        None, description="Structured data if applicable"
    )
    success: bool = Field(True, description="Whether agent execution was successful")
    error: Optional[str] = Field(None, description="Error message if execution failed")
    execution_time: Optional[float] = Field(
        None, description="Execution time in seconds"
    )
    tokens_used: Optional[int] = Field(None, description="Number of tokens used")

    # Response metadata
    confidence: Optional[float] = Field(
        None, ge=0, le=1, description="Confidence in response"
    )
    sources: List[str] = Field(default_factory=list, description="Data sources used")
    timestamp: datetime = Field(default_factory=datetime.now)


class ErrorInfo(BaseModel):
    """Error information for debugging and monitoring"""

    error_type: str = Field(..., description="Type/category of error")
    error_message: str = Field(..., description="Detailed error message")
    context: Dict[str, Any] = Field(default_factory=dict, description="Error context")
    timestamp: datetime = Field(default_factory=datetime.now)
    recoverable: bool = Field(True, description="Whether error is recoverable")
    retry_suggested: bool = Field(False, description="Whether retry is suggested")


# New models for message and summary management

class ConversationMessage(BaseModel):
    """Message in the conversation history"""
    role: Literal["user", "agent"]
    content: str
    agent_name: Optional[str] = None
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    structured_data: Optional[Dict[str, Any]] = None  # For agent response data


class WorkflowSummary(BaseModel):
    """Conversation summary with metadata"""
    summary: str = Field(..., description="Main conversation summary")
    key_topics: List[str] = Field(default_factory=list, description="Key discussion topics")
    companies_mentioned: List[str] = Field(default_factory=list, description="Companies discussed")
    last_updated: str = Field(default_factory=lambda: datetime.now().isoformat())
    message_count_at_generation: int = Field(0, description="Message count when summary was generated")


class ChatResponse(BaseModel):
    """Structured response from chat agent"""
    content: str = Field(..., description="Main response content")
    educational_context: Optional[str] = Field(None, description="Educational explanation if applicable")
    references: List[str] = Field(default_factory=list, description="References or sources")
    follow_up_suggestions: List[str] = Field(default_factory=list, description="Suggested follow-up questions")
    confidence: Optional[float] = Field(None, ge=0, le=1, description="Response confidence")


# Type aliases for convenience
FinancialDataType = Union[
    IncomeStatementData, CompanyFinancialsData, StockPriceData, CompanyProfileData
]
WorkflowResponse = Union[str, FinancialReport, AgentResponse, ChatResponse]
