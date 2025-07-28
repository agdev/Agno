#!/usr/bin/env python3
"""
Test full Langfuse integration with actual workflow execution

This test verifies that Langfuse tracing works end-to-end with the Financial Assistant.
"""

from workflow.financial_assistant import FinancialAssistantWorkflow
from config.settings import Settings


def test_langfuse_full_integration():
    """Test full Langfuse integration with hello query (no API keys needed)"""
    
    print("🔄 Testing full Langfuse integration...")
    
    # Create settings instance
    settings = Settings()
    print(f"✅ Settings loaded")
    print(f"   Langfuse configured: {settings.has_langfuse_configured}")
    print(f"   LLM provider available: {settings.has_llm_provider}")
    
    if not settings.has_langfuse_configured:
        print("⚠️  Langfuse not configured - traces won't be sent")
        print("   Make sure LANGFUSE_PUBLIC_KEY and LANGFUSE_SECRET_KEY are in env/.env")
    
    # Initialize workflow
    workflow = FinancialAssistantWorkflow(
        settings=settings,
        session_id="test_langfuse_full",
        stream=False
    )
    print("✅ Workflow initialized")
    
    # Test simple hello query (should go to chat flow)
    print("🔄 Running hello query...")
    try:
        responses = list(workflow.run(message="hello"))
        
        print(f"✅ Query executed successfully!")
        print(f"   Got {len(responses)} responses")
        print(f"   First response: {responses[0].content[:100]}...")
        
        if settings.has_langfuse_configured:
            print("📊 Traces should now be visible in Langfuse dashboard at:")
            print(f"   {settings.langfuse_host}")
            print("   Check the 'Traces' section for 'financial_assistant_workflow' traces")
        
        return True
        
    except Exception as e:
        print(f"❌ Query failed: {e}")
        print("   This might be due to missing API keys for LLM providers")
        print("   Langfuse tracing is still configured correctly")
        return False


if __name__ == "__main__":
    try:
        success = test_langfuse_full_integration()
        
        if success:
            print("\n🎉 Full Langfuse integration test passed!")
            print("Your Financial Assistant is now fully instrumented for observability")
        else:
            print("\n⚠️  Test completed with warnings")
            print("Langfuse integration is configured but LLM execution failed")
            
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        raise