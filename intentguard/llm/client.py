"""
Groq API client for IntentGuard
Handles communication with Groq for LLM explanations.

Design: `explain_command` takes an optional `client_factory` so tests can
inject a fake; production uses the real GroqClient backed by GROQ_API_KEY.
"""

import json
import os

from dotenv import load_dotenv

from .prompts import get_command_suggestion_prompt, get_explanation_prompt

load_dotenv()

# Groq decommissions model ids periodically (llama-3.3-70b-versatile died Aug 2026);
# GROQ_MODEL env var overrides without a code change.
DEFAULT_MODEL = "openai/gpt-oss-120b"


def get_model_id() -> str:
    return os.getenv("GROQ_MODEL", DEFAULT_MODEL)


def _get_groq_client():
    """Lazily import and construct the real Groq client (key required)."""
    from groq import Groq

    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY not set — add it to .env (see .env.example)")
    # timeout<=3s + zero retries keeps the flagged-command path under ~3s worst
    # case; SDK default retries turn one failure into ~10s of hanging.
    return Groq(api_key=api_key, timeout=3.0, max_retries=0)


def get_fallback_explanation(command: str, error: str) -> dict:
    """Local fallback so a flagged command never stalls the demo if the API fails."""
    return {
        "what_it_does": f"Runs `{command}` on this system.",
        "impact": "Unable to reach explanation service — treat this command as risky and review it manually.",
        "safer_alternative": "No direct alternative — review manually",
        "fallback": True,
        "error": error,
    }


def explain_command(command, flagged_by, reason, risk_level="high", client_factory=None) -> dict:
    """
    Generate (what_it_does, impact, safer_alternative) for a flagged command.

    Args:
        command: The command that was flagged.
        flagged_by: "rule_engine" or "classifier".
        reason: Why it was flagged.
        risk_level: severity label.
        client_factory: callable returning a Groq-like client. Defaults to the
            real Groq client (requires GROQ_API_KEY).

    Returns:
        Dict with what_it_does / impact / safer_alternative keys.
    """
    prompt = get_explanation_prompt(command, flagged_by, reason, risk_level)

    try:
        client = (client_factory or _get_groq_client)()
        completion = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model=get_model_id(),
            temperature=0.3,
            max_completion_tokens=4096,  # documented knob; legacy max_tokens may be ignored for reasoning models
            reasoning_effort="low",  # GPT-OSS: short thinking so JSON always fits
            response_format={"type": "json_object"},
        )
        raw = completion.choices[0].message.content
        parsed = json.loads(raw)
        return {
            "what_it_does": parsed.get("what_it_does", ""),
            "impact": parsed.get("impact", ""),
            "safer_alternative": parsed.get("safer_alternative", ""),
        }
    except Exception as e:  # missing key, rate limit, parse failure, network
        return get_fallback_explanation(command, str(e))


def suggest_command(intent: str, client_factory=None) -> dict:
    """
    NL mode: turn a plain-English intent into ONE suggested bash command.

    Returns {"command": str|None, "why": str}; command is None + fallback flag
    on any API/parse failure so the caller degrades gracefully.
    """
    prompt = get_command_suggestion_prompt(intent)
    try:
        client = (client_factory or _get_groq_client)()
        completion = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model=get_model_id(),
            temperature=0.2,
            max_completion_tokens=4096,  # same reasoning-token caveat as explain_command
            reasoning_effort="low",
            response_format={"type": "json_object"},
        )
        parsed = json.loads(completion.choices[0].message.content)
        return {"command": parsed.get("command"), "why": parsed.get("why", "")}
    except Exception as e:  # same failure classes as explain_command
        return {"command": None, "why": "", "fallback": True, "error": str(e)}