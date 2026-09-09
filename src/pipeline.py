from __future__ import annotations
import pandas as pd
from .intent import classify
from .retrieval import SupportMemory
from .risk_gate import route
from .llm_agent import llm_generate, LLMUnavailable

class Agent:
    def __init__(self, cases: pd.DataFrame, use_llm: bool=False):
        self.memory=SupportMemory(cases)
        self.use_llm=use_llm

    def run(self, message: str):
        intent, conf=classify(message)
        retrieved=self.memory.retrieve(message, k=3)
        evidence_strength=retrieved[0].score if retrieved else 0.0
        if self.use_llm:
            try:
                out=llm_generate(message, intent, [r.__dict__ for r in retrieved])
                intent=out.get('intent', intent)
                conf=float(out.get('intent_confidence', conf))
                draft=out.get('reply','')
                drafting_mode='llm_grounded'
            except (LLMUnavailable, ValueError, KeyError):
                draft=self._template(intent)
                drafting_mode='deterministic_fallback'
        else:
            draft=self._template(intent)
            drafting_mode='deterministic_template'
        decision, risk, reason=route(message, conf, retrieved, draft)
        return {'intent':intent,'intent_confidence':round(conf,2),'reply':draft,'drafting_mode':drafting_mode,'decision':decision,'risk_score':risk,'evidence_strength':round(evidence_strength,3),'reason':reason,'evidence':[r.__dict__ for r in retrieved]}

    @staticmethod
    def _template(intent):
        from .core import draft
        return draft('', intent)
