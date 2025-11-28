from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

# 🧍 User model (used for signup/login)
class UserCreate(BaseModel):
    username: str
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class UserResponse(BaseModel):
    username: str
    referral_id: str

# 💬 Message model (used in chat rooms)
class Message(BaseModel):
    sender: str
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

# 🏠 Chat room model
class ChatRoom(BaseModel):
    room_name: str
    members: List[str]
    messages: Optional[List[Message]] = []

# 🧠 AI chat request
class ChatRequest(BaseModel):
    username: str          # <-- REQUIRED for history
    message: str
    model: str = "llama-3.1-8b-instant"

