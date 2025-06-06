# app/llm_client.py

import requests

# ─── Hard-code your Groq API Key here ───────────────────────────────────────────────
GROQ_API_KEY = "put ur api key"

GROQ_CHAT_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_TEXT_URL = "https://api.groq.com/v1/completions"
API_URL = GROQ_CHAT_URL  # or switch to GROQ_TEXT_URL if needed

def _get_api_key() -> str:
    if not isinstance(GROQ_API_KEY, str) or not GROQ_API_KEY.strip():
        raise EnvironmentError(
            "GROQ_API_KEY is not set correctly in app/llm_client.py."
        )
    return GROQ_API_KEY.strip()

def get_completion(
    prompt: str,
    model: str = "meta-llama/llama-4-scout-17b-16e-instruct",
    max_tokens: int = 2000,
    temperature: float = 0.7,
) -> str:
    api_key = _get_api_key()
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }

    if API_URL == GROQ_CHAT_URL:
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": temperature,
            "n": 1
        }
    else:
        payload = {
            "model": model,
            "prompt": prompt,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "n": 1
        }

    resp = requests.post(API_URL, headers=headers, json=payload)
    resp.raise_for_status()
    data = resp.json()

    if API_URL == GROQ_CHAT_URL:
        try:
            return data["choices"][0]["message"]["content"]
        except (KeyError, IndexError):
            raise ValueError(f"Unexpected chat response: {data}")
    else:
        try:
            return data["choices"][0]["text"]
        except (KeyError, IndexError):
            raise ValueError(f"Unexpected text response: {data}")
