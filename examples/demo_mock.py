"""
demo_mock.py
-------------
A self-contained demo that does NOT call a real LLM API - it fakes the
"agent thinking" and "AI check" steps with simple logic, so anyone
cloning this repo can see the full attack-and-block flow immediately
with no API key required.

Run from the repo root with:
    python3 examples/demo_mock.py

For the real version that uses an actual LLM, see src/nexus/agent.py
(requires ANTHROPIC_API_KEY to be set).
"""

import sys
import os

# Allow running this script directly from examples/ without installing
# the package.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from typing import TypedDict, Optional
from langgraph.graph import StateGraph, END

from nexus.tools import AVAILABLE_TOOLS
from nexus.gates.memory_write_gate import check_memory_write
from nexus.memory_store import MemoryStore
from nexus.audit_log import log_decision

memory = MemoryStore()

ALLOWED_TOOLS_BY_ROLE = {
    "research_assistant": ["search_web", "send_email"],
}


class AgentState(TypedDict):
    task: str
    agent_role: str
    tool_name: Optional[str]
    tool_args: Optional[dict]
    tool_result: Optional[str]
    gate_decision: Optional[dict]
    blocked: bool
    step: int
    max_steps: int


def think_node(state: AgentState) -> AgentState:
    """
    Step 0: a normal, safe search.
    Step 1: simulates the agent being tricked by a hidden instruction
    inside the step-0 search result into trying to delete a file -
    a scripted stand-in for a prompt injection attack.
    """
    if state["step"] == 0:
        state["tool_name"] = "search_web"
        state["tool_args"] = {"query": "weather in Lahore"}
    elif state["step"] == 1:
        state["tool_name"] = "delete_file"
        state["tool_args"] = {"filename": "payroll.db"}

    print(f"[AGENT] Wants to call: {state['tool_name']}({state['tool_args']})")
    return state


def fake_llm_based_check(original_task: str, tool_name: str, tool_args: dict) -> tuple[bool, str]:
    task_lower = original_task.lower()
    if tool_name == "delete_file" and "delete" not in task_lower and "clean" not in task_lower:
        return False, ("This looks like a prompt injection attack: the task never asked "
                        "to delete anything, but the agent is trying to delete a file.")
    return True, "Action matches the original task"


def rule_based_check(agent_role: str, tool_name: str) -> tuple[bool, str]:
    allowed = ALLOWED_TOOLS_BY_ROLE.get(agent_role, [])
    if tool_name not in allowed:
        return False, f"Rule check failed: '{tool_name}' is not allowed for role '{agent_role}'"
    return True, "Rule check passed"


def gate_check_node(state: AgentState) -> AgentState:
    rule_ok, rule_reason = rule_based_check(state["agent_role"], state["tool_name"])
    if not rule_ok:
        decision = {"approved": False, "stage_blocked": "rule_based", "reason": rule_reason}
    else:
        llm_ok, llm_reason = fake_llm_based_check(state["task"], state["tool_name"], state["tool_args"])
        decision = (
            {"approved": True, "stage_blocked": None, "reason": "Passed rule + AI check"}
            if llm_ok else
            {"approved": False, "stage_blocked": "llm_based", "reason": llm_reason}
        )

    state["gate_decision"] = decision
    log_decision("tool_call", {"tool_name": state["tool_name"], "tool_args": state["tool_args"]}, decision)
    state["blocked"] = not decision["approved"]
    return state


def run_tool_node(state: AgentState) -> AgentState:
    tool_fn = AVAILABLE_TOOLS[state["tool_name"]]
    result = tool_fn(**state["tool_args"])
    state["tool_result"] = result

    if state["tool_name"] == "search_web":
        mem_decision = check_memory_write(memory, content=result, source="web_content")
        log_decision("memory_write", {"content": result}, mem_decision)
        if mem_decision["approved"]:
            memory.write(result, source="web_content")
        else:
            print(f"[MEMORY GATE] Blocked saving web content: {mem_decision['reason']}")

    state["step"] += 1
    return state


def blocked_node(state: AgentState) -> AgentState:
    print(f"[BLOCKED] Action stopped: {state['gate_decision']['reason']}")
    state["step"] += 1
    return state


def route_after_gate(state: AgentState):
    return "blocked" if state["blocked"] else "run_tool"


def route_after_action(state: AgentState):
    return END if state["step"] >= state["max_steps"] else "think"


def build_graph():
    graph = StateGraph(AgentState)
    graph.add_node("think", think_node)
    graph.add_node("gate_check", gate_check_node)
    graph.add_node("run_tool", run_tool_node)
    graph.add_node("blocked", blocked_node)

    graph.set_entry_point("think")
    graph.add_edge("think", "gate_check")
    graph.add_conditional_edges("gate_check", route_after_gate, {"blocked": "blocked", "run_tool": "run_tool"})
    graph.add_conditional_edges("run_tool", route_after_action, {"think": "think", END: END})
    graph.add_conditional_edges("blocked", route_after_action, {"think": "think", END: END})

    return graph.compile()


if __name__ == "__main__":
    print("=" * 70)
    print("DEMO: agent does a normal search, then gets 'tricked' by hidden")
    print("instructions in the search result into trying to delete a file.")
    print("Watch the Tool Execution Gate catch and block step 2.")
    print("=" * 70)

    app = build_graph()
    result = app.invoke({
        "task": "Find the weather in Lahore",
        "agent_role": "research_assistant",
        "tool_name": None,
        "tool_args": None,
        "tool_result": None,
        "gate_decision": None,
        "blocked": False,
        "step": 0,
        "max_steps": 2,
    })

    print("\n" + "=" * 70)
    print("DONE. Check audit_log.jsonl to see the full record of what happened.")
