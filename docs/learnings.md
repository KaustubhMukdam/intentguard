# Learnings — IntentGuard

> Fill this in at the end of every session, 5 minutes max. Explanation in your own words, not copy-pasted from AI.

---

## 2026-08-14 — Rule engine: regex pitfalls and rule/dataset alignment

### What I learned
- Regex alternation with a leading `-`: `.*-(a|-b)` is broken — `.*-` already consumes the dash, so `-b` needs a *second* dash. Put the dash inside the branch: `.*(-b|a)`. The `find ... -exec rm` pattern hit exactly this.
- Rule broadness must match the dataset: an overly broad `rm -rf /...` rule flagged `rm -rf /tmp/test_dir`, which the dataset labels *safe*. Rule engine and classifier would then disagree at runtime.
- TDD caught both: the `dd` test was already failing (regex required `of\s+=?` but dd syntax is `of=/dev/sda`, no space); the safe-pass-through specs caught the over-broad `rm` rule.

### Code snippet that clicked
```python
# Broken: .*- consumes the '-', then '-exec' needs another '-'
DANGEROUS_FIND_DELETE_PATTERN = r'\bfind\s+/\S*\s+.*-(delete|-exec\s+rm\b)'
# Fixed: dash lives inside the alternation branch
DANGEROUS_FIND_DELETE_PATTERN = r'\bfind\s+/\S*\s+.*(-exec\s+rm\b|delete)'
```

### What confused me today
Why the `find / -delete` case passed but `find /etc -exec rm` failed with the same-looking pattern — it was the double-dash alternation, invisible until you trace the consumed characters.

### How I solved it
Isolated each regex segment against the failing command in a throwaway script until the exact failing piece was found, then fixed and re-ran the full suite.

### What I'd do differently
Write the safe-pass-through spec (zero false positives on ~26 everyday commands) *before* tuning the patterns, not after.

---

## 2026-08-14 — shlex normalizes the command before rules see it

### What I learned
`rules.py` runs `" ".join(tokenize_command(command))` before matching, so shlex already collapses whitespace, unquotes, and strips `\;` → `;`. Patterns can rely on single-space normalized form; the quoted-command test (`rm -rf '/'`) passes *because* of this.

### Code snippet that clicked
```python
normalized_command = " ".join(tokenize_command(command))
```

### What confused me today
A raw string test passed while the same string through `check_rule_match` failed — the tokenizer had transformed it.

### How I solved it
Debugged through the actual pipeline (`check_rule_match`), not against the raw input.

### What I'd do differently
None — this layering (tokenize first, then regex) is the right call.

---

## 2026-08-15 — Daemon version handshake: snapshot at startup, never live-compute

### What I learned
A daemon holding OLD in-memory code must not re-hash the source files at ping time — disk always matches disk, so a stale daemon "certifies itself" as up-to-date forever. The version has to be captured once, when the process starts, and reported from memory.

### Code snippet that clicked
```python
_VERSION = code_version()   # module level, evaluated at import/startup
...
if "ping" in payload:
    reply = json.dumps({"version": _VERSION})  # NOT code_version() live
```

### What confused me today
Fixes kept "not working" while tests passed — because an older WSL daemon kept serving pre-fix code, and my handshake design guaranteed it would never be restarted.

### How I solved it
`pkill -f intentguard.daemon` once, then every future restart became automatic (disk hash ≠ startup snapshot).

### What I'd do differently
After any IPC-protocol change, kill long-lived processes before judging whether a fix worked. Three rounds of debugging were masked by this one thing.

---

## 2026-08-15 — gpt-oss on Groq: reasoning tokens eat your JSON budget

### What I learned
gpt-oss models think BEFORE answering, and reasoning tokens count against the completion budget. Small budgets truncate to empty output → Groq's `json_validate_failed` ("max completion tokens reached"). Two knobs fix it: the documented `max_completion_tokens` parameter (legacy `max_tokens` may not set that budget anymore) and `reasoning_effort="low"`, which is GPT-OSS-specific and keeps thinking short for tiny structured jobs like emitting one JSON object.

### Code snippet that clicked
```python
completion = client.chat.completions.create(
    model="openai/gpt-oss-120b",
    max_completion_tokens=4096,
    reasoning_effort="low",
    response_format={"type": "json_object"},
)
```

### What confused me today
The same request succeeded then failed seconds later — looked like quota. It was sampling variance: sometimes the model's tangent fit the budget, sometimes not. A `429 rate_limit_exceeded` is the *quota* error; `400 json_validate_failed` is *this* problem.

### How I solved it
Low effort + generous documented budget + giving the model an unambiguous quoted command (see next entry) so it doesn't ramble about tokenization.

### What I'd do differently
Read the provider's model page (reasoning support? param names?) before wiring structured output, not after three flaky failures.

---

## 2026-08-15 — printf %q flattening destroys argv boundaries

### What I learned
Passing `rm -rf "$HOME/ig test dir"` through the bash wrapper as ONE `%q`-escaped word is fine for rules (they shlex-split), but by the time the string reaches the LLM prompt, `/home/k/ig test dir` is indistinguishable from three separate targets — the model explained the wrong command. Grouping info must be re-encoded where it still exists: at argv parsing time, via per-token `shlex.quote`.

### Code snippet that clicked
```python
tokens = shlex.split(args[0]) if len(args) == 1 else list(args)
command = " ".join(shlex.quote(t) for t in tokens)
# -> rm -rf '/home/k/ig test dir'   (one target, unambiguous everywhere)
```
Rules stay correct because `check_rule_match` re-tokenizes and strips quotes anyway.

### What confused me today
My first fix tried to re-quote inside the prompt builder — impossible there; the boundary was already lost two layers earlier. The failing test proved quoting can't be recovered downstream.

### How I solved it
Normalize ONCE at the CLI edge into the canonical quoted form; everything downstream (rules, classifier, LLM, display) consumes it safely.

### What I'd do differently
Decide the canonical internal representation (quoted shell form) at the trust boundary on day one, instead of letting each layer improvise its own escaping.

---

## [Date] — [Topic]

### What I learned
[Concept]: [Explanation in your own words]

### Code snippet that clicked
```python

```

### What confused me today
[Be precise]

### How I solved it
[Tool used, what fixed it, why it works]

### What I'd do differently
[Hindsight]

---
