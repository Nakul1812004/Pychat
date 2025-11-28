# backend/routes/users.py

from fastapi import APIRouter, HTTPException, Depends
from backend.database import get_db
from backend.auth import (
    hash_password, verify_password,
    create_access_token, decode_token
)
from backend.models import UserCreate, UserLogin, UserResponse
import uuid, random, string, time

router = APIRouter()


# -------------------------------------------------------------------
# INTERNAL: safe WebSocket sender (avoids circular imports)
# -------------------------------------------------------------------
async def send_ws(username: str, payload: dict):
    """Lazy-import ws_send to avoid circular import"""
    from backend.routes.websocket import ws_send
    await ws_send(username, payload)


# -------------------------------------------------------------------
#   Utility: generate referral ID
# -------------------------------------------------------------------
def generate_referral_id(length: int = 6):
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))


# -------------------------------------------------------------------
#   SIGNUP
# -------------------------------------------------------------------
@router.post("/signup", response_model=UserResponse)
async def signup(user: UserCreate, db=Depends(get_db)):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not connected")

    existing = await db.users.find_one({"username": user.username})
    if existing:
        raise HTTPException(status_code=400, detail="Username already taken")

    referral_id = str(uuid.uuid4())[:8]

    new_user = {
        "username": user.username,
        "password": hash_password(user.password),
        "referral_id": referral_id,
        "friends": [],
        "notifications": [],
        "rooms": []
    }

    await db.users.insert_one(new_user)

    return {
        "username": user.username,
        "referral_id": referral_id
    }


# -------------------------------------------------------------------
#   LOGIN
# -------------------------------------------------------------------
@router.post("/login")
async def login(user: UserLogin, db=Depends(get_db)):
    db_user = await db.users.find_one({"username": user.username})
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    if not verify_password(user.password, db_user["password"]):
        raise HTTPException(status_code=401, detail="Incorrect password")

    token = create_access_token({"username": db_user["username"]})

    return {
        "username": db_user["username"],
        "referral_id": db_user["referral_id"],
        "token": token
    }


# -------------------------------------------------------------------
#   ADD FRIEND (real-time)
# -------------------------------------------------------------------
@router.post("/add_friend")
async def add_friend(referral_id: str, token: str):
    db = await get_db()
    user_data = decode_token(token)

    if not user_data:
        raise HTTPException(status_code=401, detail="Invalid token")

    sender = user_data["username"]

    receiver = await db.users.find_one({"referral_id": referral_id})
    if not receiver:
        raise HTTPException(status_code=404, detail="Friend not found")

    receiver_username = receiver["username"]

    if receiver_username == sender:
        raise HTTPException(status_code=400, detail="You cannot add yourself")

    # Save notification
    await db.users.update_one(
        {"username": receiver_username},
        {"$push": {
            "notifications": {
                "type": "friend_request",
                "from": sender,
                "timestamp": time.time()
            }
        }}
    )

    # REAL-TIME notification
    await send_ws(receiver_username, {
        "type": "notification",
        "event": "friend_request",
        "from": sender
    })

    return {"message": f"Friend request sent to {receiver_username}"}


# -------------------------------------------------------------------
#   GET NOTIFICATIONS
# -------------------------------------------------------------------
@router.get("/notifications")
async def get_notifications(token: str):
    db = await get_db()
    user_data = decode_token(token)

    if not user_data:
        raise HTTPException(status_code=401, detail="Invalid token")

    user = await db.users.find_one({"username": user_data["username"]})
    return user.get("notifications", [])


# -------------------------------------------------------------------
#   ACCEPT FRIEND REQUEST  (real-time)
# -------------------------------------------------------------------
@router.post("/accept_friend")
async def accept_friend(sender: str, token: str, db=Depends(get_db)):
    user_data = decode_token(token)
    if not user_data:
        raise HTTPException(status_code=401, detail="Invalid token")

    receiver_username = user_data["username"]

    # Add each other as friends
    await db.users.update_one(
        {"username": receiver_username},
        {"$addToSet": {"friends": sender}}
    )

    await db.users.update_one(
        {"username": sender},
        {"$addToSet": {"friends": receiver_username}}
    )

    # Remove old notification
    await db.users.update_one(
        {"username": receiver_username},
        {"$pull": {"notifications": {"type": "friend_request", "from": sender}}}
    )

    # Real-time updates BOTH ways
    await send_ws(receiver_username, {
        "type": "friend_list_update",
        "event": "friend_accepted",
        "from": sender
    })

    await send_ws(sender, {
        "type": "friend_list_update",
        "event": "friend_accepted",
        "from": receiver_username
    })

    return {"message": "Friend added successfully"}


# -------------------------------------------------------------------
#   GET USER PROFILE
# -------------------------------------------------------------------
@router.get("/me")
async def get_me(token: str, db=Depends(get_db)):
    user_data = decode_token(token)

    if not user_data:
        raise HTTPException(status_code=401, detail="Invalid token")

    user = await db.users.find_one({"username": user_data["username"]})

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.setdefault("friends", [])
    user.setdefault("notifications", [])

    user["_id"] = str(user["_id"])
    return user
