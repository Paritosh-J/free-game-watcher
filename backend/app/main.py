import os
import uvicorn
from fastapi import FastAPI, HTTPException, BackgroundTasks
from app.config import settings
from app.schemas import SubscribeIn, VerifyIn, UnsubscribeIn
from app.utils import normalize_phone
from app.otp import create_and_store_otp, verify_otp, cleanup_expired_otps
from app.messaging import send_sms_otp
from app.db import init_db, get_session
from app.models import User
from app.scheduler import start_scheduler, shutdown_scheduler
from sqlmodel import select
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("freegamewatcher")

app = FastAPI(title="FreeGameWatcher - Backend (MVP)")

@app.get("/health")
async def health_check():
    from datetime import datetime, timezone
    logger.info("ℹ️  Health endpoint: OK✅")
    return {"ok": True, "now": datetime.now(timezone.utc).isoformat()}

@app.on_event("startup")
async def on_startup():
    logger.info("ℹ️  Initializing DB and scheduler...")
    
    await init_db()
    
    # prevent scheduler from running in reload parent process
    if os.environ.get("RUN_MAIN") == "true" or os.environ.get("UVICORN_RELOAD") != "true":
        start_scheduler()
    else:
        logger.info("⏭️  Scheduler skipped in reload watcher process")


@app.on_event("shutdown")
async def on_shutdown():
    shutdown_scheduler()


@app.post("/subscribe")
async def subscribe(payload: SubscribeIn, background_tasks: BackgroundTasks):
    logger.info("ℹ️  Subscribing...")
    
    phone = normalize_phone(payload.phone)
    # create or find user (unverified)
    async with get_session() as session:  # AsyncSession
        q = select(User).where(User.phone == phone)
        res = await session.execute(q)
        user = res.scalar_one_or_none()
        if user and user.verified:
            raise HTTPException(status_code=400, detail="Phone already subscribed and verified.")
        if not user:
            user = User(phone=phone, verified=False)
            session.add(user)
            await session.commit()
            await session.refresh(user)

    # create OTP and send SMS in background
    code = await create_and_store_otp(phone)
    # send SMS async (non-blocking) - use background task
    background_tasks.add_task(send_sms_otp, phone, code)
    
    return {"success": True, "message": "OTP sent (if SMS provider configured). Please verify."}


@app.post("/verify")
async def verify(payload: VerifyIn):
    phone = normalize_phone(payload.phone)
    
    ok = await verify_otp(phone, payload.code)
    if not ok:
        raise HTTPException(status_code=400, detail="Invalid or expired OTP.")
    # mark user verified
    async with get_session() as session:
        q = select(User).where(User.phone == phone)
        res = await session.execute(q)
        user = res.scalar_one_or_none()
        if not user:
            # create user if not exists
            user = User(phone=phone, verified=True)
            session.add(user)
        else:
            user.verified = True
        await session.commit()
    
    return {"success": True, "message": "Phone verified and subscribed for alerts."}


@app.post("/unsubscribe")
async def unsubscribe(payload: UnsubscribeIn):
    logger.info(f"ℹ️  Unsubscribing {payload.phone}")
    
    phone = normalize_phone(payload.phone)
    async with get_session() as session:
        q = select(User).where(User.phone == phone)
        res = await session.execute(q)
        user = res.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=404, detail="Phone not found.")
        await session.delete(user)
        await session.commit()
    
    return {"success": True, "message": "Unsubscribed and removed."}


@app.get("/test-poll-now")
async def run_poll_now():
    logging.debug("ℹ️  Testing manual poll now...")
    
    from app.scheduler import poll_and_alert
    await poll_and_alert()
    
    return {"message": "Poll job executed manually"}


@app.get("/status/{phone}")
async def status(phone: str):
    logger.info(f"ℹ️  Checking subscription status for {phone}")
    phone = normalize_phone(phone)
    async with get_session() as session:
        q = select(User).where(User.phone == phone)
        res = await session.execute(q)
        user = res.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=404, detail="Not found.")
        return {"phone": user.phone, "verified": user.verified, "last_alert_at": str(user.last_alert_at) if user.last_alert_at else None}


@app.post("/debug/cleanup_otps")
async def debug_cleanup_otps():
    await cleanup_expired_otps()
    return {"ok": True}


if __name__ == "__main__":
    uvicorn.run("app.main:app", host=settings.APP_HOST, port=settings.APP_PORT, reload=(settings.ENV == "development"))
