# Experiment Log — IntentGuard (Classifier)

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
