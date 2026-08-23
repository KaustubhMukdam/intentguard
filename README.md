# IntentGuard

> An AI safety layer for your terminal. It understands what a Linux command is about to do — and blocks the destructive ones with a plain-English explanation and a safer alternative.

**Built solo · Free-tier only · C-DAC Hackathon, Track 2** — "AI-Based System Intent Engine for Safe Linux Command Execution"

---

## The problem

Linux users — students, junior sysadmins, even experienced engineers under time pressure — regularly run destructive commands (`rm -rf /`, `dd if=/dev/zero of=/dev/sda`, `chmod -R 777 /`, misplaced wildcard deletes) without anything understanding *what the command is actually about to do* before it does it. Blocklists either miss novel commands or don't explain anything.

## What it does

Before a command runs, IntentGuard decides:

```
rm -rf /var/log/*
│
├─ LAYER 1  Rule Engine (regex + shlex)   → instant, deterministic catch
├─ LAYER 2  ML Classifier (TF-IDF + LinearSVC) → scores ambiguous/novel commands
└─ LAYER 3  LLM Explainer (Groq)           → plain-English what / impact / alternative
```

If any layer flags it, you see this — and you decide:

```
⚠️  INTENTGUARD FLAGGED THIS COMMAND

Command: rm -rf /var/log/*
Flagged by: rule_engine — rm -rf on root or system directory

What this does:  Permanently deletes all system log files in /var/log.
Blast radius:    Loss of audit trails and boot logs. Not reversible.
Safer alternative: journalctl --vacuum-time=7d

Proceed anyway? [y/N]:
```

Safe commands (`ls`, `git status`, `pip install`, `df -h`) pass through **invisibly** — no prompt, ~1ms added.

## Quick start

```bash
# 1. install deps
pip install -r requirements.txt

# 2. (optional) add your Groq key for real explanations
cp .env.example .env   # add GROQ_API_KEY=...

# 3. intercept commands
source shell/intentguard.sh
intentguard rm -rf /            # flagged, asks for confirmation
intentguard ls -la              # passes through silently

# 4. natural-language mode (suggestions are vetted through the same pipeline)
intentguard --ask "show disk usage in human readable form"

# optional: demo mode — shadow rm/dd/… so PLAIN commands are guarded too.
# Throwaway terminal only, never .bashrc. `unshim` removes it.
source shell/intentguard-demo.sh
```

Without a Groq key, IntentGuard still runs — flagged commands get a local fallback explanation instead of an API call.

## Why a 3-layer pipeline?

| Layer | Why |
|-------|-----|
| Rule engine (regex/shlex) | Known catastrophic patterns caught with **zero latency and zero API cost** |
| ML classifier (TF-IDF + LinearSVC) | Catches **ambiguous/novel** dangerous commands rules miss — the honest baseline is "rule engine alone catches 60% of risky commands; +classifier catches 96.8%" |
| LLM explainer (Groq) | **Explains** flagged commands in plain English — the part blocklists can't do |

Defense in depth, cheapest layer first. Only commands flagged by layer 1 or 2 ever touch the LLM, so cost and latency stay low.

## Performance (eval.md)

| Approach | F1 (risky) | Recall (risky) | Precision (risky) |
|----------|-----------|----------------|-------------------|
| Majority baseline | 0.00 | 0.00 | — |
| Rule engine only | — | 0.60 | — |
| **Full pipeline** | **0.984** | **0.968** | **1.000** |

A recall of 0.968 on the risky class means the classifier misses ~3 dangerous commands per 100 — and those cost one extra confirmation prompt, not silent damage. Misses are strictly worse than false alarms in a safety tool.

## Project structure

```
shell/intentguard.sh       bash wrapper (source in .bashrc)
intentguard/
  cli.py                   thin client + confirmation UI
  daemon.py                background daemon (holds loaded model)
  socketutil.py            portable IPC (Unix socket / TCP loopback)
  decision.py              orchestrates the 3 layers
  rules.py                 regex pattern list
  tokenizer.py             shlex-based safe tokenization
  classifier/              train.py · predict.py · model.joblib
  llm/                     client.py (Groq) · prompts.py
data/                      self-curated labeled dataset (318 commands)
tests/                     78 specs, all green
docs/                      full context (PRD, architecture, eval, model card, test-cases)
```

Runs on Linux/WSL and **Windows PowerShell** — the CLI speaks to a background
daemon over a Unix socket on Linux and TCP loopback on Windows, so the demo
works from either environment.

## Honest scoping (see docs/)

- **Shell-level, not kernel-level.** This is a safety net for well-intentioned mistakes, not a security boundary against an attacker — a determined user can bypass any shell wrapper (that's Track 1's job, deliberately out of scope).
- **Dataset is self-curated** (318 commands, labeled by hand + verified), not scraped — original submission per hackathon rules.
- **Training runs locally on CPU**; the model artifact is a local `model.joblib`. No live cloud dependency at demo time — Groq is only consulted for explanations when a command is already flagged, and degrades to a local fallback if unreachable.
- **Not a general NL-to-shell translator** — that's a different, larger problem. IntentGuard answers "is this command safe?" not "write me a command."

## Docs

Full context lives in [`docs/`](docs/README.md): PRD, architecture, tech stack, evaluation, model card, and the day-by-day task log.

---

*Solo submission, C-DAC Hackathon 2026 — Track 2. Free tier throughout: scikit-learn, Groq free tier, no paid infra.*
