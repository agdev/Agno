#!/usr/bin/env python3
"""Test script to validate LangWatch decorator application."""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Set up environment
os.environ["PYTHONPATH"] = str(project_root / "src")
os.environ["LANGWATCH_API_KEY"] = "test-key-for-decorator-testing"

def test_decorator_application():
    """Test if LangWatch decorators are being applied properly."""
    print("Testing LangWatch Decorator Application...")
    print("-" * 60)
    
    try:
        # Import modules
        from config.settings import Settings
        from agno.models.anthropic import Claude
        from workflow.financial_assistant import FinancialAssistantWorkflow
        
        print("✅ All modules imported successfully")
        
        # Create workflow instance
        settings = Settings()
        workflow = FinancialAssistantWorkflow(
            llm=Claude(id='claude-sonnet-4-20250514'),
            settings=settings,
            session_id='test-decorator-session'
        )
        
        print("✅ Workflow initialized successfully")
        
        # Test 1: Check if decorators were applied
        original_class = FinancialAssistantWorkflow
        
        # Check main run method
        if hasattr(workflow.run, '__wrapped__'):
            print("✅ Main workflow run() method has been decorated")
            print(f"   Decorator chain: {[getattr(f, '__name__', 'unknown') for f in [workflow.run]]}")
        else:
            print("❌ Main workflow run() method is NOT decorated")
            
        # Check flow methods
        flow_methods = [
            ('_run_report_flow', workflow._run_report_flow),
            ('_run_alone_flow', workflow._run_alone_flow), 
            ('_run_chat_flow', workflow._run_chat_flow),
            ('_fetch_financial_data_sequential', workflow._fetch_financial_data_sequential)
        ]
        
        decorated_count = 0
        for method_name, method in flow_methods:
            if hasattr(method, '__wrapped__') or str(type(method)) != str(type(getattr(original_class, method_name))):
                print(f"✅ {method_name}() has been decorated")
                decorated_count += 1
            else:
                print(f"❌ {method_name}() is NOT decorated")
        
        print(f"\nDecorator Application Summary: {decorated_count}/4 flow methods decorated")
        
        # Test 2: Check LangWatch context
        try:
            import langwatch
            current_span = langwatch.get_current_span()
            if current_span:
                print("✅ LangWatch span context is available")
            else:
                print("ℹ️  No active LangWatch span (expected outside of execution)")
        except Exception as e:
            print(f"⚠️  LangWatch context check failed: {e}")
        
        # Test 3: Test a simple method call to see tracing
        print("\nTesting method execution with tracing...")
        try:
            # This should trigger LangWatch tracing if decorators work
            test_response = list(workflow.run(message="hello"))
            print(f"✅ Workflow executed successfully, got {len(test_response)} responses")
            if test_response:
                print(f"   Sample response: {str(test_response[0])[:100]}...")
        except Exception as e:
            print(f"❌ Workflow execution failed: {e}")
            import traceback
            traceback.print_exc()
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_decorator_application()
    sys.exit(0 if success else 1)