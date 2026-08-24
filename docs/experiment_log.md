# Experiment Log — IntentGuard

## 2026-08-15 — Run 03: retrain for sklearn version alignment

- **Hypothesis:** re-pickling the final model under the runtime venv's scikit-learn (1.5.0) removes the `InconsistentVersionWarning` unpickle risk without changing behavior.
- **Change made:** same config as Run 02 winner (`--ngram 1 3`, `class_weight='balanced'`); no hyperparameter changes. Trigger: model.joblib was pickled on sklearn 1.9.0 but served by a 1.5.0 venv.
- **Dataset:** unchanged — 318 commands (165 safe / 153 risky), 80/20 stratified (random_state=42).
- **Environment:** Windows CPU (.venv), scikit-learn 1.5.0.
- **Result:** byte-for-byte identical metrics to Run 02 — accuracy **0.9844**, risky F1 **0.9836**, risky recall **0.9677**, risky precision **1.0000** (n=64). Confirms split determinism; zero behavioral drift. Suite green with zero version warnings post-retrain; daemon auto-restart picked up the new artifact via the code-version hash (model mtime+size included).

## 2026-08-14 — Run 01: Baseline TF-IDF + LinearSVC

- **Hypothesis:** Character n-grams over shlex-tokenized commands + LinearSVC gives meaningful F1/recall on the risky class vs. majority baseline.
- **Change made:** First training run; no tuning yet. Char analyzer, n-gram (2,4), `class_weight='balanced'`, dual=False, max_iter=1000.
- **Dataset:** 318 commands (165 safe / 153 risky), 80/20 stratified split (random_state=42).
- **Environment:** Local CPU (WSL), scikit-learn 1.9.0.
- **Metric focus (per eval.md):** F1 and recall on the risky class.
- **Result:** accuracy 0.9688, risky F1 0.9677, risky recall 0.9677, risky precision 0.9677 (n=64 test commands). Model saved to `intentguard/classifier/model.joblib`.

## 2026-08-14 — Run 02: n-gram sweep → final model

- **Hypothesis:** character n-gram range tradeoff — shorter ranges (1-3, 1-4) capture more word/stem signal and improve risky-class precision without hurting recall.
- **Change made:** swept ngram ranges (1,3), (1,4), (3,5), (2,4) — all with `class_weight='balanced'`. Also tested `--no-balance` on (1,3).
- **Dataset:** same 318 commands, same 80/20 stratified split (random_state=42).
- **Environment:** Local CPU (WSL), scikit-learn 1.9.0.
- **Result:** winner = **ngram (1,3)**: accuracy 0.9844, risky F1 **0.9836**, risky recall 0.9677, risky precision **1.000**. `--no-balance` gave identical numbers, so keep `balanced` (safer default). Only 1 error in 64: missed `systemctl stop firewalld` (risky → predicted safe). Saved as final model to `intentguard/classifier/model.joblib`.

### Comparison
| ngram | risky F1 | risky recall | risky precision | accuracy |
|-------|----------|--------------|-----------------|----------|
| (1,3) | 0.9836 | 0.9677 | 1.0000 | 0.9844 |
| (1,4) | 0.9836 | 0.9677 | 1.0000 | 0.9844 |
| (2,4) | 0.9677 | 0.9677 | 0.9677 | 0.9688 |
| (3,5) | 0.9508 | 0.9355 | 0.9667 | 0.9531 | (Classifier)

> Log every training run of the TF-IDF + LinearSVC command classifier, no matter how small the change.

---

## Experiment 1 — [date]

**Environment:** Local CPU / Kaggle (free GPU) / Colab (free GPU) — [pick one]

**Hypothesis:** [e.g. "Baseline TF-IDF (unigrams only) + LinearSVC will separate obviously-dangerous from obviously-safe commands well, but struggle on ambiguous ones like `chmod` variants."]

**Change made:**
```python
# e.g.
vectorizer = TfidfVectorizer(ngram_range=(1,1))
model = LinearSVC()
```

**Results:**

| Metric | Train | Val/Test |
|--------|-------|----------|
| Accuracy | | |
| F1 (risky class) | | |
| Precision | | |
| Recall | | |

**What happened:** [plain English]
**Why (your understanding):** [mechanistic explanation]
**Next experiment:** [what this tells you to try next — e.g. "try bigrams to capture patterns like 'rm -rf' as a unit, not two separate tokens"]

---

## Experiment 2 — [date]

**Environment:** Local CPU / Kaggle (free GPU) / Colab (free GPU) — [pick one]

**Hypothesis:**

**Change made:**
```python

```

**Results:**

| Metric | Before | After | Change |
|--------|--------|-------|--------|
| Accuracy | | | |
| F1 (risky) | | | |

**What happened:**
**Why:**
**Next experiment:**

---
