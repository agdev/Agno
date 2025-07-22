"""
Minimal test workflow to debug the async_generator issue
"""

from typing import Iterator
from agno.run.response import RunResponse, RunResponseEvent, RunResponseContentEvent
from agno.workflow import Workflow


class MinimalTestWorkflow(Workflow):
    """Minimal workflow with no agents"""
    
    def run(self, **kwargs) -> Iterator[RunResponseEvent]:
        """Minimal run method"""
        message = kwargs.get("message", "hello")
        
        print(f"DEBUG: MinimalTestWorkflow.run() called with message: {message}")
        
        yield RunResponseContentEvent(
            run_id=self.run_id,
            content=f"Minimal response: {message}"
        )


if __name__ == "__main__":
    workflow = MinimalTestWorkflow()
    print("Testing minimal workflow...")
    
    try:
        responses = workflow.run(message="test")
        print(f"workflow.run() returned: {type(responses)}")
        
        if responses is None:
            print("ERROR: Workflow returned None")
        else:
            for response in responses:
                print(f"Response: {response.content}")
                
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()