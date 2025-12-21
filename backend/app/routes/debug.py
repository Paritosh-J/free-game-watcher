from fastapi import APIRouter
from app.scheduler import poll_and_alert
import logging

logging.basicConfig(level=logging.INFO)

router = APIRouter(prefix="/debug", tags=["Debug"])

@router.post("/run-poll-now")
async def run_poll_now():
    logging.debug("ℹ️  Testing manual poll now...")
    
    await poll_and_alert()
    
    return {"message": "Poll job executed manually"}
