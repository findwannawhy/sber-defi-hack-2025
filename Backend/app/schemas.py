from pydantic import BaseModel
from typing import Optional
from datetime import datetime

# Схема для возврата jwt после авторизации
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

# Какие поля пользователя безопасно возвращать клиенту
class UserPublic(BaseModel):
    id: int
    email: str
    name: Optional[str]
    telegram_user_id: Optional[int]
    is_verified: bool
    created_at: datetime

    class Config:
        orm_mode = True

# Схема для обновления данных пользователя
class ProfileUpdate(BaseModel):
    name: Optional[str]

# Схема для запроса на привязку Telegram
class TelegramLinkRequest(BaseModel):
    telegram_id: int

# Схема для проверки кода верификации
class CodeVerifyRequest(BaseModel):
    code: str

# Схема входных для добавления контракта
class ContractCreate(BaseModel):
    address: str
    network: str

# Схема выходных для получения контракта
class ContractRead(BaseModel):
    id: int
    address: str
    network: str
    name: Optional[str]
    user_id: int

    class Config:
        orm_mode = True

# Схема для удаления контракта
class ContractDelete(BaseModel):
    id: int

# Схема для ответа при старте привязки
class TelegramStartLinkResponse(BaseModel):
    code: str
    bot_username: str

# Схема для представления отчета аудита (данные для PDF)
class AuditReport(BaseModel):
    contract_address: str
    network: str
    audit_timestamp: datetime
    findings: list[str] # Список найденных уязвимостей или замечаний
    summary: str # Общее заключение

# Схема для представления найденной уязвимости
class VulnerabilityFinding(BaseModel):
    vulnerability: str  # Название уязвимости
    description: str    # Описание уязвимости
    function_name: str  # Имя функции, где найдена уязвимость
    confidence: str     # Уровень уверенности (например, High, Medium, Low)
    code_snippet: str   # Фрагмент кода с уязвимостью