# Hiver SDE Intern Take-Home — AppleSupport Memory + Risk Gate

## What this demonstrates

This is a compact support-automation prototype for **AppleSupport** using the [Customer Support on Twitter (TWCS) dataset](https://www.kaggle.com/datasets/thoughtvector/customer-support-on-twitter). It makes a trust decision rather than acting as a generic chatbot:

`customer message → intent → historical support memory → draft → risk gate → AUTO-HANDLE / ESCALATE`

The repository ships a 990-case AppleSupport-derived sample, not the roughly 500 MB TWCS raw CSV. The raw file is intentionally ignored; place it at `data/raw/twcs.csv` only to reproduce preprocessing.

## Quick reproduction (no API key; under 15 minutes)

```bash
python3 -m pip install -r requirements.txt
python3 run.py --demo
python3 run.py --evaluate
```

The evaluation regenerates `results/metrics.json`, `results/intent_confusion_matrix.png`, and the ignored local `results/agent_outputs.jsonl`. It evaluates the committed 990-case retrieval/training sample against the 200-row golden set. A full raw-data rebuild is optional:

```bash
python3 src/build_case_store.py
```

## Verified deterministic results

The final deterministic run reports the following values from `results/metrics.json`:

| System | Intent accuracy | Intent macro-F1 |
|---|---:|---:|
| Always-`account_access` trivial baseline | 0.100 | 0.018 |
| TF-IDF + logistic regression simple baseline | 0.600 | 0.570 |
| Rule intent benchmark | 0.910 | 0.833 |
| Support-memory + risk-gate agent | 0.910 | 0.833 |

Routing for the deterministic agent: accuracy **0.940**, AUTO-HANDLE precision **0.969**, AUTO-HANDLE recall **0.912**, and unsafe-auto rate **0.031** (3 false AUTO-HANDLE decisions among 98 gold escalations).

These are deterministic-path results only. The final draft is a named `deterministic_template`; it is not presented as LLM-generated or as a retrieved historical reply. Retrieval still informs the risk gate through evidence strength and private-handoff precedent.

## Data, taxonomy, and leakage control

- **Taxonomy:** `account_access`, `billing_purchase`, `purchase_refund`, `subscription`, `connectivity`, `messages_calls`, `apps_appstore`, `battery_charging`, `software_update`, and `device_hardware`.
- **Golden set:** 200 candidate-reviewed examples, 20 per intent. The review policy and provenance are in `data/golden/`.
- **Integrity check:** this checkout has 0 duplicate golden IDs, 0 duplicate normalized texts, and 0 customer-ID or normalized-text overlaps between the golden set and committed retrieval sample.
- **Corrections:** `data/golden/annotation_corrections.csv` is the row-level correction mechanism. The evaluator applies it to the immutable base set rather than treating it as a replacement dataset.

Initial stratification was rule-assisted, so the benchmark is not an independent random annotation study. Candidate review is self-review, not third-party annotation. The simple baseline is trained on weak labels from the deterministic classifier; it is a transparent engineering baseline, not an independent estimate of real-world model quality.

## Optional LLM drafting path

```bash
export OPENAI_API_KEY="..."
export OPENAI_MODEL="..."
# Optional for an OpenAI-compatible provider such as OpenRouter:
export OPENAI_BASE_URL="https://openrouter.ai/api/v1"
python3 run.py --demo --llm --message "My iPhone battery is draining after the update."
```

For the supplied free-router configuration, set `OPENAI_MODEL=openrouter/free`; the judge records its model and base URL alongside every genuine score. On a successful LLM call, `drafting_mode` is `llm_grounded` and the prompt includes the top three retrieved AppleSupport customer/support pairs. The system prompt forbids invented policy and public requests for secrets. Provider failure produces an explicit `deterministic_fallback`; it must not be reported as an LLM result. The risk gate always runs independently after drafting.

## Optional LLM-as-judge and human comparison

First create deterministic outputs, then run a 50-example judge pass:

```bash
python3 run.py --evaluate
python3 evaluation/llm_judge.py --limit 50
python3 evaluation/compare_judge.py
```

The judge uses correctness, groundedness, issue coverage, safety, and tone (0–2 each). It respects `OPENAI_BASE_URL`, uses a bounded per-call timeout, retries transient/API-format failures, and saves genuine partial scores separately if it cannot finish. It writes `results/llm_judge_scores.csv` and a 50-row agreement file only after all 50 calls complete.

`evaluation/human_judge_sheet.csv` contains 50 completed candidate-review rows. Final validation completed 50 genuine external judge calls: 18 rows used `openrouter/free` and 32 used `gemini-3.6-flash` after free-provider limits. Per-row model provenance is recorded in `results/llm_judge_scores.csv`. The matching 50-row comparison in `results/judge_human_agreement.csv` reports exact agreement / Cohen's kappa of 0.26 / -0.045 (correctness), 0.26 / -0.008 (groundedness), 0.08 / -0.062 (issue coverage), 0.92 / -0.020 (safety), 0.54 / 0.000 (tone), and 0.16 / 0.031 (total). This is a genuine mixed-provider judge run, not a single-model agreement estimate.

## Limitations, failure analysis, and next week

The strong deterministic headline is easy to overread: labels were rule-assisted and actions were candidate-reviewed under a policy similar to the risk gate. It is a bounded single-message benchmark, not proof of safe multi-turn deployment. Accuracy also hides the asymmetric cost of a false AUTO-HANDLE decision; use unsafe-auto rate and AUTO precision alongside routing accuracy.

Observed deterministic failures include Apple ID/App Store ambiguity (`G004`), payment-declined tweets dominated by update keywords (`G024`), unsupported “unsubscribe” phrasing (`G062`), recurring update/hardware failures being auto-handled (`G189`), and conservative escalation of persistent device symptoms (`G192`). See [the report](report/report.md) for the examples and next-week plan.

## Repository map

```text
data/sample_data.csv                    # 990-case committed AppleSupport sample
data/golden/                            # 200-row policy/provenance-backed golden set
src/                                    # retrieval, intent, risk gate, optional LLM path
evaluation/evaluate_all.py              # baselines and end-to-end deterministic metrics
evaluation/llm_judge.py                 # resumable 50-example external judge harness
evaluation/compare_judge.py             # 50-row judge-vs-candidate comparison
report/report.md                        # concise evaluation report
decision_log.md                         # 15 implementation decisions
```

## Attribution

The underlying source is ThoughtVector’s [Customer Support on Twitter dataset](https://www.kaggle.com/datasets/thoughtvector/customer-support-on-twitter). No raw TWCS file or external API secret is committed.
