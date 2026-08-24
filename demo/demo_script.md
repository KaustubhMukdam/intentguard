# IntentGuard — Demo Scripts

## PART A — VIDEO RECORDING SCRIPT (~2.5 min, for YouTube submission)

**Setup before recording:** open a WSL terminal, font size 18+, repo root.
Run `intentguard echo warmup` once (daemon boot happens off-camera), then start
recording. Speak slowly and politely.

---

### Scene 1 — Hook (0:00–0:25)

TYPE:
```bash
intentguard rm -rf /
```
SAY:
> "Hi, I'm Kaustubh, and this is IntentGuard. I just typed a command that would
> delete every file on this Linux system. Before bash could run it, IntentGuard
> stopped it — and explained exactly what would have happened."

Press **N**. SAY: "I'll decline, of course."

### Scene 2 — Zero friction on safe commands (0:25–0:45)

TYPE:
```bash
intentguard ls -la
intentguard git status
```
SAY:
> "Everyday commands pass through instantly — no prompts, no waiting. IntentGuard
> speaks up only when something is genuinely dangerous."

### Scene 3 — Not just a blocklist: the ML layer (0:45–1:20)

TYPE:
```bash
intentguard shred /dev/sda1
```
SAY:
> "'shred' is not in any hardcoded blocklist. Our machine-learning model — trained
> locally on CPU, on a self-curated dataset of 318 commands — recognized it as
> destructive and flagged it. This is layer two catching what rules can't."
Press **N**.

### Scene 4 — The explanation layer (1:20–1:50)

TYPE:
```bash
mkdir -p /tmp/demo-logs && intentguard rm -rf /tmp/demo-logs
```
SAY (while reading the prompt):
> "When a command IS flagged, you get a plain-English explanation: what it does,
> its blast radius, and a safer alternative. That's layer three, powered by an
> LLM through the Groq API."
Press **N**.

### Scene 5 — AI suggestions, vetted by our own pipeline (1:50–2:20)

TYPE:
```bash
intentguard --ask "show disk usage"
```
SAY: "You can also describe what you want in plain English."

Then TYPE:
```bash
intentguard --ask "delete everything in /etc"
```
SAY:
> "But watch this — I asked for something dangerous. The assistant suggests a
> command… and IntentGuard's own safety pipeline flags that suggestion before
> anything happens. Even AI output gets checked here."

Press **N** if prompted.

### Scene 6 — Close (2:20–2:40)

SAY:
> "IntentGuard: rule engine for instant catches, machine learning for novel ones,
> and an LLM that explains in plain language. Built solo, free-tier only.
> Thank you for watching."

Upload as **Unlisted** on YouTube; paste link in the submission form.

---

## PART B — LIVE PITCH SCRIPT (original)

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
intentguard echo warmup          # pays the one-time daemon boot
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

Turn it toward the classifier:

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
