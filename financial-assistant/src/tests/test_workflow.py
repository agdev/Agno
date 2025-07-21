"""
Unit tests for the Financial Assistant Workflow

This module contains tests for the core workflow functionality.
"""

import os
import sys
from unittest.mock import MagicMock, patch

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from tools.financial_modeling_prep import FinancialModelingPrepTools
from workflow.financial_assistant import FinancialAssistantWorkflow


class TestFinancialAssistantWorkflow:
    """Test class for FinancialAssistantWorkflow"""

    def test_workflow_initialization(self):
        """Test that the workflow initializes correctly"""
        workflow = FinancialAssistantWorkflow()

        # Check that workflow is created
        assert workflow is not None
        assert isinstance(workflow, FinancialAssistantWorkflow)

        # Check that core agents are created
        assert hasattr(workflow, "router_agent")
        assert hasattr(workflow, "symbol_extraction_agent")
        assert hasattr(workflow, "chat_agent")
        assert hasattr(workflow, "summary_agent")

        # Check that report composition method exists (replaced agent)
        assert hasattr(workflow, "_compose_financial_report")

        # Check that session state is initialized
        assert workflow.session_state is not None
        assert "messages" in workflow.session_state
        assert "companies_discussed" in workflow.session_state

    def test_workflow_with_custom_llm(self):
        """Test workflow creation with custom LLM"""
        from agno.models.anthropic import Claude

        custom_llm = Claude(id="claude-sonnet-4-20250514")
        workflow = FinancialAssistantWorkflow(llm=custom_llm)

        assert workflow is not None
        assert workflow.llm == custom_llm

    def test_context_generation_without_summary(self):
        """Test context generation when no summary exists"""
        workflow = FinancialAssistantWorkflow()

        # Test empty context
        context = workflow._get_conversation_context()
        assert context == ""

        # Test with companies discussed
        workflow.session_state["companies_discussed"] = ["AAPL", "MSFT"]
        context = workflow._get_conversation_context()
        assert "AAPL, MSFT" in context

    def test_context_generation_with_summary(self):
        """Test context generation when summary exists"""
        workflow = FinancialAssistantWorkflow()

        # Mock summary object
        mock_summary = MagicMock()
        mock_summary.summary = "User asked about Apple stock performance"
        workflow.session_state["conversation_summary"] = mock_summary
        workflow.session_state["companies_discussed"] = ["AAPL"]

        context = workflow._get_conversation_context()
        assert (
            "Previous conversation: User asked about Apple stock performance" in context
        )
        assert "AAPL" in context

    def test_summary_update_logic(self):
        """Test that summary update logic works correctly"""
        workflow = FinancialAssistantWorkflow()

        # Add some messages
        workflow.session_state["messages"] = [
            {"role": "user", "content": "What is Apple stock price?"},
            {
                "role": "agent",
                "content": "The current price is $150",
                "agent_name": "stock_price",
            },
        ]

        # Mock the summary agent
        with patch.object(workflow.summary_agent, "run") as mock_run:
            mock_response = MagicMock()
            mock_response.content = MagicMock()
            mock_response.content.summary = "User asked about Apple stock price"
            mock_run.return_value = mock_response

            # Test that summary updates with new messages
            result = workflow._update_conversation_summary()
            assert result is not None
            assert workflow.session_state["last_summary_message_count"] == 2


class TestFinancialModelingPrepTools:
    """Test class for FinancialModelingPrepTools"""

    def test_tools_initialization(self):
        """Test that tools initialize correctly"""
        tools = FinancialModelingPrepTools()
        assert tools is not None
        assert hasattr(tools, "search_symbol")
        assert hasattr(tools, "get_income_statement")
        assert hasattr(tools, "get_company_financials")
        assert hasattr(tools, "get_stock_price")


class TestWorkflowIntegration:
    """Test class for workflow integration"""

    def test_session_state_initialization(self):
        """Test that session state is properly initialized"""
        workflow = FinancialAssistantWorkflow()

        # Check default session state
        assert workflow.session_state["messages"] == []
        assert workflow.session_state["companies_discussed"] == []
        assert workflow.session_state["conversation_summary"] is None
        assert workflow.session_state["last_summary_message_count"] == 0

    def test_workflow_has_tools_access(self):
        """Test that workflow has access to financial tools"""
        workflow = FinancialAssistantWorkflow()

        # Check that tools are available
        assert hasattr(workflow.symbol_extraction_agent, "tools")
        if workflow.symbol_extraction_agent.tools:
            assert len(workflow.symbol_extraction_agent.tools) > 0
