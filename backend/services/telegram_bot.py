"""Telegram bot service for sending messages."""
import logging
import httpx
import re
from config import settings

logger = logging.getLogger(__name__)


def sanitize_telegram_message(text: str) -> str:
    """Sanitize message text for Telegram to prevent 400 errors.
    
    Args:
        text: Raw message text
        
    Returns:
        Sanitized text safe for Telegram
    """
    if not text:
        return ""
    
    # Remove problematic dict/object representations
    if text.startswith("{") and "'" in text:
        logger.warning("Detected dict-like string, using fallback")
        return "I processed your request! Let me know if you need anything else."
    
    # Telegram has 4096 character limit
    MAX_LENGTH = 4000  # Leave buffer for safety
    if len(text) > MAX_LENGTH:
        logger.warning(f"Message too long ({len(text)} chars), truncating")
        text = text[:MAX_LENGTH] + "\n\n(message truncated...)"
    
    # Remove NULL bytes and other control characters that break Telegram
    text = re.sub(r'[\x00-\x08\x0b-\x0c\x0e-\x1f\x7f]', '', text)
    
    # Remove any problematic special characters that cause 400 errors
    # Keep it simple - just clean obvious issues
    text = text.replace('\x00', '')  # NULL bytes
    
    return text.strip()


async def send_telegram_message(chat_id: str, text: str, parse_mode: str = "Markdown"):
    """Send a message via Telegram Bot API.
    
    Args:
        chat_id: Telegram chat ID
        text: Message text
        parse_mode: Parse mode (Markdown or HTML, or None for plain text)
    """
    # Validate and clean the message
    if not text or text.strip() == "":
        logger.warning("Attempted to send empty message, skipping")
        return
    
    # Sanitize the message
    text = sanitize_telegram_message(text)
    
    url = f"https://api.telegram.org/bot{settings.telegram_bot_token}/sendMessage"
    
    payload = {
        "chat_id": chat_id,
        "text": text
    }
    
    # Detect if message has Markdown formatting
    has_markdown = any(char in text for char in ['*', '_', '`', '['])
    
    # Only add parse_mode if message has formatting and mode is valid
    if parse_mode and parse_mode in ["Markdown", "HTML"] and has_markdown:
        payload["parse_mode"] = parse_mode
    else:
        # Skip parse_mode for plain text to avoid 400 errors
        logger.debug("Sending as plain text (no Markdown detected or disabled)")
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, timeout=10.0)
            response.raise_for_status()
            logger.debug(f"✅ Sent Telegram message to {chat_id} ({len(text)} chars)")
            
    except httpx.HTTPStatusError as e:
        # If 400 error and we used parse_mode, retry as plain text
        if e.response.status_code == 400:
            logger.warning(f"Telegram 400 error, retrying as plain text. Error: {e.response.text}")
            payload.pop("parse_mode", None)
            
            # Also strip ALL markdown characters for clean plain text
            clean_text = re.sub(r'[*_`\[\]]', '', text)
            payload["text"] = clean_text
            
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.post(url, json=payload, timeout=10.0)
                    response.raise_for_status()
                    logger.info(f"✅ Sent Telegram message (plain text fallback, cleaned)")
                    return
            except Exception as retry_error:
                logger.error(f"Failed even with plain text: {retry_error}", exc_info=True)
        else:
            logger.error(f"Error sending Telegram message (status {e.response.status_code}): {e}")
            logger.error(f"Response: {e.response.text}")
        
    except httpx.HTTPError as e:
        logger.error(f"Error sending Telegram message: {e}", exc_info=True)


async def set_telegram_webhook(webhook_url: str):
    """Set Telegram webhook URL.
    
    Args:
        webhook_url: Full webhook URL (e.g., https://api.example.com/webhook/telegram)
    """
    url = f"https://api.telegram.org/bot{settings.telegram_bot_token}/setWebhook"
    
    payload = {
        "url": webhook_url
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, timeout=10.0)
            response.raise_for_status()
            logger.info(f"Set Telegram webhook: {webhook_url}")
            return response.json()
            
    except httpx.HTTPError as e:
        logger.error(f"Error setting webhook: {e}")
        raise


async def get_telegram_webhook_info():
    """Get current Telegram webhook information.
    
    Returns:
        Webhook info dict
    """
    url = f"https://api.telegram.org/bot{settings.telegram_bot_token}/getWebhookInfo"
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, timeout=10.0)
            response.raise_for_status()
            return response.json()
            
    except httpx.HTTPError as e:
        logger.error(f"Error getting webhook info: {e}")
        return {}

