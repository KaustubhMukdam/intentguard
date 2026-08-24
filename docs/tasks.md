# Tasks — IntentGuard

> Note: hackathon runs 28 Jul – 25 Aug 2026. Today is 15 Aug — 10 days remain. Plan below is built for that.

## Current queue (updated 15 Aug evening)
| # | Task | State |
|---|------|-------|
| 1 | Latency fix (daemon boot race, fast-fail LLM, model swap) | ✅ done |
| 2 | Transport round-trip unit test | ✅ done |
| 3 | Audit trail (`audit.py`, JSONL) | ✅ done |
| 4 | Recursive-force-delete rule (`rm -rf myproject` now prompts) | ✅ done |
| 5 | NL mode (`--ask "intent"` → vetted suggestion) | ✅ done |
| 5b | Stale-daemon auto-restart (ping/shutdown code-version handshake) | ✅ done |
| 6 | Real-time shell integration — prefix wrapper quoting fixed (`printf %q` + `shlex.quote` canonical form); optional `shell/intentguard-demo.sh` shim mode (throwaway-only, fail-closed, `unshim` to revert); `--ask` works via wrapper | ✅ done |
| — | Retrain model locally (kills sklearn 1.9-vs-1.5 warning) | ✅ done — Run 03 logged, metrics identical, zero warnings |
| — | Final docs batch: README feature list, test-cases NL section | ✅ done |
| — | Backup demo video (your manual task) | ⬜ before submission |

**Verified end-to-end (15 Aug, WSL):** flagged→real LLM explanation ✓ · N aborts/y proceeds ✓ · /tmp exempt ✓ · `--ask` safe+suggestion ✓ · destructive intent caught by own pipeline ✓ · demo shims ✓ · audit JSONL ✓. A Groq **429 rate-limit** during the sweep is expected free-tier behavior and degrades gracefully to the local fallback explanation — not a bug.


## In progress
- [x] Set up `intentguard/` folder structure per `folder_structure.md`
- [x] Start curating `data/commands_dataset.csv` — labeled safe vs. risky commands

## Up next (Days 1–2 · Aug 11–12) — Foundation
- [x] Repo scaffold + folder structure
- [x] Write `dataset_notes.md` documenting how commands are sourced/curated (originality trail)
- [x] Curate first pass of labeled dataset: 150–250 commands, roughly balanced safe/risky, covering: destructive filesystem ops, disk ops (`dd`, `mkfs`), permission changes, fork bombs, network/firewall changes, package removal, and a wide range of everyday safe commands (`ls`, `git`, `cd`, `grep`, `docker ps`, etc.)
- [x] Draft the rule engine pattern list in `rules.py` (10–15 hardcoded catastrophic patterns)

## Days 3–4 (Aug 13–14) — Rule engine + tokenizer
- [x] Implement `tokenizer.py` (shlex-based)
- [x] Implement `rules.py` matching logic + unit tests (`test_rules.py`)
- [x] Confirm rule engine catches all MVP acceptance-criteria commands with zero false positives on 10 sample safe commands

## Days 5–7 (Aug 15–17) — ML classifier
- [x] Finalize dataset (target 300+ labeled examples if time allows) — 318 commands (165 safe / 153 risky)
- [x] `train.py`: TF-IDF + LinearSVC pipeline, train/test split — train locally on CPU (this is fast, no cloud needed for the baseline)
- [x] Log first training run in `experiment_log.md` (note environment: local CPU)
- [x] Establish baseline metric (majority-class baseline) in `eval.md`
- [x] Iterate: try adjusting TF-IDF n-gram range, class weighting for imbalance — log each attempt
- [x] **Decision point:** baseline is strong (risky F1 0.984, recall 0.968, precision 1.000) — clearly not missing a category, so no heavier experiment needed; skip to Day 8
- [ ] *(Optional, only if triggered above)* Set up a Kaggle Notebook or Colab notebook with free GPU, run the heavier experiment (e.g. embedding-based classifier), export the resulting model artifact, download it into `intentguard/classifier/model.joblib`, confirm it loads and runs locally with no cloud dependency
- [x] Fill in `model_card.md` once a final model is picked, noting which environment it was trained in

## Days 8–10 (Aug 18–20) — LLM layer + integration
- [x] `llm/prompts.py`: structured prompt for explanation/impact/alternative (force JSON output)
- [x] `llm/client.py`: Groq API wrapper, env-var key loading
- [x] `decision.py`: wire rule engine → classifier → LLM → confirmation flow together
- [x] `shell/intentguard.sh`: bash wrapper function, source in `.bashrc`, test interception works end-to-end
- [x] End-to-end smoke test: type a dangerous command in terminal, see explanation, confirm/decline both paths work

## Days 11–12 (Aug 21–22) — Testing & edge cases
- [x] `test_pipeline.py`: canned dangerous + safe commands, assert correct routing through all 3 layers
- [x] Test latency end-to-end — confirm flagged-command path stays under ~3 seconds
- [x] Test edge cases: quoted/escaped dangerous commands, commands with sudo prefix, chained commands (`&&`, `;`, `|`)
- [x] Fix false positives/negatives found during testing

## Day 13 (Aug 23) — Polish
- [x] Write submission-facing `README.md`
- [x] Write `demo/demo_script.md` — exact sequence of commands to run live, in the order that creates the strongest "oh it caught that" moment early
- [ ] Record backup demo video in case live demo has issues — **your task**: run `demo/demo_script.md` on a recorder (OBS/terminal recorder) per the timing checklist
- [x] Clean up code — remove debug prints, dead code, unused imports (anti-vibe-coding checklist)

## Day 14 (Aug 24) — Buffer
- [x] Final run-through of demo script, timed — cold-start fixed (~2.8s → ~200ms/command via persistent daemon + thin CLI)
- [x] Fix anything that broke during polish — daemon prewarm + model cache
- [ ] Prepare 2-3 sentence answer for: "what happens if someone bypasses the wrapper?" and "how does this scale to a fleet?" (anticipated judge questions) — drafted in `demo/demo_script.md` ACT 4; **your task is to keep these in your head, not code**

## Post-Day-14 (Aug 15) — Windows transport fix
- [x] **Found:** native Windows Python 3.11 has no `AF_UNIX` support → `intentguard.cli` reported "failed to start daemon" (daemon crashed at socket bind; unit suite passed because it never exercised cli/daemon)
- [x] Fixed via `intentguard/socketutil.py` — Unix socket on Linux/WSL, TCP loopback (`127.0.0.1:45670`) on Windows; both daemon + CLI resolve the same endpoint
- [x] Verified end-to-end on Windows PowerShell: safe pass-through, rule_engine flag, classifier flag (conf 0.73), y/N paths, live Groq explanations
- [x] Added `docs/test-cases.md` — manual PowerShell test cases (safe / dangerous / edge / transport regression)
- [x] **Task 1 — latency:** daemon binds instantly (lazy `importlib` pipeline import, no blocking prewarm); Groq capped at 3s/0 retries; dead `llama-3.3-70b-versatile` replaced by `openai/gpt-oss-120b` (+ `GROQ_MODEL` env override); stderr hint on fallback explanations
- [x] **Task 2 — transport round-trip unit test** (`tests/test_runtime.py`): real daemon on a stubbed test port, client talks through production code path
- [x] **Task 3 — audit trail:** `intentguard/audit.py`, JSONL per flagged command in `~/.intentguard/audit.jsonl`, best-effort I/O, TDD'd in `tests/test_audit.py`
- [ ] **Known issue (queued):** sklearn version mismatch — `model.joblib` pickled on 1.9.0, venv runs 1.5.0 (`InconsistentVersionWarning`). Fix: retrain locally (`python -m intentguard.classifier.train --ngram 1 3`) or pin sklearn
- [x] **Task 4 — recursive-force rule:** `rm -rf <any non-temp path>` now prompts (medium risk); `/tmp` + `/var/tmp` exempt; system dirs stay critical; plain `rm file.txt` still frictionless. TDD'd in `tests/test_rules.py::RecursiveForceDeleteSpec`
- [x] ~~transport round-trip unit test~~ → **done as Task 2** (`tests/test_runtime.py::TransportRoundTripSpec`)

## Aug 25 — Submit
- [ ] Final submission before deadline

## Blocked
- [ ] None yet

## Ideas / backlog (only if time remains after Day 12)
- [ ] Natural-language mode — **being built now as Task 5** (`--ask`)
- [x] Session logging/audit trail for the "scalability" pitch — **done as Task 3**
- [ ] zsh support — *recommend skipping*: bash is the stated MVP target, disclose in pitch instead