# Nexus — A Security Framework for AI Agentic Systems

[![Tests](https://github.com/YOUR_GITHUB_USERNAME/nexus-agent-security/actions/workflows/tests.yml/badge.svg)](https://github.com/YOUR_GITHUB_USERNAME/nexus-agent-security/actions/workflows/tests.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

A middleware security framework that validates every AI agent tool
call and memory write **before** it executes — designed to catch
prompt injection, tool hijacking, and memory poisoning in autonomous,
tool-using LLM agents.

Built as a Final Year Project at the Department of Computer Science,
University of the Punjab (FCIT), extended into an open-source
prototype.

## The problem

Agent frameworks like LangGraph, AutoGen, and CrewAI let an LLM agent
plan, call tools, and write to shared memory — but execute those
actions directly, with no independent verification. A single
malicious instruction hidden inside a webpage, email, or document the
agent reads can hijack its next action, because tool outputs are fed
back into the model's context as if they were trustworthy.

## The approach

Nexus inserts two checkpoints between the agent and the outside world:

- **Tool Execution Gate** — every tool call is checked against a
  role-based allow-list, then judged by an LLM for whether it
  actually matches the agent's original task.
- **Memory Write Gate** — every memory write is checked for whether
  its source is trustworthy (grounding) and whether it contradicts
  existing memory (contradiction detection).

Every decision — approved or blocked — is written to an append-only
audit log.

See [`docs/architecture.md`](docs/architecture.md) for the full design
and a discussion of its current limitations.

## Quick start (no API key needed)

```bash
git clone https://github.com/YOUR_GITHUB_USERNAME/nexus-agent-security.git
cd nexus-agent-security
pip install -e .
python3 examples/demo_mock.py
```

You'll see an agent do a normal web search, get "tricked" by a hidden
instruction inside the (simulated) result, and have the malicious
follow-up action **blocked automatically** — with the full decision
trail written to `audit_log.jsonl`.

## Running the real version (with an LLM)

```bash
export ANTHROPIC_API_KEY=your_key_here
python3 -m nexus.agent
```

This uses a real LLM both to decide the agent's next action and to
judge whether that action aligns with its original task.

## Running the tests

```bash
pip install -e ".[dev]"
pytest tests/ -v --cov=nexus
```

## Project structure

```
src/nexus/            # the actual package
  tools.py            # simulated agent tools
  memory_store.py      # simple in-memory fact store
  gates/
    tool_execution_gate.py
    memory_write_gate.py
  audit_log.py
  agent.py             # LangGraph wiring
examples/
  demo_mock.py         # runnable demo, no API key required
tests/                 # pytest unit tests
docs/
  architecture.md
.github/workflows/     # CI: runs tests on every push
```

## Roadmap

- [ ] Least-privilege, per-tool credentials
- [ ] Network-layer egress allow-listing
- [ ] Human-approval flow for destructive actions
- [ ] FastAPI wrapper so gates can be called over HTTP / as an MCP server
- [ ] Web dashboard reading from the audit log
- [ ] Attack simulation suite (prompt injection, tool hijacking, memory poisoning) with measured attack-success-rate / false-positive-rate / latency-overhead comparisons

## Team

- Laiba Naveed
- Ayesha Waqar
- Syeda Sadaf Gillani

Supervised by Ms. Irfana Bibi and Dr. Madeeha Aman, Department of
Computer Science, FCIT, University of the Punjab.

## License

MIT — see [LICENSE](LICENSE).
