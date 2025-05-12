from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime
from sqlalchemy import UniqueConstraint

class User(SQLModel, table=True):
    __tablename__ = "users"
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(index=True, nullable=False)
    name: Optional[str] = None
    telegram_user_id: Optional[int] = None
    verification_code: Optional[str] = None
    is_verified: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)

class Contract(SQLModel, table=True):
    __tablename__ = "contracts"
    __table_args__ = (UniqueConstraint("user_id", "network", "address", name="_user_network_address_uc"),)

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int
    network: str = Field(index=True)
    address: str = Field(index=True)
    name: Optional[str] = None
