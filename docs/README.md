# IntentGuard — Docs Index

Read `project_context.md` first — paste it at the top of every AI chat/session (opencode, ChatGPT, Claude, etc.) per the dev system's Golden Prompt Format. Then reference the rest as needed:

| File | When to open it |
|------|------------------|
| `project_context.md` | Every session, every AI chat — paste at top |
| `PRD.md` | When unsure what's in/out of scope |
| `tech_stack.md` | When deciding a library/tool, or explaining a choice |
| `architecture.md` | Before writing pipeline/integration code |
| `folder_structure.md` | When creating new files — check where it belongs |
| `tasks.md` | Start and end of every session — update checkboxes |
| `design_prompt.md` | When building the confirmation-prompt output styling or optional demo banner |
| `test-cases.md` | Manual test cases to run on Windows PowerShell (safe/dangerous/edge cases) |
| `learnings.md` | End of every session, 5 min |
| `debug_log.md` | Whenever a non-trivial bug is solved |
| `experiment_log.md` | After every classifier training run |
| `model_card.md` | Once a final classifier is chosen |
| `data_doc.md` | Building/extending the labeled dataset |
| `eval.md` | Reporting classifier performance, writing the submission's results section |

## Current status (15 Aug 2026)
Pre-submission. MVP pipeline complete and tested (44 specs green). Runs end-to-end on
**Windows PowerShell** (daemon transport fixed — Unix socket on Linux, TCP loopback on
Windows). Next action: final demo run-through — see `tasks.md`.
