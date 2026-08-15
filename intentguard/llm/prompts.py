"""
Prompt templates for IntentGuard LLM layer
Structured prompts for explanation generation
"""


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

Command: {command}
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