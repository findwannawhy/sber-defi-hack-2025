from pydantic import BaseModel
from typing import List
import uuid

class NotificationResponse(BaseModel):
    notification_id: str
    status: str

class BotNotificationRequest(BaseModel):
    user_ids: List[int]
    url: str
    contract_name: str 