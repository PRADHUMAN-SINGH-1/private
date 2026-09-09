from __future__ import annotations
from dataclasses import dataclass
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

@dataclass
class RetrievedCase:
    customer_text: str
    support_text: str
    score: float
    customer_tweet_id: int
    support_tweet_id: int

class SupportMemory:
    def __init__(self, cases: pd.DataFrame):
        self.cases = cases.reset_index(drop=True).copy()
        self.vectorizer = TfidfVectorizer(stop_words='english', ngram_range=(1,2), min_df=2, max_features=50000)
        self.matrix = self.vectorizer.fit_transform(self.cases.customer_text.fillna(''))

    def retrieve(self, query: str, k: int = 3):
        q = self.vectorizer.transform([query])
        scores = cosine_similarity(q, self.matrix)[0]
        idx = scores.argsort()[-k:][::-1]
        return [RetrievedCase(self.cases.iloc[i].customer_text, self.cases.iloc[i].support_text, float(scores[i]), int(self.cases.iloc[i].customer_tweet_id), int(self.cases.iloc[i].support_tweet_id)) for i in idx]

