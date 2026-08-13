# Evaluation — IntentGuard

## Why these metrics

**Primary metric: F1 score on the `risky` class**
**Why:** This is a safety tool — the cost of a false negative (missing a genuinely destructive command) is much higher than a false positive (an extra confirmation prompt on something actually safe). Plain accuracy would be misleading if the dataset is imbalanced, and doesn't tell you which *kind* of error the model is making. F1 on the risky class specifically forces attention on recall (catching dangerous commands) without ignoring precision (not crying wolf on every command).

**Secondary metric: Recall on the `risky` class, tracked separately**
**Why:** For this specific use case, recall matters more than precision — a missed dangerous command (false negative) can cause irreversible damage, while a false positive just costs the user one extra confirmation prompt. Worth reporting recall on its own, not just buried inside F1, because it's the number that answers "how safe is this, really."

## Baseline
**Majority-class baseline:** predict the more common label for every command. This should sit around [X]% accuracy (fill in once dataset composition is final) — establishes the floor the actual model has to beat meaningfully.

**Rule-engine-only baseline:** what does the pattern-matching layer alone catch, before the classifier is added at all? This is actually the more honest baseline for this project specifically, since the rule engine already exists as Layer 1 — the classifier's whole value proposition is catching what rules *miss*. Report this explicitly: "Rule engine alone catches X% of the risky test set; adding the classifier catches Y% additional."

## Results vs baseline

| Approach | F1 (risky) | Recall (risky) | Precision (risky) | Accuracy |
|----------|------------|-----------------|---------------------|----------|
| Majority-class baseline | | | | |
| Rule engine only | | | | |
| Rule engine + Classifier (final) | | | | |

*(Fill in from `experiment_log.md` final run)*

## Error analysis
[Once trained: look at the confusion matrix specifically for the risky class. Which dangerous commands got missed (false negatives)? Are they a pattern — e.g. all obfuscated/unusual phrasing? Which safe commands got flagged (false positives) — are they annoyingly common ones that would make the tool feel untrustworthy in daily use?]

For this project, **false negatives are strictly worse than false positives** — a missed `rm -rf /important_data` is real damage; an extra confirmation on a harmless command is a minor annoyance. If forced to tune the threshold one way, tune toward higher recall even at some precision cost, and say so explicitly in the writeup — it's a defensible, judge-legible design decision, not an oversight.

## What the numbers actually mean
[Fill in with plain-English translation once final numbers exist — e.g. "A recall of 0.85 on the risky class means the classifier layer alone catches 85% of dangerous commands the rule engine misses, without the LLM layer needing to be consulted for those already-classified ones. Combined with the rule engine's deterministic catch rate on known patterns, the full pipeline's effective catch rate is higher than either layer alone."]
