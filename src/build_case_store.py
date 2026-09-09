"""Build a compact, link-aware AppleSupport support-memory dataset.

The raw TWCS file is large. This script performs two streaming passes:
1) collect all AppleSupport outbound tweets;
2) collect inbound customer tweets that point to those tweets via response IDs,
   then join the referenced support reply text.
"""
from __future__ import annotations
import csv, json, re
from pathlib import Path
from collections import defaultdict
import pandas as pd

RAW = Path('data/raw/twcs.csv')
OUT = Path('data/processed')
OUT.mkdir(parents=True, exist_ok=True)

COLS = ['tweet_id','author_id','inbound','created_at','text','response_tweet_id','in_response_to_tweet_id']


def ids(value):
    if pd.isna(value):
        return []
    return [int(x.strip()) for x in str(value).split(',') if x.strip().isdigit()]


def main():
    support = {}
    print('[1/2] Collecting AppleSupport replies...')
    for ch in pd.read_csv(RAW, usecols=COLS, chunksize=150_000):
        g = ch[(ch.author_id == 'AppleSupport') & (~ch.inbound)]
        for r in g.itertuples(index=False):
            support[int(r.tweet_id)] = {
                'tweet_id': int(r.tweet_id),
                'created_at': r.created_at,
                'text': str(r.text or ''),
                'response_tweet_id': r.response_tweet_id,
                'in_response_to_tweet_id': r.in_response_to_tweet_id,
            }
    print(f'AppleSupport outbound tweets: {len(support):,}')

    cases = []
    print('[2/2] Linking customer messages to AppleSupport replies...')
    for ch in pd.read_csv(RAW, usecols=COLS, chunksize=150_000):
        g = ch[ch.inbound & ch.response_tweet_id.notna()]
        for r in g.itertuples(index=False):
            customer_id = int(r.tweet_id)
            for rid in ids(r.response_tweet_id):
                if rid in support:
                    cases.append({
                        'customer_tweet_id': customer_id,
                        'support_tweet_id': rid,
                        'customer_created_at': r.created_at,
                        'customer_text': str(r.text or '').replace('\n',' ').strip(),
                        'support_text': support[rid]['text'].replace('\n',' ').strip(),
                        'customer_parent_id': int(r.in_response_to_tweet_id) if pd.notna(r.in_response_to_tweet_id) else None,
                    })
                    break
    df = pd.DataFrame(cases).drop_duplicates(subset=['customer_tweet_id'])
    df['word_count'] = df.customer_text.str.split().str.len()
    df = df[df.customer_text.str.len().ge(8)].copy()
    df.to_csv(OUT / 'apple_cases.csv', index=False)
    # Small reproducible sample; no raw full dataset required for demo.
    sample = df.sort_values(['customer_created_at','customer_tweet_id']).head(1000)
    sample.to_csv(OUT / 'sample_data.csv', index=False)
    print(f'Usable customer->support pairs: {len(df):,}')
    print(f'Demo sample written: {len(sample):,}')

if __name__ == '__main__':
    main()
