"""
Audit-trail specs (PRD nice-to-have: session logging for the fleet pitch).

  FEATURE: Flagged commands are recorded locally as JSONL
    SCENARIO: a flagged command appends one structured record
    SCENARIO: repeated flags append, never overwrite
    SCENARIO: safe commands are never logged
    SCENARIO: audit I/O failures never break evaluation
    SCENARIO: default location is ~/.intentguard/audit.jsonl
"""

import json
import tempfile
import unittest
from pathlib import Path


class AuditLogSpec(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.log_path = Path(self.tmp.name) / "audit.jsonl"
        self.addCleanup(self.tmp.cleanup)

    def test_flagged_command_appends_one_record(self):
        from intentguard.audit import log_flag

        result = {
            "action": "confirm_then_execute",
            "layer": "rule_engine",
            "risk_level": "critical",
            "reason": "rm -rf on root or system directory",
        }
        log_flag("rm -rf /", result, log_path=self.log_path)

        lines = self.log_path.read_text(encoding="utf-8").strip().splitlines()
        self.assertEqual(len(lines), 1)
        rec = json.loads(lines[0])
        for key in ("timestamp", "command", "layer", "risk_level", "reason"):
            self.assertIn(key, rec)
        self.assertEqual(rec["command"], "rm -rf /")
        self.assertEqual(rec["layer"], "rule_engine")
        self.assertEqual(rec["risk_level"], "critical")

    def test_appends_not_overwrites(self):
        from intentguard.audit import log_flag

        r = {"action": "confirm_then_execute", "layer": "classifier",
             "risk_level": "medium", "reason": "ml"}
        log_flag("shred /dev/sda1", r, log_path=self.log_path)
        log_flag("wipefs /dev/sdb", r, log_path=self.log_path)
        self.assertEqual(len(self.log_path.read_text().strip().splitlines()), 2)

    def test_safe_commands_not_logged(self):
        from intentguard.audit import log_flag

        log_flag("ls -la", {"action": "execute"}, log_path=self.log_path)
        self.assertFalse(self.log_path.exists())

    def test_creates_missing_parent_dirs(self):
        from intentguard.audit import log_flag

        nested = Path(self.tmp.name) / "a" / "b" / "audit.jsonl"
        log_flag("rm -rf /",
                 {"action": "confirm_then_execute", "layer": "rule_engine"},
                 log_path=nested)
        self.assertTrue(nested.exists())

    def test_io_failure_never_raises(self):
        from intentguard.audit import log_flag

        blocker = Path(self.tmp.name) / "blocker"
        blocker.write_text("x")
        bad = blocker / "child" / "audit.jsonl"  # mkdir under a file -> error
        log_flag("rm -rf /", {"action": "confirm_then_execute"}, log_path=bad)

    def test_default_log_location(self):
        from intentguard.audit import default_log_path

        self.assertEqual(default_log_path(),
                         Path.home() / ".intentguard" / "audit.jsonl")


if __name__ == "__main__":
    unittest.main()
