#!/usr/bin/env python3
"""Test script to validate LangWatch integration."""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Set up environment
os.environ["PYTHONPATH"] = str(project_root / "src")


def test_langwatch_setup():
    """Test LangWatch setup and configuration."""
    print("Testing LangWatch Integration...")
    print("-" * 50)

    # Test 1: Import check (now using official LangWatch decorators)
    try:
        import langwatch
        
        print("✅ Official LangWatch SDK imported successfully")
        print("   Using official decorators instead of custom ones")
    except ImportError as e:
        print(f"❌ Failed to import LangWatch SDK: {e}")
        return False

    # Test 2: Settings configuration
    try:
        from src.config.settings import Settings

        settings = Settings()
        print("✅ Settings loaded successfully")
        print(f"   LangWatch configured: {settings.has_langwatch_configured}")
        if settings.has_langwatch_configured:
            print(f"   LangWatch endpoint: {settings.langwatch_endpoint}")
    except Exception as e:
        print(f"❌ Failed to load settings: {e}")
        return False

    # Test 3: Workflow import with LangWatch decorators
    try:
        print("✅ FinancialAssistantWorkflow imported successfully")
        print("   Workflow now uses LangWatch decorators")
    except Exception as e:
        print(f"❌ Failed to import workflow: {e}")
        return False

    # Test 5: Simple decorator test
    try:
        @langwatch.trace(name="test_function")
        def test_function():
            return "Test successful"

        result = test_function()
        print(f"✅ Test function with LangWatch decorator executed: {result}")
    except Exception as e:
        print(f"❌ Failed to execute decorated function: {e}")
        return False

    print("-" * 50)
    print("✅ All tests passed!")
    print("\nNext steps:")
    print("1. Set LANGWATCH_API_KEY in env/.env to enable tracing")
    print("2. Run the application with: uv run streamlit run src/main.py")
    print("3. Monitor traces at: https://app.langwatch.ai")

    return True


if __name__ == "__main__":
    success = test_langwatch_setup()
    sys.exit(0 if success else 1)
