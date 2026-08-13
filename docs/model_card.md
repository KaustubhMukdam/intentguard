# Model Card — IntentGuard Command Risk Classifier

## Model overview
- **Type:** Linear Support Vector Classifier (LinearSVC) over TF-IDF features
- **Task:** Binary classification — Linux command text → `safe` / `risky`
- **Training date:** [fill in]
- **Framework:** scikit-learn [version]
- **Training environment:** Local CPU (laptop) / Kaggle Notebook (free GPU) / Google Colab (free GPU) — [pick one; note that inference always runs locally on CPU regardless of where training happened]

## Training data
- **Source:** Self-curated dataset — see `data_doc.md` for full sourcing/curation notes
- **Size:** [rows] commands
- **Features used:** Raw command string → TF-IDF vector ([n-gram range])
- **Target variable:** `label` — [X]% safe, [Y]% risky
- **Preprocessing:** shlex tokenization before vectorization; [stratified train/test split — fill in ratio]

## Performance

| Metric | Train | Test |
|--------|-------|------|
| Accuracy | | |
| F1 (risky class) | | |
| Precision (risky) | | |
| Recall (risky) | | |

*(Fill in from final run in `experiment_log.md` and full rationale in `eval.md`)*

## What it does well
[e.g. "Reliably separates commands with clear destructive verbs (rm, dd, mkfs, chmod -R) from routine commands (ls, git, cd)."]

## Known limitations
[Be honest — e.g. "Struggles with novel/obfuscated dangerous commands not resembling training examples; struggles with commands that are dangerous only in specific contexts (e.g. `git push --force` is fine solo, catastrophic on a shared branch — the model has no context awareness of *who else* depends on the target)."]

## Bias and fairness
- Not applicable in the demographic sense — this classifies command text, not people.
- **Coverage bias to disclose honestly:** the dataset skews toward commands I'm familiar with (general Linux admin, Python/ML dev workflows). It may under-represent domain-specific dangerous commands (e.g. database admin, networking-heavy ops) — noted as a known limitation, not hidden.

## Intended use
Flagging destructive Linux commands for confirmation before execution, as one layer in a defense-in-depth pipeline (rule engine catches the obvious cases first; classifier catches the ambiguous ones the rule engine misses).

## Out-of-scope use
- Not intended as a standalone security boundary against an adversarial/malicious user.
- Not intended for languages/shells other than bash command syntax it was trained on.
- Not a replacement for the rule engine — it's a complementary layer, not the sole gate.
