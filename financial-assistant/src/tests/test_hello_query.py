"""
Test the "hello" query with the available API keys

This test verifies that the hello query works end-to-end with the 
sync-only Agno workflow architecture after fixing the dual method conflict.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))  # Point to src/

from dotenv import load_dotenv
import os
env_path = os.path.join(os.path.dirname(__file__), '..', '..', 'env', '.env')
load_dotenv(env_path)

print("Testing hello query with working Financial Assistant Workflow...")

try:
    from config.settings import Settings
    from workflow.financial_assistant import FinancialAssistantWorkflow
    from agno.models.groq import Groq  # Use Groq since we have that API key
    
    print("✓ Imports successful")
    
    # Create settings and workflow with Groq model (we have that API key)
    settings = Settings()
    llm = Groq(id="llama-3.3-70b-versatile")  # Use available model
    
    workflow = FinancialAssistantWorkflow(llm=llm, settings=settings)
    print("✓ Workflow creation successful with Groq LLM")
    
    # Test the hello query
    print("Running hello query...")
    responses = workflow.run(message="hello")
    print(f"✓ workflow.run() returned: {type(responses)}")
    
    if responses is None:
        print("✗ ERROR: Workflow returned None!")
    else:
        print("✓ Workflow returned a generator")
        try:
            # Test consuming the generator
            result_list = list(responses)
            print(f"✓ Generator consumed successfully, got {len(result_list)} responses")
            if result_list and len(result_list) > 0:
                first_result = result_list[0]
                if first_result is not None and hasattr(first_result, 'content') and first_result.content is not None:
                    print(f"✓ Response content: {first_result.content[:200]}...")
                    print("\n" + "="*50)
                    print("FULL RESPONSE:")
                    print("="*50)
                    print(first_result.content)
                    print("="*50)
        except Exception as e:
            print(f"✗ Error consuming generator: {e}")
            import traceback
            traceback.print_exc()
        
except Exception as e:
    print(f"✗ ERROR: {e}")
    import traceback
    traceback.print_exc()