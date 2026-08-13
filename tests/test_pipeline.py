"""
Unit tests for IntentGuard decision engine
"""

import unittest
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'intentguard'))

from intentguard.decision import evaluate_command

class TestDecisionEngine(unittest.TestCase):
    
    def test_safe_command(self):
        """Test that safe commands return execute action"""
        result = evaluate_command("ls -la")
        self.assertIn(result["action"], ["execute"])
        selfEqual(result["layer"], "none")
        
    def test_dangerous_command_rule_engine(self):
        """Test that dangerous commands trigger confirmation"""
        result = evaluate_command("rm -rf /")
        # Should be confirm_then_execute due to rule engine match
        self.assertEqual(result["action"], "confirm_then_execute")
        self.assertEqual(result["layer"], "rule_engine")
        
    def test_another_dangerous_command(self):
        """Test another dangerous command"""
        result = evaluate_command("dd if=/dev/zero of=/dev/sda")
        self.assertEqual(result["action"], "confirm_then_execute")
        self.assertEqual(result["layer"], "rule_engine")

if __name__ == "__main__":
    unittest.main()