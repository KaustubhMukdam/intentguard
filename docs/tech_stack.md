# Tech Stack — IntentGuard

## Interception layer
| Technology | Why chosen |
|------------|------------|
| Bash function wrapper (shell hook via `.bashrc` sourcing) | Only way to intercept commands *before* execution without kernel access. Zero install friction for judges — one `source` line. |

## Rule engine
| Technology | Why chosen |
|------------|------------|
| Python 3 | Consistency with rest of stack, fast to iterate |
| `re` (regex) | Instant pattern matching for known-catastrophic commands, zero latency, zero API cost |
| `shlex` | Safely tokenizes commands so pattern matching isn't fooled by quoting/escaping tricks |

## ML classifier
| Technology | Why chosen |
|------------|------------|
| scikit-learn | Standard toolkit, well-documented, I already know this workflow from Disaster Tweet Classification |
| TF-IDF vectorizer | Commands are short text sequences — same reasoning as tweet classification, proven approach for me |
| LinearSVC | Fast to train on CPU, no GPU needed, interpretable enough to explain in the submission writeup |
| joblib | Model serialization/loading |

## Training compute (updated)
| Environment | Used for | Why |
|-------------|----------|-----|
| Local CPU (laptop) | TF-IDF + LinearSVC baseline training, all local inference at demo time | Trains in seconds, no GPU needed for this model class, zero setup overhead |
| Kaggle Notebooks / Google Colab (free GPU tier) | *Optional escalation* — only if baseline plateaus and a heavier approach is worth testing (e.g. sentence-embedding-based classifier, small transformer fine-tune, larger hyperparameter search) | Free GPU compute the laptop doesn't have; used strictly as an offline training environment, never as a live dependency |

**Rule for using cloud compute:** train there, export a small local-runnable artifact, bring it back down. The demo must never call out to a live Kaggle/Colab session — that introduces latency and a failure point during the pitch that a fully local pipeline doesn't have.

## Alternatives considered

## LLM reasoning layer
| Technology | Why chosen |
|------------|------------|
| Groq API (llama-3.3-70b-versatile) | Free tier, extremely fast inference (matters for live demo latency), already my primary agentic backend — reused routing pattern from opencode setup |

## CLI / packaging
| Technology | Why chosen |
|------------|------------|
| Python (argparse or Typer) | Simple, no extra dependency weight for a hackathon MVP |

## Alternatives considered
- **eBPF/kernel hooking for true interception** — rejected: requires kernel dev expertise and safe test environment I don't have time to build in 14 days solo; also explicitly Track 1, not this problem statement's track.
- **LLM-only pipeline (skip rule engine + classifier)** — rejected: slower (every command needs an API call), more expensive on rate-limited free tier, and less defensible to judges asking "why not just regex/ML, why LLM at all" — the layered approach answers both "why AI" and "why not *just* AI."
- **Fine-tuning a small local model instead of TF-IDF+SVC** — not fully rejected, downgraded to optional: local laptop alone can't do this, but Kaggle/Colab free GPU makes it feasible as a stretch experiment *if* the baseline classifier shows a real gap (e.g. missing paraphrased/novel dangerous commands). Only pursued if time allows after the MVP pipeline works end-to-end — the baseline TF-IDF+SVC is still the default and the fallback if the heavier experiment doesn't finish in time.

## Known tradeoffs
- Shell-wrapper interception can be bypassed by a determined user (e.g. calling `/bin/rm` directly, or a different shell). This is disclosed explicitly in the pitch as a scoping decision, not hidden — the tool is a safety net for well-intentioned mistakes, not an adversarial security boundary.
- Groq free tier has rate limits — mitigated by only calling the LLM layer when the rule engine or classifier actually flags something, not on every single command.
- Splitting training (cloud) from inference (local) adds a manual export/download step between Kaggle/Colab and the repo — small workflow overhead, but avoids the much bigger risk of a live demo depending on external compute availability.
