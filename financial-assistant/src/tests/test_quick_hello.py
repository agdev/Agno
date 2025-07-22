"""
Quick test for hello query with proper environment loading
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Load environment from the correct path
from dotenv import load_dotenv
import os

# Go up two levels from src/tests/ to get to project root, then to env/
env_path = os.path.join(os.path.dirname(__file__), '..', '..', 'env', '.env')
print(f"Loading env from: {env_path}")
load_dotenv(env_path)

# Check if key is loaded
groq_key = os.getenv('GROQ_API_KEY')
print(f"GROQ_API_KEY loaded: {'Yes' if groq_key else 'No'}")

if groq_key:
    print("Testing with loaded API key...")
    
    try:
        from config.settings import Settings
        from workflow.financial_assistant import FinancialAssistantWorkflow
        from agno.models.groq import Groq
        
        # Create workflow
        settings = Settings()
        llm = Groq(id="llama-3.3-70b-versatile")
        
        workflow = FinancialAssistantWorkflow(llm=llm, settings=settings)
        print("✓ Workflow created")
        
        # Test hello query
        responses = workflow.run(message="hello")
        
        if responses is None:
            print("✗ ERROR: Workflow returned None!")
        else:
            print("✓ Workflow returned generator")
            try:
                result_list = list(responses)
                print(f"✓ Got {len(result_list)} responses")
                if result_list and len(result_list) > 0:
                    first_result = result_list[0]
                    if first_result is not None and hasattr(first_result, 'content') and first_result.content is not None:
                        print(f"✓ Response: {first_result.content[:100]}...")
            except Exception as e:
                print(f"✗ Error: {e}")
    
    except Exception as e:
        print(f"✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        
else:
    print("✗ No API key loaded - check environment file path")