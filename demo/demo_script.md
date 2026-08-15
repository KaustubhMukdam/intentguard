# IntentGuard — Live Demo Script

Goal: judges understand what this is within the first 60 seconds. The "oh, it caught that" moment goes FIRST. This entire script runs locally, offline — only flagged commands call Groq.

## Setup (before the pitch, 2 minutes)

```bash
# from the repo root
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env            # add GROQ_API_KEY=... for real explanations
source shell/intentguard.sh     # defines the intentguard() wrapper
```

Note: the first `intentguard` call of a session spawns a background daemon (loads the model once, ~3s). Subsequent commands are ~200ms. Warm it up before judges arrive:

```bash
intentguard echo warmup          # pays the one-time ~3s daemon boot
```

Verify: `intentguard echo demo-ok` → prints `demo-ok` with no prompt, near-instant.

---

## ✦ ACT 1 — "oh, it caught that" (the hook, ~30s)

Run this with confidence, hands off the keyboard:

```bash
intentguard rm -rf /                       # CRITICAL catch, red
```

Everyone sees the styled warning immediately. Don't confirm it. Say: *"I typed a command that would wipe this machine. IntentGuard stopped it before bash could run it."*

Then the contrast — type both in a row:

```bash
intentguard ls -la                         # passes through, invisible
intentguard echo "zero friction on safe commands"   # no prompt
```

Say: *"Safe commands have zero delay. It's not nagging you — it only speaks up when it matters."*

## ✦ ACT 2 — "it's not a blocklist" (the insight, ~45s)

Show the multi-layer story with two more catches:

```bash
intentguard dd if=/dev/zero of=/dev/sda   # rule engine, critical
# decline with N

intentguard ":(){ :|:& };:"                # fork bomb, rule engine
```

Say: *"These aren't in a giant blocklist — this is a rule engine that tokenizes the command and understands structure. Now watch the part rules can't do."*

Turn it toward the classifier (a command that is risky but NOT a hardcoded pattern):

```bash
intentguard shred /dev/sda1                # classifier path (not a rule)
# decline with N
```

Say: *"No rule matched this one. The ML classifier — trained locally on CPU — still recognized it as destructive. That's layer 2 catching what a blocklist never could."*

## ✦ ACT 3 — the explanation layer (the "why", ~30s)

Confirm one and read the output out loud — this is the differentiator vs. any blocklist:

```bash
intentguard rm -rf /var/log/*              # confirm with y ONLY if safe to demo
```

Read the plain-English explanation + safer alternative. Say: *"It doesn't just say NO — it tells you what would happen and gives you a safer command. That's layer 3, the LLM."*

## ✦ ACT 4 — the honest answers (judge Q&A, ~30s)

Preempt the two guaranteed questions:

**"What if someone calls `/bin/rm` directly, or uses another shell?"**
> *"They get past it — it's a shell-level safety net for well-intentioned mistakes, not a security boundary against an attacker. That's a deliberate scoping decision; kernel-level protection is Track 1."*

**"How does this scale to a fleet?"**
> *"It's pure rules + a small model + cheap on-demand calls, all local. Rolling it out = one `source` line in a shared bashrc. Policy, logging, and central tuning are the natural roadmap."*

**"Where was the model trained?"**
> *"Locally, on CPU, on a self-curated 318-command dataset. The demo has zero live cloud dependency — Groq is only consulted for explanations on already-flagged commands."*

---

## Closed-window fallbacks (no internet / no Groq key)

- Without `GROQ_API_KEY`, flagged commands still show the warning with a **local fallback explanation** — the demo doesn't stall.
- Train the model once before the pitch: `python -m intentguard.classifier.train --ngram 1 3`.
- If the terminal font mangles the ⚠ emoji, run the flag with output piped through a simple `cat` — or pre-render the expected warning text in a slide.

## Timing checklist

- [ ] `intentguard echo demo-ok` fast (< 1s)
- [ ] `rm -rf /` → red warning, no execution
- [ ] `ls -la` → invisible pass-through
- [ ] `dd if=/dev/zero of=/dev/sda` → warning
- [ ] `shred /dev/sda1` → **classifier** path warning
- [ ] confirmed command shows explanation + alternative
- [ ] total pitch time ≈ 2 minutes of live typing