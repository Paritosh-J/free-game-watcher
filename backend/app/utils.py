import logging
logger = logging.getLogger("utils")

def normalize_phone(phone: str) -> str:
    """
    Minimal normalization for E.164 formatting requirement:
    - User must input a phone number including country code ideally.
    For now we'll strip spaces and dashes.
    You can improve using phonenumbers library later.
    """
    p = phone.strip().replace(" ", "").replace("-", "")
    return p
