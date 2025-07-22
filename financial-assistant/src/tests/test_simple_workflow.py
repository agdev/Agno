"""
Simple test workflow to verify basic Agno patterns work correctly
"""

import os
from typing import AsyncIterator, Iterator

from agno.agent import Agent
from agno.models.groq import Groq
from agno.run.response import RunResponse
from agno.workflow import Workflow

# Load environment variables
from dotenv import load_dotenv

env_path = os.path.join(os.path.dirname(__file__), "..", "..", "env", ".env")
load_dotenv(env_path)

groq_key = os.getenv("GROQ_API_KEY")


class SimpleTestWorkflow(Workflow):
    """Simple workflow to test basic Agno patterns"""

    def __init__(self):
        super().__init__()

        # Simple chat agent without structured output
        self.chat_agent = Agent(
            name="Simple Chat Agent",
            role="Provide simple conversational responses",
            # model=Claude(id="claude-sonnet-4-20250514"),
            model=Groq(id="llama-3.3-70b-versatile", api_key=groq_key),
            instructions=[
                "Provide simple, friendly responses to user messages",
                "Keep responses concise and helpful",
            ],
        )

    def run(self, **kwargs) -> Iterator[RunResponse]:  # pyright: ignore[reportIncompatibleMethodOverride]
        """Simple run method following Agno patterns"""

        message = kwargs.get("message", "hello")

        # Get response from agent without streaming to return proper RunResponse
        response = self.chat_agent.run(message)

        # Yield proper RunResponse object
        yield RunResponse(run_id=self.run_id, content=response.content)

    async def arun(self, **kwargs) -> AsyncIterator[RunResponse]:  # pyright: ignore[reportIncompatibleMethodOverride]
        """Simple run method following Agno patterns"""

        message = kwargs.get("message", "hello")

        # Get response from agent without streaming to return proper RunResponse
        response = await self.chat_agent.arun(message)

        # Yield proper RunResponse object
        yield RunResponse(run_id=self.run_id, content=response.content)


if __name__ == "__main__":
    # Test the simple workflow
    workflow = SimpleTestWorkflow()

    print("Testing simple workflow with 'hello'...")

    try:
        responses = workflow.run(message="hello")
        print(f"Workflow.run() returned: {type(responses)}")

        if responses is None:
            print("ERROR: Workflow returned None!")
        else:
            print("SUCCESS: Workflow returned an iterator")

            # Try to iterate over responses
            for i, response in enumerate(responses):
                print(
                    f"Response {i + 1}: {type(response)} - {response.content if hasattr(response, 'content') else response}"
                )

    except Exception as e:
        print(f"ERROR: {e}")
        import traceback

        traceback.print_exc()
