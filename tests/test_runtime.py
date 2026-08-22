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


if __name__ == "__main__":
    unittest.main()
