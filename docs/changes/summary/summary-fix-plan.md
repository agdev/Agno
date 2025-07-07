# Financial Assistant Message & Summary Management Fix Plan

## Overview

This document outlines the comprehensive plan to fix the message handling and conversation summary issues in the Financial Assistant application. The current implementation has several critical problems that need to be addressed to properly implement workflow-level state management using Agno framework best practices.

## Current Issues Identified

### 1. **Broken Session Summary Logic**
- `get_session_summary()` method tries to access `self.router_agent.memory.get_session_summary()` 
- **Architectural Problem**: Wrong pattern of accessing agent-level memory from workflow level
- **Fundamental Issue**: This approach is incorrect regardless of agent memory configuration
- Logic assumes agent-level memory management when it should be workflow-level
- Attempts to get user_id and session_id from agent attributes that don't exist

### 2. **Incorrect Message and Summary Handling**
- Messages are stored at individual agent level but workflow has no visibility
- No workflow-level message tracking for user inputs and agent outputs  
- Session summaries are not stored in workflow state
- No proper conversation history management at the workflow level
- Broken conversation context retrieval

### 3. **Agents Returning Markdown Instead of Pydantic Models**
- Report generation agent returns markdown text instead of structured `FinancialReport` model
- Financial data formatting done at workflow level instead of returning structured models
- Chat agent returns plain text instead of structured response
- Inconsistent data flow between agents and UI

## Solution Architecture

### **Core Principle: Workflow-Level State Management**
- Use Agno's `self.session_state` for persistent conversation tracking
- Leverage existing SQLite storage for automatic persistence
- Simple session strategy: one persistent conversation per browser session

### **Data Flow Design**
```
User Input → Workflow tracks message → Agent processes → Workflow stores structured response → UI formats for display
```

### **Session Management Strategy**
- **Composite Session ID**: Use `f"{user_id}_{session_id}"` for Agno workflow storage
- **user_id**: Browser-persistent identifier (`st.session_state.user_id`)
- **session_id**: Conversation-specific identifier (`st.session_state.session_id`)
- One persistent conversation per browser session (no multiple sessions)
- Automatic persistence via Agno's storage integration with composite ID for user isolation

## Detailed Implementation Plan

### **Phase 1: Create Required Pydantic Models**

#### 1.1 Add to `src/models/schemas.py`

```python
class ConversationMessage(BaseModel):
    """Message in the conversation history"""
    role: Literal["user", "agent"]
    content: str
    agent_name: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)
    structured_data: Optional[Dict[str, Any]] = None  # For agent response data

class WorkflowSummary(BaseModel):
    """Conversation summary with metadata"""
    summary: str = Field(..., description="Main conversation summary")
    key_topics: List[str] = Field(default_factory=list, description="Key discussion topics")
    companies_mentioned: List[str] = Field(default_factory=list, description="Companies discussed")
    last_updated: datetime = Field(default_factory=datetime.now)
    message_count_at_generation: int = Field(0, description="Message count when summary was generated")

class ChatResponse(BaseModel):
    """Structured response from chat agent"""
    content: str = Field(..., description="Main response content")
    educational_context: Optional[str] = Field(None, description="Educational explanation if applicable")
    references: List[str] = Field(default_factory=list, description="References or sources")
    follow_up_suggestions: List[str] = Field(default_factory=list, description="Suggested follow-up questions")
    confidence: Optional[float] = Field(None, ge=0, le=1, description="Response confidence")
```

### **Phase 2: Fix Workflow Session State Structure**

#### 2.1 Update Workflow Initialization
- Create composite session ID from `f"{st.session_state.user_id}_{st.session_state.session_id}"`
- Pass composite session ID to workflow constructor
- Initialize proper session state structure

#### 2.2 Session State Schema
```python
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
```

### **Phase 3: Create Summary Management Agent**

#### 3.1 Add Summary Agent
```python
class SummaryAgent(Agent):
    """Agent responsible for generating and updating conversation summaries"""
    response_model = WorkflowSummary
    
    instructions = [
        "Generate conversation summaries from message history",
        "Update existing summaries with new messages efficiently",
        "Track key topics, companies mentioned, and important insights",
        "Keep summaries concise but comprehensive",
        "Maintain context for financial discussions and data requests"
    ]
```

#### 3.2 Summary Generation Logic
```python
def _update_conversation_summary(self) -> Optional[WorkflowSummary]:
    """Generate or update conversation summary when needed"""
    message_count = len(self.session_state.get('messages', []))
    last_count = self.session_state.get('last_summary_message_count', 0)
    
    # Generate summary every 5-10 messages
    if message_count - last_count >= 5:
        new_messages = self.session_state['messages'][last_count:]
        existing_summary = self.session_state.get('conversation_summary')
        
        # Prepare context for summary agent
        summary_context = {
            'existing_summary': existing_summary.summary if existing_summary else None,
            'new_messages': [msg.dict() for msg in new_messages],
            'message_count': message_count
        }
        
        # Generate updated summary
        updated_summary = self.summary_agent.run(summary_context)
        
        # Store in session state
        self.session_state['conversation_summary'] = updated_summary.content
        self.session_state['last_summary_message_count'] = message_count
        
        return updated_summary.content
    
    return self.session_state.get('conversation_summary')
```

### **Phase 4: Remove Report Generation Agent**

#### 4.1 Delete Report Agent
- Remove `self.report_generation_agent` from workflow
- Remove related agent initialization code

#### 4.2 Implement Manual Report Composition
```python
def _compose_financial_report(
    self, 
    symbol: str,
    income_data: IncomeStatementData,
    financials_data: CompanyFinancialsData,
    price_data: StockPriceData
) -> FinancialReport:
    """Manually compose financial report from structured data"""
    
    # Auto-generate insights based on data
    key_insights = self._generate_key_insights(income_data, financials_data, price_data)
    
    return FinancialReport(
        symbol=symbol,
        company_name=financials_data.company_name,
        income_statement=income_data,
        company_financials=financials_data,
        stock_price=price_data,
        key_insights=key_insights,
        generated_at=datetime.now(),
        data_quality_score=self._calculate_data_quality(income_data, financials_data, price_data),
        completeness_score=self._calculate_completeness(income_data, financials_data, price_data)
    )

def _generate_key_insights(self, income_data, financials_data, price_data) -> List[str]:
    """Generate key insights from financial data"""
    insights = []
    
    # Revenue analysis
    if income_data.revenue > 0:
        insights.append(f"Revenue: ${income_data.revenue:,.0f}")
    
    # Profitability analysis
    if income_data.net_income_ratio > 0:
        insights.append(f"Net margin: {income_data.net_income_ratio:.1%}")
    
    # Valuation analysis
    if financials_data.pe_ratio > 0:
        insights.append(f"P/E ratio: {financials_data.pe_ratio:.2f}")
    
    # Performance analysis
    if price_data.change_percent != 0:
        direction = "up" if price_data.change_percent > 0 else "down"
        insights.append(f"Stock {direction} {abs(price_data.change_percent):.2f}% today")
    
    return insights
```

### **Phase 5: Fix Agent Response Models**

#### 5.1 Update Financial Modeling Prep Tools
- Modify all tool methods to return Pydantic models directly
- Remove dictionary returns, use structured models

```python
# Before (returns dict)
def get_income_statement(self, symbol: str) -> Dict[str, Any]:
    # ... API call logic
    return {
        "symbol": symbol,
        "revenue": income_statement.get("revenue", 0),
        # ... other fields
    }

# After (returns Pydantic model)
def get_income_statement(self, symbol: str) -> IncomeStatementData:
    # ... API call logic
    return IncomeStatementData(
        symbol=symbol,
        date=income_statement.get("date", "Unknown"),
        period=income_statement.get("period", "annual"),
        revenue=income_statement.get("revenue", 0),
        gross_profit=income_statement.get("grossProfit", 0),
        operating_income=income_statement.get("operatingIncome", 0),
        net_income=income_statement.get("netIncome", 0),
        eps=income_statement.get("eps", 0),
        gross_profit_ratio=income_statement.get("grossProfitRatio", 0),
        operating_income_ratio=income_statement.get("operatingIncomeRatio", 0),
        net_income_ratio=income_statement.get("netIncomeRatio", 0),
        research_and_development=income_statement.get("researchAndDevelopmentExpenses", 0),
        total_operating_expenses=income_statement.get("totalOperatingExpenses", 0),
        success=True
    )
```

#### 5.2 Update Chat Agent
```python
self.chat_agent = Agent(
    name="Chat Agent",
    role="Handle conversational interactions and general financial queries",
    model=self.llm,
    response_model=ChatResponse,  # Add structured response
    instructions=[
        "Provide conversational responses about finance using conversation context",
        "Structure responses with main content and educational context",
        "Suggest relevant follow-up questions when appropriate",
        "Include confidence scores for complex explanations",
        # ... existing instructions
    ]
)
```

### **Phase 6: Implement Message Tracking**

#### 6.1 Update Workflow Run Method
```python
def run(self, **kwargs: Any) -> Iterator[RunResponse]:
    """Main workflow execution with proper message tracking"""
    
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
    
    self.session_state['messages'].append(user_message)
    
    # Update conversation summary if needed
    self._update_conversation_summary()
    
    # Get conversation context for agents
    conversation_context = self._get_conversation_context()
    
    # Route the request
    category_response = self.router_agent.run(
        f"User request: {message}\n{conversation_context}"
    )
    
    # Track router agent response
    router_message = ConversationMessage(
        role="agent",
        content=category_response.content,
        agent_name="Router Agent",
        structured_data=category_response.dict() if hasattr(category_response, 'dict') else None
    )
    self.session_state['messages'].append(router_message)
    
    # Continue with workflow logic...
    category = category_response.content.strip().lower()
    
    # Execute appropriate flow and track responses
    if category == "report":
        yield from self._run_report_flow(message, conversation_context)
    elif category == "chat":
        yield from self._run_chat_flow(message, conversation_context)
    else:
        yield from self._run_alone_flow(message, category, conversation_context)
```

#### 6.2 Fix Context Retrieval
```python
def _get_conversation_context(self) -> str:
    """Generate conversation context from workflow state"""
    
    # Get current summary
    summary = self.session_state.get('conversation_summary')
    summary_text = summary.summary if summary else "No previous conversation"
    
    # Get recent messages (last 3-5)
    recent_messages = self.session_state.get('messages', [])[-5:]
    recent_context = []
    
    for msg in recent_messages:
        role_prefix = "User" if msg.role == "user" else f"Agent ({msg.agent_name})"
        recent_context.append(f"{role_prefix}: {msg.content}")
    
    context = f"""
Conversation Summary: {summary_text}

Recent Messages:
{chr(10).join(recent_context)}

Companies Previously Discussed: {', '.join(self.session_state.get('companies_discussed', []))}
"""
    
    return context.strip()
```

### **Phase 7: Update UI Layer**

#### 7.1 Handle Structured Responses in Streamlit
```python
def process_user_input(user_input: str) -> Generator[str, None, None]:
    """Process user input and handle structured responses"""
    
    try:
        # Process through workflow
        responses = st.session_state.workflow.run(message=user_input)
        
        for response in responses:
            if hasattr(response, "content"):
                # Check if response contains structured data
                if isinstance(response.content, (FinancialReport, ChatResponse)):
                    # Format structured data for display
                    formatted_content = format_structured_response(response.content)
                    yield formatted_content
                else:
                    # Plain text response
                    yield str(response.content)
            else:
                yield str(response)
                
    except Exception as e:
        yield f"❌ Error processing request: {str(e)}"

def format_structured_response(structured_data) -> str:
    """Format structured Pydantic responses for UI display"""
    
    if isinstance(structured_data, FinancialReport):
        return format_financial_report(structured_data)
    elif isinstance(structured_data, ChatResponse):
        return format_chat_response(structured_data)
    elif isinstance(structured_data, (IncomeStatementData, CompanyFinancialsData, StockPriceData)):
        return format_financial_data(structured_data)
    else:
        return str(structured_data)

def format_financial_report(report: FinancialReport) -> str:
    """Format FinancialReport for markdown display"""
    
    markdown = f"""# Financial Report - {report.symbol}

## Executive Summary
{report.executive_summary or 'Generated from comprehensive financial analysis'}

## Key Insights
{chr(10).join(f'• {insight}' for insight in report.key_insights)}

## Financial Data

### Income Statement
"""
    
    if report.income_statement:
        markdown += f"""
- **Revenue**: ${report.income_statement.revenue:,.0f}
- **Net Income**: ${report.income_statement.net_income:,.0f}
- **EPS**: ${report.income_statement.eps:.2f}
- **Net Margin**: {report.income_statement.net_income_ratio:.1%}
"""
    
    if report.stock_price:
        markdown += f"""
### Stock Price
- **Current Price**: ${report.stock_price.price:.2f}
- **Change**: {report.stock_price.change:+.2f} ({report.stock_price.change_percent:+.2f}%)
- **Market Cap**: ${report.stock_price.market_cap:,.0f}
"""
    
    return markdown
```

#### 7.2 Update Workflow Initialization in Main
```python
def initialize_workflow(settings: Settings, llm, storage) -> FinancialAssistantWorkflow:
    """Initialize workflow with proper session management"""
    
    # Create composite session ID for user isolation
    composite_session_id = f"{st.session_state.user_id}_{st.session_state.session_id}"
    
    return FinancialAssistantWorkflow(
        llm=llm,
        settings=settings,
        storage=storage,
        session_id=composite_session_id  # Use composite ID for storage
    )
```

## Implementation Checklist

### **Phase 1: Models & Schema** ✅
- [ ] Add `ConversationMessage` model to schemas.py
- [ ] Add `WorkflowSummary` model to schemas.py  
- [ ] Add `ChatResponse` model to schemas.py
- [ ] Update imports in workflow file

### **Phase 2: Workflow State Management** ⚠️
- [ ] Update workflow constructor to accept session_id parameter
- [ ] Initialize session_state with proper structure
- [ ] Remove broken `get_session_summary()` method
- [ ] Implement `_get_conversation_context()` method

### **Phase 3: Summary Management** ⚠️
- [ ] Create `SummaryAgent` class
- [ ] Implement `_update_conversation_summary()` method
- [ ] Add summary agent to workflow initialization
- [ ] Test summary generation logic

### **Phase 4: Remove Report Agent** ⚠️
- [ ] Delete `report_generation_agent` initialization
- [ ] Implement `_compose_financial_report()` method
- [ ] Implement `_generate_key_insights()` method
- [ ] Update report flow to use manual composition

### **Phase 5: Fix Agent Models** ⚠️
- [ ] Update `FinancialModelingPrepTools.get_income_statement()` to return `IncomeStatementData`
- [ ] Update `FinancialModelingPrepTools.get_company_financials()` to return `CompanyFinancialsData`
- [ ] Update `FinancialModelingPrepTools.get_stock_price()` to return `StockPriceData`
- [ ] Add `response_model=ChatResponse` to chat agent
- [ ] Remove all markdown formatting from workflow methods

### **Phase 6: Message Tracking** ⚠️
- [ ] Update `run()` method to track user input messages
- [ ] Track all agent responses as `ConversationMessage` objects
- [ ] Update all workflow flow methods (`_run_report_flow`, `_run_alone_flow`, `_run_chat_flow`)
- [ ] Test message persistence across workflow runs

### **Phase 7: UI Updates** ⚠️
- [ ] Update `process_user_input()` to handle structured responses
- [ ] Implement `format_structured_response()` function
- [ ] Implement `format_financial_report()` function
- [ ] Implement `format_chat_response()` function
- [ ] Update workflow initialization to pass session_id
- [ ] Test UI formatting with new structured data

### **Phase 8: Testing & Validation** ❌
- [ ] Test conversation persistence across app restarts
- [ ] Test summary generation with multiple messages
- [ ] Test all three workflow paths (alone, report, chat)
- [ ] Test concurrent user session isolation
- [ ] Validate Pydantic model serialization/deserialization
- [ ] Run full integration tests

## Success Criteria

### **Functional Requirements**
1. ✅ **Session Persistence**: Conversations survive app restarts and continue seamlessly
2. ✅ **Message Tracking**: All user inputs and agent responses stored in workflow state
3. ✅ **Smart Summaries**: Automatic conversation summarization every 5-10 messages
4. ✅ **Structured Data**: All agents return proper Pydantic models instead of markdown
5. ✅ **Clean Architecture**: Clear separation between data processing and presentation

### **Technical Requirements**
1. ✅ **No Agent Memory**: Remove all broken agent-level memory access
2. ✅ **Workflow State**: All conversation data stored in `self.session_state`
3. ✅ **Storage Integration**: Automatic persistence via Agno's SQLite storage
4. ✅ **Type Safety**: Full Pydantic model usage throughout the data flow
5. ✅ **Performance**: Efficient summary generation and data caching

### **User Experience**
1. ✅ **Conversation Continuity**: Users can pick up where they left off
2. ✅ **Context Awareness**: Agents understand conversation history and context
3. ✅ **Rich Display**: Properly formatted financial data and reports
4. ✅ **Error Handling**: Graceful error recovery and user-friendly messages

## Risk Mitigation

### **Data Migration**
- Current users will lose existing conversation history (acceptable for fix)
- New session state structure will start fresh for all users

### **Performance Impact**
- Summary generation may add latency every 5-10 messages
- Mitigate by making summary generation asynchronous where possible

### **Storage Growth**
- Conversation messages will accumulate over time
- Implement cleanup strategy for old conversations if needed

### **Backward Compatibility**
- Some existing session state data may be incompatible
- Implement graceful handling of missing or invalid session data

## Conclusion

This comprehensive plan addresses all identified issues in the Financial Assistant's message and summary management system. The implementation will result in a robust, scalable conversation system that properly leverages Agno's workflow state management capabilities while providing a clean, maintainable architecture.

The key insight is to move from agent-level memory (which doesn't work) to workflow-level state management using Agno's built-in `session_state` persistence, combined with structured Pydantic models for clean data flow and proper separation of concerns between data processing and presentation.