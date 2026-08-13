#!/usr/bin/env python3
"""
IntentGuard CLI entrypoint
Receives command string, orchestrates the pipeline
"""

import sys
import os
from . import rules
from . import tokenizer
from .classifier import predict
from . import decision

def main():
    if len(sys.argv) < 2:
        print("Usage: intentguard <command>")
        sys.exit(1)
    
    # Join all arguments as the command string
    command = " ".join(sys.argv[1:])
    
    # Process through the pipeline
    result = decision.evaluate_command(command)
    
    # Exit codes:
    # 0 = safe, execute command
    # 1 = flagged, user declined
    # 2 = flagged, user confirmed
    
    if result["action"] == "execute":
        sys.exit(0)
    elif result["action"] == "abort":
        sys.exit(1)
    elif result["action"] == "confirm_then_execute":
        sys.exit(2)
    else:
        # Default to safe execution
        sys.exit(0)

if __name__ == "__main__":
    main()