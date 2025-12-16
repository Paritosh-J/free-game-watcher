import os
from pydantic import BaseSettings

class Settings(BaseSettings):
    APP_HOST: str = os.getenv("APP_HOST")
    APP_PORT: str = int(os.getenv("APP_PORT"))
    ENV: str = os.getenv("ENV")
    
    DATABASE_URL: str = os.getenv("DATABASE_URL")
    
    # Twilio
    TWILIO_ACCOUNT_STD: str = os.getenv("TWILIO_ACCOUNT_SID")
    TWILIO_AUTH_TOKEN: str = os.getenv("TWILIO_AUTH_TOKEN")
    TWILIO_SMS_FROM: str = os.getenv("TWILIO_SMS_FROM")
    TWILIO_WHATSAPP_FROM: str = os.getenv("TWILIO_WHATSAPP_FROM")

    # APIs
    GAMERPOWER_API: str = os.getenv("GAMERPOWER_API")
    EPIC_API: str = os.getenv("EPIC_API")

    POLL_INTERVAL_MINUTES: int = int(os.getenv("POLL_INTERVAL_MINUTES"))

    class Config:
        env_file = ".env"


settings = Settings()