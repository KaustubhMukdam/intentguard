"""
IntentGuard daemon — holds the loaded model + imports so every CLI invocation
doesn't pay sklearn/joblib cold-start (~2.8s). Listens on a Unix socket, one
line-JSON evaluation request per connection.

Speaks with intentguard/cli.py (the thin client). Protocol: receive a line of
JSON {"command": "..."}, reply with a line of JSON decision dict.
"""

import json
import socket
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from intentguard.socketutil import addr, is_unix, socket_path


def evaluate(text: str) -> dict:
    """Evaluate one command through the real pipeline (rule + classifier + LLM)."""
    # Lazy import via import_module: consults sys.modules directly, so resolution
    # truly happens at call time and sklearn/joblib never block daemon startup.
    import importlib
    decision = importlib.import_module("intentguard.decision")
    try:
        result = decision.evaluate_command(text)
    except Exception as e:  # model missing, API/parse error — never crash the loop
        return {"action": "error", "layer": "none", "reason": str(e)}
    # Audit trail (best-effort): one JSONL line per flagged command
    from intentguard.audit import log_flag
    log_flag(text, result)
    return result


def _prewarm():
    """Load the model at startup so the first command isn't slow."""
    try:
        from intentguard.classifier.predict import load_model
        load_model()
    except Exception:
        pass  # no model yet — classifier path will report the error per command


def handle_ask(intent: str) -> dict:
    """NL mode: suggest a command for an intent, then vet it through the pipeline.
    Lives in the daemon because Groq/dotenv are loaded here, not in the thin CLI."""
    from intentguard.llm.client import suggest_command
    sugg = suggest_command(intent)
    if not sugg.get("command"):
        return {"action": "error",
                "reason": f"LLM unavailable ({sugg.get('error', 'no suggestion')})"}
    verdict = evaluate(sugg["command"])
    return {"action": "suggest", "command": sugg["command"],
            "why": sugg.get("why", ""), "verdict": verdict}


def serve():
    unix = is_unix()
    server = socket.socket(socket.AF_UNIX if unix else socket.AF_INET,
                           socket.SOCK_STREAM)
    if unix:
        if socket_path().exists():
            socket_path().unlink()
        server.bind(str(socket_path()))
    else:
        _, port = addr()
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind(("127.0.0.1", port))
    server.listen(16)

    # Bind FIRST so the CLI can connect immediately; prewarm in background.
    # On Windows, importing sklearn + loading the model can take 10-20s on the
    # first run (AV/DLL scanning) — blocking here would make the CLI time out.
    import threading
    threading.Thread(target=_prewarm, daemon=True).start()

    while True:
        conn, _ = server.accept()
        try:
            raw = b""
            while True:
                chunk = conn.recv(8192)
                if not chunk:
                    break
                raw += chunk
                if b"\n" in raw:
                    break
            payload = json.loads(raw.decode().split("\n", 1)[0])
            if "ask" in payload:
                reply = json.dumps(handle_ask(payload["ask"])).encode() + b"\n"
            else:
                reply = json.dumps(evaluate(payload["command"])).encode() + b"\n"
            conn.sendall(reply)
        except Exception:
            pass
        finally:
            conn.close()


if __name__ == "__main__":
    serve()  # binds immediately; _prewarm runs in the background thread inside serve()