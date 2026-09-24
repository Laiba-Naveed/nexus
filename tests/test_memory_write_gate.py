import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from nexus.gates.memory_write_gate import grounding_check, contradiction_check, check_memory_write
from nexus.memory_store import MemoryStore


def test_trusted_source_passes_grounding_check():
    ok, reason = grounding_check("user_input")
    assert ok is True


def test_untrusted_source_fails_grounding_check():
    ok, reason = grounding_check("web_content")
    assert ok is False
    assert "not trustworthy" in reason


def test_contradiction_is_detected():
    memory = MemoryStore()
    memory.write("The user lives in Lahore", source="user_input")

    ok, reason = contradiction_check(memory, "The user lives in Tokyo")
    assert ok is False


def test_non_contradicting_fact_passes():
    memory = MemoryStore()
    memory.write("The user lives in Lahore", source="user_input")

    ok, reason = contradiction_check(memory, "The user likes tea")
    assert ok is True


def test_full_gate_blocks_untrusted_source_even_without_contradiction():
    memory = MemoryStore()
    decision = check_memory_write(memory, content="Some new fact", source="web_content")
    assert decision["approved"] is False
    assert decision["stage_blocked"] == "grounding"


def test_full_gate_approves_trusted_non_contradicting_write():
    memory = MemoryStore()
    decision = check_memory_write(memory, content="The user likes coffee", source="user_input")
    assert decision["approved"] is True
