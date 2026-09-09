from __future__ import annotations
import json, os
from typing import Any

SYSTEM = '''You are a customer support assistant for the selected brand. The objective is safe, evidence-grounded support, not creative writing.
Return ONLY valid JSON with keys: intent, intent_confidence, reply.
The intent must be one of: account_access, billing_purchase, connectivity, messages_calls, apps_appstore, battery_charging, software_update, device_hardware, other_services.
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
    evidence='\n\n'.join([f"CASE {i+1}\nCustomer: {r['customer_text']}\nSupport: {r['support_text']}\nSimilarity: {r['score']:.3f}" for i,r in enumerate(retrieved)])
    prompt=f"Customer message:\n{message}\n\nHeuristic intent hint: {intent_hint}\n\nHistorical evidence:\n{evidence}"
    client=OpenAI(api_key=key)
    resp=client.chat.completions.create(model=model, messages=[{'role':'system','content':SYSTEM},{'role':'user','content':prompt}], temperature=0)
    content=resp.choices[0].message.content or '{}'
    # tolerate fenced JSON
    content=content.strip().removeprefix('```json').removesuffix('```').strip()
    data=json.loads(content)
    return data
