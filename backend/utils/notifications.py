from backend.database import db

async def send_friend_request(to_username: str, from_username: str):
    """Send a friend request notification"""
    await db.users.update_one(
        {"username": to_username},
        {"$push": {"notifications": {"type": "friend_request", "from": from_username}}}
    )
    return {"message": f"Friend request sent to {to_username}"}


async def send_room_invite(to_username: str, room_name: str, from_username: str):
    """Send a chat room invitation"""
    await db.users.update_one(
        {"username": to_username},
        {"$push": {"notifications": {"type": "room_invite", "room": room_name, "from": from_username}}}
    )
    return {"message": f"Invitation to join '{room_name}' sent to {to_username}"}


async def get_notifications(username: str):
    """Retrieve a user's notifications"""
    user = await db.users.find_one({"username": username})
    if not user:
        return []
    return user.get("notifications", [])


async def clear_notifications(username: str):
    """Clear all notifications after user reads them"""
    await db.users.update_one(
        {"username": username},
        {"$set": {"notifications": []}}
    )
    return {"message": "Notifications cleared"}
