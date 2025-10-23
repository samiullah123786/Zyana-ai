"""
Telegram Polling Mode - Run bot without webhooks (easier for local testing)
"""
import asyncio
import logging
from datetime import datetime
from config import settings
from services.parser import message_parser
from agents.router import main_agent
import httpx

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Telegram API base URL
TELEGRAM_API = f"https://api.telegram.org/bot{settings.telegram_bot_token}"

# Store last processed update ID
last_update_id = 0


async def send_message(chat_id: int, text: str):
    """Send a message to Telegram chat.
    
    Args:
        chat_id: Telegram chat ID
        text: Message text to send
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{TELEGRAM_API}/sendMessage",
                json={"chat_id": chat_id, "text": text, "parse_mode": "Markdown"},
                timeout=10.0
            )
            response.raise_for_status()
            logger.info(f"✅ Sent message to chat {chat_id}")
    except Exception as e:
        logger.error(f"❌ Error sending message: {e}")


async def handle_message(message: dict):
    """Process incoming Telegram message.
    
    Args:
        message: Telegram message object
    """
    try:
        chat_id = message["chat"]["id"]
        text = message.get("text", "")
        user_id = str(message["from"]["id"])
        
        logger.info(f"📨 Received message from {user_id}: {text}")
        
        # Handle commands
        if text.startswith("/"):
            response = await handle_command(text, user_id)
            await send_message(chat_id, response)
            return
        
        # Parse message using Zyana
        parsed = await message_parser.parse(text)
        logger.info(f"🧠 Parsed intent: {parsed.intent}, confidence: {parsed.confidence}")
        
        # Check for missing fields
        if parsed.missing_fields:
            response = f"I need more information: {', '.join(parsed.missing_fields)}\nCan you provide these details?"
            await send_message(chat_id, response)
            return
        
        # Route to agent
        agent_response = await main_agent.route(parsed, user_id=user_id)
        
        # Send response
        await send_message(chat_id, agent_response.message)
        
    except Exception as e:
        logger.error(f"❌ Error handling message: {e}", exc_info=True)
        try:
            await send_message(
                message["chat"]["id"],
                "Sorry, I encountered an error processing your message. Please try again."
            )
        except:
            pass


async def handle_command(command: str, user_id: str) -> str:
    """Handle Telegram bot commands.
    
    Args:
        command: Command string (e.g., "/start")
        user_id: User ID
        
    Returns:
        Response message
    """
    if command == "/start":
        return (
            "👋 *Welcome to Zyana!*\n\n"
            "I'm your personal AI assistant. I can help you:\n"
            "• Track finances across your businesses\n"
            "• Manage calendar events\n"
            "• Search your personal memory\n"
            "• And much more!\n\n"
            "Just send me a message like:\n"
            "_\"I lent Ahmad Rs 10,000 from Vidify\"_\n\n"
            "*Commands:*\n"
            "/status - Check balances\n"
            "/report - Generate report\n"
            "/help - Show help"
        )
    
    elif command == "/status":
        return "📊 *Status*\n\nVidify: Rs 125,000\nMilkBusiness: Rs 85,000\nYazman Express: Rs 50,000"
    
    elif command == "/report":
        return "📈 Generating your report... (Feature coming soon!)"
    
    elif command == "/help":
        return (
            "🤖 *Zyana Help*\n\n"
            "Send me natural messages like:\n"
            "• 'Received 50k from milk sales today'\n"
            "• 'Meeting with team tomorrow at 3pm'\n"
            "• 'How much did I lend Ahmad?'\n\n"
            "*Commands:*\n"
            "/start - Welcome message\n"
            "/status - Check balances\n"
            "/report - Generate report\n"
            "/help - Show help"
        )
    
    else:
        return "Unknown command. Type /help for available commands."


async def get_updates():
    """Get updates from Telegram using long polling.
    
    Returns:
        List of updates
    """
    global last_update_id
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{TELEGRAM_API}/getUpdates",
                params={
                    "offset": last_update_id + 1,
                    "timeout": 30,
                    "allowed_updates": ["message"]
                },
                timeout=35.0
            )
            response.raise_for_status()
            data = response.json()
            
            if data["ok"]:
                updates = data["result"]
                if updates:
                    last_update_id = updates[-1]["update_id"]
                return updates
            else:
                logger.error(f"Telegram API error: {data}")
                return []
                
    except httpx.TimeoutException:
        # Timeout is normal with long polling
        return []
    except Exception as e:
        logger.error(f"Error getting updates: {e}")
        return []


async def main():
    """Main polling loop."""
    logger.info("🤖 Starting Zyana Telegram Bot (Polling Mode)")
    logger.info(f"Bot token: {settings.telegram_bot_token[:20]}...")
    logger.info("📡 Listening for messages... (Press Ctrl+C to stop)")
    
    # Test connection
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{TELEGRAM_API}/getMe")
            response.raise_for_status()
            bot_info = response.json()
            if bot_info["ok"]:
                logger.info(f"✅ Connected to bot: @{bot_info['result']['username']}")
            else:
                logger.error(f"❌ Failed to connect to bot: {bot_info}")
                return
    except Exception as e:
        logger.error(f"❌ Cannot connect to Telegram API: {e}")
        logger.error("Check your TELEGRAM_BOT_TOKEN in .env file")
        return
    
    # Main polling loop
    while True:
        try:
            updates = await get_updates()
            
            for update in updates:
                if "message" in update:
                    await handle_message(update["message"])
            
            # Small delay between polls
            if not updates:
                await asyncio.sleep(1)
                
        except KeyboardInterrupt:
            logger.info("\n👋 Stopping bot...")
            break
        except Exception as e:
            logger.error(f"❌ Error in main loop: {e}", exc_info=True)
            await asyncio.sleep(5)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")

