import os
import httpx
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from dotenv import load_dotenv
from datetime import datetime
from backend.database import get_db
from backend.models import ChatRequest

load_dotenv("D:/Chat bot/backend/.env")

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

ai_router = APIRouter()


async def query_groq_api(model: str, prompt: str) -> str:
    url = "https://api.groq.com/openai/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json",
    }

    body = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.6,
    }

    async with httpx.AsyncClient() as client:
        r = await client.post(url, json=body, headers=headers)

    if r.status_code != 200:
        raise HTTPException(status_code=500, detail=r.text)

    return r.json()["choices"][0]["message"]["content"]


# ------------------------------------------------
#  SAVE AI CHAT MESSAGE TO DATABASE
# ------------------------------------------------
async def save_ai_message(db, user: str, role: str, message: str):
    await db.ai_messages.insert_one({
        "user": user,
        "role": role,
        "message": message,
        "timestamp": datetime.utcnow()
    })


# ------------------------------------------------
#  LOAD AI CHAT HISTORY
# ------------------------------------------------
@ai_router.get("/history")
async def get_ai_history(username: str, db=Depends(get_db)):
    msgs = await db.ai_messages.find({"user": username}).sort("timestamp", 1).to_list(500)

    formatted = []
    for m in msgs:
        formatted.append({
            "role": m["role"],
            "message": m["message"],
            "timestamp": m["timestamp"].isoformat()
        })

    return formatted


# ------------------------------------------------
#  MAIN AI CHAT ENDPOINT
# ------------------------------------------------
@ai_router.post("/chat")
async def chat(request: ChatRequest, db=Depends(get_db)):
    # Generate model reply
    reply = await query_groq_api(request.model, request.message)

    # Save both prompt + reply
    await save_ai_message(db, request.username, "user", request.message)
    await save_ai_message(db, request.username, "assistant", reply)

    return {"reply": reply}
