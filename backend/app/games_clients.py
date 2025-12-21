import httpx
from app.config import settings
from typing import List, Dict, Optional
from datetime import datetime
import logging

logger = logging.getLogger("games_client")


async def fetch_gamerpower(platform: Optional[str] = None) -> List[Dict]:
    """
    Fetch giveaways from GamerPower.
    Eg. https://www.gamerpower.com/api/giveaways?platform=steam
    Returns a list of giveaways as dicts.
    """
    params = {}
    if platform:
        params["platform"] = platform
    
    url = settings.GAMERPOWER_API
    
    async with httpx.AsyncClient(timeout=20.0) as client:
        try:
            r = await client.get(url, params=params)
            r.raise_for_status()
            data = r.json()
            logger.info("ℹ️  Data fetched from GamePowet API")
            # data is a list of giveaways
            return data
        
        except Exception as e:
            logger.exception("❌ Failed to fetch GamerPower API")
            return []
        
        
async def fetch_epic_freegames() -> List[Dict]:
    """
    Fetch Epic free games from Epic's public promotions endpoint.
    The official endpoint returns a complex structure; we parse and return a list of entries with id/title/url/end_point
    """
    url = settings.EPIC_API
    params = {"locale":"en-IN", "country":"IN", "allowCountries":"IN"}
    
    async with httpx.AsyncClient(timeout=20.0) as client:
        try:
            r = await client.get(url, params=params)
            r.raise_for_status()
            data = r.json()
            out = []
            
            # traverse data structure to extract freebies (safe parsing)
            elements = data.get("data", {}).get("searchStore", {}).get("elements", [])
            
            for el in elements:
                # check promotions
                promotions = el.get("promotions") or {}
                
                # find current promotional offers
                current = promotions.get("promotionalOffers", []) or []
                
                if current:
                    # check if price is 0 or there's a free promotion
                    for block in current:
                        offers = block.get("promotionalOffers", [])
                        for o in offers:
                            start = o.get("startDate")
                            end = o.get("endDate")
                            out.append({
                                "id": el.get("id") or el.get("productSlug") or el.get("title"),
                                "title": el.get("title"),
                                "url": f"https://www.epicgames.com/store/en-US/p/{el.get('productSlug')}" if el.get("productSlug") else None,
                                "start_date": start,
                                "end_date": end
                            })
            
            logger.info("ℹ️  Data fetched from Epic Games API")
            return out
        
        except Exception as e:
            logger.exception("❌ Failed to fetch Epic API")
            return []
            

def normalize_gamerpower_item(item: Dict) -> Dict:
    """
    Normalize a GamerPower giveaway item to our internal representation:
    { id, title, url, platform, ends_at }
    """
    # GamerPower fields: id, title, worth, platform, end_date, giveaway_url
    game_id = str(item.get("id") or item.get("title"))
    title = item.get("title") or "Unknown"
    url = item.get("giveaway_url") or item.get("open_giveaway_url") or item.get("worth")
    platform = item.get("platform")
    ends_at = item.get("end_date")
    
    return {"id": game_id, "title": title, "url": url, "platform": platform, "ends_at": ends_at}