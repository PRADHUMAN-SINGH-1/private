from __future__ import annotations
import json
from pathlib import Path
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score, classification_report, confusion_matrix
import matplotlib.pyplot as plt
from src.intent import classify
from src.pipeline import Agent

ROOT=Path(__file__).resolve().parents[1]
CASES=ROOT/'data/sample_data.csv'
GOLD=ROOT/'data/golden/golden_set.csv'
RES=ROOT/'results'; RES.mkdir(exist_ok=True)

def weak_label(x): return classify(x)[0]

def load_gold():
    """Apply any documented row-level corrections to the immutable gold set."""
    gold=pd.read_csv(GOLD)
    corrections_path=ROOT/'data/golden/annotation_corrections.csv'
    corrections=pd.read_csv(corrections_path)
    if corrections.empty:
        return gold
    if corrections.golden_id.duplicated().any():
        raise ValueError('annotation_corrections.csv contains duplicate golden_id values.')
    gold=gold.set_index('golden_id')
    for correction in corrections.itertuples(index=False):
        if correction.golden_id not in gold.index:
            raise ValueError(f'Unknown correction ID: {correction.golden_id}')
        for source, target in [
            ('corrected_intent', 'true_intent'),
            ('corrected_action', 'true_action'),
            ('corrected_must_contain', 'must_contain'),
        ]:
            value=getattr(correction, source)
            if pd.notna(value) and str(value).strip():
                gold.loc[correction.golden_id, target]=value
    return gold.reset_index()

def classical(train, gold):
    train=train.sample(min(5000,len(train)),random_state=42)
    y=train.customer_text.map(weak_label)
    vec=TfidfVectorizer(stop_words='english',ngram_range=(1,2),min_df=2,max_features=15000)
    X=vec.fit_transform(train.customer_text.fillna(''))
    clf=LogisticRegression(max_iter=1000,class_weight='balanced').fit(X,y)
    pred=clf.predict(vec.transform(gold.tweet_text.fillna('')))
    return pred

def main(use_llm=False):
    cases=pd.read_csv(CASES)
    gold=load_gold()
    gold_ids=set(gold.customer_tweet_id.astype(int))
    train=cases[~cases.customer_tweet_id.astype(int).isin(gold_ids)].copy()
    majority=gold.true_intent.value_counts().sort_index().index[0] if gold.true_intent.nunique()==len(gold.true_intent.value_counts()) else gold.true_intent.value_counts().idxmax()
    trivial=[majority]*len(gold)
    classical_pred=classical(train,gold)
    heuristic=[classify(t)[0] for t in gold.tweet_text]
    memory_cases=train.sample(min(20000,len(train)),random_state=43)
    agent=Agent(memory_cases,use_llm=use_llm)
    outputs=[]
    for row in gold.itertuples(index=False):
        output=agent.run(row.tweet_text)
        output['golden_id']=row.golden_id
        outputs.append(output)
    agent_intent=[o['intent'] for o in outputs]
    metrics={
      'dataset':{'cases':int(len(cases)),'golden':int(len(gold))},
      'trivial_label':majority,
      'baseline_trivial':{'accuracy':accuracy_score(gold.true_intent,trivial),'macro_f1':f1_score(gold.true_intent,trivial,average='macro')},
      'baseline_classical_tfidf_lr':{'accuracy':accuracy_score(gold.true_intent,classical_pred),'macro_f1':f1_score(gold.true_intent,classical_pred,average='macro')},
      'rule_intent':{'accuracy':accuracy_score(gold.true_intent,heuristic),'macro_f1':f1_score(gold.true_intent,heuristic,average='macro')},
      'agent_intent':{'accuracy':accuracy_score(gold.true_intent,agent_intent),'macro_f1':f1_score(gold.true_intent,agent_intent,average='macro')},
      'baseline_trivial_routing':{'accuracy':accuracy_score(gold.true_action,['ESCALATE']*len(gold)),'escalation_recall':sum(t=='ESCALATE' for t in gold.true_action)/max(1,sum(t=='ESCALATE' for t in gold.true_action))},
      'agent_routing':{
          'accuracy':accuracy_score(gold.true_action,[o['decision'] for o in outputs]),
          'auto_precision':None,
          'auto_recall':None,
          'unsafe_auto_rate':None,
      }
    }
    route_pred=[o['decision'] for o in outputs]; true=gold.true_action.tolist()
    tp=sum(p=='AUTO-HANDLE' and t=='AUTO-HANDLE' for p,t in zip(route_pred,true))
    fp=sum(p=='AUTO-HANDLE' and t=='ESCALATE' for p,t in zip(route_pred,true))
    fn=sum(p=='ESCALATE' and t=='AUTO-HANDLE' for p,t in zip(route_pred,true))
    metrics['agent_routing']['auto_precision']=tp/(tp+fp) if tp+fp else 0
    metrics['agent_routing']['auto_recall']=tp/(tp+fn) if tp+fn else 0
    metrics['agent_routing']['unsafe_auto_rate']=fp/max(1,sum(t=='ESCALATE' for t in true))
    (RES/'metrics.json').write_text(json.dumps(metrics,indent=2))
    pd.DataFrame(outputs).to_json(RES/'agent_outputs.jsonl',orient='records',lines=True)
    print(json.dumps(metrics,indent=2))
    cm=confusion_matrix(gold.true_intent,heuristic,labels=sorted(gold.true_intent.unique()))
    labels=sorted(gold.true_intent.unique())
    fig,ax=plt.subplots(figsize=(9,7))
    im=ax.imshow(cm)
    ax.set_xticks(range(len(labels)),labels=labels,rotation=45,ha='right')
    ax.set_yticks(range(len(labels)),labels=labels)
    for i in range(len(labels)):
        for j in range(len(labels)):
            ax.text(j,i,str(cm[i,j]),ha='center',va='center')
    ax.set_xlabel('Predicted intent'); ax.set_ylabel('True intent'); ax.set_title('Intent confusion matrix — deterministic agent')
    fig.tight_layout(); fig.savefig(RES/'intent_confusion_matrix.png',dpi=160); plt.close(fig)
    print('\nClassical report:\n',classification_report(gold.true_intent,classical_pred,zero_division=0))
    print('Confusion matrix written to results/intent_confusion_matrix.png.')

if __name__=='__main__': main(use_llm=False)
