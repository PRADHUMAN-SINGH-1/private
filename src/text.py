import re

def clean_text(text: str) -> str:
    s = str(text or '')
    s = re.sub(r'@\w+', ' ', s)
    s = re.sub(r'https?://\S+', ' ', s)
    s = re.sub(r'\s+', ' ', s).strip()
    return s
