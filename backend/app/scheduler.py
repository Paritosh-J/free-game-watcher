import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from app.config import settings
from app.games_clients import fetch_gamerpower, fetch_epic_freegames, normalize_gamerpower_item
from app.db import get_session
from app.models import User, AlertedGame
from app.messaging import send_whatsapp_message
from sqlmodel import select
from datetime import datetime, timezone
from sqlmodel.ext.asyncio.session import AsyncSessionq
from types import List

logger = logging.getLogger("scheduler")
scheduler = AsyncIOScheduler()

async def poll_and_alert():
    logger.info("ℹ️  Poll job started: fetching games...")
    
    # fetch from gamerpower (both steam and epic)
    gp_steam = await fetch_gamerpower(platform="steam")
    gp_epic = await fetch_epic_freegames(platform="epic-games-store")
    epic_raw = await fetch_epic_freegames()
    
    # collect normalized games into dict by id
    games = {}
    
    # normalize gamerpower steam
    for item in gp_steam:
        g = normalize_gamerpower_item(item)
        games[g["id"]] = g
        
    # normalize gamerpwer epic
    for item in gp_epic:
        g = normalize_gamerpower_item(item)
        games[g["id"]] = g
        
    # normalize epic official
    for item in epic_raw:
        gid = str(item.get("id") or item.get("title"))
        games[gid] = {"id": gid, "title": item.get["title"], "url": item.get("url"), "platform": "epic", "ends_at": item.get("end_date")}
        
    # now if no games, nothing to do
    if not games:
        logger.info("No free games found in this poll.")
        return
    
    # load users and decide which to alert
    async with get_session() as session:
        result = await session.execute(select(User).where(User.verified == True))
        users: List[User] = result.scalars().all()
        
        for user in users:
            # for each game, check if alerted earlier
            to_alert = []
            for gid, g in games.items():
                q = select(AlertedGame).where(AlertedGame.user_id == user.id, AlertedGame.game_id == str(gid))
                res = await session.execute(q)
                already = res.scalar_one_or_none()
                
                if not already:
                    to_alert.append(g)
                    
            if not to_alert:
                continue
            
        # compose message
        lines = ["🎮 *Free Game Alert!*", ""]
        for g in to_alert:
            title = g.get("title")
            url = g.get("url") or ""
            ends_at = g.get("ends_at") or ""
            lines.append(f"• {title} — ends: {ends_at}\n  {url}")
        
        lines.append("")
        lines.append("Grab them quickly!!!")
        
        message_text = "\n".join(lines)
        
        # send alert via WhatsApp
        sent = await send_whatsapp_message(user.phone, message_text)
        if sent:
            # record alerted game
            for g in to_alert:
                ag = AlertedGame(user_id=user.id, game_id=str(g.get("id")), game_title=g.get("title"))
                session.add(ag)
                
            # update user's last_alert_at
            user.last_alert_at = datetime.now(timezone.utc)
            await session.commit()
            
            logger.info(f"ℹ️  Sent {len(to_alert)} alerts to user {user.phone}")
        
        else:
            logger.warning(f"❌ Failed to send alert to {user.phone}")
            

def start_scheduler():
    logger.info("ℹ️  Starting scheduler")
    
    scheduler.remove_all_jobs()
    interval = settings.POLL_INTERVAL_MINUTES
    scheduler.add_job(poll_and_alert, IntervalTrigger(minutes=interval), id="poll_and_alert", replace_existing=True, next_run_time=None)
    
    scheduler.start()
    logger.info("✅ Scheduler start successful")


def shutdown_scheduler():
    try:
        scheduler.shutdown(wait=False)
        logger.info("✅ Scheduler shutdown successful")
    except Exception:
        logger.exception("❌ Error shutting down scheduler")