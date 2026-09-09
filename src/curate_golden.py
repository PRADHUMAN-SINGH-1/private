from __future__ import annotations
import re
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
CASES = ROOT / 'data/processed/apple_cases.csv'
OUT = ROOT / 'data/golden/golden_set.csv'

INTENT_PATTERNS = {
    'account_access': [r'\bapple ?id\b', r'\bicloud\b', r'password', r'\bsign[ -]?in\b', r'\blog ?in\b', r'login', r'locked out', r'account recovery', r'account.*hacked', r'activation lock', r'verify.*identity'],
    'billing_purchase': [r'charged', r'\bcharge\b', r'payment method', r'payment.*declin', r'billed', r'credit card', r'debit card', r'invoice', r'receipt', r'wrong amount', r'duplicate charge', r'price.*(paid|pay|cost)'],
    'purchase_refund': [r'\brefund\b', r'money back', r'refund.*(wait|pending)', r'return.*(iphone|ipad|mac|purchase|order)', r'unauthori[sz]ed purchase', r'charge.*not mine'],
    'subscription': [r'\bsubscription\b', r'subscribe', r'\brenewal\b', r'renewed', r'cancel.*subscription', r'subscription.*cancel', r'free trial'],
    'connectivity': [r'\bwifi\b', r'\bwi-fi\b', r'bluetooth', r'hotspot', r'cellular', r'no service', r'\bnetwork\b', r'\binternet\b', r'\bsignal\b', r'won.t connect', r'cannot connect'],
    'messages_calls': [r'imessage', r'facetime', r'not receiving messages', r'can.t send.*imessage', r'can.t send.*message', r'message.*(?:delay|missing|disappear)', r'\bvoicemail\b', r'call.*(?:drop|fail|not work)', r'notification.*not'],
    'apps_appstore': [r'\bapp store\b', r'\bitunes store\b', r'(?:download|install).*app', r'app.*(?:crash|freeze|won.t|doesn.t|not working)', r'cannot.*download.*app', r'can.t.*download.*app'],
    'battery_charging': [r'\bbattery\b', r'battery.*drain', r'drain.*battery', r'\bcharger\b', r'\bcharging\b', r'not charging', r'won.t charge', r'charge.*(?:slow|fast|drop)', r'battery health', r'gets? hot.*charging'],
    'software_update': [r'\bios\s?\d', r'software update', r'\bmacos\b', r'update.*(?:fail|error|stuck|crash|problem|issue)', r'(?:after|since).*\bupdate\b', r'cannot.*update', r'can.t.*update', r'install.*update', r'restore.*iphone'],
    'device_hardware': [r'\bscreen\b', r'\bdisplay\b', r'camera', r'keyboard', r'home button', r'touch(?:screen| id)?', r'speaker', r'microphone', r'earpiece', r'\bport\b', r'crack(?:ed)?', r'broken.*(?:screen|camera|button|keyboard)', r'overheat.*(not charging|device|phone)', r'physical damage'],
}


NEGATIVE_INTENT_HINTS = {
    'device_hardware': [r'\bbattery\b', r'\bcharger\b', r'charging', r'\bwifi\b', r'\bbluetooth\b'],
    'billing_purchase': [r'\bbattery\b', r'\bcharger\b', r'charging'],
    'software_update': [r'\bbattery\b'],
}


def clean(s: str) -> str:
    s = re.sub(r'@\w+', ' ', str(s or ''))
    s = re.sub(r'https?://\S+', ' ', s)
    return re.sub(r'\s+', ' ', s).strip()

def score(text: str, label: str) -> int:
    t = text.lower()
    pos = sum(1 for p in INTENT_PATTERNS[label] if re.search(p, t))
    neg = sum(1 for p in NEGATIVE_INTENT_HINTS.get(label, []) if re.search(p, t))
    return pos - neg

def classify(text: str) -> tuple[str, float]:
    t = text.lower()
    ordered = ['purchase_refund','subscription','battery_charging','connectivity','messages_calls','apps_appstore','software_update','billing_purchase','device_hardware','account_access']
    scores = {k: score(text, k) for k in INTENT_PATTERNS}
    # Primary operational symptom takes precedence over generic product/account words.
    for label in ordered:
        if scores[label] > 0:
            # Prefer labels with strong, distinctive matches.
            if label == 'battery_charging' and re.search(r'\bbattery\b|\bcharger\b|charging|not charging', t): return label, 2.5
            if label == 'connectivity' and re.search(r'\bwifi\b|\bwi-fi\b|bluetooth|cellular|hotspot|no service', t): return label, 2.5
            if label == 'messages_calls' and re.search(r'imessage|facetime|not receiving messages|message.*(?:delay|missing)|call.*(?:drop|fail|not work)', t): return label, 2.4
            if label == 'apps_appstore' and re.search(r'app store|itunes store|(?:download|install).*app|app.*(?:crash|freeze|won.t|doesn.t|not working)', t): return label, 2.4
            if label == 'purchase_refund' and re.search(r'\brefund\b|money back|unauthori[sz]ed purchase|charge.*not mine', t): return label, 2.6
            if label == 'subscription' and re.search(r'\bsubscription\b|subscribe|renewal|free trial', t): return label, 2.4
            if label == 'software_update' and re.search(r'\bios\s?\d|software update|\bmacos\b|after.*update|since.*update|cannot.*update|can.t.*update|update.*(?:fail|error|stuck|crash|problem)', t): return label, 2.3
            if label == 'billing_purchase' and re.search(r'charged|\bcharge\b|payment method|billed|credit card|debit card|invoice|receipt|duplicate charge|wrong amount', t) and not re.search(r'\bbattery\b|charger|charging', t): return label, 2.2
            if label == 'device_hardware' and re.search(r'\bscreen\b|\bdisplay\b|camera|keyboard|home button|touch(?:screen| id)?|speaker|microphone|earpiece|\bport\b|crack(?:ed)?|physical damage', t): return label, 2.2
            if label == 'account_access' and re.search(r'\bapple ?id\b|\bicloud\b|password|\bsign[ -]?in\b|\blog ?in\b|login|activation lock|account recovery|account.*hacked', t): return label, 2.1
    return 'other_services', 0.0

def action(text: str, label: str) -> str:
    t = text.lower()
    sensitive = [r'password', r'verification code', r'otp', r'credit card', r'card number', r'bank', r'account number', r'identity', r'personal information', r'\bssn\b']
    financial = [r'\brefund\b', r'charged', r'\bcharge\b', r'payment', r'billed', r'purchase', r'order', r'money back']
    persistent = [r'\bstill\b', r'\bagain\b', r'keeps?', r'\bfailed\b', r'error', r'\bcrash', r'broken', r'already tried', r'nothing works']
    safety = [r'explod', r'fire', r'smoke', r'shock', r'burning', r'overheat']
    procedural = [r'how do i', r'how can i', r'where do i', r'can i', r'what is', r'is there a way']
    if any(re.search(p,t) for p in sensitive + financial + safety): return 'ESCALATE'
    if label == 'account_access': return 'ESCALATE'
    if any(re.search(p,t) for p in persistent): return 'ESCALATE'
    if label == 'other_services': return 'ESCALATE'
    if label == 'subscription' and not any(re.search(p,t) for p in procedural): return 'ESCALATE'
    return 'AUTO-HANDLE'

def must_contain(label: str) -> str:
    return {
        'account_access': 'Do not request credentials publicly; use safe account-recovery or secure handoff guidance.',
        'billing_purchase': 'Acknowledge the billing/payment issue and avoid unsupported charge or refund claims.',
        'purchase_refund': 'Avoid promising a refund; route account-specific purchase/refund handling safely.',
        'subscription': 'Address subscription settings/cancellation and avoid unsupported billing claims.',
        'connectivity': 'Give a relevant connectivity troubleshooting step and avoid requesting sensitive details.',
        'messages_calls': 'Address the messaging/call symptom and provide a relevant settings/troubleshooting step.',
        'apps_appstore': 'Address the app/App Store symptom with a concrete troubleshooting or support path.',
        'battery_charging': 'Address the battery/charging symptom with a concrete safe troubleshooting step.',
        'software_update': 'Tie the answer to the reported update/OS behavior without inventing version-specific facts.',
        'device_hardware': 'Address the specific hardware/display/input symptom without guessing about repair outcomes.',
        'other_services': 'Acknowledge the request and avoid inventing unsupported policy or capability.'
    }[label]

def main():
    df = pd.read_csv(CASES)
    df['tweet_text'] = df.customer_text.map(clean)
    df = df[df.tweet_text.str.split().str.len().between(8, 70)].copy()
    # Drop near-duplicates to avoid repeated templates dominating the gold set.
    df = df.drop_duplicates('tweet_text').copy()
    preds=[]
    for t in df.tweet_text:
        label,conf=classify(t); preds.append((label,conf))
    df['pred']=[x[0] for x in preds]; df['confidence']=[x[1] for x in preds]
    # Require a reasonably unambiguous match and avoid obvious multi-issue texts.
    counts={
        'account_access':20,'billing_purchase':20,'purchase_refund':20,'subscription':20,
        'connectivity':20,'messages_calls':20,'apps_appstore':20,'battery_charging':20,
        'software_update':20,'device_hardware':20,'other_services':0,
    }
    selected=[]
    for label,target in counts.items():
        sub=df[df.pred==label].copy().sort_values(['confidence','customer_created_at'], ascending=[False,True])
        # Sample across time from the strongest portion.
        top=sub.head(min(len(sub), target*8))
        if len(top)<target:
            raise RuntimeError(f'Not enough candidates for {label}: {len(top)}')
        # Spread by index to reduce repeated near-identical issue descriptions.
        picks=top.iloc[::max(1, len(top)//max(target,1))].head(target)
        if len(picks)<target: picks=top.head(target)
        selected.append(picks)
    gold=pd.concat(selected,ignore_index=True)
    gold['true_intent']=gold.pred
    gold['true_action']=[action(t,i) for t,i in zip(gold.tweet_text,gold.true_intent)]
    gold['must_contain']=gold.true_intent.map(must_contain)
    gold.insert(0,'golden_id',[f'G{i:03d}' for i in range(1,len(gold)+1)])
    cols=['golden_id','tweet_text','true_intent','true_action','must_contain','customer_tweet_id','support_tweet_id','customer_created_at','support_text']
    gold[cols].to_csv(OUT,index=False)
    print(gold.true_intent.value_counts().sort_index().to_string())
    print(gold.true_action.value_counts().to_string())
    print('wrote', OUT, len(gold))
if __name__=='__main__': main()
