"""
NL-mode specs (PRD nice-to-have: type intent, get a safe command suggestion).

  FEATURE: --ask "intent" suggests a command
    SCENARIO: LLM returns JSON {command} and it is surfaced
    SCENARIO: prompt carries the intent and demands strict JSON
    SCENARIO: API failure degrades to an explicit no-suggestion
"""

import unittest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from tests.test_llm import make_groq_fake


class SuggestCommandSpec(unittest.TestCase):

    def test_returns_suggested_command(self):
        from intentguard.llm.client import suggest_command

        content = '{"command": "df -h", "why": "shows human-readable disk usage"}'
        factory, _ = make_groq_fake(content)
        result = suggest_command("show disk usage", client_factory=factory)
        self.assertEqual(result["command"], "df -h")
        self.assertEqual(result["why"], "shows human-readable disk usage")

    def test_prompt_contains_intent_and_json_contract(self):
        from intentguard.llm.client import suggest_command
        from intentguard.llm.prompts import get_command_suggestion_prompt

        factory, capture = make_groq_fake('{"command": "ls", "why": ""}')
        suggest_command("list files by size", client_factory=factory)
        sent = capture()["messages"][0]["content"]
        self.assertIn("list files by size", sent)
        self.assertIn('"command"', sent)

        prompt = get_command_suggestion_prompt("show disk usage")
        self.assertIn("show disk usage", prompt)
        self.assertIn("JSON", prompt)

    def test_api_failure_yields_no_suggestion(self):
        from intentguard.llm.client import suggest_command

        def broken():
            raise RuntimeError("offline")
        result = suggest_command("anything", client_factory=broken)
        self.assertIsNone(result["command"])
        self.assertTrue(result.get("fallback"))


if __name__ == "__main__":
    unittest.main()
