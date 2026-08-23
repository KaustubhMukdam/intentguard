# Debug Log — IntentGuard

---

## 2026-08-14 — dd regex: `of\s+=?` requires whitespace that dd never has

**Error message:**
```
FAIL: test_dd_to_device — AssertionError: False is not true
# check_rule_match("dd if=/dev/zero of=/dev/sda") returned {"matched": False}
```

**Root cause:** Pattern `\bdd\s+.*\bof\s+=?\/dev\/(sd|hd|vd|mmcblk)` — `\s+` after `of` requires a space, but dd syntax is `of=/dev/sda` (no space). The `\s+` also swallowed `=?`.

**Fix:**
```python
# Before (broken)
DANGEROUS_DD_PATTERN = r'\bdd\s+.*\bof\s+=?\/dev\/(sd|hd|vd|mmcblk)'
# After (fixed)
DANGEROUS_DD_PATTERN = r'\bdd\b.*\bof\s*=\s*/dev/(sd|hd|vd|mmcblk|nvme)'
```

**Time lost:** ~15 minutes
**How I found it:** failing unit test, then isolated each regex segment
**Pattern to remember:** flag forms (`-rf`, `of=`) don't use the `\s+` you'd write for prose.

---

## 2026-08-14 — find -exec rm: `.*-(a|-b)` double-dash alternation bug

**Error message:**
```
FAIL: test_find_recursive_delete_is_caught
AssertionError: False is not true : find /etc -exec rm -rf {} \;
```

**Root cause:** `.*-` consumes the leading `-`, so the `-exec` branch of `(delete|-exec\s+rm\b)` needs a second dash. `find / -delete` passed only because `delete` has no leading dash.

**Fix:**
```python
# Before (broken)
DANGEROUS_FIND_DELETE_PATTERN = r'\bfind\s+/\S*\s+.*-(delete|-exec\s+rm\b)'
# After (fixed) — dash inside the branch
DANGEROUS_FIND_DELETE_PATTERN = r'\bfind\s+/\S*\s+.*(-exec\s+rm\b|delete)'
```

**Time lost:** ~20 minutes
**How I found it:** compared the two alternations (`.*-exec\s+rm\b` matched alone; the grouped version didn't) then traced consumed characters
**Pattern to remember:** when an alternation branch starts with a literal, keep that literal inside the branch — never in the `.*`-prefix.

---

## 2026-08-14 — over-broad rm rule contradicted the dataset

**Error message:**
```
test_safe_commands_pass_without_flag FAILED: False positive on: rm -rf /tmp/test_dir
```

**Root cause:** old pattern `\brm\s+-rf\s+/?` matched any `rm -rf /...`, but the dataset labels `rm -rf /tmp/test_dir` **safe**. Rule engine and classifier would disagree at runtime.

**Fix:** anchor to root/system dirs only (`/`, `/*`, `/etc /usr /var /bin /sbin /lib /boot /home /root`), leaving `rm -rf /tmp/...` to the classifier.
```python
DANGEROUS_RM_PATTERN = (
    r'\brm\b\s+(-(?:r[fF]|[fF]r)\s+|(-r\s+-f\s+|-f\s+-r\s+))'
    r'(/(\s|$)|/\*|/(?:etc|usr|var|bin|sbin|lib|boot|home|root)\b)'
)
```

**Time lost:** ~15 minutes
**How I found it:** the safe-pass-through spec I added as a TDD guardrail
**Pattern to remember:** a rule layer and an ML layer over the same inputs must agree on labels, or the pipeline's "defense in depth" story is a lie.

---

## 2026-08-14 — escaped char-class in assembled regex (`-\[rR\]` matched literal brackets)

**Error message:**
```
FAIL: test_rm_with_separate_flags_is_caught
'rm -r -f /home/*' -> no rule_engine match
```

**Root cause:** when building `DANGEROUS_RM_PATTERN` by string-concatenating `RM_FLAGS`, the separate-flags alternative was written `-\[rR\]` — which matches the literal text `[rR]`, not a character class. Concatenation doesn't change raw-string meaning; the bracket escaped-ness was the bug.

**Fix:**
```python
# Before (broken — literal bracket match)
r'-\[rR\]\s+-\[fF\]\s+|-[fF]\s+-\[rR\]\s+|'
# After (character class)
r'-[rR]\s+-[fF]\s+|-[fF]\s+-[rR]\s+|'
```

**Time lost:** ~10 minutes
**How I found it:** isolated the pattern against the tokenized command in a throwaway script
**Pattern to remember:** when composing regex from string fragments, character classes `[rR]` must not be written `\[rR\]`.

---

## 2026-08-14 — model reloaded on every safe command (69ms/call)

**Error message:** no error — latency finding from benchmark
**Root cause:** `load_model()` ran `joblib.load()` on every `predict_command` call, so even safe commands (which route through the classifier) paid a 69ms disk load.
**Fix:** `@lru_cache(maxsize=1)` on `load_model()` → safe path 69ms → 1.3ms.
**Time lost:** ~10 minutes
**How I found it:** micro-benchmarked each pipeline path (safe / rule / classifier)
**Pattern to remember:** cache immutable loaded artifacts; measure, don't assume.

---

## 2026-08-15 — "failed to start daemon" on native Windows (AF_UNIX)

**Error message:**
```
IntentGuard: failed to start daemon
```
**Root cause:** `socket.AF_UNIX` doesn't exist on Windows Python 3.11; daemon died at bind while CLI polled a port nothing listened on.
**Fix:** `intentguard/socketutil.py` — Unix socket on Linux/WSL, TCP loopback `127.0.0.1:45670` on Windows; both sides resolve via one helper.
**Pattern to remember:** transport choice is a platform decision — isolate it in one module both peers import.

---

## 2026-08-15 — empty reply → JSONDecodeError (import outside try)

**Error message:**
```
json.decoder.JSONDecodeError: Expecting value: line 1 column 1 (char 0)
```
**Root cause:** `daemon.evaluate()` did the lazy pipeline import OUTSIDE its try/except; on dep-less Python the ModuleNotFoundError escaped to the serve loop's silent `except: pass`, no reply sent, client parsed b"".
**Fix:** move the import inside try → every failure becomes an error-dict reply.
**Pattern to remember:** "never crash the loop" only works if the try actually wraps everything that can throw.

---

## 2026-08-15 — stale daemon self-certifies as up-to-date

**Error message:** fixes kept not appearing live; tests green, behavior unchanged.
**Root cause:** ping handler computed `code_version()` from disk at request time — daemon-with-old-code compared new disk against new disk → always matched.
**Fix:** `_VERSION = code_version()` snapshotted at module import; ping returns the snapshot.
**Time lost:** ~3 debug rounds masked by this.
**Pattern to remember:** identity checks must reflect the RUNNING process's provenance, not current external state.

---

## 2026-08-15 — json_validate_failed / max completion tokens reached (gpt-oss)

**Error message:**
```
400 json_validate_failed ... 'max completion tokens reached before generating a valid document'
```
**Root cause:** three stacked issues — gpt-oss reasoning tokens consume completion budget; legacy `max_tokens` param vs documented `max_completion_tokens`; and an unquoted spaced path made the model reason about a command that didn't exist.
**Fix:** `max_completion_tokens=4096` + `reasoning_effort="low"` + canonical quoted command form (`shlex.quote` per token at CLI edge).
**How I found it:** Groq docs (reasoning page) + noticing successful explanations misread `/home/k/ig test dir` as three targets.
**Pattern to remember:** reasoning models need budget for thinking AND unambiguous input; read provider model pages before structured output.

---

## 2026-08-15 — double confirmation prompt (wrapper eval re-entered demo shim)

**Error message:** user answered y, prompt appeared AGAIN, deletion happened once.
**Root cause:** with both modes sourced, wrapper's post-confirm `eval "$command"` invoked the shimmed `rm()` function, which ran the CLI a second time.
**Fix:** wrapper sets `IG_VIA_WRAPPER=1` around eval; shims see it and delegate straight to `command <bin>`. Also `--ask` now skips eval entirely (meta command, nothing to execute).
**Pattern to remember:** layered guards must recognize when a command was already guarded upstream.

---

## [Date] — [Short bug title]

**Error message:**
```
[paste exact error here]
```

**Root cause:** [What actually caused it]

**Fix:**
```python
# Before (broken)

# After (fixed)

```

**Time lost:** [e.g. 45 minutes]
**How I found it:** [tool/method]
**Pattern to remember:** [generalizable lesson]

---
