# Architecture

## Problem

AI agents that autonomously call tools and write to memory can be
manipulated through prompt injection, tool hijacking, and memory
poisoning. Most agent frameworks (LangGraph, AutoGen, CrewAI) execute
these actions directly, with no independent verification step.

## Approach

Nexus sits as a middleware layer between the agent and its tools /
memory. No action executes until it passes through the relevant gate.

```
┌─────────────┐      ┌───────────────────────┐      ┌──────────────┐
│  LangGraph  │────▶ │  Tool Execution Gate   │────▶│  Real Tool    │
│    Agent    │      │  (rule + LLM check)    │      │  (email, DB)  │
└─────────────┘      └───────────────────────┘      └──────────────┘
       │
       │              ┌───────────────────────┐      ┌──────────────┐
       └────────────▶ │  Memory Write Gate     │────▶│  Memory      │
                       │  (grounding +          │      │  Store       │
                       │   contradiction check) │      │              │
                       └───────────────────────┘      └──────────────┘
                                  │
                                  ▼
                       ┌───────────────────────┐
                       │   Append-only          │
                       │   Audit Log            │
                       └───────────────────────┘
```

## Defense layers (in order of cost)

Following current agent-security research, cheap/deterministic checks
run before expensive/probabilistic ones:

1. **Rule-based allow-list** — is this tool even permitted for this
   agent's role? (`tool_execution_gate.rule_based_check`)
2. **LLM-based task-alignment check** — does this action make sense
   given the agent's original task? (`tool_execution_gate.llm_based_check`)
3. **Grounding check** — for memory writes, is the source of this
   fact trustworthy? (`memory_write_gate.grounding_check`)
4. **Contradiction check** — does this fact conflict with something
   already known? (`memory_write_gate.contradiction_check`)

> **Note on limitations:** LLM-based judgment checks are a useful
> additional layer, but research (e.g. *"The Attacker Moves Second,"*
> arXiv:2510.09023) has shown that classifier/judge-style defenses
> alone can be defeated by adaptive attacks. A production version of
> this system should add deterministic containment controls
> (least-privilege credentials per tool, network-level egress
> allow-lists, and human approval for destructive actions) alongside
> the checks implemented here. See `docs/roadmap.md` (planned).

## Why LangGraph

LangGraph models an agent's process as an explicit graph of steps,
which makes it straightforward to insert the gates as their own nodes
in the flow (`gate_check` before `run_tool`), rather than embedding
security logic inside tool-calling code.

## Module map

| Module | Responsibility |
|---|---|
| `nexus.tools` | Simulated tool implementations |
| `nexus.memory_store` | In-memory fact store with contradiction detection |
| `nexus.gates.tool_execution_gate` | Checkpoint before any tool call |
| `nexus.gates.memory_write_gate` | Checkpoint before any memory write |
| `nexus.audit_log` | Append-only record of every gate decision |
| `nexus.agent` | LangGraph graph wiring the agent to both gates |
