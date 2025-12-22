from app.config import settings
import logging

logger = logging.getLogger("messaging")

TWILIO_ENABLED = bool(settings.TWILIO_ACCOUNT_STD and settings.TWILIO_AUTH_TOKEN)

if TWILIO_ENABLED:
    from twilio.rest import Client
    twilio_client = Client(settings.TWILIO_ACCOUNT_STD, settings.TWILIO_AUTH_TOKEN)
else:
    twilio_client = None
    
    
async def send_sms_otp(phone: str, code: str) -> bool:
    """
    Sends OTP via SMS. 
    If Twilio is configured, uese Twilio SMS. 
    Otherwise logs to console.
    """
    body = f"Your Free-Game-Watcher OTP is: {code} (valid for 5 mins)"
    
    if TWILIO_ENABLED and settings.TWILIO_SMS_FROM:
        try:
            message = twilio_client.messages.create(
                body=body,
                from_=settings.TWILIO_SMS_FROM,
                to=phone
            )
            
            logger.info(f"ℹ️  Twilio SMS sent SID={message.sid} to {phone}")
        
            return True
        
        except Exception as e:
            logger.exception("❌ Failed to send SMS via Twilio: {e}")
            return False
        
    else:
        # local dev fallback (prints to console)
        logger.info(f"ℹ️  [DEV MODE] OTP for {phone}: {code}")
        print(f"ℹ️  [DEV MODE] OTP for {phone}: {code}")
        return True
    
    
async def send_whatsapp_message(phone: str, message_text: str) -> bool:
    """
    Send message_text via WhatsApp. 
    Requires Twilio creds and a WhatsApp-enabled Twilio sender.
    Twilio wants both from and to prefixed with 'whatsapp:'.
    Fallback to logging if no Twiwlio configured.
    """
    if TWILIO_ENABLED and settings.TWILIO_WHATSAPP_FROM:
        # ensure 'whatsapp:' prefix fro twilio
        if not phone.startswith("whatsapp:"):
            phone = f"whatsapp:{phone}"
            
        try:
            message = twilio_client.messages.create(
                from_=settings.TWILIO_WHATSAPP_FROM,
                to=phone,
                body=message_text
            )
            logger.info(f"ℹ️  WhatsApp message sent SID={message.sid}")
            return True
        
        except Exception as e:
            logger.exception("❌ Failed to send WhatsApp message via Twilio: {e}")
            return False
        
    else:
        # fallback: print to console
        logger.info(f"ℹ️  [DEV MODE] WhatsApp message to {phone}: {message_text}")
        return True