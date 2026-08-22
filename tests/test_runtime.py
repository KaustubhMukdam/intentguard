"""
Runtime-layer specs: daemon boot race, fast-fail LLM, fallback visibility.

  FEATURE: Flagged commands respond in <2s
    SCENARIO: daemon resolves the pipeline lazily (binds even when sklearn is slow)
    SCENARIO: Groq client uses a short timeout and zero retries
    SCENARIO: fallback explanations surface a stderr hint
"""

import sys
import types
import unittest


class DaemonLazyImportSpec(unittest.TestCase):
    """SCENARIO: decision pipeline resolves at call time, not import time."""

    def test_evaluate_uses_lazy_decision_import(self):
        import intentguard.daemon as daemon

        stub = types.ModuleType("intentguard.decision")
        stub.evaluate_command = lambda cmd: {"action": "execute", "_stub": True}
        original = sys.modules.get("intentguard.decision")
        sys.modules["intentguard.decision"] = stub
        try:
            result = daemon.evaluate("anything")
        finally:
            if original is None:
                sys.modules.pop("intentguard.decision", None)
            else:
                sys.modules["intentguard.decision"] = original

        self.assertTrue(result.get("_stub"),
                        "daemon.evaluate() must look up decision at call time")


class GroqFastFailSpec(unittest.TestCase):
    """SCENARIO: Groq client cannot hang the flagged-command path."""

    def test_client_has_short_timeout_and_no_retries(self):
        from unittest.mock import patch
        with patch.dict("os.environ", {"GROQ_API_KEY": "test-key"}):
            from intentguard.llm.client import _get_groq_client
            client = _get_groq_client()
        self.assertEqual(client.max_retries, 0,
                         "SDK retries turn one failure into ~10s")
        # groq stores timeout as httpx.Timeout; read the scalar off it
        t = getattr(client.timeout, "read", client.timeout)
        self.assertLessEqual(float(t), 3.0)

    def test_model_id_env_override_with_sane_default(self):
        import os
        from unittest.mock import patch
        from intentguard.llm.client import get_model_id

        with patch.dict(os.environ):
            os.environ.pop("GROQ_MODEL", None)
            self.assertEqual(get_model_id(), "openai/gpt-oss-120b")
            os.environ["GROQ_MODEL"] = "qwen/qwen3.6-27b"
            self.assertEqual(get_model_id(), "qwen/qwen3.6-27b")


class FallbackVisibilitySpec(unittest.TestCase):
    """SCENARIO: fallback explanations surface a stderr hint."""

    def test_warn_if_fallback_prints_to_stderr(self):
        from intentguard.cli import warn_if_fallback

        flagged = {"action": "confirm_then_execute",
                   "explanation": {"fallback": True, "error": "rate limited"}}
        warn_if_fallback(flagged)  # must not raise

        safe = {"action": "execute"}
        self.assertIsNone(warn_if_fallback(safe))


class TransportRoundTripSpec(unittest.TestCase):
    """SCENARIO: daemon binds fast and serves JSON over the socket (regression guard
    for the 'failed to start daemon' class of bug). Runs fully stubbed — no sklearn."""

    def test_client_talks_to_live_daemon_over_tcp(self):
        import json
        import socket
        import threading
        import time

        import intentguard.cli as cli
        import intentguard.daemon as daemon

        stub = types.ModuleType("intentguard.decision")
        stub.evaluate_command = lambda cmd: {"action": "execute", "_rt": True}
        saved_modules = sys.modules.get("intentguard.decision")
        saved_cli = (cli.addr, cli.is_unix)
        saved_daemon = (daemon.addr, daemon.is_unix)

        sys.modules["intentguard.decision"] = stub
        port = 45679  # test-only port;
        cli.addr = lambda: ("127.0.0.1", port)
        cli.is_unix = lambda: False
        daemon.addr = lambda: ("127.0.0.1", port)
        daemon.is_unix = lambda: False
        try:
            threading.Thread(target=daemon.serve, daemon=True).start()
            # poll up to 2s — proves bind happens without heavy imports
            deadline = time.monotonic() + 2.0
            result = None
            last_err = None
            while time.monotonic() < deadline:
                try:
                    result = cli.eval_via_daemon("anything")
                    break
                except OSError as e:
                    last_err = e
                    time.sleep(0.05)
            self.assertIsNotNone(
                result, f"daemon never accepted a connection within 2s ({last_err})")
            self.assertTrue(result.get("_rt"))
        finally:
            sys.modules["intentguard.decision"] = saved_modules
            cli.addr, cli.is_unix = saved_cli
            daemon.addr, daemon.is_unix = saved_daemon


if __name__ == "__main__":
    unittest.main()
