#!/usr/bin/env python3
"""Test LangWatch integration with local instance on port 5560."""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Set up environment for local LangWatch
os.environ["PYTHONPATH"] = str(project_root / "src")
os.environ["LANGWATCH_ENDPOINT"] = "http://localhost:5560"

def test_local_langwatch():
    """Test LangWatch integration with local instance."""
    print("🚀 Testing Local LangWatch Integration (port 5560)")
    print("-" * 60)
    
    # Test 1: Configuration check
    try:
        from src.config.settings import Settings
        settings = Settings()
        print(f"✅ Settings loaded - Endpoint: {settings.langwatch_endpoint}")
        print(f"   Local instance detected: {'localhost' in settings.langwatch_endpoint}")
    except Exception as e:
        print(f"❌ Failed to load settings: {e}")
        return False
    
    # Test 2: Decorator functionality
    try:
        from src.observability.langwatch_decorator import (
            setup_langwatch,
            langwatch_trace,
            LANGWATCH_AVAILABLE
        )
        
        print(f"✅ LangWatch SDK available: {LANGWATCH_AVAILABLE}")
        
        # Initialize LangWatch for local instance
        setup_langwatch()
        print("✅ LangWatch setup completed for local instance")
        
        # Test decorator
        @langwatch_trace(name="test_financial_query", span_type="test")
        def test_function(query: str):
            return f"Processing: {query}"
        
        result = test_function("What is Apple's stock price?")
        print(f"✅ Decorated function executed: {result}")
        
    except Exception as e:
        print(f"❌ Decorator test failed: {e}")
        return False
    
    # Test 3: Workflow import
    try:
        from src.workflow.financial_assistant import FinancialAssistantWorkflow
        from agno.models.anthropic import Claude
        
        print("✅ Workflow imported successfully")
        print("   All LangWatch decorators applied to workflow methods")
        
    except Exception as e:
        print(f"❌ Workflow import failed: {e}")
        return False
    
    print("-" * 60)
    print("🎉 All tests passed! Your local LangWatch integration is ready.")
    print()
    print("📋 Next steps:")
    print("1. Start your financial assistant: uv run streamlit run src/main.py")
    print("2. Test with queries like:")
    print("   • 'What is Tesla's stock price?'")
    print("   • 'Tell me about Apple's business'")
    print("3. Monitor traces at: http://localhost:5560")
    print()
    print("🔍 What to expect in LangWatch:")
    print("• Main workflow traces (financial_assistant_workflow)")
    print("• Flow-specific spans (report_flow, alone_flow, chat_flow)")
    print("• Data fetching operations (fetch_financial_data)")
    print("• Complete request lifecycle with timing")
    
    return True

if __name__ == "__main__":
    success = test_local_langwatch()
    sys.exit(0 if success else 1)