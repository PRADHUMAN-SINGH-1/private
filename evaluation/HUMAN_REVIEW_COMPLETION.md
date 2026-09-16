# Human review completion

The candidate reviewed the 50-example reply-quality subset in `evaluation/human_judge_sheet.csv` using the five stated rubric dimensions: correctness, groundedness, issue coverage, safety, and tone. The sheet has 50 unique golden IDs and complete score cells, with row-level notes rather than a blanket confirmation sentence.

The review is candidate-level validation, not independent third-party annotation. The automated LLM judge was successfully run during final validation. `OPENAI_API_KEY` was not available in this environment, so the judge used `openrouter/free` for the first 18 examples and `gemini-3.6-flash` for the remaining 32 after free-tier limits were hit; per-row model provenance is recorded in `results/llm_judge_scores.csv`. The resulting judge-vs-human agreement statistics are in `results/judge_human_agreement.csv` and discussed in the report — agreement was weak (low or negative Cohen's kappa on most dimensions except safety), which is reported as a limitation rather than evidence of a reliable single-model judge.

Rows worth re-checking before an interview discussion include `G001`, `G004`, and `G009`, because they expose intent/routing edge cases rather than simple successes.
