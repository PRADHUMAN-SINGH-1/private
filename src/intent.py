from __future__ import annotations
import re

INTENTS = [
    'account_access','billing_purchase','purchase_refund','subscription',
    'connectivity','messages_calls','apps_appstore','battery_charging',
    'software_update','device_hardware'
]

RULES = {
    'account_access': [r'\bapple ?id\b', r'\bicloud\b.*(?:password|login|sign|access)', r'password', r'\bsign[ -]?in\b', r'\blog ?in\b', r'login', r'activation lock', r'account recovery', r'account.*locked', r'account.*hacked'],
    'billing_purchase': [r'payment method', r'payment.*declin', r'charged', r'\bcharge\b', r'billed', r'credit card', r'debit card', r'invoice', r'receipt', r'duplicate.*charge', r'wrong.*charge'],
    'purchase_refund': [r'\brefund\b', r'money back', r'unauthori[sz]ed purchase', r'charge.*not mine', r'return.*(?:iphone|ipad|mac|purchase|order)'],
    'subscription': [r'\bsubscription\b', r'\bfree trial\b', r'\brenewal\b', r'renewed', r'cancel.*subscription', r'subscription.*cancel', r'subscribe.*(?:apple music|icloud)'],
    'connectivity': [r'\bwifi\b', r'\bwi-fi\b', r'bluetooth', r'hotspot', r'cellular', r'no service', r'\bnetwork\b', r'\binternet\b', r'\bsignal\b'],
    'messages_calls': [r'\bimessage\b', r'\bfacetime\b', r'not receiving messages', r'can.t send.*(?:message|imessage)', r'messages?.*(?:missing|disappear|delay|late)', r'call.*(?:drop|fail|not work)', r'\bvoicemail\b'],
    'apps_appstore': [r'\bapp store\b', r'\bitunes store\b', r'(?:download|install).*\bapp\b', r'\bapp\b.*(?:crash|freeze|won.t|doesn.t|not working)'],
    'battery_charging': [r'\bbattery\b', r'\bcharger\b', r'\bcharging\b', r'not charging', r'battery.*drain', r'battery health', r'gets?.*hot.*charging'],
    'software_update': [r'\bios\s?\d', r'\bmacos\b.*update', r'software update', r'(?:after|since|following).*\bupdate\b', r'cannot.*update', r'can.t.*update', r'update.*(?:fail|error|stuck|crash|problem|issue)', r'install.*update'],
    'device_hardware': [r'\bscreen\b', r'\bdisplay\b', r'camera.*(?:not|won|broken|black)', r'keyboard.*(?:not|won|broken)', r'home button', r'\btouch ?id\b', r'\bspeaker\b.*(?:not|won|broken)', r'\bmicrophone\b.*(?:not|won|broken)', r'\bport\b.*(?:broken|damaged|not)', r'\bcrack(?:ed)?\b', r'physical damage'],
}

PRIORITY = ['purchase_refund','subscription','battery_charging','connectivity','messages_calls','apps_appstore','software_update','billing_purchase','device_hardware','account_access']

def classify(text: str):
    t = str(text or '').lower()
    for label in PRIORITY:
        for p in RULES[label]:
            if re.search(p, t):
                # Strong confidence for distinctive matched phrases; this is intentionally not calibrated.
                return label, 0.84
    return 'other_services', 0.30
