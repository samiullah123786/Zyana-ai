"""Telegram bot service for sending messages."""
import logging
import httpx
from config import settings

logger = logging.getLogger(__name__)


async def send_telegram_message(chat_id: str, text: str, parse_mode: str = "Markdown"):
    """Send a message via Telegram Bot API.
    
    Args:
        chat_id: Telegram chat ID
        text: Message text
        parse_mode: Parse mode (Markdown or HTML)
    """
    url = f"https://api.telegram.org/bot{settings.telegram_bot_token}/sendMessage"
    
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": parse_mode
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, timeout=10.0)
            response.raise_for_status()
            logger.debug(f"Sent Telegram message to {chat_id}")
            
    except httpx.HTTPError as e:
        logger.error(f"Error sending Telegram message: {e}")


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

