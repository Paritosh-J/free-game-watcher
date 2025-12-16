from sqlmodel import SQLModel, Field, Column, String, Boolean, DateTime
from typing import Optional
from datetime import datetime, timezone

class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    phone: str = Field(index=True, sa_column=Column(String, unique=True, nullable=False))
    verified: bool = Field(default=False)
    created_at = datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
class OTP(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    phone: str = Field(index=True, sa_column=Column(String, nullable=False))
    code: str = Field(sa_column=Column(index=True, nullable=False))
    expires_at: datetime = Field(nullable=False)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
class AlertedGame(SQLModel, table=True):
    """
    Records that a given game (by external id) was alerted to a specific user.
    This avoids duplicate alerts to same user.
    """
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(index=True)
    game_id: str = Field(index=True, sa_column=Column(String, nullable=False))
    game_title: str = Field(sa_column=Column(String, nullable=False))
    alerted_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: Optional[datetime] = None  # optional expiry (store game expiry if available)