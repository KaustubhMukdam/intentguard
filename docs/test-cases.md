# IntentGuard — Manual Test Cases (Windows PowerShell)

> Purpose: run the full 3-layer pipeline end-to-end on Windows PowerShell and
> confirm the exact behaviors a judge will see. These complement the automated
> suite (`python -m pytest tests -q` — 44 specs).
>
> All commands assume you're in the repo root with the venv active:
> ```powershell
> cd D:\Hackathon\CDAC\intentguard
> .\.venv\Scripts\Activate.ps1
> ```
>
> The first `intentguard.cli` call of a session spawns the background daemon
> (loads the model, ~3s). Subsequent commands reuse it (~200ms).

---

## A. Safe commands — pass through with zero friction

Expected: **exit code 0, no prompt, no output**.

```powershell
python -m intentguard.cli "ls -la"
python -m intentguard.cli "cd /home/user"
python -m intentguard.cli "pwd"
python -m intentguard.cli "git status"
python -m intentguard.cli "git push origin main"
python -m intentguard.cli "docker ps"
python -m intentguard.cli "df -h"
python -m intentguard.cli "ps aux"
python -m intentguard.cli "systemctl status sshd"
python -m intentguard.cli "pip install requests"
python -m intentguard.cli "python script.py"
python -m intentguard.cli "curl -O https://example.com/file.tar.gz"
python -m intentguard.cli "rm -rf /tmp/test_dir"   # /tmp is NOT a system dir
python -m intentguard.cli "rm file.txt"
python -m intentguard.cli "systemctl stop nginx"    # generic service stop is safe
python -m intentguard.cli "sudo systemctl restart nginx"
python -m intentguard.cli "find . -name '*.py'"     # non-destructive find
python -m intentguard.cli "ssh user@server"
```

Verify exit code in PowerShell: `echo $LASTEXITCODE` → expect `0`.

---

## B. Rule engine — known-catastrophic commands flagged instantly

Expected: **warning prompt shown, no exit until you answer**, "Flagged by: rule_engine".

```powershell
python -m intentguard.cli "rm -rf /"
python -m intentguard.cli "rm -rf /*"
python -m intentguard.cli "rm -rf /etc"
python -m intentguard.cli "rm -r -f /home/*"        # separate flags
python -m intentguard.cli "rm --recursive --force /etc"   # long-form flags
python -m intentguard.cli "rm -rfv /boot"            # combined flags
python -m intentguard.cli "rm -rf /; echo ok"        # chained
python -m intentguard.cli "sudo rm -rf /"            # sudo prefix
python -m intentguard.cli "dd if=/dev/zero of=/dev/sda"
python -m intentguard.cli "dd if=/dev/random of=/dev/nvme0n1"
python -m intentguard.cli "> /dev/sda"               # raw redirect to block device
python -m intentguard.cli "mkfs.ext4 /dev/sda1"
python -m intentguard.cli "chmod -R 777 /"
python -m intentguard.cli "chown -R root:root /"
python -m intentguard.cli ":(){ :|:& };"             # fork bomb
python -m intentguard.cli "ufw disable"
python -m intentguard.cli "iptables -F"
python -m intentguard.cli "systemctl stop firewalld" # NOT a generic service stop
python -m intentguard.cli "find / -delete"
python -m intentguard.cli "find /etc -exec rm -rf {} \;"
python -m intentguard.cli "apt remove -y linux-image-generic"
```

Verify: each shows `⚠️  INTENTGUARD FLAGGED THIS COMMAND`, a plain-English
explanation, and "Flagged by: rule_engine — <pattern description>".

---

## C. ML classifier — ambiguous/novel commands the rules miss

Expected: **warning prompt**, "Flagged by: classifier", confidence printed.

```powershell
python -m intentguard.cli "shred /dev/sda1"
python -m intentguard.cli "wipefs --all /dev/sdb1"
```

`shred` and `wipefs` have no rule pattern — only the classifier catches them.
This proves layer 2 adds value beyond the blocklist.

---

## D. Confirmation flow — both paths

```powershell
# Decline -> exit code 1, command not run, "Command aborted by IntentGuard"
python -m intentguard.cli "rm -rf /"
#   type N, then: echo $LASTEXITCODE  -> 1

# Confirm -> exit code 0 (bash wrapper would then run it)
python -m intentguard.cli "rm -rf /"
#   type y, then: echo $LASTEXITCODE  -> 0
```

---

## E. LLM explanation layer

Confirm a flagged command with `y` and read the output: it must contain
(1) plain-English `What this does`, (2) `Blast radius`, (3) `Safer alternative`.

```powershell
python -m intentguard.cli "rm -rf /var/log/*"
#   type y -> explanation is the live Groq output
```

Without `GROQ_API_KEY` (rename `.env` temporarily), flagged commands still
show a **local fallback explanation** — the demo never stalls:

```powershell
python -m intentguard.cli "rm -rf /"
#   no key -> warning still renders, explanation is generic fallback text
```

---

## F. Regression guard — the transport fix

The daemon<->CLI IPC must work (this is what `AF_UNIX` broke on native Windows):

```powershell
# 1. Safe path through the daemon
python -m intentguard.cli "ls -la" ; echo "exit=$LASTEXITCODE"

# 2. Flagged path through the daemon (spawns on first call)
python -m intentguard.cli "rm -rf /" ; echo "exit=$LASTEXITCODE"
```

Expected: first call may take ~3s (daemon boot), then `exit=0` for safe,
prompt for flagged. If you see `IntentGuard: failed to start daemon`, the
transport is broken — check the port isn't taken (`netstat -ano | findstr 45670`)
or that `socketutil.py` is on disk.

---

## G. Full automated suite

```powershell
python -m pytest tests -q
```

Expected: `44 passed`.