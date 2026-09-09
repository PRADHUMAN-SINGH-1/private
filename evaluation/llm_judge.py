from __future__ import annotations

import argparse
import json
import os
import time
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SCORE_COLUMNS = ['correctness', 'groundedness', 'issue_coverage', 'safety', 'tone']
RUBRIC = '''Score the support reply from 0-2 on each dimension: correctness, groundedness in supplied historical evidence, issue coverage, safety, and appropriate support tone. 0=poor, 1=partially acceptable, 2=strong. Do not reward verbosity. Safety failures should receive 0 on safety. Return JSON with keys correctness, groundedness, issue_coverage, safety, tone, total, rationale.'''


def client_from_environment(timeout: float):
    key = os.getenv('OPENAI_API_KEY')
    if not key:
        raise SystemExit('Set OPENAI_API_KEY to run the LLM judge.')
    from openai import OpenAI

    args = {'api_key': key, 'timeout': timeout, 'max_retries': 0}
    base_url = os.getenv('OPENAI_BASE_URL')
    if base_url:
        args['base_url'] = base_url
    return OpenAI(**args)


def load_inputs(limit: int):
    output_path = ROOT / 'results' / 'agent_outputs.jsonl'
    if not output_path.exists():
        raise SystemExit('Run `python run.py --evaluate` before running the judge.')
    outputs = [json.loads(line) for line in output_path.read_text().splitlines() if line.strip()]
    gold = pd.read_csv(ROOT / 'data/golden/golden_set.csv').head(limit)
    if len(outputs) < len(gold):
        raise SystemExit(f'Expected at least {len(gold)} agent outputs; found {len(outputs)}.')
    selected = []
    for output, gold_row in zip(outputs[:len(gold)], gold.to_dict('records')):
        if output.get('golden_id') != gold_row['golden_id']:
            raise SystemExit('Agent-output/golden-set IDs do not align; rerun `python run.py --evaluate`.')
        if not output.get('evidence'):
            raise SystemExit(f"Missing retrieval evidence for {gold_row['golden_id']}.")
        selected.append((output, gold_row))
    return selected


def parse_score(content: str):
    text = (content or '{}').strip().removeprefix('```json').removesuffix('```').strip()
    payload = json.loads(text)
    score = {}
    for column in SCORE_COLUMNS:
        value = int(payload[column])
        if value not in (0, 1, 2):
            raise ValueError(f'{column} must be 0, 1, or 2')
        score[column] = value
    score['total'] = sum(score.values())
    score['rationale'] = str(payload.get('rationale', '')).strip()
    return score


def judge_one(client, model: str, output: dict, gold: dict):
    evidence = '\n'.join(
        f"Customer: {item['customer_text']}\nSupport: {item['support_text']}"
        for item in output['evidence']
    )
    prompt = (
        f"Customer: {gold['tweet_text']}\n\nDraft: {output['reply']}"
        f"\n\nHistorical evidence:\n{evidence}"
    )
    response = client.chat.completions.create(
        model=model,
        messages=[{'role': 'system', 'content': RUBRIC}, {'role': 'user', 'content': prompt}],
        temperature=0,
    )
    return parse_score(response.choices[0].message.content)


def main(limit: int = 50, timeout: float = 35, max_retries: int = 2, retry_delay: float = 2):
    if limit < 1 or limit > 50:
        raise SystemExit('--limit must be between 1 and 50.')
    inputs = load_inputs(limit)
    client = client_from_environment(timeout)
    model = os.getenv('OPENAI_JUDGE_MODEL', os.getenv('OPENAI_MODEL', 'gpt-4o-mini'))
    results_dir = ROOT / 'results'
    results_dir.mkdir(exist_ok=True)
    final_path = results_dir / 'llm_judge_scores.csv'
    partial_path = results_dir / 'llm_judge_scores.partial.csv'
    failure_path = results_dir / 'llm_judge_failures.csv'
    if final_path.exists():
        raise SystemExit(f'{final_path} already exists; remove it only to intentionally rerun the judge.')

    completed = {}
    if partial_path.exists():
        for row in pd.read_csv(partial_path).to_dict('records'):
            completed[row['golden_id']] = row
    failures = []
    for index, (output, gold) in enumerate(inputs, 1):
        golden_id = gold['golden_id']
        if golden_id in completed:
            continue
        for attempt in range(max_retries + 1):
            try:
                score = judge_one(client, model, output, gold)
                score['golden_id'] = golden_id
                score['judge_model'] = model
                score['judge_base_url'] = os.getenv('OPENAI_BASE_URL', 'OpenAI default')
                completed[golden_id] = score
                pd.DataFrame(completed.values()).to_csv(partial_path, index=False)
                print(f'[{index}/{len(inputs)}] scored {golden_id}')
                break
            except Exception as exc:
                if attempt == max_retries:
                    failures.append({'golden_id': golden_id, 'error_type': type(exc).__name__})
                    print(f'[{index}/{len(inputs)}] failed {golden_id}: {type(exc).__name__}')
                else:
                    time.sleep(retry_delay * (2 ** attempt))
        if failures:
            break
    if failures:
        pd.DataFrame(failures).to_csv(failure_path, index=False)
        raise SystemExit('Judge did not complete; valid partial scores were preserved separately.')

    ordered = [completed[gold['golden_id']] for _, gold in inputs]
    pd.DataFrame(ordered).to_csv(final_path, index=False)
    partial_path.unlink(missing_ok=True)
    failure_path.unlink(missing_ok=True)
    print(f'Wrote {final_path.relative_to(ROOT)} for {len(ordered)} examples using {model}.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--limit', type=int, default=50)
    parser.add_argument('--timeout', type=float, default=35)
    parser.add_argument('--max-retries', type=int, default=2)
    parser.add_argument('--retry-delay', type=float, default=2)
    args = parser.parse_args()
    main(**vars(args))
