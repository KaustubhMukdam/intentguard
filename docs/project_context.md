# project_context.md

## Project
Name: IntentGuard
Status: in-progress
Started: 2026-08-11

## One-liner
An AI safety layer that intercepts Linux commands before execution, understands the *intent* behind them, and blocks/warns on destructive operations with a plain-English explanation and a safer alternative.

## Hackathon context
- Event: C-DAC "Integration of AI capabilities in the OS ecosystem"
- Track: Track 2 (AI at Application Level)
- Problem statement locked: "AI-Based System Intent Engine for Safe Linux Command Execution"
- Mode: Solo participant
- Deadline: 25 Aug 2026 (today: 11 Aug 2026 — 14 days)
- Judging criteria: innovation, feasibility, scalability, impact
- Official statement: "Create an intelligent safety layer that understands the intent behind Linux commands before they execute. The system should detect risky operations, explain their potential impact, and suggest safer alternatives to prevent accidental system damage."

## Stack
- Interception layer: Bash function/wrapper (shell hook, not a kernel module)
- Rule engine: Python (regex + lightweight command parsing via `shlex`)
- ML classifier: scikit-learn (TF-IDF + LinearSVC — same approach as my Disaster Tweet Classification project)
- LLM reasoning layer: Groq API (llama-3.3-70b-versatile), free tier
- CLI: Python (Typer or argparse)
- No frontend required for MVP; optional minimal terminal-styled HTML demo page for the pitch
- **Compute for heavier inference/training:** laptop is CPU-only, but the classifier is trained offline, not at demo-time — so if a heavier model is worth trying (e.g. a small transformer instead of TF-IDF+SVC, or a larger hyperparameter/embedding search), training runs on **Kaggle Notebooks or Google Colab free GPU tier**, then the final serialized model (`model.joblib` or exported weights) is downloaded and used for **local, lightweight inference** at demo time. The live demo itself never depends on live cloud compute — that would be a latency and reliability risk during the actual pitch.

## Compute strategy (updated 11 Aug 2026)
- **Default path (MVP):** TF-IDF + LinearSVC trains fine on CPU locally in seconds — no cloud needed for the baseline classifier.
- **Escalation path (if needed):** if local experiments show TF-IDF+SVC plateauing, or if there's appetite to try a small embedding-based classifier (e.g. sentence-transformers + a shallow classifier head) for better handling of paraphrased/novel dangerous commands, move that specific training run to Kaggle/Colab free GPU.
- **Hard rule:** whatever trains on Kaggle/Colab must export to a small artifact (`.joblib`, `.onnx`, or safetensors) that runs locally, offline, on the laptop for the actual demo. No live notebook dependency during the pitch — that's a single point of failure judges will notice if it lags or fails.
- This also strengthens the "free-tier only, no paid infra" story for the submission — Kaggle/Colab GPU is still free tier, just a different free tier for the training step specifically.

## Key decisions made
- Chose a **shell wrapper**, not a kernel module — Track 1 (kernel-level) ideas are out of scope for a solo 14-day build with no kernel dev background. This is explicitly Track 2 (application level).
- Three-layer pipeline (rule engine → ML classifier → LLM explainer) instead of LLM-only — cheaper, faster, more defensible to judges as "explainable AI," and reuses the GuardianLLM architecture I already understand deeply.
- Groq for the LLM layer — free tier, fast inference, already my primary agentic coding backend.
- Scope is deliberately narrow: destructive filesystem/disk/permission commands. NOT a general-purpose NL-to-shell translator (that's a different, larger problem — Idea 7 in the same track).

## Current focus
Building the dataset of labeled safe/dangerous commands (Day 1-2 task) and the rule-engine pattern list.

## Known issues / blockers
- None yet — pre-build phase.

## What this project is NOT doing
- Not a kernel-level intrusion detection system (that's Track 1, out of scope).
- Not a natural-language-to-shell-command translator (that's the general assistant idea, out of scope for MVP — could be a stretch feature if time remains).
- Not doing real OS-level sandboxing or actual command execution interception at the syscall level — this is a shell-level wrapper, which is honestly disclosed as a scoping decision in the submission, not hidden.
- Not building for any shell other than bash for the MVP (zsh/fish support = nice-to-have).
