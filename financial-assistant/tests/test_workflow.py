"""
Unit tests for the Financial Assistant Workflow

This module contains tests for the core workflow functionality.
"""

import os
import sys
import pytest
from unittest.mock import patch, MagicMock

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from workflow.financial_assistant import FinancialAssistantWorkflow, create_financial_assistant_workflow
from tools.financial_modeling_prep import FinancialModelingPrepTools


class TestFinancialAssistantWorkflow:
    """Test class for FinancialAssistantWorkflow"""
    
    def setup_method(self):
        """Setup method run before each test"""
        # Set up mock environment variables
        os.environ['FINANCIAL_MODELING_PREP_API_KEY'] = 'test_fmp_key'
        os.environ['ANTHROPIC_API_KEY'] = 'test_anthropic_key'
    
    def test_workflow_initialization(self):
        """Test that the workflow initializes correctly"""
        workflow = create_financial_assistant_workflow()
        
        # Check that workflow is created
        assert workflow is not None
        assert isinstance(workflow, FinancialAssistantWorkflow)
        
        # Check that all agents are created
        assert hasattr(workflow, 'router_agent')
        assert hasattr(workflow, 'symbol_extraction_agent')
        assert hasattr(workflow, 'income_statement_agent')
        assert hasattr(workflow, 'company_financials_agent')
        assert hasattr(workflow, 'stock_price_agent')
        assert hasattr(workflow, 'report_generation_agent')
        assert hasattr(workflow, 'chat_agent')
        
        # Check that tools are initialized
        assert hasattr(workflow, 'fmp_tools')
        assert isinstance(workflow.fmp_tools, FinancialModelingPrepTools)
    
    def test_workflow_with_custom_llm(self):
        """Test workflow creation with custom LLM"""
        from agno.models.anthropic import Claude
        
        custom_llm = Claude(id="claude-sonnet-4-20250514")
        workflow = create_financial_assistant_workflow(llm=custom_llm)
        
        assert workflow is not None
        assert workflow.llm == custom_llm
    
    @patch.dict(os.environ, {}, clear=True)
    def test_workflow_missing_api_keys(self):
        """Test that workflow creation fails gracefully without API keys"""
        with pytest.raises(ValueError):
            # Should fail because FINANCIAL_MODELING_PREP_API_KEY is missing
            create_financial_assistant_workflow()


class TestFinancialModelingPrepTools:
    """Test class for FinancialModelingPrepTools"""
    
    def setup_method(self):
        """Setup method run before each test"""
        os.environ['FINANCIAL_MODELING_PREP_API_KEY'] = 'test_fmp_key'
    
    def test_tools_initialization(self):
        """Test that tools initialize correctly"""
        tools = FinancialModelingPrepTools()
        
        assert tools is not None
        assert tools.api_key == 'test_fmp_key'
        assert tools.base_url == "https://financialmodelingprep.com/api/v3"
    
    @patch.dict(os.environ, {}, clear=True)
    def test_tools_missing_api_key(self):
        """Test that tools fail without API key"""
        with pytest.raises(ValueError):
            FinancialModelingPrepTools()
    
    @patch('requests.get')
    def test_search_symbol_success(self, mock_get):
        """Test successful symbol search"""
        # Mock successful API response for search endpoint
        mock_response = MagicMock()
        mock_response.json.return_value = [{"symbol": "AAPL", "name": "Apple Inc.", "exchangeShortName": "NASDAQ"}]
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        tools = FinancialModelingPrepTools()
        result = tools.search_symbol("Apple Inc")  # Use longer name to trigger search
        
        assert result["found"] is True
        assert result["symbol"] == "AAPL"
        assert result["name"] == "Apple Inc."
        assert result["exchange"] == "NASDAQ"
    
    @patch('requests.get')
    def test_search_symbol_not_found(self, mock_get):
        """Test symbol search when no results found"""
        # Mock empty API response
        mock_response = MagicMock()
        mock_response.json.return_value = []
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        tools = FinancialModelingPrepTools()
        result = tools.search_symbol("NonExistentCompany")
        
        assert result["found"] is False
        assert result["symbol"] == "UNKNOWN"
        assert "error" in result
    
    @patch('requests.get')
    def test_get_income_statement_success(self, mock_get):
        """Test successful income statement retrieval"""
        # Mock successful API response
        mock_response = MagicMock()
        mock_response.json.return_value = [{
            "date": "2023-12-31",
            "period": "FY",
            "revenue": 1000000000,
            "grossProfit": 600000000,
            "operatingIncome": 400000000,
            "netIncome": 300000000,
            "eps": 5.50
        }]
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        tools = FinancialModelingPrepTools()
        result = tools.get_income_statement("AAPL")
        
        assert result["success"] is True
        assert result["symbol"] == "AAPL"
        assert result["revenue"] == 1000000000
        assert result["net_income"] == 300000000
        assert result["eps"] == 5.50


class TestWorkflowIntegration:
    """Integration tests for the complete workflow"""
    
    def setup_method(self):
        """Setup method run before each test"""
        os.environ['FINANCIAL_MODELING_PREP_API_KEY'] = 'test_fmp_key'
        os.environ['ANTHROPIC_API_KEY'] = 'test_anthropic_key'
    
    def test_session_state_initialization(self):
        """Test that session state is properly initialized"""
        workflow = create_financial_assistant_workflow()
        
        # Session state should be available
        assert hasattr(workflow, 'session_state')
        
        # Should be able to set and get values
        workflow.session_state['test_key'] = 'test_value'
        assert workflow.session_state.get('test_key') == 'test_value'
    
    @patch('workflow.financial_assistant.FinancialModelingPrepTools')
    def test_workflow_agents_have_tools(self, mock_tools_class):
        """Test that data agents have access to tools"""
        mock_tools = MagicMock()
        mock_tools_class.return_value = mock_tools
        
        workflow = create_financial_assistant_workflow()
        
        # Check that agents have tools
        assert hasattr(workflow.symbol_extraction_agent, 'tools')
        assert hasattr(workflow.income_statement_agent, 'tools')
        assert hasattr(workflow.company_financials_agent, 'tools')
        assert hasattr(workflow.stock_price_agent, 'tools')
        
        # Tools should contain our mock
        assert mock_tools in workflow.symbol_extraction_agent.tools


if __name__ == "__main__":
    pytest.main([__file__, "-v"])