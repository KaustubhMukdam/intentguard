"""
BDD specs for the IntentGuard LLM explanation layer.

  FEATURE: LLM explanation generation
    SCENARIO: A flagged command produces a structured explanation
    SCENARIO: API failures fall back to a local explanation (never stalls)
"""

import unittest
import sys
import os
from unittest.mock import Mock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from intentguard.llm.client import explain_command, get_fallback_explanation
from intentguard.llm.prompts import get_explanation_prompt


def make_groq_fake(response_content: str):
    """Return (client_factory, dict_to_inspect_calls)."""
    calls = {}
    client = Mock()
    client.chat.completions.create = Mock(
        return_value=Mock(
            choices=[Mock(message=Mock(content=response_content))]
        )
    )

    def factory():
        return client

    def capture():
        calls["messages"] = client.chat.completions.create.call_args.kwargs["messages"]
        return calls

    return factory, capture


class ExplainerSpec(unittest.TestCase):
    """SCENARIO: flagged command -> structured explanation"""

    def test_returns_structured_fields(self):
        content = ('{"what_it_does": "Deletes all files under /etc", '
                   '"impact": "System config lost", '
                   '"safer_alternative": "sudo apt clean"}')
        factory, _ = make_groq_fake(content)
        result = explain_command("rm -rf /etc/*", "rule_engine", "rm on system dir", client_factory=factory)
        self.assertEqual(result["what_it_does"], "Deletes all files under /etc")
        self.assertEqual(result["impact"], "System config lost")
        self.assertEqual(result["safer_alternative"], "sudo apt clean")

    def test_prompt_includes_command_and_reason(self):
        factory, capture = make_groq_fake('{}')
        explain_command("dd if=/dev/zero of=/dev/sda", "rule_engine", "dd to block device", client_factory=factory)
        sent = capture()["messages"][0]["content"]
        self.assertIn("dd if=/dev/zero of=/dev/sda", sent)
        self.assertIn("dd to block device", sent)

    def test_prompt_asks_for_json(self):
        factory, capture = make_groq_fake('{}')
        explain_command("rm -rf /", "rule_engine", "system dir", client_factory=factory)
        sent = capture()["messages"][0]["content"]
        self.assertIn("JSON", sent)

    def test_fallback_on_api_error(self):
        def broken_factory():
            raise RuntimeError("no network")
        result = explain_command("rm -rf /", "rule_engine", "boom", client_factory=broken_factory)
        self.assertTrue(result.get("fallback"))
        self.assertIn("review", result["safer_alternative"])

    def test_fallback_is_local_and_never_blocks(self):
        fallback = get_fallback_explanation("rm -rf /", "rate limited")
        for key in ("what_it_does", "impact", "safer_alternative"):
            self.assertIn(key, fallback)

    def test_prompt_contract_is_json(self):
        prompt = get_explanation_prompt("rm -rf /", "rule_engine", "system dir", "critical")
        self.assertIn('"what_it_does"', prompt)
        self.assertIn('"impact"', prompt)
        self.assertIn('"safer_alternative"', prompt)


if __name__ == "__main__":
    unittest.main()
