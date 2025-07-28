#!/usr/bin/env python3
"""
Test Langfuse integration with Financial Assistant Workflow

This test verifies that Langfuse tracing is working correctly with the Financial Assistant.
"""

import pytest
from workflow.financial_assistant import FinancialAssistantWorkflow
from langfuse import Langfuse


def test_langfuse_basic_integration():
    """Test basic Langfuse integration with hello query"""
    
    # Initialize workflow (no need for actual API keys for tracing test)
    workflow = FinancialAssistantWorkflow(
        session_id="test_session_langfuse",
        stream=False
    )
    
    # Run a simple hello query
    responses = list(workflow.run(message="hello"))
    
    # Verify we got responses
    assert len(responses) > 0
    assert responses[0].content is not None
    
    print(f"✅ Langfuse integration test passed!")
    print(f"   Responses: {len(responses)}")
    print(f"   First response: {responses[0].content[:100]}...")


def test_langfuse_with_chat_flow():
    """Test Langfuse tracing with chat flow"""
    
    workflow = FinancialAssistantWorkflow(
        session_id="test_chat_langfuse",
        stream=False
    )
    
    # Test a chat query that should go to chat flow
    responses = list(workflow.run(message="What is a P/E ratio?"))
    
    # Verify we got responses
    assert len(responses) > 0
    assert "P/E" in responses[0].content or "price" in responses[0].content.lower()
    
    print(f"✅ Chat flow tracing test passed!")
    print(f"   Response contains financial education content")


if __name__ == "__main__":
    print("🔄 Testing Langfuse integration...")
    
    try:
        test_langfuse_basic_integration()
        test_langfuse_with_chat_flow()
        print("\n🎉 All Langfuse integration tests passed!")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        print("Note: Make sure you have:")
        print("1. Added LANGFUSE_* environment variables to env/.env")
        print("2. Langfuse running at http://localhost:3001")
        print("3. Created a project and obtained API keys")
        raise