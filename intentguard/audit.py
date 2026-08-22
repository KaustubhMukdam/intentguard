"""
Audit trail for IntentGuard (PRD nice-to-have: session logging / fleet pitch).

Appends one JSONL record per flagged command to ~/.intentguard/audit.jsonl.
Best-effort by design: any I/O failure is swallowed so auditing can never
break or slow down command evaluation.
"""

import json
import time
from pathlib import Path


def default_log_path() -> Path:
    return Path.home() / ".intentguard" / "audit.jsonl"


def log_flag(command: str, result: dict, log_path: Path = None) -> None:
    """Append one structured record for a flagged command. Never raises."""
    if result.get("action") != "confirm_then_execute":
        return
    path = Path(log_path) if log_path else default_log_path()
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        record = {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "command": command,
            "layer": result.get("layer", "unknown"),
            "risk_level": result.get("risk_level", "unknown"),
            "reason": result.get("reason", ""),
        }
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(record) + "\n")
    except OSError:
        pass  # best-effort: never break evaluation over logging
