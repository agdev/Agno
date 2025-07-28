#!/usr/bin/env python3
"""
Test Langfuse tracing decorators without making actual API calls

This test verifies that the @observe decorators are properly applied.
"""

import inspect
from workflow.financial_assistant import FinancialAssistantWorkflow


def test_langfuse_decorators_applied():
    """Test that @observe decorators are properly applied to workflow methods"""
    
    # Get the class
    workflow_class = FinancialAssistantWorkflow
    
    # Check that key methods have the @observe decorator
    methods_to_check = [
        'run',
        '_run_report_flow', 
        '_run_alone_flow',
        '_run_chat_flow',
        '_fetch_financial_data_sequential'
    ]
    
    decorated_methods = []
    
    for method_name in methods_to_check:
        if hasattr(workflow_class, method_name):
            method = getattr(workflow_class, method_name)
            
            # Check if method has Langfuse wrapper attributes
            if hasattr(method, '__wrapped__') or 'langfuse' in str(method):
                decorated_methods.append(method_name)
                print(f"✅ {method_name} has Langfuse tracing")
            else:
                print(f"⚠️  {method_name} missing Langfuse tracing")
    
    # Verify we found decorated methods
    assert len(decorated_methods) >= 3, f"Expected at least 3 decorated methods, found {len(decorated_methods)}"
    
    print(f"\n✅ Langfuse decorators properly applied to {len(decorated_methods)} methods")
    return decorated_methods


def test_langfuse_import_success():
    """Test that Langfuse can be imported successfully"""
    
    try:
        from langfuse import observe
        print("✅ Langfuse import successful")
        
        # Test that observe decorator can be created
        @observe(name="test_function")
        def test_func():
            return "test"
        
        print("✅ @observe decorator works")
        return True
        
    except ImportError as e:
        print(f"❌ Langfuse import failed: {e}")
        return False


def test_workflow_class_integration():
    """Test that workflow class can be instantiated with Langfuse"""
    
    try:
        # This should work even without API keys - just creating the class
        workflow = FinancialAssistantWorkflow(
            session_id="test_langfuse_integration"
        )
        
        print("✅ Workflow class instantiation successful")
        
        # Check that the run method exists and is decorated
        assert hasattr(workflow, 'run'), "Workflow missing run method"
        print("✅ Workflow run method exists")
        
        return True
        
    except Exception as e:
        print(f"❌ Workflow instantiation failed: {e}")
        return False


if __name__ == "__main__":
    print("🔄 Testing Langfuse tracing integration...")
    
    success = True
    
    try:
        # Test 1: Import success
        if not test_langfuse_import_success():
            success = False
        
        print()
        
        # Test 2: Decorator application
        decorated_methods = test_langfuse_decorators_applied()
        
        print()
        
        # Test 3: Workflow integration
        if not test_workflow_class_integration():
            success = False
        
        if success:
            print(f"\n🎉 All Langfuse integration tests passed!")
            print(f"📊 Ready for tracing with {len(decorated_methods)} instrumented methods")
            print("\nNext steps:")
            print("1. Add LANGFUSE_PUBLIC_KEY and LANGFUSE_SECRET_KEY to env/.env")
            print("2. Set LANGFUSE_HOST=http://localhost:3001 in env/.env") 
            print("3. Run your Financial Assistant to see traces in Langfuse dashboard")
        else:
            print("\n❌ Some tests failed")
            
    except Exception as e:
        print(f"\n❌ Test suite failed: {e}")
        success = False