"""
Tokenizer module for IntentGuard
Provides shlex-based safe command tokenization
"""

import shlex

def tokenize_command(command: str) -> list:
    """
    Safely tokenize a command string using shlex
    This prevents pattern matching from being fooled by quoting/escaping tricks
    
    Args:
        command: Raw command string
        
    Returns:
        List of tokens
    """
    try:
        return shlex.split(command)
    except ValueError:
        # If shlex fails (e.g., unmatched quotes), fall back to simple split
        return command.split()

def normalize_command(command: str) -> str:
    """
    Normalize command for consistent processing
    Apply whitespace normalization
    
    Args:
        command: Raw command string
        
    Returns:
        Normalized command string
    """
    # Whitespace normalization
    return " ".join(command.split())