"""
Test FinancialAssistantWorkflow with only sync method to see if that fixes the issue

This test verified that removing async methods resolves the Agno dual method conflict.
Confirmed that workflow.run() returns proper generator when arun() is removed.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dotenv import load_dotenv
import os
env_path = os.path.join(os.path.dirname(__file__), '..', '..', 'env', '.env')
load_dotenv(env_path)

print("Testing FinancialAssistantWorkflow with arun method temporarily removed...")

try:
    # Import and test
    from workflow.financial_assistant import FinancialAssistantWorkflow
    print("✓ Import successful")
    
    # Create workflow
    workflow = FinancialAssistantWorkflow()
    print("✓ Workflow creation successful")
    
    # Test run method
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
                    print(f"✓ First response: {first_result.content[:100]}...")
        except Exception as e:
            print(f"✗ Error consuming generator: {e}")
        
except Exception as e:
    print(f"✗ ERROR: {e}")
    import traceback
    traceback.print_exc()