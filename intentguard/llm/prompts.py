"""
Prompt templates for IntentGuard LLM layer
Structured prompts for explanation generation
"""

import shlex


def _shell_quoted(command: str) -> str:
    """Canonical quoted form so spaced paths read as ONE target, not many."""
    try:
        return shlex.join(shlex.split(command))
    except ValueError:
        return command


def get_explanation_prompt(command: str, flagged_by: str, reason: str, risk_level: str = "high") -> str:
    """
    Generate a structured prompt for the LLM to explain a flagged command.

    Args:
        command: The command that was flagged.
        flagged_by: Which layer flagged it (rule_engine / classifier).
        reason: Why it was flagged.
        risk_level: severity label from the rule engine (critical/high) or classifier.

    Returns:
        Formatted prompt string.
    """
    return f"""You are a Linux safety expert for a tool called IntentGuard. A user tried to
run a command and it was flagged as risky. Explain it so a non-expert understands in seconds.

Command: {_shell_quoted(command)}
Flagged by: {flagged_by}
Risk level: {risk_level}
Reason: {reason}

Respond ONLY with valid JSON in exactly this shape:
{{
  "what_it_does": "plain-English, what the command would actually do",
  "impact": "specific blast radius or damage if executed",
  "safer_alternative": "a safer command/approach, or 'No direct alternative — review manually' if none"
}}

Rules:
- Keep "what_it_does" and "impact" to at most 2-3 short lines each.
- Be concrete and technical, not generic ("deletes files" is too vague).
- Never mention JSON or prompts in the output.
"""


def get_command_suggestion_prompt(intent: str) -> str:
    """NL-mode prompt: plain-English intent -> ONE safe bash command (strict JSON)."""
    return f"""You are a Linux command assistant for a tool called IntentGuard.
The user describes an intent in plain English. Suggest ONE concrete bash command
that accomplishes it as safely as possible.

Intent: {intent}

Respond ONLY with valid JSON in exactly this shape:
{{
  "command": "the single bash command to run",
  "why": "one short line on what it does"
}}

Rules:
- Prefer non-destructive, read-only forms whenever possible.
- If the intent requires deletion or modification, return the most targeted, minimal
  command that does it anyway — IntentGuard's safety layers will review whatever you return.
- Exactly one command — no chaining, no newlines.
- Never mention JSON or prompts in the output.
"""