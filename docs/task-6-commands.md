# Task 6 Verification Commands — Shell Integration

Run suites where noted. PowerShell = Windows venv. Bash = WSL/Linux only
(the wrapper is a bash function; PowerShell testing stays on `python -m intentguard.cli`).

## 0. Regression suite (PowerShell)

```powershell
python -m pytest tests -q          # expect: 65 passed
```

## 1. Prefix wrapper — quoting round trip (WSL bash)

Proves paths-with-spaces survive evaluate→confirm→eval intact.
NOTE: use a HOME-path target — `/tmp` is intentionally exempt (dataset labels
temp-area deletes safe).

```bash
cd /mnt/d/Hackathon/CDAC/intentguard
source shell/intentguard.sh

mkdir -p "$HOME/ig test dir" && touch "$HOME/ig test dir/file.txt"

intentguard rm -rf "$HOME/ig test dir"
# EXPECT: medium-risk warning -> answer N -> aborted

ls -d "$HOME/ig test dir" && echo "STILL EXISTS (correct)"

intentguard rm -rf "$HOME/ig test dir"   # again, answer y -> really deletes
ls -d "$HOME/ig test dir" 2>/dev/null || echo "DELETED (correct)"

# temp areas stay frictionless BY DESIGN:
mkdir -p /tmp/ig-tmp-check
intentguard rm -rf /tmp/ig-tmp-check && echo "tmp delete passed silently (correct)"
```

## 2. NL mode through the wrapper (WSL bash)

```bash
intentguard --ask "show disk usage in human readable form"
# EXPECT: Suggested command: df -h  ...  safe to run.
```

## 3. Demo shim mode — plain `rm` guarded (WSL bash, throwaway terminal ONLY)

```bash
source shell/intentguard-demo.sh

mkdir -p "$HOME/ig-shim-target"
rm -rf "$HOME/ig-shim-target"
# EXPECT: same warning UI, NO intentguard prefix typed

unshim                                   # remove all shims
rm -rf "$HOME/ig-shim-target" 2>/dev/null
# EXPECT: real rm runs immediately, no prompt (unguarded binary again)
```

## Notes

- **Fail-closed:** under demo shims, if the daemon can't start, guarded binaries
  refuse to run (exit 125) instead of executing unchecked.
- **WSL dependency caveat:** bare system `python3` may lack sklearn/joblib.
  After the lazy-import fix, *rule-engine-flagged* commands still work (warning +
  local fallback explanation); *safe pass-through* needs the full deps:
  ```bash
  python3 -m venv .venv-wsl && source .venv-wsl/bin/activate
  pip install -r requirements.txt
  ```
  If pip has no network in WSL, flagged-path demos still work — safe-path
  returns a clear `IntentGuard: No module named 'joblib'` error instead of hanging.
- **Stale daemons are self-healing:** after any code edit, the next command
  auto-restarts the daemon (ping/version handshake). Manual kills no longer needed.
