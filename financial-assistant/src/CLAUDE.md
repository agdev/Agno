# Agno Framework Async Implementation Rules

## Overview

This document provides comprehensive guidelines for implementing async patterns in Agno workflows and agents, based on official framework documentation and best practices. These rules ensure consistent, efficient, and maintainable async code.

## Core Principles

### 1. Dual Method Pattern

Every Agno workflow should support both synchronous and asynchronous execution:

```python
class MyWorkflow(Workflow):
    # Synchronous version
    def run(self, **kwargs) -> Iterator[RunResponse]:
        """Synchronous workflow execution"""
        pass
    
    # Asynchronous version
    async def arun(self, **kwargs) -> AsyncIterator[RunResponse]:
        """Asynchronous workflow execution"""
        pass
```

### 2. Consistent Return Types

- **Sync methods**: `Iterator[RunResponse]`
- **Async methods**: `AsyncIterator[RunResponse]`
- **Always use `RunResponse`** - never `RunResponseContentEvent`

### 3. Agent Call Patterns

Match workflow type with agent call type:

```python
# In sync methods
response = self.agent.run(message)
yield from self.agent.run(message, stream=True)

# In async methods  
response = await self.agent.arun(message)
async for resp in self.agent.arun(message, stream=True):
    yield resp
```

## Mandatory Rules

### ❌ NEVER DO

#### 1. Mixed Sync/Async Anti-Pattern

```python
# WRONG - Never call async methods from sync context
def run(self, **kwargs) -> Iterator[RunResponse]:
    async_result = asyncio.run(self._async_method())  # ❌ WRONG
    return async_result
```

#### 2. Wrong Return Types

```python
# WRONG - Don't use RunResponseContentEvent
async def arun(self, **kwargs) -> AsyncIterator[RunResponseContentEvent]:  # ❌ WRONG
    yield RunResponseContentEvent(content="test")  # ❌ WRONG
```

#### 3. Collecting Async Responses

```python
# WRONG - Defeats streaming purpose
async def collect_responses(self, async_iter):
    responses = []
    async for response in async_iter:
        responses.append(response)  # ❌ WRONG
    return responses
```

#### 4. Mixing Agent Call Types

```python
# WRONG - Don't mix sync and async agent calls
def run(self, **kwargs) -> Iterator[RunResponse]:
    result = asyncio.run(self.agent.arun(message))  # ❌ WRONG
    return result
```

### ✅ ALWAYS DO

#### 1. Proper Sync Implementation

```python
def run(self, **kwargs) -> Iterator[RunResponse]:
    # Use sync agent calls
    response = self.agent.run(message)
    
    # Stream responses properly
    yield from self.agent.run(message, stream=True)
    
    # Create proper RunResponse objects
    yield RunResponse(
        run_id=self.run_id,
        content=response.content,
        event=RunEvent.workflow_completed
    )
```

#### 2. Proper Async Implementation

```python
async def arun(self, **kwargs) -> AsyncIterator[RunResponse]:
    # Use async agent calls
    response = await self.agent.arun(message)
    
    # Stream responses properly
    async for resp in self.agent.arun(message, stream=True):
        yield resp
    
    # Create proper RunResponse objects
    yield RunResponse(
        run_id=self.run_id,
        content=response.content,
        event=RunEvent.workflow_completed
    )
```

#### 3. Parallel Execution Patterns (2024 Best Practices)

```python
import asyncio
from concurrent.futures import ThreadPoolExecutor

# BEST: Async parallel execution using TaskGroup (Python 3.11+)
async def arun(self, **kwargs) -> AsyncIterator[RunResponse]:
    # Use asyncio.TaskGroup for structured concurrency (2024 recommendation)
    async with asyncio.TaskGroup() as tg:
        task1 = tg.create_task(self.tool.async_method(arg1))
        task2 = tg.create_task(self.tool.async_method(arg2))
        task3 = tg.create_task(self.tool.async_method(arg3))
    
    # Tasks are automatically awaited when exiting context
    results = [task1.result(), task2.result(), task3.result()]

# ALTERNATIVE: asyncio.gather() for simple cases
async def arun(self, **kwargs) -> AsyncIterator[RunResponse]:
    # Use asyncio.gather() for pure async operations (still valid)
    results = await asyncio.gather(
        self.tool.async_method(arg1),
        self.tool.async_method(arg2),
        return_exceptions=True
    )

# SYNC-TO-ASYNC BRIDGE: Running async code from sync methods
def run(self, **kwargs) -> Iterator[RunResponse]:
    # Modern approach: Use asyncio.run() with TaskGroup
    async def _async_parallel():
        async with asyncio.TaskGroup() as tg:
            task1 = tg.create_task(self.tool.async_method(arg1))
            task2 = tg.create_task(self.tool.async_method(arg2))
        return [task1.result(), task2.result()]
    
    results = asyncio.run(_async_parallel())

# LEGACY: ThreadPoolExecutor (only for blocking operations)
def run(self, **kwargs) -> Iterator[RunResponse]:
    # Use only when you must work with purely blocking/sync tools
    with ThreadPoolExecutor() as executor:
        futures = [executor.submit(self.sync_tool.method, arg) for arg in args]
        results = [f.result() for f in futures]
```

### 4. Parallel Execution Decision Framework (2024)

**When choosing parallel execution approach:**

```python
# 1. BEST: TaskGroup for structured concurrency (Python 3.11+)
async def arun(self, **kwargs) -> AsyncIterator[RunResponse]:
    # Recommended for all new async code
    async with asyncio.TaskGroup() as tg:
        task1 = tg.create_task(self.async_tool.method(arg1))
        task2 = tg.create_task(self.async_tool.method(arg2))
        task3 = tg.create_task(self.async_tool.method(arg3))
    
    # Automatic task management and exception handling
    results = [task1.result(), task2.result(), task3.result()]

# 2. ALTERNATIVE: asyncio.gather() for simple cases
async def arun(self, **kwargs) -> AsyncIterator[RunResponse]:
    # Still valid for simple concurrent operations
    results = await asyncio.gather(
        self.async_tool.method(arg1),
        self.async_tool.method(arg2),
        return_exceptions=True
    )

# 3. SYNC-TO-ASYNC: Using asyncio.run() with TaskGroup
def run(self, **kwargs) -> Iterator[RunResponse]:
    # Modern approach for running async code from sync methods
    async def _concurrent_work():
        async with asyncio.TaskGroup() as tg:
            tasks = [tg.create_task(self.async_tool.method(arg)) for arg in args]
        return [task.result() for task in tasks]
    
    results = asyncio.run(_concurrent_work())

# 4. BLOCKING-TO-ASYNC: Using asyncio.to_thread() (Python 3.9+)
async def arun(self, **kwargs) -> AsyncIterator[RunResponse]:
    # For calling blocking functions from async context
    result = await asyncio.to_thread(self.blocking_tool.method, arg)

# 5. LEGACY: ThreadPoolExecutor (only for legacy/blocking operations)
def run(self, **kwargs) -> Iterator[RunResponse]:
    # Use only when you must work with purely blocking tools
    with ThreadPoolExecutor() as executor:
        futures = [executor.submit(self.blocking_tool.method, arg) for arg in args]
        results = [f.result() for f in futures]
```

**Performance Hierarchy (Best to Worst for I/O-bound tasks):**

1. **asyncio.TaskGroup**: Best performance, structured concurrency, automatic error handling
2. **asyncio.gather()**: Good performance, simpler than TaskGroup for basic cases
3. **asyncio.to_thread()**: Good for mixing blocking code with async
4. **asyncio.run() + TaskGroup**: Modern approach for sync-to-async bridges
5. **ThreadPoolExecutor**: Legacy option, higher memory usage, lower performance

**Decision Guidelines:**

- **Use TaskGroup** for new async code with multiple concurrent operations
- **Use asyncio.gather()** for simple concurrent operations without complex error handling
- **Use asyncio.to_thread()** for occasional blocking operations within async code
- **Use asyncio.run() + TaskGroup** for running async code from sync methods
- **Use ThreadPoolExecutor** only for legacy code or when async is not available

**Performance Notes (Python 3.12+):**

- **TaskGroup**: 2-5x faster than ThreadPoolExecutor for I/O-bound tasks
- **asyncio**: ~75% performance improvement in Python 3.12
- **Memory usage**: asyncio uses ~32KB per task vs ~8MB per thread
- **Concurrency**: asyncio handles 1000+ concurrent operations efficiently

## Modern Async Patterns (Python 3.11+)

### 1. TaskGroup Structured Concurrency

TaskGroup provides structured concurrency with automatic task management and exception handling:

```python
import asyncio
from typing import List, Dict, Any

class FinancialDataWorkflow(Workflow):
    """Example using TaskGroup for parallel financial data fetching"""
    
    async def arun(self, **kwargs) -> AsyncIterator[RunResponse]:
        symbol = kwargs.get("symbol", "AAPL")
        
        # TaskGroup ensures all tasks complete or all are cancelled
        async with asyncio.TaskGroup() as tg:
            # Create tasks for parallel execution
            income_task = tg.create_task(
                self.fmp_tools.get_income_statement(symbol)
            )
            financials_task = tg.create_task(
                self.fmp_tools.get_company_financials(symbol)
            )
            price_task = tg.create_task(
                self.fmp_tools.get_stock_price(symbol)
            )
        
        # Tasks are automatically awaited when exiting context
        financial_data = {
            'income': income_task.result(),
            'financials': financials_task.result(),
            'price': price_task.result()
        }
        
        # Generate report from combined data
        report = await self.report_agent.arun(financial_data)
        
        yield RunResponse(
            run_id=self.run_id,
            content=report.content,
            event=RunEvent.workflow_completed
        )

    def run(self, **kwargs) -> Iterator[RunResponse]:
        """Sync version using asyncio.run() with TaskGroup"""
        symbol = kwargs.get("symbol", "AAPL")
        
        async def _fetch_data():
            async with asyncio.TaskGroup() as tg:
                income_task = tg.create_task(
                    self.fmp_tools.get_income_statement(symbol)
                )
                financials_task = tg.create_task(
                    self.fmp_tools.get_company_financials(symbol)
                )
                price_task = tg.create_task(
                    self.fmp_tools.get_stock_price(symbol)
                )
            
            return {
                'income': income_task.result(),
                'financials': financials_task.result(),
                'price': price_task.result()
            }
        
        # Run async code from sync context
        financial_data = asyncio.run(_fetch_data())
        
        # Generate report using sync agent call
        report = self.report_agent.run(financial_data)
        
        yield RunResponse(
            run_id=self.run_id,
            content=report.content,
            event=RunEvent.workflow_completed
        )
```

### 2. Exception Handling with TaskGroup

TaskGroup automatically cancels remaining tasks when one fails:

```python
async def arun_with_error_handling(self, **kwargs) -> AsyncIterator[RunResponse]:
    symbols = kwargs.get("symbols", ["AAPL", "GOOGL", "MSFT"])
    
    try:
        async with asyncio.TaskGroup() as tg:
            tasks = [
                tg.create_task(self.fmp_tools.get_stock_price(symbol))
                for symbol in symbols
            ]
        
        # All tasks completed successfully
        results = {symbol: task.result() for symbol, task in zip(symbols, tasks)}
        
        yield RunResponse(
            run_id=self.run_id,
            content=f"Successfully fetched data for {len(results)} symbols",
            event=RunEvent.workflow_completed
        )
        
    except* Exception as eg:
        # Handle exception groups from failed tasks
        for exc in eg.exceptions:
            yield RunResponse(
                run_id=self.run_id,
                content=f"Error occurred: {str(exc)}",
                event=RunEvent.workflow_failed
            )
```

### 3. Mixing Blocking and Async Code

Use `asyncio.to_thread()` for blocking operations within async contexts:

```python
async def arun_mixed_operations(self, **kwargs) -> AsyncIterator[RunResponse]:
    symbol = kwargs.get("symbol", "AAPL")
    
    async with asyncio.TaskGroup() as tg:
        # Async operations
        price_task = tg.create_task(
            self.fmp_tools.get_stock_price(symbol)
        )
        
        # Blocking operation run in thread
        blocking_task = tg.create_task(
            asyncio.to_thread(self.legacy_tool.blocking_method, symbol)
        )
    
    # Both async and blocking operations completed
    results = {
        'price': price_task.result(),
        'legacy_data': blocking_task.result()
    }
    
    yield RunResponse(
        run_id=self.run_id,
        content=str(results),
        event=RunEvent.workflow_completed
    )
```

## Implementation Guidelines

### 1. Workflow Structure

```python
from typing import Iterator, AsyncIterator, Any
from agno.workflow import Workflow, RunResponse, RunEvent
from agno.agent import Agent

class MyWorkflow(Workflow):
    """Example workflow with proper async patterns"""
    
    # Agent definitions
    agent1: Agent = Agent(...)
    agent2: Agent = Agent(...)
    
    def run(self, **kwargs: Any) -> Iterator[RunResponse]:
        """Synchronous workflow execution"""
        message = kwargs.get("message", "")
        
        # Sync agent calls
        response1 = self.agent1.run(message)
        response2 = self.agent2.run(response1.content)
        
        # Yield final response
        yield RunResponse(
            run_id=self.run_id,
            content=response2.content,
            event=RunEvent.workflow_completed
        )
    
    async def arun(self, **kwargs: Any) -> AsyncIterator[RunResponse]:
        """Asynchronous workflow execution"""
        message = kwargs.get("message", "")
        
        # Async agent calls
        response1 = await self.agent1.arun(message)
        response2 = await self.agent2.arun(response1.content)
        
        # Yield final response
        yield RunResponse(
            run_id=self.run_id,
            content=response2.content,
            event=RunEvent.workflow_completed
        )
```

### 2. Subflow Patterns

```python
class MyWorkflow(Workflow):
    # Sync subflows
    def _process_data(self, data: str) -> Iterator[RunResponse]:
        """Sync subflow processing"""
        result = self.agent.run(data)
        yield RunResponse(
            run_id=self.run_id,
            content=result.content,
            event=RunEvent.workflow_running
        )
    
    # Async subflows
    async def _aprocess_data(self, data: str) -> AsyncIterator[RunResponse]:
        """Async subflow processing"""
        result = await self.agent.arun(data)
        yield RunResponse(
            run_id=self.run_id,
            content=result.content,
            event=RunEvent.workflow_running
        )
```

### 3. Error Handling

```python
# Sync error handling
def run(self, **kwargs) -> Iterator[RunResponse]:
    try:
        response = self.agent.run(message)
        yield RunResponse(
            run_id=self.run_id,
            content=response.content,
            event=RunEvent.workflow_completed
        )
    except Exception as e:
        yield RunResponse(
            run_id=self.run_id,
            content=f"Error: {str(e)}",
            event=RunEvent.workflow_failed
        )

# Async error handling
async def arun(self, **kwargs) -> AsyncIterator[RunResponse]:
    try:
        response = await self.agent.arun(message)
        yield RunResponse(
            run_id=self.run_id,
            content=response.content,
            event=RunEvent.workflow_completed
        )
    except Exception as e:
        yield RunResponse(
            run_id=self.run_id,
            content=f"Error: {str(e)}",
            event=RunEvent.workflow_failed
        )
```

### 4. Tool Integration

```python
# Sync tool usage
def run(self, **kwargs) -> Iterator[RunResponse]:
    # Direct sync tool calls
    result = self.tool.sync_method(param)
    
    # Or with agent
    response = self.agent.run(message)  # Agent uses tools sync
    
    yield RunResponse(
        run_id=self.run_id,
        content=result,
        event=RunEvent.workflow_completed
    )

# Async tool usage
async def arun(self, **kwargs) -> AsyncIterator[RunResponse]:
    # Direct async tool calls
    result = await self.tool.async_method(param)
    
    # Or with agent
    response = await self.agent.arun(message)  # Agent uses tools async
    
    yield RunResponse(
        run_id=self.run_id,
        content=result,
        event=RunEvent.workflow_completed
    )
```

## Performance Best Practices

### 1. Streaming Optimization

```python
# Efficient streaming
async def arun(self, **kwargs) -> AsyncIterator[RunResponse]:
    async for chunk in self.agent.arun(message, stream=True):
        # Yield immediately for best UX
        yield chunk
```

### 2. Memory Management

```python
# Avoid collecting all responses
async def arun(self, **kwargs) -> AsyncIterator[RunResponse]:
    # Good - stream directly
    async for response in self.agent.arun(message, stream=True):
        yield response
    
    # Bad - collects all in memory
    responses = []
    async for response in self.agent.arun(message, stream=True):
        responses.append(response)  # ❌ Avoid this
    
    for response in responses:
        yield response
```

### 3. Parallel Processing

```python
# BEST: TaskGroup for structured concurrency (Python 3.11+)
async def arun(self, **kwargs) -> AsyncIterator[RunResponse]:
    try:
        async with asyncio.TaskGroup() as tg:
            task1 = tg.create_task(self.tool1.async_method(param1))
            task2 = tg.create_task(self.tool2.async_method(param2))
            task3 = tg.create_task(self.tool3.async_method(param3))
        
        # All tasks completed successfully
        results = [task1.result(), task2.result(), task3.result()]
        
        for result in results:
            yield RunResponse(
                run_id=self.run_id,
                content=result,
                event=RunEvent.workflow_running
            )
            
    except* Exception as eg:
        # Handle exception groups from failed tasks
        for exc in eg.exceptions:
            yield RunResponse(
                run_id=self.run_id,
                content=f"Error: {str(exc)}",
                event=RunEvent.workflow_failed
            )

# ALTERNATIVE: asyncio.gather() for simple cases
async def arun(self, **kwargs) -> AsyncIterator[RunResponse]:
    # Gather results efficiently
    results = await asyncio.gather(
        self.tool1.async_method(param1),
        self.tool2.async_method(param2),
        self.tool3.async_method(param3),
        return_exceptions=True  # Handle exceptions gracefully
    )
    
    # Process results
    for result in results:
        if isinstance(result, Exception):
            yield RunResponse(
                run_id=self.run_id,
                content=f"Error: {str(result)}",
                event=RunEvent.workflow_failed
            )
        else:
            yield RunResponse(
                run_id=self.run_id,
                content=result,
                event=RunEvent.workflow_running
            )
```

## Type Annotations

### Required Imports

```python
from typing import Iterator, AsyncIterator, Any, Optional
from agno.workflow import Workflow, RunResponse, RunEvent
from agno.agent import Agent
```

### Method Signatures

```python
# Sync methods
def run(self, **kwargs: Any) -> Iterator[RunResponse]:
    pass

def _subflow_method(self, param: str) -> Iterator[RunResponse]:
    pass

# Async methods
async def arun(self, **kwargs: Any) -> AsyncIterator[RunResponse]:
    pass

async def _async_subflow_method(self, param: str) -> AsyncIterator[RunResponse]:
    pass
```

## Testing Guidelines

### 1. Type Checking

```bash
# Always run pyright after changes
pyright src/
```

### 2. Functional Testing

```python
# Test both sync and async produce same results
def test_workflow_consistency():
    workflow = MyWorkflow()
    
    # Test sync
    sync_results = list(workflow.run(message="test"))
    
    # Test async  
    async_results = []
    async for result in workflow.arun(message="test"):
        async_results.append(result)
    
    # Compare results
    assert len(sync_results) == len(async_results)
    assert sync_results[0].content == async_results[0].content
```

## Common Pitfalls and Solutions

### 1. Mixing Sync/Async

**Problem**: Calling async methods from sync context
**Solution**: Implement separate sync and async code paths

### 2. Wrong Return Types

**Problem**: Using `RunResponseContentEvent` instead of `RunResponse`
**Solution**: Always use `RunResponse` with proper event types

### 3. Inefficient Streaming

**Problem**: Collecting all responses before yielding
**Solution**: Yield responses immediately as they arrive

### 4. Type Errors

**Problem**: Incorrect type annotations
**Solution**: Use proper typing imports and run pyright regularly

## Migration Checklist

When converting existing workflows to proper async patterns:

- [ ] Separate sync and async method implementations
- [ ] Update all return type annotations
- [ ] Replace `RunResponseContentEvent` with `RunResponse`
- [ ] Remove `asyncio.run()` calls from sync methods
- [ ] Remove response collection helpers
- [ ] Update agent call patterns
- [ ] **Replace `asyncio.gather()` with `asyncio.TaskGroup` for new code**
- [ ] **Update parallel execution to use TaskGroup structured concurrency**
- [ ] **Use `asyncio.to_thread()` for blocking operations in async contexts**
- [ ] **Implement proper exception handling with `except*` syntax**
- [ ] Add proper error handling
- [ ] Test both sync and async functionality
- [ ] Run pyright type checking
- [ ] Benchmark performance with Python 3.12+ optimizations

## Conclusion

Following these rules ensures:

- **Type Safety**: Proper type annotations and no type errors
- **Performance**: Efficient streaming and parallel execution
- **Maintainability**: Clear, consistent patterns
- **Compatibility**: Works with Agno framework expectations
- **Flexibility**: Both sync and async execution paths available

Always prioritize clarity, performance, and consistency when implementing async patterns in Agno workflows.
