# Data Documentation — commands_dataset.csv

## Source
- **Origin:** Self-curated, built from scratch for this project — required for the hackathon's "original and free from plagiarism" rule.
- **Curation method:**
  1. Hand-write the initial ~50-80 "obviously dangerous" and "obviously safe" commands from personal Linux experience and known sysadmin footguns.
  2. Use an LLM (ChatGPT/Groq) to *generate variations and paraphrases* of each category (e.g. different flag combinations, different target paths) — this expands coverage without copying any single existing security tool's ruleset verbatim.
  3. Manually review and re-label every generated row — do not trust generated labels blind. This is also the "understand before you use" rule from the dev system applied to data, not just code.
  4. Record generation prompts/method in this file for transparency (important if judges or evaluators ask how the dataset was built).
- **License:** N/A — self-authored, not scraped from any licensed dataset or copyrighted tool.
- **Created:** 11 Aug 2026 onward, iteratively through Days 1-7.

## Structure
- **Rows:** [fill in as dataset grows — target 300+]
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
3. [Fill in: train/val/test split ratio and whether stratified]

## Known issues
- Dataset size is small relative to a production classifier (hackathon time constraint) — documented honestly as a scoping limitation, not hidden.
- Class balance: [fill in actual split once dataset is final — aim for roughly balanced, note if not]
- Coverage skews toward commands I'm personally familiar with — see `model_card.md` bias section.
- Ambiguous/context-dependent commands (e.g. `git push --force`) are a known hard category — labeled based on typical-case risk, with the limitation noted rather than pretending the model handles context it can't see.

## What to watch out for
If extending this dataset later: resist the temptation to just scrape an existing security tool's pattern list wholesale — regenerate/paraphrase and re-verify, both for the plagiarism rule and because it's actually better practice for building an original, defensible submission.
