"""
Unit tests for the Tool Execution Gate's rule-based validator.

Note: the LLM-based validator (llm_based_check) is not unit tested
here since it calls a real external API - it should be covered by
separate integration tests that run against a live or mocked API key.
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from nexus.gates.tool_execution_gate import rule_based_check


def test_allowed_tool_passes_rule_check():
    ok, reason = rule_based_check("research_assistant", "search_web")
    assert ok is True


def test_disallowed_tool_fails_rule_check():
    ok, reason = rule_based_check("research_assistant", "delete_file")
    assert ok is False
    assert "not allowed" in reason


def test_unknown_role_has_no_permissions():
    ok, reason = rule_based_check("unregistered_role", "search_web")
    assert ok is False
