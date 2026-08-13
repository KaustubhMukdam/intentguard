# Tasks — IntentGuard

> Note: hackathon runs 28 Jul – 25 Aug 2026. Today is 11 Aug — 14 days remain, not 3 weeks. Plan below is built for that.

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
- [ ] Finalize dataset (target 300+ labeled examples if time allows)
- [ ] `train.py`: TF-IDF + LinearSVC pipeline, train/test split — train locally on CPU (this is fast, no cloud needed for the baseline)
- [ ] Log first training run in `experiment_log.md` (note environment: local CPU)
- [ ] Establish baseline metric (majority-class baseline) in `eval.md`
- [ ] Iterate: try adjusting TF-IDF n-gram range, class weighting for imbalance — log each attempt
- [ ] **Decision point:** if the baseline classifier is clearly missing a category of dangerous commands (e.g. paraphrased/novel phrasing the TF-IDF vocabulary doesn't cover), decide whether it's worth a heavier experiment. If yes → move to Kaggle/Colab for that specific run only (see below). If the baseline is good enough, skip straight to Day 8.
- [ ] *(Optional, only if triggered above)* Set up a Kaggle Notebook or Colab notebook with free GPU, run the heavier experiment (e.g. embedding-based classifier), export the resulting model artifact, download it into `intentguard/classifier/model.joblib`, confirm it loads and runs locally with no cloud dependency
- [ ] Fill in `model_card.md` once a final model is picked, noting which environment it was trained in

## Days 8–10 (Aug 18–20) — LLM layer + integration
- [ ] `llm/prompts.py`: structured prompt for explanation/impact/alternative (force JSON output)
- [ ] `llm/client.py`: Groq API wrapper, env-var key loading
- [ ] `decision.py`: wire rule engine → classifier → LLM → confirmation flow together
- [ ] `shell/intentguard.sh`: bash wrapper function, source in `.bashrc`, test interception works end-to-end
- [ ] End-to-end smoke test: type a dangerous command in terminal, see explanation, confirm/decline both paths work

## Days 11–12 (Aug 21–22) — Testing & edge cases
- [ ] `test_pipeline.py`: canned dangerous + safe commands, assert correct routing through all 3 layers
- [ ] Test latency end-to-end — confirm flagged-command path stays under ~3 seconds
- [ ] Test edge cases: quoted/escaped dangerous commands, commands with sudo prefix, chained commands (`&&`, `;`, `|`)
- [ ] Fix false positives/negatives found during testing

## Day 13 (Aug 23) — Polish
- [ ] Write submission-facing `README.md`
- [ ] Write `demo/demo_script.md` — exact sequence of commands to run live, in the order that creates the strongest "oh it caught that" moment early
- [ ] Record backup demo video in case live demo has issues
- [ ] Clean up code — remove debug prints, dead code, unused imports (anti-vibe-coding checklist)

## Day 14 (Aug 24) — Buffer
- [ ] Final run-through of demo script, timed
- [ ] Fix anything that broke during polish
- [ ] Prepare 2-3 sentence answer for: "what happens if someone bypasses the wrapper?" and "how does this scale to a fleet?" (anticipated judge questions)

## Aug 25 — Submit
- [ ] Final submission before deadline

## Blocked
- [ ] None yet

## Ideas / backlog (only if time remains after Day 12)
- [ ] Natural-language mode (borrowing from Idea 7's spirit, as a bonus feature)
- [ ] Session logging/audit trail for the "scalability" pitch
- [ ] zsh support