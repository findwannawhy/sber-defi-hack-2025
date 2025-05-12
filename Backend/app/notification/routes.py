from fastapi import APIRouter, File, UploadFile, Form, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
import uuid

from app.core.db import get_session
from app.notification import services
from app.notification.schemas import NotificationResponse

router = APIRouter()

@router.post("/run", response_model=NotificationResponse)
async def run_notification(
    address: str = Form(...),
    network: str = Form(...),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_session)
):
    notification_id = await services.save_notification_html(file)
    user_ids, contract_name = await services.get_users_for_notification(db, address, network)

    if not user_ids:
        return NotificationResponse(notification_id=notification_id, status="success, no users found")

    await services.send_notification_to_bot(user_ids, notification_id, contract_name)
    return NotificationResponse(notification_id=notification_id, status="success")

@router.get("/html/{notification_id}", response_class=FileResponse)
async def get_notification_html(notification_id: str):
    try:
        uuid.UUID(notification_id) 
    except ValueError:
        raise HTTPException(status_code=400, detail="Некорректный ID уведомления")

    file_path = services.get_notification_file_path(notification_id)
    return FileResponse(path=file_path, media_type="text/html")
