import os
import requests
from dotenv import load_dotenv

load_dotenv()

GROK_API_KEY = os.getenv("GROK_API_KEY")
GROK_API_URL = "https://api.x.ai/v1/chat/completions"

async def call_grok(message: str) -> str:

    if not GROK_API_KEY:
        return "⚠️ GROK_API_KEY not found. Please add it to your .env file."

    headers = {
        "Authorization": f"Bearer {GROK_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "grok-2",
        "messages": [
            {"role": "user", "content": message}
        ]
    }

    try:
        response = requests.post(GROK_API_URL, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()
        reply = data["choices"][0]["message"]["content"]
        return reply.strip()
    except Exception as e:
        return f"❌ Error connecting to Grok AI: {str(e)}"
