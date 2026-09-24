"""
memory_write_gate.py
----------------------
This is CHECKPOINT #2 of your product.

Before the agent is allowed to save something to memory, it must pass
through check_memory_write() first.

Two checks, matching your FYP proposal:
  1. Grounding check      -> does this fact have a trustworthy source?
  2. Contradiction check  -> does this fact conflict with something
                              already stored?
"""

from nexus.memory_store import MemoryStore

# Sources we trust more vs less. In a real system this would be more
# detailed (e.g. "verified_user_input" vs "unverified_webpage_text").
TRUSTED_SOURCES = ["user_input", "verified_tool_output"]
UNTRUSTED_SOURCES = ["web_content", "unverified_tool_output"]


def grounding_check(source: str) -> tuple[bool, str]:
    if source in UNTRUSTED_SOURCES:
        return False, f"Grounding check failed: source '{source}' is not trustworthy enough to write to memory"
    return True, "Grounding check passed"


def contradiction_check(memory: MemoryStore, new_content: str) -> tuple[bool, str]:
    conflicts = memory.find_contradictions(new_content)
    if conflicts:
        return False, f"Contradiction check failed: conflicts with existing memory {conflicts}"
    return True, "Contradiction check passed"


def check_memory_write(memory: MemoryStore, content: str, source: str) -> dict:
    ok, reason = grounding_check(source)
    if not ok:
        return {"approved": False, "stage_blocked": "grounding", "reason": reason}

    ok, reason = contradiction_check(memory, content)
    if not ok:
        return {"approved": False, "stage_blocked": "contradiction", "reason": reason}

    return {"approved": True, "stage_blocked": None, "reason": "Passed grounding and contradiction checks"}
