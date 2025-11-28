# backend/database.py

from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
from pathlib import Path
import asyncio, os, sys

ENV_PATH = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=ENV_PATH)

MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("DB_NAME", "chat_app")

client = None
db = None


# -----------------------------------------
# CONNECT TO MONGO
# -----------------------------------------
async def connect_to_mongo(retries: int = 5, delay: int = 3):
    global client, db

    if not MONGO_URI:
        print("❌ ERROR: MONGO_URI missing in backend/.env")
        sys.exit(1)

    print(f"🧩 Connecting to MongoDB → {DB_NAME}")

    for attempt in range(1, retries + 1):
        try:
            client = AsyncIOMotorClient(
                MONGO_URI,
                serverSelectionTimeoutMS=8000
            )
            await client.admin.command("ping")
            db = client[DB_NAME]
            print(f"✅ Connected to MongoDB → {DB_NAME}")
            return

        except Exception as e:
            print(f"⚠️ attempt {attempt}/{retries} failed: {e}")
            if attempt < retries:
                await asyncio.sleep(delay)

    print("❌ MongoDB connection failed after retries.")
    sys.exit(1)


# -----------------------------------------
# CLOSE MONGO
# -----------------------------------------
async def close_mongo_connection():
    global client
    if client:
        client.close()
        print("🔒 MongoDB closed.")


# -----------------------------------------
# GET DB — used everywhere
# -----------------------------------------
async def get_db():
    global db
    if db is None:
        raise RuntimeError("❌ Database not initialized.")
    return db
