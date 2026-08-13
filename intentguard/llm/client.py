"""
Groq API client for IntentGuard
Handles communication with Groq for LLM explanations
"""

import os
import json
from groq import Groq
from dotenv import load_dotenv
from .prompts.get_explanation_prompt

# Load environment variables
load_dotenv()

class GroqClient:
    def __init__(self):
        self.api_key = os.getenv("GROQ_API_KEY")
        if not self.api_key:
            raise ValueError("GROQ_API_KEY not found in environment variables")
        
        self.client = Groq(api_key=self.api_key)
        self.model = "llama-3.3-70b-versatile"
    
    def get_explanation(self, command: str, flagged_by: str, reason: str) -> dict:
        """
        Get explanation from Groq for a flagged command
        
        Args:
            command: The command that was flagged
            flagged_by: Which layer flagged it (rule_engine, classifier)
            reason: Why it was flagged
            
        Returns:
            Dict with explanation, impact, and alternative
        """
        prompt = get_explanation_prompt(command, flagged_by, reason)
        
        try:
            chat_completion = self.client.chat.completions.create(
                messages=[
                    {
                        "role": "user",
                        "content": prompt,
                    }
                ],
                model=self.model,
                temperature=0.3,
                max_tokens=500,
                response_format={"type": "json_object"}
            )
            
            response_content = chat_completion.choices[0].message.content
            return json.loads(response_content)
            
        except Exception as e:
            # Fallback explanation if API fails
            return {
                "what_it_does": f"Executes the command: {command}",
                "impact": "Unable to generate detailed explanation due to API error",
                "safer_alternative": "Review command manually before execution",
                "error": str(e)
            }

# Global client instance
_client = None

def get_client() -> GroqClient:
    """Get or create the Groq client instance"""
    global _client
    if _client is None:
        _client = GroqClient()
    return _client

def explain_command(command: str, flagged_by: str, reason: str) -> dict:
    """
    Convenience function to get command explanation
    
    Args:
        command: The command that was flagged
        flagged_by: Which layer flagged it
        reason: Why it was flagged
        
    Returns:
        Dict with explanation details
    """
    client = get_client()
    return client.get_explanation(command, flagged_by, reason)