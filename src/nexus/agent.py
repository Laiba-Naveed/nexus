"""
agent.py
---------
The LangGraph agent that routes every tool call and memory write
through Nexus's two security gates before anything executes.

Graph flow:
  1. "think"       -> LLM decides which tool to call next
  2. "gate_check"  -> Tool Execution Gate checks that decision
  3. "run_tool"    -> if approved, the real tool runs
  4. "blocked"     -> if not approved, we stop and record why

This is the middleware layer described in the Nexus FYP proposal,
implemented as an explicit step in a LangGraph flow rather than
bolted on after the fact.
"""

import json
from typing import TypedDict, Optional
from langgraph.graph import StateGraph, END
from anthropic import Anthropic

from nexus.tools import AVAILABLE_TOOLS
from nexus.gates.tool_execution_gate import check_tool_call
from nexus.gates.memory_write_gate import check_memory_write
from nexus.memory_store import MemoryStore
from nexus.audit_log import log_decision

client = Anthropic()  # reads ANTHROPIC_API_KEY from environment
memory = MemoryStore()


class AgentState(TypedDict):
    task: str
    agent_role: str
    tool_name: Optional[str]
    tool_args: Optional[dict]
    tool_result: Optional[str]
    gate_decision: Optional[dict]
    blocked: bool


def think_node(state: AgentState) -> AgentState:
    prompt = f"""You are an AI agent with role '{state['agent_role']}'.
Your task: "{state['task']}"

Available tools: search_web(query), send_email(to, subject, body), delete_file(filename)

Decide the SINGLE next tool call to make progress on the task.
Respond ONLY with JSON: {{"tool_name": "...", "tool_args": {{...}}}}
"""
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=200,
        messages=[{"role": "user", "content": prompt}],
    )
    raw = response.content[0].text.strip().replace("```json", "").replace("```", "").strip()
    decision = json.loads(raw)

    state["tool_name"] = decision["tool_name"]
    state["tool_args"] = decision["tool_args"]
    print(f"[AGENT] Wants to call: {state['tool_name']}({state['tool_args']})")
    return state


def gate_check_node(state: AgentState) -> AgentState:
    decision = check_tool_call(
        agent_role=state["agent_role"],
        original_task=state["task"],
        tool_name=state["tool_name"],
        tool_args=state["tool_args"],
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

    return state


def blocked_node(state: AgentState) -> AgentState:
    print(f"[BLOCKED] Action stopped: {state['gate_decision']['reason']}")
    return state


def build_graph():
    graph = StateGraph(AgentState)
    graph.add_node("think", think_node)
    graph.add_node("gate_check", gate_check_node)
    graph.add_node("run_tool", run_tool_node)
    graph.add_node("blocked", blocked_node)

    graph.set_entry_point("think")
    graph.add_edge("think", "gate_check")
    graph.add_conditional_edges(
        "gate_check",
        lambda state: "blocked" if state["blocked"] else "run_tool",
        {"blocked": "blocked", "run_tool": "run_tool"},
    )
    graph.add_edge("run_tool", END)
    graph.add_edge("blocked", END)

    return graph.compile()


if __name__ == "__main__":
    app = build_graph()
    result = app.invoke({
        "task": "Find information about the weather in Lahore",
        "agent_role": "research_assistant",
        "tool_name": None,
        "tool_args": None,
        "tool_result": None,
        "gate_decision": None,
        "blocked": False,
    })
    print("\nFINAL STATE:", result)
