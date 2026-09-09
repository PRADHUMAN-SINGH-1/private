from __future__ import annotations
import argparse, json
from pathlib import Path
import pandas as pd
from src.pipeline import Agent

ROOT=Path(__file__).resolve().parent
CASES=ROOT/'data/processed/apple_cases.csv' if (ROOT/'data/processed/apple_cases.csv').exists() else ROOT/'data/sample_data.csv'

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--demo',action='store_true')
    ap.add_argument('--evaluate',action='store_true')
    ap.add_argument('--llm',action='store_true')
    ap.add_argument('--message')
    args=ap.parse_args()
    if args.evaluate:
        from evaluation.evaluate_all import main as ev
        ev(use_llm=args.llm); return
    if args.demo or args.message:
        if not CASES.exists(): raise SystemExit('Run: python src/build_case_store.py first.')
        cases=pd.read_csv(CASES)
        agent=Agent(cases,use_llm=args.llm)
        msg=args.message or 'My iPhone battery is draining very quickly after the update.'
        print(json.dumps(agent.run(msg),indent=2))
        return
    ap.print_help()

if __name__=='__main__': main()
