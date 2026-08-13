# Architecture — IntentGuard

## System overview
A bash function intercepts every command typed in a monitored shell session before it reaches bash's normal execution path. The command string is passed to a Python pipeline with three layers, evaluated in increasing cost order: a zero-cost regex rule engine catches known-catastrophic patterns instantly; anything that passes the rule engine but looks unusual goes to a locally-trained ML classifier; anything either layer flags as risky is sent to an LLM (Groq) which generates a plain-English explanation, blast-radius description, and a safer alternative command. The user sees the explanation and must explicitly confirm before the original command actually executes. Safe commands pass through with no added latency or friction.

## Component diagram (ASCII)
```
[User types command in terminal]
              |
              v
[Bash wrapper function — intercepts before execution]
              |
              v
[Python CLI entrypoint: intentguard.py]
              |
              v
+---------------------------------------------------+
|  LAYER 1 — Rule Engine (regex + shlex tokenizer)   |
|  Catches: rm -rf /, dd to block device,            |
|  chmod -R 777 /, mkfs on mounted disk, fork bombs  |
+---------------------------------------------------+
       | no match                    | match → FLAGGED
       v                              v
+---------------------------+   +----------------------+
| LAYER 2 — ML Classifier   |   |                      |
| TF-IDF + LinearSVC        |-->|  LAYER 3 — LLM        |
| scores command as         |   |  Explanation Engine   |
| safe / risky              |   |  (Groq llama-3.3-70b) |
+---------------------------+   |  generates:           |
       | safe        | risky -->|  - what it does       |
       v             +--------->|  - blast radius        |
[Execute normally]              |  - safer alternative   |
                                 +----------------------+
                                          |
                                          v
                                 [User confirmation: y/N]
                                    /              \
                              y -> execute       N -> abort, show
                              original command    suggested alternative
```

## Data flow
1. User types a command in a monitored bash session.
2. Bash wrapper captures the raw command string, passes it to `intentguard.py` instead of letting bash execute it directly.
3. Rule engine tokenizes with `shlex` and checks against the pattern list (`rules.py`). If matched → jump straight to Layer 3 with a `rule_match` reason attached (skip classifier, save time).
4. If no rule match, the command is vectorized (TF-IDF) and scored by the trained classifier. If confidence is above the risk threshold → Layer 3. If safe → return control to bash immediately.
5. Layer 3 (Groq call) receives the command + which layer flagged it + why, and returns a structured explanation (what/impact/alternative).
6. CLI prints the explanation and prompts for confirmation.
7. On confirm → original command is executed via `subprocess`/`os.system`. On decline → aborted, safer alternative is optionally offered to run instead.

## Key interfaces
- Bash ↔ Python: command string passed as an argument to the CLI entrypoint; exit code / stdout drives whether bash proceeds.
- Python ↔ Groq: standard `/v1/chat/completions`-style call, prompted to return structured JSON (explanation, impact, alternative) for reliable parsing — no free-text parsing hacks.
- Rule engine ↔ Classifier: rule engine result is passed as a feature/flag into the final decision, not just an on/off gate — this lets the writeup honestly say "layered defense-in-depth," not "if/else chain."

## Training vs. inference environment
This architecture diagram describes the **runtime/demo path only** — everything in it runs locally, on CPU, at demo time. The **classifier's training** is a separate, offline step that can happen wherever it's most convenient:
- Baseline (TF-IDF + LinearSVC): trains locally on CPU in seconds — no cloud needed.
- Optional heavier classifier experiments (only if time allows and the baseline shows real gaps): trained on Kaggle Notebooks or Google Colab free GPU, then the resulting model artifact is exported and copied into `intentguard/classifier/model.joblib` (or equivalent), so Layer 2 at runtime is always just loading a local file — it never makes a network call to Kaggle/Colab. This keeps the live pipeline's dependency graph identical regardless of where training happened.

## Security considerations
- [ ] API keys (Groq) loaded from environment variables only, never hardcoded — matches personal dev system rules.
- [ ] Explicitly disclose in the submission that this is a shell-level safety net, not a kernel-level security boundary (see `tech_stack.md` tradeoffs) — get ahead of the obvious judge question instead of getting caught by it.
- [ ] No command output/history is sent anywhere except the command string itself to Groq — minimize what leaves the machine.
