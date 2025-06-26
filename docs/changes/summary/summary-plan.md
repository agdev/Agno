# Agno Session Summaries & Context Integration Plan

## **Project Overview**

This implementation adds session summary management and chat storage to the Financial Assistant application using Agno's built-in memory features. The goal is to provide conversation context to agents for better performance while maintaining chat history.

## **Key Requirements**

✅ **Session Summaries** - Automatic conversation summarization using Agno's SessionSummarizer  
✅ **Raw Chat Storage** - Complete message history persistence with SqliteStorage  
❌ **User Memories** - NOT needed (explicitly excluded)  
✅ **Context Integration** - Pass summaries to Router and Symbol Extraction agents  

## **Architecture Changes**

### **Core Components**

1. **SqliteStorage** - Persistent chat message storage
2. **SessionSummarizer** - Automatic conversation summarization
3. **Context-Aware Agents** - Router and Symbol Extraction with summary context
4. **Session Management** - UI for session control and conversation export

### **Agent Context Integration**

#### **Router Agent Enhancement**
- Receives conversation summary for better request categorization
- Distinguishes between new topics vs follow-up questions
- Context-aware routing based on conversation history

#### **Symbol Extraction Agent Enhancement**  
- Uses conversation context for symbol disambiguation
- Resolves pronouns and ambiguous references ("it", "that company")
- Prioritizes recently mentioned symbols from conversation history

## **Implementation Phases**

### **Phase 1: Core Infrastructure**

1. **Update FinancialAssistantWorkflow**
   - Add SqliteStorage for chat persistence
   - Enable `enable_session_summaries=True`
   - Configure SessionSummarizer with Claude model
   - Add session summary retrieval methods
   - Enable chat history: `add_history_to_messages=True`

2. **Update Settings Configuration**
   - Add storage configuration options
   - Database file paths and settings
   - Session management parameters

3. **Update Main.py Integration**
   - Generate/manage user_id and session_id in Streamlit session state
   - Pass storage instance to workflow
   - Initialize session management

### **Phase 2: Context-Aware Agent Enhancement**

1. **Router Agent with Summary Context**
   ```python
   category_response = self.router_agent.run(
       f"User request: {message}\n"
       f"Conversation context: {conversation_summary}\n"
       f"Previous topics: [extracted themes]"
   )
   ```

2. **Symbol Extraction Agent with Summary Context**
   ```python
   symbol_response = self.symbol_extraction_agent.run(
       f"Extract symbol from: {message}\n"
       f"Conversation context: {conversation_summary}\n"
       f"Previously mentioned symbols: [extracted symbols]"
   )
   ```

3. **Updated Workflow Logic**
   - Retrieve conversation summary before agent calls
   - Pass context to relevant agents
   - Update session summary after interactions

### **Phase 3: Session Management & UI**

1. **Session Summary Integration**
   - Implement `get_session_summary()` method
   - Store/update conversation summary in session state
   - Display real-time summary in UI

2. **Session Management UI**
   - Session selector dropdown in sidebar
   - New session / Continue session buttons
   - Session metadata display (creation time, message count)

3. **Chat History Features**
   - Conversation export (markdown/JSON)
   - Session organization and management
   - Clear session functionality

## **Technical Implementation Details**

### **Storage Configuration**
```python
storage = SqliteStorage(
    table_name="agent_sessions",
    db_file="tmp/financial_assistant_sessions.db"
)
```

### **Workflow Configuration**
```python
workflow = FinancialAssistantWorkflow(
    llm=llm,
    storage=storage,
    enable_session_summaries=True,  # YES
    enable_user_memories=False,     # NO
    add_history_to_messages=True,
    num_history_responses=3
)
```

### **Session State Management**
- `st.session_state.user_id` - Persistent user identification
- `st.session_state.session_id` - Current conversation session
- `st.session_state.conversation_summary` - Live summary updates
- `st.session_state.available_sessions` - Session history

## **Expected Benefits**

1. **Better Request Routing** - Context-aware categorization using conversation history
2. **Smart Symbol Extraction** - Resolve ambiguous references and pronouns
3. **Session Continuity** - Maintain conversation flow across app restarts
4. **Professional UX** - Session management and conversation export
5. **Performance Improvement** - Agents have relevant context for better responses
6. **Scalable Architecture** - Support multiple conversation threads

## **Files to Modify**

1. **`src/workflow/financial_assistant.py`** - Core workflow enhancements
2. **`src/main.py`** - Streamlit UI and session management  
3. **`src/config/settings.py`** - Add storage configuration options
4. **Documentation** - This plan and progress tracking

## **Success Criteria**

- [ ] Conversation summaries automatically generated and stored
- [ ] Router agent uses context for better categorization
- [ ] Symbol extraction resolves ambiguous references using context
- [ ] Chat history persists across app restarts
- [ ] Session management UI works smoothly
- [ ] Conversation export functionality
- [ ] No user memory features (confirmed exclusion)
- [ ] All existing functionality preserved

## **Risk Mitigation**

1. **Backwards Compatibility** - Ensure existing workflows continue working
2. **Performance** - Monitor summary generation overhead
3. **Storage Management** - Implement cleanup for old sessions
4. **Error Handling** - Graceful degradation when summaries unavailable
5. **Testing** - Verify context integration doesn't break agent functionality