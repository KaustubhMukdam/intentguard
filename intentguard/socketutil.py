"""
Portable IPC endpoint for IntentGuard.

Unix sockets are the fast path on Linux/WSL (AF_UNIX). Native Windows Python
(3.11) has no AF_UNIX support, so we fall back to a repo-scoped TCP loopback
port. Both daemon and CLI resolve the same endpoint so they always agree.
"""

import hashlib
import socket
import sys
import tempfile
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parents[1]
_TCP_PORT = 45670


def is_unix() -> bool:
    return sys.platform != "win32"


def socket_path() -> Path:
    """Unix socket path (Linux/WSL only)."""
    tag = hashlib.md5(str(_PROJECT_ROOT).encode()).hexdigest()[:8]
    return Path(tempfile.gettempdir()) / f"intentguard-{tag}.sock"


def addr() -> tuple:
    """Portable endpoint: ('', port) for the daemon bind, ('127.0.0.1', port) for the client."""
    if is_unix():
        return (str(socket_path()), 0)
    return ("127.0.0.1", _TCP_PORT)


def code_version() -> str:
    """Hash of the package source — lets CLI detect stale daemons after edits."""
    h = hashlib.md5()
    root = Path(__file__).resolve().parent
    for p in sorted(root.rglob("*.py")):
        if "__pycache__" in p.parts:
            continue
        h.update(p.read_bytes())
    return h.hexdigest()[:8]
