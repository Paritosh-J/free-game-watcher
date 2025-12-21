from __future__ import annotations
from pathlib import Path
from typing import Optional
from pydantic import BaseSettings, Field

_ENV_PATH = Path(__file__).resolve().parents[1] / ".env"

class Settings(BaseSettings):
    """
    Application settings loaded exclusively from the .env file located at:
      <project-root>/backend/.env

    IMPORTANT:
      - Core / required settings are declared with Field(...).
      - Optional settings are declared with default None.
      - This file intentionally does not hardcode runtime constants.
    """
    
    # import core settings
    APP_HOST: str = Field(..., env="APP_HOST")
    APP_PORT: int = Field(..., env="APP_PORT")
    ENV: str = Field(..., env="ENV")
    DATABASE_URL: str = Field(..., env="DATABASE_URL")
    
    # Twilio
    TWILIO_ACCOUNT_STD: Optional[str] = Field(..., env="TWILIO_ACCOUNT_SID")
    TWILIO_AUTH_TOKEN: Optional[str] = Field(..., env="TWILIO_AUTH_TOKEN")
    TWILIO_SMS_FROM: Optional[str] = Field(..., env="TWILIO_SMS_FROM")
    TWILIO_WHATSAPP_FROM: Optional[str] = Field(..., env="TWILIO_WHATSAPP_FROM")

    # APIs
    GAMERPOWER_API: Optional[str] = Field(..., env="GAMERPOWER_API")
    EPIC_API: Optional[str] = Field(..., env="EPIC_API")
    POLL_INTERVAL_MINUTES: Optional[int] = Field(..., env="POLL_INTERVAL_MINUTES")

    class Config:
        env_file = str(_ENV_PATH)


settings = Settings()