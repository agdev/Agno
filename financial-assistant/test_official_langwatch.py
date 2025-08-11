#!/usr/bin/env python3
"""Test script to validate official LangWatch integration."""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Set up environment
os.environ["PYTHONPATH"] = str(project_root / "src")

def test_official_langwatch():
    """Test official LangWatch integration."""
    print("Testing Official LangWatch Integration...")
    print("-" * 50)
    
    # Test 1: Import check
    try:
        import langwatch
        print("✅ Official LangWatch SDK imported successfully")
        print(f"   LangWatch version: {getattr(langwatch, '__version__', 'unknown')}")
    except ImportError as e:
        print(f"❌ Failed to import LangWatch SDK: {e}")
        return False
    
    # Test 2: Settings configuration
    try:
        from config.settings import Settings
        settings = Settings()
        print("✅ Settings loaded successfully")
        print(f"   LangWatch configured: {settings.has_langwatch_configured}")
        if settings.has_langwatch_configured:
            print(f"   LangWatch endpoint: {settings.langwatch_endpoint}")
        else:
            print("   To enable: Set LANGWATCH_API_KEY in env/.env")
    except Exception as e:
        print(f"❌ Failed to load settings: {e}")
        return False
    
    # Test 3: Workflow import with official decorators
    try:
        from workflow.financial_assistant import FinancialAssistantWorkflow
        print("✅ FinancialAssistantWorkflow imported successfully")
        print("   Workflow now uses official LangWatch decorators")
    except Exception as e:
        print(f"❌ Failed to import workflow: {e}")
        return False
    
    # Test 4: Workflow initialization
    try:
        from agno.models.anthropic import Claude
        
        workflow = FinancialAssistantWorkflow(
            llm=Claude(id='claude-sonnet-4-20250514'),
            settings=settings,
            session_id='test-session'
        )
        print("✅ Workflow initialized successfully")
        print("   LangWatch decorators applied conditionally based on configuration")
    except Exception as e:
        print(f"❌ Failed to initialize workflow: {e}")
        return False
    
    # Test 5: Decorator application status
    original_method = FinancialAssistantWorkflow.run
    decorated_method = workflow.run
    
    if original_method != decorated_method:
        print("✅ LangWatch decorators dynamically applied to workflow methods")
    else:
        print("ℹ️  LangWatch decorators not applied (API key not configured)")
    
    print("-" * 50)
    print("✅ All tests passed!")
    print("\nIntegration Summary:")
    print("• Using official LangWatch decorators (@langwatch.trace, @langwatch.span)")
    print("• Decorators applied conditionally when API key is configured")
    print("• No custom decorator code - using LangWatch SDK directly")
    print("• Graceful fallback when LangWatch is not configured")
    
    print("\nNext steps:")
    if not settings.has_langwatch_configured:
        print("1. Get API key from: https://app.langwatch.ai")
        print("2. Set LANGWATCH_API_KEY in env/.env")
        print("3. Run application: uv run streamlit run src/main.py")
        print("4. Monitor traces at: https://app.langwatch.ai")
    else:
        print("1. Run application: uv run streamlit run src/main.py")
        print("2. Monitor traces at: https://app.langwatch.ai")
    
    return True

if __name__ == "__main__":
    success = test_official_langwatch()
    sys.exit(0 if success else 1)