# backend/auth.py
from passlib.context import CryptContext
from jose import jwt, JWTError, ExpiredSignatureError
from datetime import datetime, timedelta
import uuid
import os
from dotenv import load_dotenv

load_dotenv()

# -------------------- CONFIG --------------------
SECRET_KEY = os.getenv("SECRET_KEY", "supersecretkey123")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_HOURS = 5

pwd_context = CryptContext(
    schemes=["argon2"],
    deprecated="auto",
    argon2__memory_cost=102400,
    argon2__parallelism=8,
    argon2__time_cost=3
)

# -------------------------------------------------
#   PASSWORD HASHING
# -------------------------------------------------
def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


# -------------------------------------------------
#   CREATE ACCESS TOKEN
# -------------------------------------------------
def create_access_token(data: dict, expires_delta: timedelta = None) -> str:
    """Generate JWT token with username + token_id + exp + type."""

    if expires_delta is None:
        expires_delta = timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)

    to_encode = data.copy()

    # Add required fields for WS authentication
    to_encode.update({
        "exp": datetime.utcnow() + expires_delta,
        "type": "access",
        "token_id": str(uuid.uuid4())  # prevents reuse after logout
    })

    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


# -------------------------------------------------
#   DECODE TOKEN
# -------------------------------------------------
def decode_token(token: str):
    """
    Decode JWT safely.
    
    Returns:
        - dict(user data) → if valid
        - None → if invalid or expired
    """

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

        # Required fields check
        if (
            "username" not in payload or
            "type" not in payload or
            payload["type"] != "access"
        ):
            return None

        return payload

    except ExpiredSignatureError:
        print("❌ Token expired")
        return None

    except JWTError:
        print("❌ Invalid token")
        return None
