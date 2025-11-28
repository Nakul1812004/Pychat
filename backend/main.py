# backend/main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# DB
from backend.database import connect_to_mongo, close_mongo_connection

# Routers
from backend.routes.users import router as user_router
from backend.routes.chat import router as chat_router
from backend.routes.chat_history import router as history_router
from backend.routes.ai_chat import ai_router
from backend.routes.websocket import websocket_endpoint


# ---------------------------------------------------------
#    FASTAPI APP
# ---------------------------------------------------------
app = FastAPI(title="Pychat Backend")


# ---------------------------------------------------------
#    CORS (Allow all — required for ngrok/public access)
# ---------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # Allow ngrok + other PCs
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------
#    ROUTES
# ---------------------------------------------------------
app.include_router(user_router, prefix="/users", tags=["Users"])
app.include_router(chat_router, prefix="/chat", tags=["Chat"])
app.include_router(history_router, tags=["History"])
app.include_router(ai_router, prefix="/ai", tags=["AI"])

# WebSocket (single correct endpoint)
app.websocket("/ws/{username}")(websocket_endpoint)


# ---------------------------------------------------------
#    STARTUP + SHUTDOWN
# ---------------------------------------------------------
@app.on_event("startup")
async def startup_event():
    print("🔥 Starting Pychat backend...")
    await connect_to_mongo()
    print("✅ MongoDB connected.")
    print("🌐 WebSocket endpoint ready at /ws/<username>")


@app.on_event("shutdown")
async def shutdown_event():
    print("🛑 Shutting down backend...")
    await close_mongo_connection()
    print("🗄 MongoDB connection closed.")
