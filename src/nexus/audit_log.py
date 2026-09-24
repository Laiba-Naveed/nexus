"""
audit_log.py
-------------
Records every decision made by either gate, so you can show a company
"here is exactly what we blocked, and why" - this is your compliance /
audit trail feature.
"""

import json
import datetime

LOG_FILE = "audit_log.jsonl"


def log_decision(action_type: str, details: dict, decision: dict):
    entry = {
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "action_type": action_type,   # "tool_call" or "memory_write"
        "details": details,
        "approved": decision["approved"],
        "stage_blocked": decision.get("stage_blocked"),
        "reason": decision["reason"],
    }
    with open(LOG_FILE, "a") as f:
        f.write(json.dumps(entry) + "\n")

    status = "APPROVED" if entry["approved"] else "BLOCKED"
    print(f"[AUDIT LOG] {status} | {action_type} | {entry['reason']}")
    return entry


def read_all_logs():
    entries = []
    try:
        with open(LOG_FILE, "r") as f:
            for line in f:
                entries.append(json.loads(line))
    except FileNotFoundError:
        pass
    return entries
