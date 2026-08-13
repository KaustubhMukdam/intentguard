"""
Decision engine for IntentGuard
Ties rule engine, classifier, and LLM output into final flag/explain/confirm flow
"""

import sys
import os
from typing import Dict, Any
from . import rules
from . import tokenizer
from .classifier import predict
from .llm import client

# Risk threshold for classifier - can be tuned
RISK_THRESHOLD = 0.6

def evaluate_command(command: str) -> Dict[str, Any]:
    """
    Main decision function - evaluates command through the pipeline
    
    Args:
        command: Raw command string to evaluate
        
    Returns:
        Dict with action to take and explanation if needed
        action can be: "execute", "abort", "confirm_then_execute"
    """
    # Step 1: Normalize and tokenize command
    normalized_command = " ".join(tokenizer.tokenize_command(command))
    
    # Step 2: Rule engine check (zero latency)
    rule_result = rules.check_rule_match(normalized_command)
    if rule_result["matched"]:
        # Rule engine match - skip classifier, go straight to LLM
        explanation = client.explain_command(
            command, 
            flagged_by="rule_engine", 
            reason=rule_result["description"]
        )
        return {
            "action": "confirm_then_execute",
            "reason": rule_result["description"],
            "layer": "rule_engine",
            "explanation": explanation
        }
    
    # Step 3: ML classifier check
    try:
        classifier_result = predict.predict_command(normalized_command)
        if classifier_result["is_risky"] and classifier_result["confidence"] >= RISK_THRESHOLD:
            # Classifier flagged as risky - go to LLM
            explanation = client.explain_command(
                command,
                flagged_by="classifier",
                reason=f"ML classifier detected risky intent (confidence: {classifier_result['confidence']:.2f})"
            )
            return {
                "action": "confirm_then_execute",
                "reason": f"ML classifier detected risky intent",
                "layer": "classifier",
                "confidence": classifier_result["confidence"],
                "explanation": explanation
            )
    except Exception as e:
        # If classifier fails (e.g., model not trained), continue without it
        # In a real implementation, we might want to log this
        pass
    
    # Step 4: If we get here, command is considered safe
    return {
        "action": "execute",
        "reason": "Command deemed safe by all layers",
        "layer": "none"
    }

def get_confirmation_prompt(explanation: dict) -> str:
    """
    Format the explanation into a user-friendly confirmation prompt
    
    Args:
        explanation: Dict from LLM with what_it_does, impact, safer_alternative
        
    Returns:
        Formatted prompt string for user confirmation
    """
    prompt = f"""��⚠��️  INTENTGUARD FLAGGED THIS COMMAND

Command: {explanation.get('command', 'N/A')}
Flagged by: {explanation.get('layer', 'unknown')}

What this does: {explanation.get('what_it_does', 'Unknown')}
Blast radius: {explanation.get('impact', 'Unknown')}
Safer alternative: {explanation.get('safer_alternative', 'None')}

Proceed anyway? [y/N]:
"""
    return prompt

if __name__ == "__main__":
    # Test the decision engine
    test_commands = [
        "ls -la",
        "rm -rf /",
        "dd if=/dev/zero of=/dev/sda",
        "chmod 755 file.txt",
        ":(){ :|:& };:"
    ]
    
    for cmd in test_commands:
        print(f"Evaluating: {cmd}")
        result = evaluate_command(cmd)
        print(f"  Action: {result['action']}")
        if result['action'] == 'confirm_then_execute':
            print(f"  Reason: {result['reason']}")
            print(f"  Layer: {result.get('layer', 'unknown')}")
        print()