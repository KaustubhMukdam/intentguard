#!/bin/bash
# IntentGuard shell wrapper function.
# Source this in .bashrc:  source /path/to/intentguard/shell/intentguard.sh
# Usage: intentguard <command>   (or alias it to intercept every command)
#
# Wraps a command so it is evaluated by the IntentGuard pipeline before bash
# executes it. Exit codes from intentguard/cli.py:
#   0 = safe (or flagged + confirmed) -> run the command
#   1 = flagged + declined (or usage error) -> do not run
#
# Args are re-quoted with printf %q before eval so paths with spaces survive
# the round trip intact ("/tmp/my dir" stays one path).

intentguard() {
    if [ "$#" -eq 0 ]; then
        echo "usage: intentguard <command...>  |  intentguard --ask \"intent\"" >&2
        return 1
    fi

    local project_dir
    project_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

    local command_str
    printf -v command_str '%q ' "$@"

    PYTHONPATH="$project_dir" python3 -m intentguard.cli "$command_str"
    local exit_code=$?

    # --ask is meta (suggests a command); nothing to execute afterwards
    if [[ "$1" == --ask* ]]; then
        return "$exit_code"
    fi

    if [ "$exit_code" -eq 0 ]; then
        # IG_VIA_WRAPPER tells demo shims to stand down — this command was
        # already guarded; without it, shims would evaluate a second time.
        IG_VIA_WRAPPER=1 eval "$command_str"
        return $?
    fi
    return "$exit_code"
}

export -f intentguard
