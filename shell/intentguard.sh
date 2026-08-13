#!/bin/bash
# IntentGuard shell wrapper function
# This function intercepts commands before execution and passes them to the Python pipeline

intentguard() {
    # Capture the command string
    local command="$*"
    
    # Pass to Python pipeline
    python3 -m intentguard.cli "$command"
    
    # Check the exit code from the Python script
    # If it returns 0, the command was safe and should execute
    # If it returns 1, the command was flagged and user declined
    # If it returns 2, the command was flagged but we should still execute (after confirmation)
    local exit_code=$?
    
    if [ $exit_code -eq 0 ]; then
        # Safe command - execute normally
        eval "$command"
    elif [ $exit_code -eq 2 ]; then
        # Flagged but user confirmed - execute
        eval "$command"
    else
        # Flagged and user declined or error - don't execute
        echo "Command aborted by IntentGuard"
        return 1
    fi
}

# Export the function so it's available in subshells
export -f intentguard