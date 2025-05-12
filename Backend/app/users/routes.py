from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
import secrets
from app.schemas import UserPublic, ProfileUpdate
from app.schemas import TelegramStartLinkResponse
from app.auth.jwt import get_current_user
from app.core.db import get_session
from sqlmodel.ext.asyncio.session import AsyncSession
from app.models import User
from app.core.config import settings

router = APIRouter()

@router.get("/profile", response_model=UserPublic)
async def read_profile(current_user: User = Depends(get_current_user)):
    return current_user

@router.put("/profile", response_model=UserPublic)
async def update_profile(
    data: ProfileUpdate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    if data.name:
        current_user.name = data.name
    session.add(current_user)
    await session.commit()
    await session.refresh(current_user)
    return current_user

@router.post("/profile/telegram/start-linking", response_model=TelegramStartLinkResponse)
async def start_telegram_linking(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    if current_user.telegram_user_id and current_user.is_verified:
        raise HTTPException(status_code=400, detail="Telegram уже привязан и подтвержден.")

    code = secrets.token_hex(3)

    current_user.verification_code = code
    current_user.is_verified = False
    current_user.telegram_user_id = None
    session.add(current_user)
    await session.commit()

    bot_username = getattr(settings, 'TELEGRAM_BOT_USERNAME', 'SafeDeFi_bot')

    return TelegramStartLinkResponse(code=code, bot_username=f"@{bot_username}")

@router.delete("/profile/telegram", response_model=UserPublic)
async def unlink_telegram(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    if not current_user.telegram_user_id or not current_user.is_verified:
        raise HTTPException(status_code=400, detail="Telegram не привязан или не подтвержден.")

    current_user.telegram_user_id = None
    current_user.verification_code = None
    current_user.is_verified = False
    session.add(current_user)
    await session.commit()
    await session.refresh(current_user)
    return current_user
