# Hiver SDE Intern Take-Home — Support Memory + Risk Gate

## Thesis

This project is intentionally not a generic RAG chatbot. It treats customer support automation as a **trust decision**:

`Customer message → intent → historical support memory → evidence-backed draft → risk gate → AUTO-HANDLE / ESCALATE`

The agent is designed to learn both **what the brand tends to do** and **when the brand historically handles cases privately**.

## Dataset

Primary dataset: ThoughtVector's Customer Support on Twitter (TWCS). Source: https://www.kaggle.com/datasets/thoughtvector/customer-support-on-twitter The raw file is **not** committed. Place it at `data/raw/twcs.csv` when reproducing the full preprocessing. A 990-case derived sample is committed at `data/sample_data.csv` for quick demonstrations.

## Reproduce

### Full preprocessing (one time)

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python src/build_case_store.py
```

This creates `data/processed/apple_cases.csv` and `data/processed/sample_data.csv`.

### Demo — no API key required

```bash
python run.py --demo
python run.py --demo --message "My iPhone battery is draining really fast after the update and I already restarted it twice."
```

### Evaluation — deterministic path

```bash
python run.py --evaluate
```

This runs the trivial baseline, TF-IDF + Logistic Regression baseline, rule-based intent benchmark, and the support-memory + risk-gate pipeline against the 200-example evaluation set.

### LLM path

Set:

```bash
export OPENAI_API_KEY="..."
export OPENAI_MODEL="..."
```

Then:

```bash
python run.py --evaluate --llm
```

The LLM path uses retrieved historical cases as evidence. The key is never committed.

### LLM-as-judge (optional)

The judge harness is implemented but requires an external LLM API key. Generate agent outputs first, then:

```bash
python evaluation/llm_judge.py
python evaluation/compare_judge.py
```

The judge scores 50 examples on correctness, groundedness, issue coverage, safety, and tone. `evaluation/human_judge_sheet.csv` contains candidate-reviewed scores for the matching examples. The checked-in repo intentionally does **not** claim a judge-vs-human agreement result because the external judge was not run.

## Evaluation protocol

- **Golden set:** 200 stratified examples across 10 intents.
- **Leakage control:** golden tweet IDs are excluded from training/retrieval cases.
- **Intent metrics:** accuracy + macro-F1 + per-class results.
- **Routing metrics:** accuracy, AUTO precision/recall, unsafe-auto rate, escalation recall.
- **Reply metrics:** candidate review on a 50-example subset; optional LLM judge comparison when an API key is available.

## Important evaluation note

The 200-example golden set is a **candidate-reviewed reference set** based on the documented annotation policy. The 50-example reply-quality subset is also candidate-reviewed with row-level notes.

The repository includes a real LLM-as-judge harness (`evaluation/llm_judge.py`) and a comparison script, but no external LLM call was executed in this environment because no API key was available. `results/judge_human_agreement.csv` therefore records `NOT_RUN` rather than a fabricated agreement number.

The deterministic path (`python run.py --evaluate`) is the reproducible no-key benchmark. The optional LLM path is the intended production-style drafting path because it receives retrieved historical support cases as evidence.

## Repository layout

```text
src/
  build_case_store.py     # link-aware extraction from TWCS
  brand_analysis.py       # brand viability analysis
  intent.py               # compact intent taxonomy + deterministic fallback
  retrieval.py            # support memory
  risk_gate.py            # conservative automation policy
  llm_agent.py            # optional LLM generation
  pipeline.py             # end-to-end agent

evaluation/
  evaluate_all.py         # baselines + end-to-end metrics
  llm_judge.py            # judge harness

data/
  sample_data.csv
  golden/golden_set.csv
  golden/ANNOTATION_POLICY.md

report/report.md
results/metrics.json
results/agent_outputs.jsonl
```
