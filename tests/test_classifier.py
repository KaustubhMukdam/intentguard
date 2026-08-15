"""
BDD specs for the IntentGuard ML classifier.

Acceptance criteria (from PRD + eval.md):
  FEATURE: ML intent classifier
    SCENARIO: Novel/ambiguous dangerous commands are scored risky
    SCENARIO: Everyday safe commands are scored safe
    SCENARIO: Model is a real trained artifact that loads locally (no cloud)
"""

import unittest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from intentguard.classifier.predict import predict_command, MODEL_PATH


class ClassifierSpec(unittest.TestCase):
    """SCENARIO: dangerous and safe commands are scored correctly"""

    @classmethod
    def setUpClass(cls):
        if not os.path.exists(MODEL_PATH):
            raise unittest.SkipTest(
                "model.joblib not present — run "
                "`python -m intentguard.classifier.train` first"
            )

    def test_obvious_dangerous_commands_are_risky(self):
        for cmd in ["rm -rf /boot", "dd if=/dev/zero of=/dev/sda", "chmod -R 777 /etc"]:
            self.assertEqual(predict_command(cmd)["label"], "risky", cmd)

    def test_everyday_safe_commands_are_safe(self):
        for cmd in ["ls -la", "git status", "pip install requests", "df -h", "cat file.txt"]:
            self.assertEqual(predict_command(cmd)["label"], "safe", cmd)

    def test_novel_dangerous_command(self):
        result = predict_command("wipefs --all /dev/sdb1")
        self.assertEqual(result["label"], "risky")

    def test_model_is_local_file(self):
        self.assertTrue(os.path.exists(MODEL_PATH))
        self.assertTrue(str(MODEL_PATH).endswith(".joblib"))

    def test_predict_returns_expected_shape(self):
        result = predict_command("ls")
        for key in ("label", "confidence", "is_risky"):
            self.assertIn(key, result)


if __name__ == "__main__":
    unittest.main()
