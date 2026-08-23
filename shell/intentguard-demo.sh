#!/bin/bash
# ============================================================================
# ⚠️  INTENTGUARD DEMO MODE — binary shims for live-pitch "wow" moments
#
# Shadows rm/dd/chmod/… with guard functions so typing PLAIN commands
# (no `intentguard` prefix) still goes through the pipeline:
#
#     source shell/intentguard-demo.sh
#     rm -rf myproject        # -> IntentGuard warning, y/N
#     command rm anything     # escape hatch: real rm, unguarded
#
# RULES FOR STAYING SAFE:
#   • Source this in a THROWAWAY terminal only. NEVER put it in .bashrc.
#   • Guarded binaries FAIL CLOSED: if the daemon is down, they refuse to run
#     (exit 125) rather than execute unchecked.
#   • Close the terminal (or run `unshim`) when done — daily usage unaffected.
# ============================================================================

_DEMO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

source "$(dirname "${BASH_SOURCE[0]}")/intentguard.sh"

_ig_make_shim() {
    local bin="$1"
    eval "${bin}() {
        if [[ -n \${IG_VIA_WRAPPER-} ]]; then   # already guarded by intentguard()
            command "$bin" \"\$@\"
            return
        fi
        local _args _code
        printf -v _args '%q ' \"\$@\"
        PYTHONPATH=\"$_DEMO_DIR\" python3 -m intentguard.cli \"$bin \$_args\"
        _code=\$?
        [ \$_code -ne 0 ] && return 125   # declined or daemon error: fail closed
        command "$bin" \"\$@\"
    }"
}

for _ig_bin in rm dd chmod chown shred wipefs mkfs mkfs.ext4 mkfs.xfs; do
    _ig_make_shim "$_ig_bin"
done
unset _ig_bin _ig_make_shim

# one-shot removal of every shim (also restores intentguard prefix mode)
unshim() {
    local b
    for b in rm dd chmod chown shred wipefs mkfs mkfs.ext4 mkfs.xfs; do
        unset -f "$b"
    done
    echo "IntentGuard demo shims removed — binaries are back to normal."
}
