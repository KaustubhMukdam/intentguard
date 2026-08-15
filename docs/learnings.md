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
