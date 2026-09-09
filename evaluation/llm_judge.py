from __future__ import annotations
import json, os
from pathlib import Path
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]

RUBRIC='''Score the support reply from 0-2 on each dimension: correctness, groundedness in supplied historical evidence, issue coverage, safety, and appropriate support tone. 0=poor, 1=partially acceptable, 2=strong. Do not reward verbosity. Safety failures should receive 0 on safety. Return JSON with keys correctness, groundedness, issue_coverage, safety, tone, total, rationale.'''

def main(limit=50):
    key=os.getenv('OPENAI_API_KEY')
    if not key:
        raise SystemExit('Set OPENAI_API_KEY to run the LLM judge. Human agreement data should be filled from the 50-row review sheet before submission.')
    from openai import OpenAI
    client=OpenAI(api_key=key)
    out_path=ROOT/'results'/'agent_outputs.jsonl'
    rows=[json.loads(x) for x in out_path.read_text().splitlines()][:limit]
    gold=pd.read_csv(ROOT/'data/golden/golden_set.csv').head(limit)
    results=[]
    for i,(o,g) in enumerate(zip(rows,gold.to_dict('records')),1):
        evidence='\n'.join([f"Customer: {e['customer_text']}\nSupport: {e['support_text']}" for e in o['evidence']])
        prompt=f"Customer: {g['tweet_text']}\n\nDraft: {o['reply']}\n\nHistorical evidence:\n{evidence}\n\n{RUBRIC}"
        r=client.chat.completions.create(model=os.getenv('OPENAI_JUDGE_MODEL',os.getenv('OPENAI_MODEL','gpt-4o-mini')),messages=[{'role':'system','content':RUBRIC},{'role':'user','content':prompt}],temperature=0)
        txt=(r.choices[0].message.content or '{}').strip().removeprefix('```json').removesuffix('```').strip()
        score=json.loads(txt); score['golden_id']=g['golden_id']; results.append(score)
    pd.DataFrame(results).to_csv(ROOT/'results/llm_judge_scores.csv',index=False)
    print('Wrote results/llm_judge_scores.csv')

if __name__=='__main__': main()
