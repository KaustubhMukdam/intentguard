# Model Card — IntentGuard Command Risk Classifier

## Model overview
- **Type:** Linear Support Vector Classifier (LinearSVC) over TF-IDF features
- **Task:** Binary classification — Linux command text → `safe` / `risky`
- **Training date:** 2026-08-14 (Run 02); re-pickled 2026-08-15 (Run 03) under the serving venv's scikit-learn to eliminate the unpickle version mismatch
- **Framework:** scikit-learn 1.5.0 (runtime venv; metrics identical to the original 1.9.0 run)
- **Training environment:** Local CPU — no cloud needed; inference always runs locally on CPU

## Training data
- **Source:** Self-curated dataset — see `data_doc.md` for full sourcing/curation notes
- **Size:** 318 commands
- **Features used:** shlex-tokenized command string → TF-IDF vector, character analyzer, n-gram range (1,3)
- **Target variable:** `label` — 52% safe (165), 48% risky (153)
- **Preprocessing:** shlex tokenization before vectorization; stratified 80/20 train/test split (random_state=42)

## Performance

| Metric | Train | Test |
|--------|-------|------|
| Accuracy | — | 0.984 |
| F1 (risky class) | — | 0.984 |
| Precision (risky) | — | 1.000 |
| Recall (risky) | — | 0.968 |

*(From `experiment_log.md` Run 02 — final model, ngram (1,3). Full rationale in `eval.md`.)*

## What it does well
Reliably separates commands with clear destructive verbs (rm, dd, mkfs, chmod, chown, shred, wipefs, ufw/iptables, destructive package removal) from routine commands (ls, git, cd, pip, docker, systemctl status, ssh, curl). Perfect precision on the risky class in the held-out test — zero false alarms in 64 samples.

## Known limitations
- Missed `systemctl stop firewalld` in initial testing (predicted safe) — since addressed by adding a firewall pattern to the rule engine (`systemctl stop|disable firewalld`, `service firewalld stop`) rather than the model; service-stop commands targeting security daemons remain a category the training data under-represents.
- Struggles with novel/obfuscated dangerous commands not resembling training examples.
- No context awareness: `git push --force` is fine solo, catastrophic on a shared branch — the model labels by typical-case risk only.

## Bias and fairness
- Not applicable in the demographic sense — this classifies command text, not people.
- **Coverage bias to disclose honestly:** the dataset skews toward commands familiar to a general Linux/Python-ML admin workflow. It under-represents domain-specific dangerous commands (database admin, network-heavy ops) — noted as a known limitation, not hidden.

## Intended use
Flagging destructive Linux commands for confirmation before execution, as one layer in a defense-in-depth pipeline (rule engine catches the obvious cases first; classifier catches the ambiguous ones the rule engine misses).

## Out-of-scope use
- Not intended as a standalone security boundary against an adversarial/malicious user.
- Not intended for languages/shells other than bash command syntax it was trained on.
- Not a replacement for the rule engine — it's a complementary layer, not the sole gate.
