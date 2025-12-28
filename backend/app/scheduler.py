import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from app.config import settings
from app.games_clients import fetch_gamerpower, fetch_epic_freegames, normalize_gamerpower_item
from app.db import get_session
from app.models import User, AlertedGame
from app.messaging import send_whatsapp_message
from sqlmodel import select
from datetime import datetime, timezone, timedelta

logger = logging.getLogger("scheduler")
scheduler = AsyncIOScheduler(timezone="UTC")

async def poll_and_alert():
    logger.info("ℹ️  Poll job started: fetching games...")
    
    # fetch from gamerpower (both steam and epic)
    gp_steam = await fetch_gamerpower(platform="steam")
    gp_epic = await fetch_epic_freegames()
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
        games[gid] = {"id": gid, "title": item.get("title"), "url": item.get("url"), "platform": "epic", "ends_at": item.get("end_date")}
        
    # now if no games, nothing to do
    if not games:
        logger.info("ℹ️  No free games found in this poll.")
        return
    
    # load users and decide which to alert
    logger.info("ℹ️  Loading users for alerting...")
    async with get_session() as session:
        result = await session.exec(
            select(User).where(User.verified == True)
        )
        users = result.all()
        
        for user in users:
            to_alert = []

            # for each game, check if alerted earlier
            for gid, g in games.items():
                q = select(AlertedGame).where(
                    AlertedGame.user_id == user.id,
                    AlertedGame.game_id == str(gid),
                )

                res = await session.exec(q)
                already = res.first()

                if not already:
                    to_alert.append(g)

            if not to_alert:
                continue

            lines = ["🎮 *Free Game Alert!*", ""]
            for g in to_alert:
                lines.append(
                    f"• {g.get('title')} — ends: {g.get('ends_at')}\n  {g.get('url')}"
                )

            lines.append("")
            lines.append("Grab them quickly!!!")

            message_text = "\n".join(lines)

            # send alert via WhatsApp
            sent = await send_whatsapp_message(user.phone, message_text)

            if sent:
                for g in to_alert:
                    session.add(
                        AlertedGame(
                            user_id=user.id,
                            game_id=str(g.get("id")),
                            game_title=g.get("title"),
                        )
                    )

                user.last_alert_at = datetime.now(timezone.utc)
                await session.commit()

                logger.info(f"✅ Sent {len(to_alert)} alerts to {user.phone}")
            else:
                logger.warning(f"❌ Failed to send alert to {user.phone}")
                try:
                    await session.rollback()
                except Exception:
                    logger.exception("❌ Failed to rollback session after error.")
            

def start_scheduler():
    logger.info("ℹ️  Starting scheduler.")
    
    scheduler.remove_all_jobs()
    
    interval = settings.POLL_INTERVAL_MINUTES
    # schedule first run immediately for testing
    first_run = datetime.now(timezone.utc) + timedelta(seconds=5)
    # set trigger
    trigger = IntervalTrigger(
        minutes=interval, 
        start_date=first_run, 
        timezone="UTC"
    )
    
    scheduler.add_job(
        poll_and_alert,
        trigger=trigger,
        id="poll_and_alert",
        replace_existing=True
    )
    scheduler.start()
    
    logger.info("✅ Scheduler start successful.")


def shutdown_scheduler():
    try:
        scheduler.shutdown(wait=False)
        logger.info("✅ Scheduler shutdown successful.")
    except Exception:
        logger.exception("❌ Error shutting down scheduler.")