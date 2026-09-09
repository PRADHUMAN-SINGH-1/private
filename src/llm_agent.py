from __future__ import annotations
import json
import os
from typing import Any

VALID_INTENTS = {
    'account_access', 'billing_purchase', 'purchase_refund', 'subscription',
    'connectivity', 'messages_calls', 'apps_appstore', 'battery_charging',
    'software_update', 'device_hardware', 'other_services',
}

SYSTEM = '''You are a customer support assistant for the selected brand. The objective is safe, evidence-grounded support, not creative writing.
Return ONLY valid JSON with keys: intent, intent_confidence, reply.
The intent must be one of: account_access, billing_purchase, purchase_refund, subscription, connectivity, messages_calls, apps_appstore, battery_charging, software_update, device_hardware, other_services.
Use the historical cases as evidence. Do not invent policies, refund decisions, timelines, or capabilities. Never ask for passwords, OTPs, full card numbers, or other secrets in a public reply. If evidence is insufficient, draft a safe handoff-oriented response.
Keep the reply concise and natural for a public social-support interaction.'''

class LLMUnavailable(RuntimeError): pass

def llm_generate(message: str, intent_hint: str, retrieved: list[dict[str, Any]]):
    try:
        from openai import OpenAI
    except Exception as e:
        raise LLMUnavailable('Install openai and set OPENAI_API_KEY to use the LLM path.') from e
    key=os.getenv('OPENAI_API_KEY')
    if not key: raise LLMUnavailable('OPENAI_API_KEY is not set.')
    model=os.getenv('OPENAI_MODEL','gpt-4o-mini')
    base_url=os.getenv('OPENAI_BASE_URL')
    evidence='\n\n'.join([f"CASE {i+1}\nCustomer: {r['customer_text']}\nSupport: {r['support_text']}\nSimilarity: {r['score']:.3f}" for i,r in enumerate(retrieved)])
    prompt=f"Customer message:\n{message}\n\nHeuristic intent hint: {intent_hint}\n\nHistorical evidence:\n{evidence}"
    client_args = {
        'api_key': key,
        'timeout': float(os.getenv('OPENAI_TIMEOUT_SECONDS', '45')),
        # The caller falls back safely when the optional provider is unavailable.
        'max_retries': 0,
    }
    if base_url:
        client_args['base_url'] = base_url
    try:
        client=OpenAI(**client_args)
        resp=client.chat.completions.create(
            model=model,
            messages=[{'role':'system','content':SYSTEM},{'role':'user','content':prompt}],
            temperature=0,
        )
        content=resp.choices[0].message.content or '{}'
        # Tolerate a Markdown fence while still requiring a complete JSON object.
        content=content.strip().removeprefix('```json').removesuffix('```').strip()
        data=json.loads(content)
        intent=str(data.get('intent', '')).strip()
        confidence=float(data.get('intent_confidence'))
        reply_value=data.get('reply')
        reply=reply_value.strip() if isinstance(reply_value, str) else ''
    except Exception as exc:
        raise LLMUnavailable(f'LLM generation unavailable ({type(exc).__name__}).') from exc
    if intent not in VALID_INTENTS or not 0.0 <= confidence <= 1.0 or not reply:
        raise LLMUnavailable('LLM returned an invalid intent, confidence, or reply.')
    return {'intent': intent, 'intent_confidence': confidence, 'reply': reply}
