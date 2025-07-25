# Streaming Implementation Plan for Financial Assistant

## Overview
This document outlines the implementation plan for adding streaming functionality to the Financial Assistant application using Agno's streaming capabilities with sync methods.

## Decision: Sync Methods with Streaming Parameters
After analysis, we've decided to implement streaming using the existing sync methods with streaming parameters rather than converting to async. This approach:
- Avoids previous Agno framework conflicts with dual sync/async methods
- Maintains backward compatibility
- Leverages Agno's built-in streaming support in `run()` method
- Simplifies implementation and maintenance

## Objective
Enable real-time streaming of agent responses with optional intermediate step visibility, improving user experience through faster perceived response times and transparency into agent reasoning.

## Key Benefits
- **Faster Time-to-First-Byte**: Users see responses immediately as they're generated
- **Better UX for Long Responses**: Especially beneficial for comprehensive financial reports
- **Transparency**: Optional visibility into agent reasoning process
- **Backward Compatible**: No breaking changes to existing code

## Implementation Tasks

### Phase 1: Infrastructure Setup ✅
- [x] Research Agno streaming capabilities (stream parameter in both run/arun)
- [x] Design streaming architecture using sync methods with parameters
- [x] Add streaming toggle checkbox to Streamlit sidebar
- [x] Add intermediate steps toggle (conditional on streaming being enabled)

### Phase 2: Workflow Streaming Implementation ✅
- [x] Add streaming parameters to workflow initialization
- [x] Create `_process_streaming_event()` method to handle RunResponseEvent objects
- [x] Update existing `run()` method to handle streaming mode
- [x] Keep existing sync flow methods (`_run_report_flow`, `_run_alone_flow`, `_run_chat_flow`)
- [x] Handle both iterator (streaming) and single response (non-streaming) returns

### Phase 3: Agent Streaming Integration ✅
- [x] Update router agent calls to include streaming parameters
- [x] Update symbol extraction agent calls with streaming support
- [x] Update chat agent calls for streaming responses
- [x] Update summary agent calls for streaming (if applicable)
- [x] Handle RunResponseEvent iteration in workflow methods

### Phase 4: UI Streaming Support ✅
- [x] Update `process_user_input()` to handle streaming iterators
- [x] Implement proper streaming display in Streamlit
- [x] Add error handling for partial/interrupted streams
- [x] Pass streaming settings from UI to workflow initialization
- [x] Auto-reinitialize workflow when streaming settings change

### Phase 5: Testing & Optimization 🧪
- [x] Test basic app startup and workflow creation with streaming
- [ ] Test streaming with single information queries
- [ ] Test streaming with comprehensive reports
- [ ] Test streaming with chat interactions
- [ ] Test intermediate steps visibility
- [ ] Optimize token usage with streaming
- [ ] Performance benchmarking (streaming vs non-streaming)

### Phase 6: Error Handling & Edge Cases ✅
- [x] Handle network interruptions during streaming
- [x] Implement graceful degradation to non-streaming mode
- [x] Handle partial responses on errors
- [x] Add timeout handling for long-running streams
- [x] Ensure session state consistency with streaming

## Technical Implementation Details

### 1. Workflow Changes (`financial_assistant.py`)

```python
# Add to __init__
def __init__(self, ..., stream: bool = False, stream_intermediate_steps: bool = False):
    self.stream = stream
    self.stream_intermediate_steps = stream_intermediate_steps

# Update existing run method
def run(self, **kwargs: Any) -> Iterator[RunResponse]:
    message = kwargs.get("message", "")
    
    # Use run with streaming parameters
    response = self.router_agent.run(
        message, 
        stream=self.stream,
        stream_intermediate_steps=self.stream_intermediate_steps
    )
    
    if self.stream:
        # Handle streaming response (iterator of RunResponseEvent)
        for event in response:
            yield self._process_streaming_event(event)
    else:
        # Handle non-streaming response (single RunResponse)
        yield RunResponse(content=response.content)
```

### 2. Streamlit UI Changes (`main.py`)

```python
# Update workflow initialization with streaming settings
workflow = FinancialAssistantWorkflow(
    llm=llm_model,
    settings=settings,
    storage=storage,
    session_id=composite_session_id,
    stream=st.session_state.get("streaming_enabled", False),
    stream_intermediate_steps=st.session_state.get("stream_intermediate_steps", False)
)

# Keep process_user_input as sync but handle streaming
def process_user_input(user_input: str) -> Generator[str, None, None]:
    responses = st.session_state.workflow.run(message=user_input)
    
    for response in responses:
        if hasattr(response, "content") and response.content:
            yield str(response.content)
        else:
            yield str(response)
```

### 3. Simplified Content Extraction

```python
def _extract_content_from_chunk(self, chunk) -> Optional[str]:
    """Extract content from streaming chunk (simplified based on Agno examples)"""
    # Based on Agno examples, chunks have direct content access
    if hasattr(chunk, 'content') and chunk.content:
        return str(chunk.content)
    
    # If intermediate steps enabled, show what we can
    if self.stream_intermediate_steps:
        return f"📊 {str(chunk)}"
    
    return None

# Simple streaming pattern following Agno examples:
for chunk in response:
    content = self._extract_content_from_chunk(chunk)
    if content:
        yield RunResponse(run_id=self.run_id, content=content)
```

## Considerations

### Performance
- Streaming may slightly increase token usage due to intermediate steps
- Network latency becomes more critical with streaming
- Consider implementing response caching for repeated queries

### User Experience
- Clear visual indicators for streaming vs complete responses
- Smooth UI updates without flickering
- Ability to stop/interrupt long generations
- Progress indicators for multi-step workflows

### Error Handling
- Graceful handling of partial responses
- Clear error messages for streaming failures
- Automatic fallback to non-streaming mode on errors
- Session state recovery after interruptions

## Success Criteria
1. ✅ Streaming toggle works correctly in UI
2. ⏳ All agent responses can be streamed when enabled
3. ⏳ Intermediate steps are visible when enabled
4. ⏳ No performance degradation vs non-streaming mode
5. ⏳ Error handling works gracefully
6. ⏳ UI remains responsive during streaming

## Notes
- Using sync methods with streaming parameters to avoid Agno framework conflicts
- Agno's `run()` method natively supports streaming with `stream=True` parameter
- RunResponseEvent objects are returned when streaming is enabled
- The approach maintains backward compatibility while adding streaming capabilities
- No need for async/await complexity in the main workflow

## References
- [Agno Agent Streaming Documentation](https://docs.agno.com/reference/agents/agent)
- [Agno Async Examples](https://docs.agno.com/examples/introduction)
- Current Implementation: `/home/yoda/Library/Projects/Portfolio/Agno/financial-assistant/`