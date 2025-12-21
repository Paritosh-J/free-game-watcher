# backend/app/models.py
from __future__ import annotations
from typing import Optional
from datetime import datetime, timezone

from sqlmodel import SQLModel, Field
from sqlalchemy import Column, String, Integer, DateTime, Boolean


class User(SQLModel, table=True):
    """
    Subscriber record
    """
    id: Optional[int] = Field(default=None, primary_key=True)
    phone: str = Field(
        index=True,
        sa_column=Column("phone", String(length=32), unique=True, nullable=False),
    )
    verified: bool = Field(default=False, sa_column=Column("verified", Boolean, nullable=False))
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column("created_at", DateTime(timezone=True), nullable=False),
    )
    last_alert_at: Optional[datetime] = Field(
        default=None,
        sa_column=Column("last_alert_at", DateTime(timezone=True), nullable=True),
    )


class OTP(SQLModel, table=True):
    """
    One-time-passwords for verification.
    """
    id: Optional[int] = Field(default=None, primary_key=True)
    phone: str = Field(
        index=True,
        sa_column=Column("phone", String(length=32), nullable=False),
    )
    code: str = Field(
        sa_column=Column("code", String(length=6), nullable=False),
    )
    expires_at: datetime = Field(
        sa_column=Column("expires_at", DateTime(timezone=True), nullable=False),
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column("created_at", DateTime(timezone=True), nullable=False),
    )


class AlertedGame(SQLModel, table=True):
    """
    Records which user was alerted about which game (by external id).
    """
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(
        index=True,
        sa_column=Column("user_id", Integer, nullable=False),
    )
    game_id: str = Field(
        index=True,
        sa_column=Column("game_id", String(length=128), nullable=False),
    )
    game_title: str = Field(
        sa_column=Column("game_title", String(length=255), nullable=False),
    )
    alerted_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column("alerted_at", DateTime(timezone=True), nullable=False),
    )
    expires_at: Optional[datetime] = Field(
        default=None,
        sa_column=Column("expires_at", DateTime(timezone=True), nullable=True),
    )
