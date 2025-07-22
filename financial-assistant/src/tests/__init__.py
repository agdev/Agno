"""
Test suite for Financial Assistant Workflow

This directory contains comprehensive tests for the Agno-based financial assistant,
including workflow tests, agent tests, tool tests, and Agno framework compatibility tests.

Test Categories:
- test_workflow.py: Core workflow execution tests
- test_hello_query.py: End-to-end hello query test
- test_financial_*.py: Financial data flow tests  
- test_agno_*.py: Agno framework compatibility tests
- test_minimal_*.py: Minimal component tests for debugging

Agno Framework Testing Notes:
- All tests designed for sync-only workflow architecture
- Tests verify workflow.run() returns generator (not None)
- Tests check for absence of async_generator warnings
- Compatible with Agno 1.7.1+ sync-only patterns
"""