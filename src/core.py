from dataclasses import dataclass, asdict
from typing import Dict, Any
from .intent import classify
from .risk_gate import route

@dataclass
class Decision:
    intent: str
    intent_confidence: float
    evidence_strength: float
    reply: str
    decision: str
    reason: str

def draft(text: str, intent: str):
    templates={
      'account_access':'For account access, please use Apple’s official recovery flow and do not share your password or verification codes publicly.',
      'billing_purchase':'For a billing issue, avoid posting payment details publicly. Account-specific billing questions should go through Apple Support’s secure support path.',
      'purchase_refund':'For a purchase/refund request, avoid posting payment details publicly. Apple Support can review account-specific purchase details securely.',
      'subscription':'For subscription changes, use your Apple subscription settings. If the subscription or charge is not behaving as expected, use Apple Support for account-specific help.',
      'connectivity':'Start by reconnecting the affected network or Bluetooth device and restarting the device. If the issue continues, check whether it occurs on another connection.',
      'messages_calls':'Check the relevant Messages/FaceTime/Phone settings, restart the device, and confirm the software is current. Persistent failures may need deeper support.',
      'apps_appstore':'Restart the device and check for an available app/software update. For one affected app, reinstalling it can be a useful troubleshooting step.',
      'battery_charging':'Check the cable/charger and Battery settings, then restart the device. Avoid continued use if there is heat, smoke, or physical damage.',
      'software_update':'Confirm the device has enough free storage and a stable connection, then retry the update. Repeated failures may require deeper troubleshooting.',
      'device_hardware':'Avoid guessing about repairs. For a physical symptom, note the affected component and use Apple Support/service guidance; do not share private account information.',
      'other_services':'I need a little more context about the Apple product or service and the exact symptom before recommending a safe next step.'}
    return templates.get(intent, templates['other_services'])

def run(text: str, evidence_strength=0.0, evidence=None) -> Dict[str,Any]:
    intent,conf=classify(text)
    reply=draft(text,intent)
    decision,risk,reason=route(text,conf,evidence or [],reply)
    return asdict(Decision(intent,conf,evidence_strength,reply,decision,reason))
