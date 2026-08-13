"""
Prompt templates for IntentGuard LLM layer
Structured prompts for explanation generation
"""

def get_explanation_prompt(command: str, flagged_by: str, reason: str) -> str:
    """
    Generate a structured prompt for the LLM to explain a flagged command
    
    Args:
        command: The command that was flagged
        flagged_by: Which layer flagged it (rule_engine, classifier)
        reason: Why it was flagged
        
    Returns:
        Formatted prompt string
    """
    return f"""You are a Linux safety expert. Analyze this command and provide:
1. What the command actually does (in plain English)
2. The potential blast radius/impact if executed
3. A safer alternative command (if applicable)

Command: {command}
Flagged by: {flagged_by}
Reason: {reason}

Respond ONLY with valid JSON in this exact format:
{{
  "what_it_does": "clear explanation of what the command does",
  "impact": "description of potential damage or consequences",
  "safer_alternative": "safer command to achieve similar goal, or 'No direct alternative - review manually' if none"
}}

Keep explanations concise (2-3 lines max for what_it_does and impact).
Focus on safety and clarity."""