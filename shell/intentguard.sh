#!/bin/bash
# IntentGuard shell wrapper function.
# Source this in .bashrc:  source /path/to/intentguard/shell/intentguard.sh
# Usage: intentguard <command>   (or alias it to intercept every command)
#
# Wraps a command so it is evaluated by the IntentGuard pipeline before bash
# executes it. Exit codes from intentguard/cli.py:
#   0 = safe (or flagged + confirmed) -> run the command
#   1 = flagged + declined (or usage error) -> do not run

intentguard() {
    if [ "$#" -eq 0 ]; then
        echo "usage: intentguard <command...>" >&2
        return 1
    fi

    local command="$*"
    local project_dir
    project_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

    PYTHONPATH="$project_dir" python3 -m intentguard.cli "$command"
    local exit_code=$?

    if [ "$exit_code" -eq 0 ]; then
        eval "$command"
        return $?
    fi
    return "$exit_code"
}

export -f intentguard