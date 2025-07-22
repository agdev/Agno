"""
Test script to identify which component creates async_generator during initialization
"""

import os
from typing import Iterator

from agno.run.response import RunResponse
from agno.workflow import Workflow
from agno.agent import Agent
from agno.models.anthropic import Claude
from agno.storage.sqlite import SqliteStorage

# Load environment variables
from dotenv import load_dotenv
import os
env_path = os.path.join(os.path.dirname(__file__), '..', '..', 'env', '.env')
load_dotenv(env_path)

print("Testing workflow components to find async_generator source...\n")

# Test 1: Empty workflow
print("Test 1: Empty workflow")
class EmptyWorkflow(Workflow):
    def run(self, **kwargs) -> Iterator[RunResponse]:
        yield RunResponse(run_id=self.run_id, content="test")

try:
    w = EmptyWorkflow()
    r = w.run(message="test")
    print("✓ Empty workflow works\n")
except Exception as e:
    print(f"✗ Empty workflow failed: {e}\n")

# Test 2: Workflow with storage
print("Test 2: Workflow with SqliteStorage")
class WorkflowWithStorage(Workflow):
    def __init__(self):
        super().__init__()
        self.storage = SqliteStorage(
            table_name="test_table",
            db_file="test.db"
        )
    
    def run(self, **kwargs) -> Iterator[RunResponse]:
        yield RunResponse(run_id=self.run_id, content="test")

try:
    w = WorkflowWithStorage()
    r = w.run(message="test")
    print("✓ Workflow with storage works\n")
except Exception as e:
    print(f"✗ Workflow with storage failed: {e}\n")

# Test 3: Workflow with simple agent (no response model)
print("Test 3: Workflow with simple agent")
class WorkflowWithSimpleAgent(Workflow):
    def __init__(self):
        super().__init__()
        self.agent = Agent(
            name="Test Agent",
            role="Test role"
        )
    
    def run(self, **kwargs) -> Iterator[RunResponse]:
        yield RunResponse(run_id=self.run_id, content="test")

try:
    w = WorkflowWithSimpleAgent()
    r = w.run(message="test")
    print("✓ Workflow with simple agent works\n")
except Exception as e:
    print(f"✗ Workflow with simple agent failed: {e}\n")

# Test 4: Workflow with agent using Claude model
print("Test 4: Workflow with agent using Claude model")
class WorkflowWithClaudeAgent(Workflow):
    def __init__(self):
        super().__init__()
        self.agent = Agent(
            name="Test Agent",
            role="Test role",
            model=Claude(id="claude-sonnet-4-20250514")
        )
    
    def run(self, **kwargs) -> Iterator[RunResponse]:
        yield RunResponse(run_id=self.run_id, content="test")

try:
    w = WorkflowWithClaudeAgent()
    r = w.run(message="test")
    print("✓ Workflow with Claude agent works\n")
except Exception as e:
    print(f"✗ Workflow with Claude agent failed: {e}\n")

# Test 5: Workflow with agent using response model
print("Test 5: Workflow with agent using response model")
from pydantic import BaseModel, Field
from typing import Optional, List

class ChatResponse(BaseModel):
    content: str = Field(..., description="Main response content")
    educational_context: Optional[str] = Field(None, description="Educational information")
    follow_up_questions: Optional[List[str]] = Field(None, description="Suggested follow-up questions")
    confidence_score: Optional[float] = Field(None, description="Confidence in the response")

class WorkflowWithResponseModelAgent(Workflow):
    def __init__(self):
        super().__init__()
        self.agent = Agent(
            name="Test Agent",
            role="Test role",
            model=Claude(id="claude-sonnet-4-20250514"),
            response_model=ChatResponse
        )
    
    def run(self, **kwargs) -> Iterator[RunResponse]:
        yield RunResponse(run_id=self.run_id, content="test")

try:
    w = WorkflowWithResponseModelAgent()
    r = w.run(message="test")
    print("✓ Workflow with response model agent works\n")
except Exception as e:
    print(f"✗ Workflow with response model agent failed: {e}\n")

# Test 6: Workflow with tools
print("Test 6: Workflow with FMP tools - SKIPPING (would need path setup)")
"""

class WorkflowWithTools(Workflow):
    def __init__(self):
        super().__init__()
        self.fmp_tools = FinancialModelingPrepTools()
        self.agent = Agent(
            name="Test Agent",
            role="Test role",
            model=Claude(id="claude-sonnet-4-20250514"),
            tools=[self.fmp_tools]
        )
    
    def run(self, **kwargs) -> Iterator[RunResponse]:
        yield RunResponse(run_id=self.run_id, content="test")

try:
    w = WorkflowWithTools()
    r = w.run(message="test")
    print("✓ Workflow with tools works\n")
except Exception as e:
    print(f"✗ Workflow with tools failed: {e}\n")

"""
print("Testing complete!")