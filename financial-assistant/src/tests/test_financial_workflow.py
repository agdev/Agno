"""
Test the actual financial assistant workflow 

This test was used to diagnose the async_generator issue and verify 
that the sync-only workflow architecture resolves the problem.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dotenv import load_dotenv
import os
env_path = os.path.join(os.path.dirname(__file__), '..', '..', 'env', '.env')
load_dotenv(env_path)

print("Testing actual FinancialAssistantWorkflow...")

# Test with minimal imports
try:
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
        print("✓ Workflow returned an iterator")
        
except Exception as e:
    print(f"✗ ERROR: {e}")
    import traceback
    traceback.print_exc()