# Folder Structure — IntentGuard

```
intentguard/
├── shell/
│   └── intentguard.sh          # bash wrapper function, sourced in .bashrc
├── intentguard/
│   ├── __init__.py
│   ├── cli.py                  # thin client — spawns/reuses daemon, sends one command, renders prompt
│   ├── daemon.py               # background daemon — holds loaded model, evaluates over socket
│   ├── socketutil.py           # portable IPC endpoint (Unix socket on Linux, TCP loopback on Windows)
│   ├── audit.py                # JSONL audit trail of flagged commands (~/.intentguard/audit.jsonl)
│   ├── rules.py                # regex/pattern definitions for known-catastrophic commands
│   ├── tokenizer.py            # shlex-based safe command tokenization
│   ├── classifier/
│   │   ├── __init__.py
│   │   ├── train.py            # trains TF-IDF + LinearSVC on labeled dataset
│   │   ├── predict.py          # loads trained model, scores a command
│   │   └── model.joblib        # serialized trained model (generated, gitignored)
│   ├── llm/
│   │   ├── __init__.py
│   │   ├── client.py           # Groq API wrapper
│   │   └── prompts.py          # structured prompt templates for explanation generation
│   └── decision.py             # ties rule + classifier + LLM output into final flag/explain/confirm flow
├── data/
│   ├── commands_dataset.csv    # labeled safe/dangerous commands (self-curated, see data_doc.md)
│   └── dataset_notes.md        # sourcing/curation notes for originality/plagiarism disclosure
├── tests/
│   ├── test_rules.py
│   ├── test_classifier.py
│   ├── test_llm.py
│   ├── test_nl.py
│   ├── test_audit.py
│   ├── test_runtime.py
│   └── test_pipeline.py        # end-to-end tests using canned dangerous/safe commands
├── docs/                        # all docs from this dev system live here
│   ├── project_context.md
│   ├── PRD.md
│   ├── tech_stack.md
│   ├── architecture.md
│   ├── folder_structure.md
│   ├── tasks.md
│   ├── design_prompt.md
│   ├── test-cases.md           # manual test cases to run on Windows PowerShell
│   ├── learnings.md
│   ├── debug_log.md
│   ├── experiment_log.md
│   ├── model_card.md
│   ├── data_doc.md
│   └── eval.md
├── demo/
│   └── demo_script.md          # exact commands to run live for judges, in order
├── requirements.txt
├── README.md                    # submission-facing readme, judges will read this first
└── .env.example                 # GROQ_API_KEY=your_key_here
```

## Naming conventions
- Python files: snake_case (`predict.py`, `test_pipeline.py`)
- Rule pattern constants: SCREAMING_SNAKE_CASE (`DANGEROUS_RM_PATTERN`)
- CLI-facing functions: verb-first (`evaluate_command()`, `explain_risk()`)
- Dataset labels: `safe` / `risky` (binary, consistent lowercase strings across dataset and code)
