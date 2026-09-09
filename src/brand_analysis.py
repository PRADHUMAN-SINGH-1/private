from __future__ import annotations
from pathlib import Path
from collections import Counter, defaultdict
import pandas as pd

RAW=Path('data/raw/twcs.csv')
OUT=Path('results/brand_comparison.csv')

def main():
    outbound=Counter(); direct=Counter(); usable=Counter(); ids=defaultdict(set)
    for ch in pd.read_csv(RAW,usecols=['tweet_id','author_id','inbound','text','in_response_to_tweet_id'],chunksize=200_000):
        g=ch[(~ch.inbound)&ch.author_id.notna()]
        for b,gg in g.groupby('author_id'):
            outbound[b]+=len(gg); ids[b].update(gg.tweet_id.astype('int64'))
    owner={tid:b for b,s in ids.items() for tid in s}
    for ch in pd.read_csv(RAW,usecols=['tweet_id','author_id','inbound','text','in_response_to_tweet_id'],chunksize=200_000):
        g=ch[ch.inbound & ch.in_response_to_tweet_id.notna()].copy()
        g['parent']=g.in_response_to_tweet_id.astype('int64')
        g['brand']=g.parent.map(owner)
        g=g[g.brand.notna()]
        for b,n in g.brand.value_counts().items(): direct[b]+=int(n)
        g['words']=g.text.fillna('').str.split().str.len()
        for b,n in g[g.words>=8].brand.value_counts().items(): usable[b]+=int(n)
    rows=[]
    for b in outbound:
        rows.append({'brand':b,'outbound':outbound[b],'direct_inbound':direct[b],'usable_8w':usable[b],'usable_ratio':usable[b]/max(1,direct[b])})
    out=pd.DataFrame(rows).sort_values(['usable_8w','direct_inbound'],ascending=False)
    out.to_csv(OUT,index=False)
    print(out.head(15).to_string(index=False))
if __name__=='__main__': main()
