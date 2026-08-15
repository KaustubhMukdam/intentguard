"""
BDD specs for the IntentGuard 3-layer pipeline (decision.py).

  FEATURE: Rule Engine -> Classifier -> LLM routing
    SCENARIO: Known-catastrophic command -> flagged by rule engine, skips classifier
    SCENARIO: Ambiguous command -> judged by classifier
    SCENARIO: Everyday safe command -> passes through invisibly
"""

import unittest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from intentguard import decision


class FakeExplainer:
    def __call__(self, command, flagged_by, reason, risk_level="high"):
        return {
            "what_it_does": "fake explanation for " + command,
            "impact": "fake impact",
            "safer_alternative": "fake alternative",
            "_flagged_by": flagged_by,
        }


class PipelineRoutingSpec(unittest.TestCase):
    """SCENARIO: routing through the 3 layers"""

    def setUp(self):
        self.explain = FakeExplainer()

    def test_rule_engine_match_skips_classifier(self):
        result = decision.evaluate_command("rm -rf /", explain_fn=self.explain)
        self.assertEqual(result["action"], "confirm_then_execute")
        self.assertEqual(result["layer"], "rule_engine")
        self.assertEqual(result["risk_level"], "critical")
        # classifier is skipped on rule match — no confidence key present
        self.assertNotIn("confidence", result)
        self.assertEqual(result["explanation"]["_flagged_by"], "rule_engine")

    def test_classifier_flags_ambiguous_risky_command(self):
        # 'shred /dev/sda1' is not a rule pattern but the classifier learned it risky
        result = decision.evaluate_command("shred /dev/sda1", explain_fn=self.explain)
        self.assertEqual(result["action"], "confirm_then_execute")
        self.assertEqual(result["layer"], "classifier")
        self.assertIn("confidence", result)
        self.assertEqual(result["explanation"]["_flagged_by"], "classifier")

    def test_safe_command_passes_through(self):
        result = decision.evaluate_command("ls -la", explain_fn=self.explain)
        self.assertEqual(result["action"], "execute")
        self.assertEqual(result["layer"], "none")
        self.assertNotIn("explanation", result)

    def test_more_safe_commands_pass(self):
        for cmd in ["git status", "pip install requests", "df -h", "cat file.txt"]:
            result = decision.evaluate_command(cmd, explain_fn=self.explain)
            self.assertEqual(result["action"], "execute", cmd)

    def test_rule_engine_catches_more_destructive(self):
        for cmd in ["dd if=/dev/zero of=/dev/sda", "chmod -R 777 /", ":(){ :|:& };:"]:
            result = decision.evaluate_command(cmd, explain_fn=self.explain)
            self.assertEqual(result["layer"], "rule_engine", cmd)

    def test_quoted_dangerous_command_is_caught(self):
        for cmd in ["rm -rf '/'", 'rm -rf "/"', "rm -rf '/etc/*'"]:
            result = decision.evaluate_command(cmd, explain_fn=self.explain)
            self.assertEqual(result["action"], "confirm_then_execute", cmd)
            self.assertEqual(result["layer"], "rule_engine", cmd)

    def test_sudo_prefixed_dangerous_command_is_caught(self):
        for cmd in ["sudo rm -rf /", "sudo dd if=/dev/zero of=/dev/sda"]:
            result = decision.evaluate_command(cmd, explain_fn=self.explain)
            self.assertEqual(result["action"], "confirm_then_execute", cmd)
            self.assertEqual(result["layer"], "rule_engine", cmd)

    def test_chained_dangerous_command_is_caught(self):
        for cmd in ["rm -rf / && echo ok", "rm -rf /etc; echo ok", "echo hi | rm -rf /"]:
            result = decision.evaluate_command(cmd, explain_fn=self.explain)
            self.assertEqual(result["action"], "confirm_then_execute", cmd)
            self.assertEqual(result["layer"], "rule_engine", cmd)

    def test_longform_and_combined_rm_flags_are_caught(self):
        for cmd in ["rm --recursive --force /etc", "rm -rfv /boot"]:
            result = decision.evaluate_command(cmd, explain_fn=self.explain)
            self.assertEqual(result["action"], "confirm_then_execute", cmd)
            self.assertEqual(result["layer"], "rule_engine", cmd)

    def test_firewalld_disable_is_caught_not_generic_service_stops(self):
        result = decision.evaluate_command("systemctl stop firewalld", explain_fn=self.explain)
        self.assertEqual(result["action"], "confirm_then_execute")
        self.assertEqual(result["layer"], "rule_engine")
        for safe_cmd in ["systemctl stop nginx", "systemctl disable cron", "service ssh restart"]:
            safe = decision.evaluate_command(safe_cmd, explain_fn=self.explain)
            self.assertEqual(safe["action"], "execute", safe_cmd)

    def test_chained_safe_commands_pass(self):
        for cmd in ["ls -la && echo hi", "cat file | grep foo", "cd /tmp && pwd"]:
            result = decision.evaluate_command(cmd, explain_fn=self.explain)
            self.assertEqual(result["action"], "execute", cmd)


class LatencySpec(unittest.TestCase):
    """SCENARIO: flagged path stays far under the ~3s budget (local, CPU only)."""

    def test_pipeline_latency_without_llm_is_milliseconds(self):
        import time
        from intentguard import decision as d

        fake = lambda cmd, *a, **k: {"what_it_does": "x", "impact": "y", "safer_alternative": "z"}
        d.evaluate_command("ls -la", explain_fn=fake)  # warmup cache

        for cmd in ["ls -la", "rm -rf /", "shred /dev/sda1"]:
            t0 = time.perf_counter()
            d.evaluate_command(cmd, explain_fn=fake)
            elapsed = time.perf_counter() - t0
            self.assertLess(elapsed, 0.5, f"{cmd} took {elapsed:.3f}s")


if __name__ == "__main__":
    unittest.main()
