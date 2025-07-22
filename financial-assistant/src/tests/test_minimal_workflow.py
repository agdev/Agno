"""
Test minimal version of FinancialAssistantWorkflow to isolate async_generator issue

This test helped identify that dual sync/async methods cause Agno to return None.
Used for debugging Agno framework compatibility issues.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import os
from typing import Iterator

from agno.agent import Agent
from agno.models.anthropic import Claude
from agno.run.response import RunResponse
from agno.storage.sqlite import SqliteStorage
from agno.workflow import Workflow
from dotenv import load_dotenv

env_path = os.path.join(os.path.dirname(__file__), "..", "..", "env", ".env")
load_dotenv(env_path)

print("Testing minimal FinancialAssistantWorkflow components...")

# Test 1: Basic workflow with storage like our class
print("Test 1: Workflow with storage and agents like FinancialAssistantWorkflow")


class MinimalFinancialWorkflow(Workflow):
    def __init__(self):
        super().__init__()

        # Initialize storage (like our workflow)
        self.storage = SqliteStorage(
            table_name="financial_assistant_sessions", db_file="tmp/test_minimal.db"
        )

        # Initialize LLM
        self.llm = Claude(id="claude-sonnet-4-20250514")

        # Initialize one agent (like our workflow)
        self.chat_agent = Agent(
            name="Chat Agent",
            role="Handle conversational interactions",
            model=self.llm,
        )

    def run(self, **kwargs) -> Iterator[RunResponse]:
        message = kwargs.get("message", "test")
        yield RunResponse(run_id=self.run_id, content=f"Response to: {message}")


try:
    w = MinimalFinancialWorkflow()
    r = w.run(message="hello")
    print(f"✓ MinimalFinancialWorkflow works, type: {type(r)}")
    result = list(r)  # Consume the iterator
    print(f"✓ Result: {result[0].content}")
except Exception as e:
    print(f"✗ MinimalFinancialWorkflow failed: {e}")
    import traceback

    traceback.print_exc()

# Test 2: Add async method to see if that causes the issue
print("\nTest 2: Same workflow but with async method added")


class MinimalWithAsync(Workflow):
    def __init__(self):
        super().__init__()

        # Initialize storage (like our workflow)
        self.storage = SqliteStorage(
            table_name="financial_assistant_sessions", db_file="tmp/test_minimal2.db"
        )

        # Initialize LLM
        self.llm = Claude(id="claude-sonnet-4-20250514")

        # Initialize one agent (like our workflow)
        self.chat_agent = Agent(
            name="Chat Agent",
            role="Handle conversational interactions",
            model=self.llm,
        )

    def run(self, **kwargs) -> Iterator[RunResponse]:
        message = kwargs.get("message", "test")
        yield RunResponse(run_id=self.run_id, content=f"Response to: {message}")

    async def arun(self, **kwargs):
        """Async version - just having this might cause the issue"""
        message = kwargs.get("message", "test")
        yield RunResponse(run_id=self.run_id, content=f"Async response to: {message}")


try:
    w = MinimalWithAsync()
    r = w.run(message="hello")
    print(f"✓ MinimalWithAsync works, type: {type(r)}")
    result = list(r)  # Consume the iterator
    print(f"✓ Result: {result[0].content}")
except Exception as e:
    print(f"✗ MinimalWithAsync failed: {e}")
    import traceback

    traceback.print_exc()

print("Testing complete!")
