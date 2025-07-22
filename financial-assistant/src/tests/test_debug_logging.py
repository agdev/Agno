"""
Comprehensive debug test to capture runtime errors with detailed logging

This test captures all the errors and warnings we're seeing to identify
the root cause of the Groq client cleanup and Agno response type issues.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dotenv import load_dotenv
import os
env_path = os.path.join(os.path.dirname(__file__), '..', '..', 'env', '.env')
load_dotenv(env_path)

print("="*60)
print("COMPREHENSIVE DEBUG TEST - Runtime Error Analysis")
print("="*60)

def test_groq_client():
    """Test Groq client lifecycle"""
    print("\n1. TESTING GROQ CLIENT LIFECYCLE")
    print("-" * 40)
    
    try:
        from config.settings import Settings
        from workflow.financial_assistant import FinancialAssistantWorkflow
        from agno.models.groq import Groq
        
        print("DEBUG: Creating Groq LLM...")
        llm = Groq(id="llama-3.3-70b-versatile")
        print(f"DEBUG: Groq LLM created: {type(llm)}")
        print(f"DEBUG: Groq LLM attributes: {list(vars(llm).keys())}")
        
        # Check client state immediately after creation
        if hasattr(llm, 'client'):
            print(f"DEBUG: Groq has client: {type(llm.client)}")
            print(f"DEBUG: Client attributes: {list(vars(llm.client).keys()) if hasattr(llm.client, '__dict__') else 'No __dict__'}")
        else:
            print("DEBUG: Groq LLM has no client attribute yet")
        
        print("\nDEBUG: Creating workflow with Groq...")
        settings = Settings()
        workflow = FinancialAssistantWorkflow(llm=llm, settings=settings)
        
        print("\nDEBUG: Testing hello query...")
        responses = workflow.run(message="hello")
        
        if responses is None:
            print("ERROR: Workflow returned None!")
            return False
        else:
            print(f"SUCCESS: Workflow returned {type(responses)}")
            
            print("\nDEBUG: Consuming responses...")
            result_list = list(responses)
            print(f"SUCCESS: Got {len(result_list)} responses")
            
            if result_list and len(result_list) > 0:
                first_result = result_list[0]
                if first_result is not None and hasattr(first_result, 'content') and first_result.content is not None:
                    print(f"RESPONSE: {first_result.content[:100]}...")
            
            print("\nDEBUG: Workflow test completed successfully")
            
            # Check client state after usage
            if hasattr(workflow.llm, 'client'):
                print(f"DEBUG: Post-usage client type: {type(workflow.llm.client)}")
                print(f"DEBUG: Post-usage client state: {list(vars(workflow.llm.client).keys()) if hasattr(workflow.llm.client, '__dict__') else 'No __dict__'}")
            
            return True
            
    except Exception as e:
        print(f"ERROR: Test failed: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_client_cleanup():
    """Test explicit client cleanup"""
    print("\n2. TESTING EXPLICIT CLIENT CLEANUP")
    print("-" * 40)
    
    try:
        from agno.models.groq import Groq
        
        print("DEBUG: Creating Groq client for cleanup test...")
        llm = Groq(id="llama-3.3-70b-versatile")
        
        # Force client creation by accessing it
        if hasattr(llm, 'get_client'):
            print("DEBUG: Forcing client creation...")
            client = llm.get_client()
            print(f"DEBUG: Client created: {type(client)}")
            print(f"DEBUG: Client state: {list(vars(client).keys()) if hasattr(client, '__dict__') else 'No __dict__'}")
            
            # Try to close it manually
            if hasattr(client, 'close'):
                print("DEBUG: Attempting manual close...")
                client.close()
                print("DEBUG: Manual close successful")
            else:
                print("DEBUG: Client has no close method")
        
        print("DEBUG: Cleanup test completed")
        return True
        
    except Exception as e:
        print(f"ERROR: Cleanup test failed: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_response_types():
    """Test response type variations"""
    print("\n3. TESTING RESPONSE TYPES")
    print("-" * 40)
    
    try:
        from agno.run.response import RunResponse
        print(f"DEBUG: RunResponse class: {RunResponse}")
        print(f"DEBUG: RunResponse module: {RunResponse.__module__}")
        
        # Try to import RunResponseEvent
        try:
            from agno.run.response import RunResponseEvent
            print(f"DEBUG: RunResponseEvent class: {RunResponseEvent}")
            print(f"DEBUG: RunResponseEvent module: {RunResponseEvent.__module__}")
        except ImportError as e:
            print(f"DEBUG: RunResponseEvent not available: {e}")
        
        # Create a test response
        test_response = RunResponse(run_id="test-123", content="Test content")
        print(f"DEBUG: Test RunResponse created: {type(test_response)}")
        print(f"DEBUG: Test RunResponse attributes: {list(vars(test_response).keys())}")
        
        return True
        
    except Exception as e:
        print(f"ERROR: Response type test failed: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run comprehensive debug tests"""
    print("Starting comprehensive debug analysis...")
    
    results = []
    
    # Test 1: Groq client lifecycle
    results.append(("Groq Client Test", test_groq_client()))
    
    # Test 2: Client cleanup
    results.append(("Client Cleanup Test", test_client_cleanup()))
    
    # Test 3: Response types
    results.append(("Response Types Test", test_response_types()))
    
    print("\n" + "="*60)
    print("DEBUG TEST RESULTS")
    print("="*60)
    
    for test_name, passed in results:
        status = "PASS" if passed else "FAIL"
        print(f"{test_name}: {status}")
    
    total_passed = sum(1 for _, passed in results if passed)
    print(f"\nTotal: {total_passed}/{len(results)} tests passed")
    
    print("\nDEBUG: Exiting main function...")

if __name__ == "__main__":
    main()
    print("DEBUG: Script execution complete")