"""
IntentGuard daemon — holds the loaded model + imports so every CLI invocation
doesn't pay sklearn/joblib cold-start (~2.8s). Listens on a Unix socket, one
line-JSON evaluation request per connection.

Speaks with intentguard/cli.py (the thin client). Protocol: receive a line of
JSON {"command": "..."}, reply with a line of JSON decision dict.
"""

import json
import socket
import tempfile
import hashlib
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from intentguard import decision


def socket_path() -> Path:
    """Repo-scoped socket in the temp dir so parallel checkouts don't collide."""
    root = str(Path(__file__).resolve().parents[1]).encode()
    tag = hashlib.md5(root).hexdigest()[:8]
    return Path(tempfile.gettempdir()) / f"intentguard-{tag}.sock"


def evaluate(text: str) -> dict:
    """Evaluate one command through the real pipeline (rule + classifier + LLM)."""
    try:
        return decision.evaluate_command(text)
    except Exception as e:  # model missing, API/parse error — never crash the loop
        return {"action": "error", "layer": "none", "reason": str(e)}


def _prewarm():
    """Load the model at startup so the first command isn't slow."""
    try:
        from intentguard.classifier.predict import load_model
        load_model()
    except Exception:
        pass  # no model yet — classifier path will report the error per command


def serve(sock_path: Path):
    if sock_path.exists():
        sock_path.unlink()
    server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    server.bind(str(sock_path))
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
            text = json.loads(raw.decode().split("\n", 1)[0])["command"]
            reply = json.dumps(evaluate(text)).encode() + b"\n"
            conn.sendall(reply)
        except Exception:
            pass
        finally:
            conn.close()


if __name__ == "__main__":
    _prewarm()
    serve(socket_path())