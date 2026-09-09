from __future__ import annotations
from pathlib import Path
import pandas as pd
from sklearn.metrics import cohen_kappa_score

ROOT=Path(__file__).resolve().parents[1]
h=pd.read_csv(ROOT/'evaluation/human_judge_sheet.csv')
l=pd.read_csv(ROOT/'results/llm_judge_scores.csv')
cols=['correctness','groundedness','issue_coverage','safety','tone']
merged=h.merge(l,on='golden_id',how='inner',suffixes=('_human','_llm'))
rows=[]
for c in cols:
    a=pd.to_numeric(merged[f'human_{c}_0_2'],errors='coerce'); b=pd.to_numeric(merged[c],errors='coerce')
    m=a.notna() & b.notna()
    if m.any(): rows.append({'dimension':c,'n':int(m.sum()),'exact_agreement':float((a[m]==b[m]).mean()),'cohen_kappa':float(cohen_kappa_score(a[m],b[m]))})
ht=pd.to_numeric(merged['human_total_0_10'],errors='coerce'); lt=pd.to_numeric(merged['total'],errors='coerce'); m=ht.notna()&lt.notna()
summary=pd.DataFrame(rows)
if m.any():
    summary=pd.concat([summary,pd.DataFrame([{'dimension':'total','n':int(m.sum()),'exact_agreement':float((ht[m]==lt[m]).mean()),'cohen_kappa':float(cohen_kappa_score(ht[m],lt[m]))}])],ignore_index=True)
summary.to_csv(ROOT/'results/judge_human_agreement.csv',index=False)
print(summary.to_string(index=False))
if not len(summary):
    raise SystemExit('No completed human scores yet.')
