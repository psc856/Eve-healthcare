import os
from datetime import datetime, timedelta

from jose import JWTError, jwt
from pwdlib import PasswordHash

from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer

from sqlmodel import Session, select

from database import engine
from models import User


password_hash = PasswordHash.recommended()

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/auth/login"
)

SECRET = os.getenv(
    "JWT_SECRET",
    "dev-secret-change-this"
)

ALGORITHM = "HS256"


def get_password_hash(password: str) -> str:
    return password_hash.hash(password)


def verify_password(password: str, hashed_password: str) -> bool:
    return password_hash.verify(
        password,
        hashed_password
    )


def create_access_token(
    data: dict,
    expires_minutes: int = 60 * 24
):
    payload = data.copy()

    expire = datetime.utcnow() + timedelta(
        minutes=expires_minutes
    )

    payload["exp"] = expire

    return jwt.encode(
        payload,
        SECRET,
        algorithm=ALGORITHM
    )


def get_current_user(
    token: str = Depends(oauth2_scheme)
):
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials"
    )

    try:
        payload = jwt.decode(
            token,
            SECRET,
            algorithms=[ALGORITHM]
        )

        user_id = payload.get("sub")

        if not user_id:
            raise credentials_exception

        user_id = int(user_id)

    except (JWTError, ValueError):
        raise credentials_exception

    with Session(engine) as session:

        user = session.get(
            User,
            user_id
        )

        if not user:
            raise credentials_exception

        return user