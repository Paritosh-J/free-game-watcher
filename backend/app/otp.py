import logging
from datetime import datetime, timedelta, timezone
import random
from app.db import get_session
from app.models import OTP
from sqlalchemy import select, delete
from sqlmodel.ext.asyncio.session import AsyncSession
from typing import Optional

# Create a logger specific to this module
logger = logging.getLogger(__name__)

OTP_TTL_SECONDS = 5 * 60 # 5 minutes


def _generate_code() -> str:
    # 6-digit numeric OTP
    code = f"{random.randint(100000, 999999)}"
    logger.debug(f"ℹ️ Generated new OTP code: {code}")
    return code

async def create_and_store_otp(phone: str) -> str:
    code = _generate_code()
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(seconds=OTP_TTL_SECONDS)
    
    try:
        async with get_session() as session:
            # AsyncSession
            otp = OTP(phone=phone, code=code, expires_at=expires_at)
            session.add(otp)
            
            await session.commit()
            logger.info(f"ℹ️ Stored new OTP for phone {phone}. Expires at {expires_at.isoformat()}")
            
            return code
    except Exception as e:
        logger.error(f"❌ Failed to store OTP for phone {phone}: {e}", exc_info=True)
        # Depending on requirements, you might want to raise the exception or handle it
        raise


async def verify_otp(phone: str, code: str) -> bool:
    logger.info(f"ℹ️ Attempting to verify OTP for phone {phone} with code provided.")
    
    now = datetime.now(timezone.utc)
    
    async with get_session() as session:
        q = select(OTP).where(OTP.phone == phone, OTP.code == code, OTP.expires_at > now)
        result = await session.execute(q)
        row = result.scalar_one_or_none()
        
        if row:
            logger.info(f"✅ Verification successful for phone {phone}. Deleting related OTP records.")
            # delete used OTP(s)
            del_q = delete(OTP).where(OTP.phone == phone)
            
            await session.execute(del_q)
            await session.commit()
            
            return True
        else:
            logger.warning(f"❌ Verification failed for phone {phone}. Invalid code or expired.")
            return False


async def cleanup_expired_otps():
    logger.info("ℹ️ Starting cleanup of expired OTPs.")
    now = datetime.now(timezone.utc)
    
    try:
        async with get_session() as session:
            del_q = delete(OTP).where(OTP.expires_at <= now)
            
            await session.execute(del_q)
            await session.commit()
            
            # rowcount might not be reliable across all DB backends for async execute directly
            logger.info("✅ Finished cleanup of expired OTPs.")
    except Exception as e:
        logger.error(f"❌ Error during expired OTP cleanup: {e}", exc_info=True)

