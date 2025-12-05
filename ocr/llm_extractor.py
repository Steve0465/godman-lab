import os
import json
from openai import OpenAI

# Small helper to call OpenAI and request a strict JSON response
SCHEMA = {
  "type": "object",
  "properties": {
    "vendor": {"type":"string"},
    "date": {"type":"string","description":"ISO date YYYY-MM-DD"},
    "subtotal": {"type":"number"},
    "tax": {"type":"number"},
    "total": {"type":"number"},
    "currency": {"type":"string"},
    "category": {"type":"string"},
    "confidence": {"type":"number","minimum":0,"maximum":1},
    "notes": {"type":"string"}
  },
  "required": ["vendor","date","subtotal"]
}

PROMPT_SYSTEM = "You are a precise extractor. Given OCR text from a receipt, return only JSON matching the schema exactly. If a field is missing, omit it or return null. The date should be ISO YYYY-MM-DD. The subtotal and tax should be numbers."


def extract_fields(text: str):
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key or api_key == 'your_openai_api_key_here':
        raise RuntimeError('OPENAI_API_KEY not set in environment')
    
    try:
        client = OpenAI(api_key=api_key)
        messages = [
            {"role":"system","content":PROMPT_SYSTEM},
            {"role":"user","content":f"Extract structured fields from this OCR text:\n\n{text}"}
        ]
        resp = client.chat.completions.create(
            model=os.getenv('OPENAI_MODEL','gpt-4o-mini'),
            messages=messages,
            temperature=0.0,
            max_tokens=512
        )
        out = resp.choices[0].message.content
        # try to load JSON from the model output
        try:
            parsed = json.loads(out)
            return parsed
        except Exception:
            # try to find JSON substring
            start = out.find('{')
            end = out.rfind('}')
            if start != -1 and end != -1:
                try:
                    parsed = json.loads(out[start:end+1])
                    return parsed
                except Exception:
                    return None
            return None
    except Exception as e:
        print('OpenAI extraction failed:', e)
        return None