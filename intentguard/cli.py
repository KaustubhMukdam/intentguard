#!/usr/bin/env python3
"""
IntentGuard CLI (thin client)
Spawns/reuses the intentguard daemon and sends one command for evaluation.
Imports only stdlib so per-invocation startup stays ~50ms instead of ~2.8s.

Exit codes (contract with shell/intentguard.sh):
  0 = safe (execute) or flagged + user confirmed (execute)
  1 = flagged + user declined (abort), daemon error, or usage error
"""

import json
import os
import socket
import subprocess
import sys
import time
from pathlib import Path

from intentguard.socketutil import addr, is_unix, socket_path

# Stitch palette -> ANSI (design_prompt.md + design/intentguard/DESIGN.md)
RED = "\033[91m"
AMBER = "\033[33m"
GREEN = "\033[92m"
DIM = "\033[2m"
BOLD = "\033[1m"
RESET = "\033[0m"

RISK_LEVEL_COLOR = {"critical": RED, "high": AMBER, "medium": AMBER}

_PROJECT_ROOT = Path(__file__).resolve().parents[1]
_DAEMON_WAIT_SECONDS = 10.0


def _daemon_alive() -> bool:
    if is_unix():
        if not socket_path().exists():
            return False
        try:
            with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as s:
                s.settimeout(0.5)
                s.connect(str(socket_path()))
            return True
        except OSError:
            return False
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(0.5)
            s.connect(addr())
        return True
    except OSError:
        return False


def _spawn_daemon():
    env = dict(os.environ, PYTHONPATH=str(_PROJECT_ROOT))
    subprocess.Popen(
        [sys.executable, "-m", "intentguard.daemon"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        env=env,
    )


def ensure_daemon(sock: Path) -> bool:
    """Return True when a responsive daemon is available, spawning one if needed."""
    if _daemon_alive():
        return True
    if is_unix() and sock.exists():
        sock.unlink()
    _spawn_daemon()
    deadline = time.monotonic() + _DAEMON_WAIT_SECONDS
    while time.monotonic() < deadline:
        if _daemon_alive():
            return True
        time.sleep(0.1)
    return False


def _roundtrip(s: socket.socket, data: bytes) -> dict:
    s.sendall(data)
    raw = b""
    while b"\n" not in raw:
        chunk = s.recv(65536)
        if not chunk:
            break
        raw += chunk
    return json.loads(raw.split(b"\n", 1)[0])


def _send(payload: dict) -> dict:
    """Send one JSON payload to the daemon; returns the JSON reply."""
    data = (json.dumps(payload) + "\n").encode()
    if is_unix():
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as s:
            s.settimeout(_DAEMON_WAIT_SECONDS)
            s.connect(str(socket_path()))
            return _roundtrip(s, data)
    host, port = addr()
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(_DAEMON_WAIT_SECONDS)
        s.connect((host, port))
        return _roundtrip(s, data)


def eval_via_daemon(command: str) -> dict:
    """Send a command to the daemon; returns the decision dict."""
    return _send({"command": command})


def ask_via_daemon(intent: str) -> dict:
    """NL mode: ask the daemon to suggest a command for an intent (pre-vetted)."""
    return _send({"ask": intent})


def render_warning(result: dict, command: str) -> str:
    """Render the confirmation prompt exactly as judges will see it."""
    risk_color = RISK_LEVEL_COLOR.get(result.get("risk_level", "high"), AMBER)
    explanation = result.get("explanation", {})
    header_color = RED if risk_color == RED else AMBER

    lines = [
        f"{BOLD}{risk_color}⚠️  INTENTGUARD {header_color}FLAGGED THIS COMMAND{RESET}",
        "",
        f"{DIM}Command:{RESET} {command}",
        f"{DIM}Flagged by:{RESET} {result.get('layer', 'unknown')} — {result.get('reason', '')}",
        "",
        f"{DIM}What this does:{RESET}  {explanation.get('what_it_does', 'Unknown')}",
        f"{DIM}Blast radius:{RESET}    {explanation.get('impact', 'Unknown')}",
        f"{GREEN}Safer alternative:{RESET} {explanation.get('safer_alternative', 'None')}",
        "",
        f"{BOLD}Proceed anyway? [y/N]:{RESET} ",
    ]
    return "\n".join(lines)


def warn_if_fallback(result: dict) -> None:
    """stderr hint when the explanation came from local fallback (LLM unreachable)."""
    explanation = result.get("explanation") or {}
    if explanation.get("fallback"):
        print(f"IntentGuard: LLM unavailable ({explanation.get('error', 'unknown')})",
              file=sys.stderr)


def confirm_flow(result: dict, display_cmd: str) -> int:
    """Show the warning, read y/N. Returns process exit code."""
    warn_if_fallback(result)
    prompt = render_warning(result, display_cmd)
    if not sys.stdout.isatty():
        for code in (RED, AMBER, GREEN, DIM, BOLD, RESET):
            prompt = prompt.replace(code, "")

    sys.stdout.write(prompt)
    sys.stdout.flush()

    try:
        answer = input().strip().lower()
    except EOFError:
        answer = "n"
    if answer in ("y", "yes"):
        return 0
    print("Command aborted by IntentGuard")
    return 1


def run_ask(intent: str) -> int:
    """NL mode: suggest a command for the intent — only after it passes the pipeline."""
    sock = socket_path()
    if not ensure_daemon(sock):
        print("IntentGuard: failed to start daemon", file=sys.stderr)
        return 1

    result = ask_via_daemon(intent)
    if result.get("action") == "error":
        print("IntentGuard: no safe suggestion for this intent.",
              file=sys.stderr)
        print(f"  ({result.get('reason', 'unknown')})", file=sys.stderr)
        print('Tip: run a specific command directly: intentguard <command>',
              file=sys.stderr)
        return 1

    cmd = result["command"]
    print(f"Suggested command: {cmd}")
    if result.get("why"):
        print(f"{DIM}{result['why']}{RESET}" if sys.stdout.isatty() else f"({result['why']})")

    verdict = result.get("verdict", {})
    if verdict.get("action") == "execute":
        print("IntentGuard check: safe to run.")
        return 0

    # The suggested command itself was flagged — show the same confirmation UI
    return confirm_flow(verdict, cmd)


def main() -> int:
    args = sys.argv[1:]
    if not args:
        print('Usage: intentguard <command>   |   intentguard --ask "intent"',
              file=sys.stderr)
        return 1

    if args[0] == "--ask":
        if len(args) < 2:
            print('Usage: intentguard --ask "describe your intent"', file=sys.stderr)
            return 1
        return run_ask(" ".join(args[1:]))

    command = " ".join(args)
    sock = socket_path()

    if not ensure_daemon(sock):
        print("IntentGuard: failed to start daemon", file=sys.stderr)
        return 1

    result = eval_via_daemon(command)

    if result.get("action") == "execute":
        return 0
    if result.get("action") == "error":
        print(f"IntentGuard: {result.get('reason', 'error')}", file=sys.stderr)
        return 1

    return confirm_flow(result, command)


if __name__ == "__main__":
    sys.exit(main())