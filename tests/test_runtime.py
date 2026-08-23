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

    def test_evaluate_returns_error_when_pipeline_import_fails(self):
        """Missing deps (e.g. bare WSL python) must yield an error reply,
        never crash the serve loop with an empty response."""
        from unittest.mock import patch

        import intentguard.daemon as daemon

        def boom(name, *a, **k):
            raise ModuleNotFoundError("No module named 'joblib'")
        with patch("importlib.import_module", side_effect=boom):
            result = daemon.evaluate("rm -rf /")
        self.assertEqual(result.get("action"), "error")
        self.assertIn("joblib", result.get("reason", ""))


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


class AskArgParsingSpec(unittest.TestCase):
    """SCENARIO: --ask must work identically typed directly OR through the
    bash wrapper (printf %q glues '--ask' and the intent into one argv word)."""

    def test_direct_form(self):
        from intentguard.cli import parse_ask_intent
        self.assertEqual(parse_ask_intent(["--ask", "show disk usage"]),
                         "show disk usage")

    def test_wrapper_glued_form_with_escapes(self):
        from intentguard.cli import parse_ask_intent
        self.assertEqual(
            parse_ask_intent(["--ask show\\ disk\\ usage\\ in\\ human\\ readable\\ form"]),
            "show disk usage in human readable form")

    def test_non_ask_returns_none(self):
        from intentguard.cli import parse_ask_intent
        self.assertIsNone(parse_ask_intent(["ls", "-la"]))

    def test_bare_ask_returns_none(self):
        from intentguard.cli import parse_ask_intent
        self.assertIsNone(parse_ask_intent(["--ask"]))


class InputNormalizationSpec(unittest.TestCase):
    """SCENARIO: wrapper sends ONE %q-escaped argv word ('rm -rf x\\ y ');
    downstream must get per-token shell-quoted form so spaced paths stay ONE
    target for the rules AND read unambiguously to the LLM."""

    def test_single_escaped_word_unwrapped_and_grouped(self):
        from intentguard.cli import normalize_input_command
        self.assertEqual(normalize_input_command(["rm -rf ig\\ test\\ dir"]),
                         "rm -rf 'ig test dir'")

    def test_multi_word_args_keep_true_boundaries(self):
        from intentguard.cli import normalize_input_command
        self.assertEqual(normalize_input_command(["rm", "-rf", "my dir"]),
                         "rm -rf 'my dir'")

    def test_plain_single_word_unchanged(self):
        from intentguard.cli import normalize_input_command
        self.assertEqual(normalize_input_command(["ls"]), "ls")

    def test_output_still_matches_rules(self):
        """Quoted output must not break rule matching (rules shlex-split it)."""
        from intentguard.cli import normalize_input_command
        from intentguard.rules import check_rule_match

        cmd = normalize_input_command(["rm -rf /home/k/ig\\ test\\ dir"])
        self.assertEqual(cmd, "rm -rf '/home/k/ig test dir'")
        # /home is a protected system root -> critical tier wins (documented)
        self.assertEqual(check_rule_match(cmd)["risk_level"], "critical")

        # non-system spaced path -> the medium recursive-force net
        proj = normalize_input_command(["rm", "-rf", "build output"])
        self.assertEqual(proj, "rm -rf 'build output'")
        result = check_rule_match(proj)
        self.assertTrue(result["matched"])
        self.assertEqual(result["risk_level"], "medium")


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


class DaemonProtocolSpec(unittest.TestCase):
    """SCENARIO: stale daemons restart themselves — CLI pings the daemon's code
    version; on mismatch it sends shutdown instead of talking to old code."""

    _next_port = 45681  # unique port per test — leaked daemons from earlier
    # tests must never collide (Windows SO_REUSEADDR allows double binds)

    def setUp(self):
        import intentguard.cli as cli
        import intentguard.daemon as daemon
        self.cli, self.daemon = cli, daemon

        type(self)._next_port += 1
        self.port = type(self)._next_port

        stub = types.ModuleType("intentguard.decision")
        stub.evaluate_command = lambda cmd: {"action": "execute"}
        self.saved_modules = sys.modules.get("intentguard.decision")
        sys.modules["intentguard.decision"] = stub

        self.saved_cli = (cli.addr, cli.is_unix)
        self.saved_daemon = (daemon.addr, daemon.is_unix)
        cli.addr = lambda: ("127.0.0.1", self.port)
        cli.is_unix = lambda: False
        daemon.addr = lambda: ("127.0.0.1", self.port)
        daemon.is_unix = lambda: False

    def tearDown(self):
        sys.modules["intentguard.decision"] = self.saved_modules
        self.cli.addr, self.cli.is_unix = self.saved_cli
        self.daemon.addr, self.daemon.is_unix = self.saved_daemon

    def _start(self):
        import threading
        threading.Thread(target=self.daemon.serve, daemon=True).start()

    def test_ping_reports_current_code_version(self):
        import time
        from intentguard.socketutil import code_version

        self._start()
        deadline = time.monotonic() + 2.0
        last = None
        while time.monotonic() < deadline:
            try:
                reply = self.cli._send({"ping": 1})
                break
            except OSError as e:
                last = e
                time.sleep(0.05)
        else:
            self.fail(f"daemon never came up ({last})")
        self.assertEqual(reply.get("version"), code_version())

    def test_ping_reports_version_captured_at_startup(self):
        """The daemon must answer with the version snapshotted when IT started,
        not re-hash disk at ping time — otherwise stale in-memory code always
        'matches' and never restarts (regression guard for exactly that bug)."""
        import time
        from unittest.mock import patch
        from intentguard import socketutil

        startup_version = socketutil.code_version()
        self._start()
        deadline = time.monotonic() + 2.0
        last = None
        while time.monotonic() < deadline:
            try:
                reply = self.cli._send({"ping": 1})
                break
            except OSError as e:
                last = e
                time.sleep(0.05)
        else:
            self.fail(f"daemon never came up ({last})")

        # simulate code edits AFTER daemon boot: disk hash changes
        with patch.object(socketutil, "code_version", lambda: "CHANGED"):
            self.assertEqual(reply.get("version"), startup_version)
            self.assertNotEqual(reply.get("version"), "CHANGED")

    def test_shutdown_stops_the_daemon(self):
        import socket
        import time

        self._start()
        deadline = time.monotonic() + 2.0
        while time.monotonic() < deadline:
            try:
                self.cli._send({"ping": 1})
                break
            except OSError:
                time.sleep(0.05)

        reply = self.cli._send({"shutdown": 1})
        self.assertTrue(reply.get("bye"))

        # port must stop accepting shortly after
        gone = False
        deadline = time.monotonic() + 2.0
        while time.monotonic() < deadline:
            try:
                with socket.create_connection(("127.0.0.1", self.port), timeout=0.3):
                    time.sleep(0.05)
            except OSError:
                gone = True
                break
        self.assertTrue(gone, "daemon still accepting after shutdown")


if __name__ == "__main__":
    unittest.main()
