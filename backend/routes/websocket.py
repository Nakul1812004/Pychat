# backend/routes/websocket.py

from fastapi import WebSocket, WebSocketDisconnect, Query
from backend.auth import decode_token
from backend.database import get_db
import json
from datetime import datetime
from typing import Dict, Optional, Any

connected_users: Dict[str, WebSocket] = {}


async def ws_send(username: str, data: dict) -> bool:

    ws = connected_users.get(username)
    if not ws:
        return False

    try:
        await ws.send_text(json.dumps(data))
        return True
    except Exception as e:

        print(f"❌ ws_send error sending to {username}: {e}")
        return False


async def websocket_endpoint(websocket: WebSocket, username: str, token: str = Query(...)):


    user = decode_token(token)
    if not user or user.get("username") != username:

        try:
            await websocket.close(code=403)
        except:
            pass
        return

    db = await get_db()
    if db is None:

        try:
            await websocket.close(code=1011)
        except:
            pass
        return

    messages_col = db["messages"]
    users_col = db["users"]

    await websocket.accept()
    connected_users[username] = websocket
    print(f"{username} connected via WebSocket")

    try:
        while True:
            raw = await websocket.receive_text()
            try:
                data = json.loads(raw)
            except Exception:
                print(f"⚠ Invalid JSON from {username}: {raw}")
                continue

            event_type = data.get("type")

            if event_type == "private":
                receiver: Optional[str] = data.get("to")
                text: Optional[str] = data.get("message", "")

                ts_iso = datetime.utcnow().isoformat()

                try:
                    await messages_col.insert_one({
                        "sender": username,
                        "receiver": receiver,
                        "message": text,
                        "timestamp": datetime.utcnow(),
                        "participants": sorted([username, receiver]) if receiver else [username]
                    })
                except Exception as e:
                    print(f"❌ DB insert failed for message from {username} to {receiver}: {e}")

                payload = {
                    "type": "message",
                    "from": username,
                    "message": text,
                    "timestamp": ts_iso
                }

                sent = await ws_send(receiver, payload)

                if not sent:
                    try:
                        await users_col.update_one(
                            {"username": receiver},
                            {"$push": {
                                "notifications": {
                                    "type": "message",
                                    "from": username,
                                    "message": text,
                                    "timestamp": ts_iso
                                }
                            }}
                        )
                        print(f"Receiver {receiver} offline — notification saved")
                    except Exception as e:
                        print(f"❌ Failed to save notification for {receiver}: {e}")

            elif event_type == "friend_request":
                receiver: Optional[str] = data.get("to")
                payload = {
                    "type": "notification",
                    "event": "friend_request",
                    "from": username,
                    "timestamp": datetime.utcnow().isoformat()
                }

                sent = await ws_send(receiver, payload)

                if not sent:
                    try:
                        await users_col.update_one(
                            {"username": receiver},
                            {"$push": {
                                "notifications": {
                                    "type": "friend_request",
                                    "from": username,
                                    "timestamp": datetime.utcnow()
                                }
                            }}
                        )
                        print(f"🔔 Friend request saved for {receiver}")
                    except Exception as e:
                        print(f"❌ Failed to save friend_request for {receiver}: {e}")

            elif event_type == "friend_accepted":
                receiver: Optional[str] = data.get("to")
                payload = {
                    "type": "friend_list_update",
                    "event": "friend_accepted",
                    "from": username,
                    "timestamp": datetime.utcnow().isoformat()
                }

                sent = await ws_send(receiver, payload)
                if not sent:
                    try:
                        await users_col.update_one(
                            {"username": receiver},
                            {"$push": {
                                "notifications": {
                                    "type": "friend_accepted",
                                    "from": username,
                                    "timestamp": datetime.utcnow()
                                }
                            }}
                        )
                        print(f"🔔 Friend accepted saved for {receiver}")
                    except Exception as e:
                        print(f"❌ Failed to save friend_accepted for {receiver}: {e}")

            else:
                # Unknown event — ignore or log
                print(f"Unknown event from {username}: {event_type}")

    except WebSocketDisconnect:
        print(f"{username} disconnected (client close)")
    except Exception as e:
        print(f"❌ WebSocket error for {username}: {e}")
    finally:
        try:
            if username in connected_users:
                del connected_users[username]
        except Exception:
            pass
        print(f"{username} removed from active connections")
