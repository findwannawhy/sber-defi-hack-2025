import uuid
import shutil
import os
from pathlib import Path
from fastapi import UploadFile, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import httpx

from app.core.config import settings
from app.notification.schemas import BotNotificationRequest
import app.models as models

TEMP_HTML_DIR = Path(__file__).parent / "temp_notification_html"

# Создаем директорию, если она не существует
try:
    os.makedirs(TEMP_HTML_DIR, exist_ok=True)
except Exception as e:
    raise HTTPException(status_code=500, detail=f"Не удалось создать директорию для уведомлений: {str(e)}")

async def save_notification_html(file: UploadFile) -> str:
    notification_id = uuid.uuid4().hex
    file_path = TEMP_HTML_DIR / f"{notification_id}.html"
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при сохранении файла уведомления: {str(e)}")
    finally:
        file.file.close()
    return notification_id

async def get_users_for_notification(db: AsyncSession, address: str, network: str) -> tuple[list[int], str]:
    query = select(models.Contract.user_id, models.Contract.name).where(
        models.Contract.address == address,
        models.Contract.network == network
    )
    result = await db.execute(query)
    rows = result.fetchall()
    user_ids = [row[0] for row in rows]
    contract_name = rows[0][1] if rows else ""
    return user_ids, contract_name

async def send_notification_to_bot(user_ids: list[int], notification_id: str, contract_name: str):
    frontend_base_url = settings.FRONTEND_BASE_URL
    bot_base_url = settings.BOT_BASE_URL

    if not bot_base_url:
        raise HTTPException(status_code=500, detail="BOT_BASE_URL не настроен")
    if not frontend_base_url:
        raise HTTPException(status_code=500, detail="FRONTEND_BASE_URL не настроен")

    notification_url = f"{frontend_base_url}/proxy-notification/{notification_id}"
    payload = BotNotificationRequest(
        user_ids=user_ids,
        url=notification_url,
        contract_name=contract_name
    ).model_dump()

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(f"{bot_base_url}/bot/notify", json=payload)
            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            raise HTTPException(status_code=500, detail=f"Ошибка при отправке уведомления боту: {e.response.status_code}")
        except httpx.RequestError as e:
            raise HTTPException(status_code=500, detail=f"Ошибка соединения при отправке уведомления боту: {str(e)}")

def get_notification_file_path(notification_id: str) -> Path:
    try:
        uuid.UUID(notification_id)
    except ValueError:
        pass

    file_path = TEMP_HTML_DIR / f"{notification_id}.html"
    if not file_path.is_file():
        raise HTTPException(status_code=404, detail="HTML файл уведомления не найден")
    return file_path 