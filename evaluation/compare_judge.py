from __future__ import annotations
from pathlib import Path
import pandas as pd
from sklearn.metrics import cohen_kappa_score

ROOT=Path(__file__).resolve().parents[1]

def main():
    human_path=ROOT/'evaluation/human_judge_sheet.csv'
    llm_path=ROOT/'results/llm_judge_scores.csv'
    if not llm_path.exists():
        raise SystemExit('No completed LLM judge file; run evaluation/llm_judge.py first.')
    h=pd.read_csv(human_path)
    l=pd.read_csv(llm_path)
    cols=['correctness','groundedness','issue_coverage','safety','tone']
    merged=h.merge(l,on='golden_id',how='inner',suffixes=('_human','_llm'))
    if len(merged) != 50:
        raise SystemExit(f'Expected 50 matching human/judge rows; found {len(merged)}.')
    rows=[]
    for c in cols:
        a=pd.to_numeric(merged[f'human_{c}_0_2'],errors='coerce'); b=pd.to_numeric(merged[c],errors='coerce')
        m=a.notna() & b.notna()
        if m.sum() != 50:
            raise SystemExit(f'Incomplete scores for {c}.')
        rows.append({'dimension':c,'n':50,'exact_agreement':float((a[m]==b[m]).mean()),'cohen_kappa':float(cohen_kappa_score(a[m],b[m]))})
    ht=pd.to_numeric(merged['human_total_0_10'],errors='coerce'); lt=pd.to_numeric(merged['total'],errors='coerce'); m=ht.notna()&lt.notna()
    if m.sum() != 50:
        raise SystemExit('Incomplete total scores.')
    summary=pd.DataFrame(rows)
    summary=pd.concat([summary,pd.DataFrame([{'dimension':'total','n':50,'exact_agreement':float((ht[m]==lt[m]).mean()),'cohen_kappa':float(cohen_kappa_score(ht[m],lt[m]))}])],ignore_index=True)
    summary.to_csv(ROOT/'results/judge_human_agreement.csv',index=False)
    print(summary.to_string(index=False))

if __name__=='__main__':
    main()
