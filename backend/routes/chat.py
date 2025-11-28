from fastapi import APIRouter, HTTPException, Depends
from backend.database import db
from backend.auth import decode_token
from backend.models import Message, ChatRoom
from datetime import datetime

router = APIRouter()

@router.post("/create_room")
async def create_room(room_name: str, token: str):
    """Create a new chat room"""
    user_data = decode_token(token)
    if not user_data:
        raise HTTPException(status_code=401, detail="Invalid token")

    existing_room = await db.chat_rooms.find_one({"room_name": room_name})
    if existing_room:
        raise HTTPException(status_code=400, detail="Chat room already exists")

    room = {
        "room_name": room_name,
        "members": [user_data["username"]],
        "messages": []
    }
    await db.chat_rooms.insert_one(room)
    return {"message": f"Chat room '{room_name}' created successfully!"}


@router.post("/join_room")
async def join_room(room_name: str, token: str):
    """Join an existing chat room"""
    user_data = decode_token(token)
    if not user_data:
        raise HTTPException(status_code=401, detail="Invalid token")

    user = user_data["username"]
    room = await db.chat_rooms.find_one({"room_name": room_name})
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")

    if user in room["members"]:
        return {"message": "Already in room"}

    await db.chat_rooms.update_one(
        {"room_name": room_name},
        {"$push": {"members": user}}
    )

    # Send notification to other members
    for member in room["members"]:
        await db.users.update_one(
            {"username": member},
            {"$push": {"notifications": {"type": "room_join", "room": room_name, "from": user}}}
        )

    return {"message": f"{user} joined the room '{room_name}'"}


@router.post("/send_message")
async def send_message(room_name: str, message: str, token: str):
    """Send a message to a chat room"""
    user_data = decode_token(token)
    if not user_data:
        raise HTTPException(status_code=401, detail="Invalid token")

    sender = user_data["username"]
    msg = {
        "sender": sender,
        "content": message,
        "timestamp": datetime.utcnow().isoformat()
    }

    result = await db.chat_rooms.update_one(
        {"room_name": room_name},
        {"$push": {"messages": msg}}
    )

    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Room not found")

    return {"message": "Message sent successfully"}


@router.get("/get_messages")
async def get_messages(room_name: str):
    """Retrieve all messages from a chat room"""
    room = await db.chat_rooms.find_one({"room_name": room_name})
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    return {"messages": room.get("messages", [])}


@router.get("/list_rooms")
async def list_rooms():
    """List all available chat rooms"""
    rooms = await db.chat_rooms.find().to_list(100)
    return [{"room_name": r["room_name"], "members": r["members"]} for r in rooms]
