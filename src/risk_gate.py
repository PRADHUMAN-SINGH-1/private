from __future__ import annotations
import re

SENSITIVE = [r'password', r'credit card', r'card number', r'account number', r'verification code', r'otp', r'\bssn\b']
FINANCIAL = [r'refund', r'money back', r'charged', r'charge', r'payment', r'purchase', r'billed', r'\breceipt\b', r'order']
ACCOUNT = [r'\bapple ?id\b', r'\bappleid\b', r'\bicloud\b', r'\bsign[ -]?in\b', r'login', r'account.*locked', r'locked.*account', r'activation lock', r'account.*hacked']
FAILURE = [r'\bstill\b', r'\bagain\b', r'\bkeeps?\b', r'\bfreeze(?:s|d|ing)?\b', r'\bfailed\b', r'\berror\b', r'\bbroken\b', r'\bcrash(?:ed|es|ing)?\b', r'nothing works', r'already tried', r'already restarted', r'no change after restart']
PRIVATE = [r'\bdm\b', r'direct message', r'private message', r'call me']
UNSAFE_DRAFT = [r'guarantee', r'100%', r'send me your password', r'send your full card', r'credit card number']


def route(message, intent_confidence, retrieved, draft=''):
    t = str(message or '').lower()
    reasons = []
    risk = 0
    if any(re.search(p, t) for p in ACCOUNT):
        risk += 3; reasons.append('account-specific access or identity issue')
    if any(re.search(p, t) for p in SENSITIVE):
        risk += 3; reasons.append('sensitive information/account security')
    if any(re.search(p, t) for p in FINANCIAL):
        risk += 3; reasons.append('financial or purchase-specific issue')
    if intent_confidence < 0.60:
        risk += 2; reasons.append('low intent confidence')
    top = float(retrieved[0].score) if retrieved else 0.0
    if top < 0.18:
        risk += 2; reasons.append('weak historical precedent')
    if retrieved:
        private_precedent = sum(1 for r in retrieved if any(x in r.support_text.lower() for x in ['direct message', 'private message', 'send us a dm', 'dm us', 'a dm', 'call us']))
        if private_precedent >= 2:
            risk += 1; reasons.append('similar historical cases were handled privately')
    if any(re.search(p, t) for p in FAILURE):
        risk += 2; reasons.append('persistent or failed troubleshooting')
    if any(re.search(p, t) for p in PRIVATE):
        risk += 1; reasons.append('case appears to require private follow-up')
    if any(re.search(p, str(draft).lower()) for p in UNSAFE_DRAFT):
        risk += 3; reasons.append('draft contains an unsafe information request or guarantee')
    decision = 'ESCALATE' if risk >= 2 else 'AUTO-HANDLE'
    reason = '; '.join(reasons) if reasons else 'low operational risk with sufficient historical precedent'
    return decision, risk, reason
