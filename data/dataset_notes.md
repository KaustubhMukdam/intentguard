# Dataset Notes — commands_dataset.csv

## Source
- **Origin:** Self-curated, built from scratch for this project — required for the hackathon's "original and free from plagiarism" rule.
- **Curation method:**
  1. Hand-wrote the initial ~50 "obviously dangerous" and "obviously safe" commands from personal Linux experience and known sysadmin footguns.
  2. Used LLM (Groq) to generate variations and paraphrases of each category (e.g. different flag combinations, different target paths) — this expands coverage without copying any single existing security tool's ruleset verbatim.
  3. Manually reviewed and re-labeled every generated row — do not trust generated labels blind. This is also the "understand before you use" rule from the dev system applied to data, not just code.
  4. Recorded generation prompts/method in this file for transparency (important if judges or evaluators ask how the dataset was built).
- **License:** N/A — self-authored, not scraped from any licensed dataset or copyrighted tool.
- **Created:** 11 Aug 2026, iteratively through Days 1-2.

## Structure
- **Rows:** 318 commands (as of 14 Aug 2026)
- **Columns:** `command` (string, raw command text), `label` (`safe` / `risky`)
- **Target column:** `label`
- **Feature types:** Text (command string) only for the MVP — no additional metadata features to keep the classifier simple and explainable.

## Category coverage (risky)
- Filesystem destruction: `rm -rf`, recursive deletes on system paths, wildcard deletes
- Disk-level ops: `dd` to block devices, `mkfs` on mounted/system disks
- Permission changes: `chmod -R 777 /`, ownership changes on system directories
- Process/resource exhaustion: fork bombs, unbounded background processes
- Network/firewall: disabling firewall rules, opening all ports
- Package management: force-removing critical system packages

## Category coverage (safe)
- Everyday navigation/inspection: `ls`, `cd`, `pwd`, `cat`, `grep`, `find` (non-destructive flags)
- Git workflows: `git status`, `git commit`, `git push` (non-force), `git log`
- Dev tooling: `docker ps`, `npm install`, `pip install` (non-sudo, project-scoped), `python script.py`
- Safe admin: `df -h`, `top`, `ps aux`, `systemctl status`

## Preprocessing applied
1. Whitespace normalization
2. shlex tokenization (before vectorization, not stored in the CSV itself)
3. Train/test split: 80/20 stratified (to be applied during training)

## Known issues
- Dataset size is small relative to a production classifier (hackathon time constraint) — documented honestly as a scoping limitation, not hidden.
- Class balance: 165 safe, 153 risky (roughly balanced, ~52% / ~48%)
- Coverage skews toward commands I'm personally familiar with — general Linux admin, Python/ML dev workflows.
- Ambiguous/context-dependent commands (e.g. `git push --force`) are labeled based on typical-case risk, with the limitation noted.

## Generation prompts used with LLM
For generating variations of dangerous commands:
"Generate 10 variations of the Linux command 'rm -rf /' that are still dangerous but use different flags, paths, or syntax. Make them look realistic but ensure they remain destructive."

For generating variations of safe commands:
"Generate 10 variations of the Linux command 'ls -la' that are safe and useful for everyday tasks. Use different flags, paths, or combinations that maintain safety."

## What to watch out for
If extending this dataset later: resist the temptation to just scrape an existing security tool's pattern list wholesale — regenerate/paraphrase and re-verify, both for the plagiarism rule and because it's actually better practice for building an original, defensible submission.