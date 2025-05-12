import time
import jwt
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select
from app.core.config import settings
from app.core.db import get_session
from app.models import User
from typing import Optional, Literal

ACCESS_TOKEN_EXPIRE_MINUTES = 15
REFRESH_TOKEN_EXPIRE_DAYS = 7
ALGORITHM = "HS256"

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth")

# Создает Access Token
def create_access_token(user_id: int) -> str:
    expire = time.time() + ACCESS_TOKEN_EXPIRE_MINUTES * 60
    payload = {"user_id": user_id, "exp": expire, "type": "access"}
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=ALGORITHM)

# Создает Refresh Token
def create_refresh_token(user_id: int) -> str:
    expire = time.time() + REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60
    payload = {"user_id": user_id, "exp": expire, "type": "refresh"}
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=ALGORITHM)

# Проверяет валидность токена и возвращает payload
def verify_token(token: str, expected_type: Optional[Literal["access", "refresh"]] = None) -> Optional[dict]:
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[ALGORITHM])
        if payload.get("exp", 0) < time.time():
            raise jwt.ExpiredSignatureError("Token has expired")
        if expected_type and payload.get("type") != expected_type:
            raise HTTPException(status_code=401, detail=f"Invalid token type. Expected '{expected_type}'.")
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.PyJWTError as e:
        return None
    except HTTPException as e:
        raise e
    except Exception as e:
        return None

# Получает текущего пользователя из базы данных по Access токену
async def get_current_user(
    token: str = Depends(oauth2_scheme),
    session: AsyncSession = Depends(get_session)
) -> User:
    payload = verify_token(token, expected_type="access")
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired access token")

    user_id = payload.get("user_id")
    if user_id is None:
         raise HTTPException(status_code=401, detail="Invalid access token payload")

    stmt = select(User).where(User.id == user_id)
    result = await session.exec(stmt)
    user = result.one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found for valid token")
    return user