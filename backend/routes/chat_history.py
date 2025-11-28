from fastapi import APIRouter, Depends, HTTPException, Query
from backend.database import get_db
from backend.auth import decode_token

router = APIRouter(prefix="/history")


@router.get("/private")
async def get_private_history(
    user: str,
    friend: str,
    token: str = Query(...),
    db=Depends(get_db)
):
    """Load private chat history between two users"""

    # Check auth
    user_data = decode_token(token)
    if not user_data:
        raise HTTPException(401, "Invalid token")

    # Prevent unauthorized viewing
    if user_data["username"] not in [user, friend]:
        raise HTTPException(403, "Not allowed")

    msgs = await db.messages.find(
        {
            "$or": [
                {"sender": user, "receiver": friend},
                {"sender": friend, "receiver": user}
            ]
        }
    ).sort("timestamp", 1).to_list(500)

    cleaned = []
    for m in msgs:
        m["_id"] = str(m["_id"])

        # Convert datetime → ISO string
        ts = m.get("timestamp")
        if hasattr(ts, "isoformat"):
            m["timestamp"] = ts.isoformat()

        cleaned.append(m)

    return cleaned


@router.get("/room")
async def get_room_history(
    room: str,
    token: str = Query(...),
    db=Depends(get_db)
):
    user_data = decode_token(token)
    if not user_data:
        raise HTTPException(401, "Invalid token")

    msgs = await db.messages.find({"room": room}).sort("timestamp", 1).to_list(500)

    cleaned = []
    for m in msgs:
        m["_id"] = str(m["_id"])
        ts = m.get("timestamp")
        if hasattr(ts, "isoformat"):
            m["timestamp"] = ts.isoformat()
        cleaned.append(m)

    return cleaned
