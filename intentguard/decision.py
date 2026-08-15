"""
Decision engine for IntentGuard
Ties rule engine, classifier, and LLM output into final flag/explain/confirm flow
"""

from . import rules
from .classifier import predict
from .llm import client as llm_client

# Classifier confidence threshold for flagging as risky (can be tuned)
RISK_THRESHOLD = 0.6


def evaluate_command(command: str, explain_fn=None) -> dict:
    """
    Evaluate a command through the 3-layer pipeline.

    Args:
        command: Raw command string.
        explain_fn: optional callable(command, flagged_by, reason, risk_level) that
            returns the LLM explanation dict. Defaults to the real Groq client;
            tests inject a fake.

    Returns:
        Dict with action ("execute" | "confirm_then_execute"), and on flag:
        reason, layer, risk_level, explanation.
    """
    explain_fn = explain_fn or llm_client.explain_command

    # Layer 1 — rule engine (zero latency, deterministic)
    rule_result = rules.check_rule_match(command)
    if rule_result["matched"]:
        return {
            "action": "confirm_then_execute",
            "reason": rule_result["description"],
            "layer": "rule_engine",
            "risk_level": rule_result["risk_level"],
            "explanation": explain_fn(
                command,
                flagged_by="rule_engine",
                reason=rule_result["description"],
                risk_level=rule_result["risk_level"],
            ),
        }

    # Layer 2 — ML classifier (ambiguous/novel commands only)
    classifier_result = predict.predict_command(command)
    if classifier_result["is_risky"] and classifier_result["confidence"] >= RISK_THRESHOLD:
        reason = f"ML classifier detected risky intent (confidence {classifier_result['confidence']:.2f})"
        return {
            "action": "confirm_then_execute",
            "reason": reason,
            "layer": "classifier",
            "risk_level": "medium",
            "confidence": classifier_result["confidence"],
            "explanation": explain_fn(
                command,
                flagged_by="classifier",
                reason=reason,
                risk_level="medium",
            ),
        }

    # Safe — pass through invisibly
    return {"action": "execute", "layer": "none", "reason": "Command deemed safe by all layers"}