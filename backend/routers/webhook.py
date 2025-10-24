"""Webhook router for receiving messages from Telegram and other platforms."""
from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
import logging

from models.schemas import WebhookMessage, AgentResponse
from services.parser import message_parser
from agents.router import main_agent
from services.telegram_bot import send_telegram_message

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/message")
async def receive_message(
    webhook_msg: WebhookMessage,
    background_tasks: BackgroundTasks
) -> JSONResponse:
    """Receive and process webhook messages from Telegram or other platforms.
    
    This endpoint:
    1. Receives the message
    2. Parses it using the message parser
    3. Routes to the appropriate agent
    4. Sends confirmation back to the user
    
    Args:
        webhook_msg: Incoming webhook message
        background_tasks: FastAPI background tasks
        
    Returns:
        JSONResponse with status
    """
    logger.info(f"Received message from {webhook_msg.platform}: {webhook_msg.message}")
    
    try:
        # Parse the message
        parsed = await message_parser.parse(
            webhook_msg.message,
            context={"user_id": webhook_msg.user_id}
        )
        
        logger.info(f"Parsed message: intent={parsed.intent}, confidence={parsed.confidence}")
        
        # Check if we need more information
        if parsed.missing_fields:
            # Send follow-up question
            response_message = await _generate_followup_question(parsed)
            
            # Send back to user
            if webhook_msg.platform == "telegram":
                background_tasks.add_task(
                    send_telegram_message,
                    webhook_msg.user_id,
                    response_message
                )
            
            return JSONResponse(content={
                "status": "awaiting_input",
                "message": response_message,
                "missing_fields": parsed.missing_fields
            })
        
        # Route to appropriate agent
        agent_response = await main_agent.route(parsed, user_id=webhook_msg.user_id)
        
        # Send confirmation back to user
        if webhook_msg.platform == "telegram":
            background_tasks.add_task(
                send_telegram_message,
                webhook_msg.user_id,
                agent_response.message
            )
        
        return JSONResponse(content={
            "status": "success",
            "message": agent_response.message,
            "data": agent_response.data
        })
        
    except Exception as e:
        logger.error(f"Error processing webhook message: {e}", exc_info=True)
        
        error_message = "Sorry, I encountered an error processing your message. Please try again."
        
        if webhook_msg.platform == "telegram":
            background_tasks.add_task(
                send_telegram_message,
                webhook_msg.user_id,
                error_message
            )
        
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": error_message,
                "error": str(e)
            }
        )


async def _generate_followup_question(parsed) -> str:
    """Generate a follow-up question for missing fields.
    
    Args:
        parsed: ParsedMessage with missing_fields
        
    Returns:
        Follow-up question string
    """
    missing = parsed.missing_fields
    
    if "business" in missing:
        return "Which business is this for? (Vidify, MilkBusiness, or Yazman Express)"
    
    if "amount" in missing:
        return "How much was the amount?"
    
    if "person" in missing:
        return "Who is this transaction with?"
    
    if "date" in missing:
        return "When did this happen?"
    
    if "category" in missing:
        return "What category should I use for this?"
    
    # Generic response
    return f"I need more information: {', '.join(missing)}. Can you provide these details?"


@router.post("/telegram")
async def telegram_webhook(data: dict, background_tasks: BackgroundTasks):
    """Receive updates from Telegram Bot API.
    
    This endpoint receives Telegram updates in the format:
    {
        "update_id": 123,
        "message": {
            "message_id": 456,
            "from": {"id": 789, "first_name": "User"},
            "chat": {"id": 789, "type": "private"},
            "text": "I lent Ahmad 10000"
        }
    }
    
    Args:
        data: Telegram update data
        background_tasks: FastAPI background tasks
        
    Returns:
        Success response
    """
    logger.debug(f"Telegram webhook data: {data}")
    
    try:
        # Extract message from Telegram update
        if "message" not in data:
            return {"ok": True}
        
        message = data["message"]
        
        # Handle text messages
        if "text" in message:
            user_id = str(message["from"]["id"])
            text = message["text"]
            
            # Handle commands
            if text.startswith("/"):
                response = await _handle_telegram_command(text, user_id)
                background_tasks.add_task(
                    send_telegram_message,
                    user_id,
                    response
                )
                return {"ok": True}
            
            # Process as regular message
            webhook_msg = WebhookMessage(
                user_id=user_id,
                message=text,
                platform="telegram",
                metadata={"chat_id": message["chat"]["id"]}
            )
            
            await receive_message(webhook_msg, background_tasks)
        
        return {"ok": True}
        
    except Exception as e:
        logger.error(f"Telegram webhook error: {e}", exc_info=True)
        return {"ok": False, "error": str(e)}


async def _handle_telegram_command(command: str, user_id: str) -> str:
    """Handle Telegram bot commands.
    
    Args:
        command: Command string (e.g., "/start")
        user_id: Telegram user ID
        
    Returns:
        Response message
    """
    if command == "/start":
        return (
            "👋 Welcome to Zyana - Your JARVIS!\n\n"
            "I'm not just an assistant - I'm your intelligent companion. I learn from every interaction and help you:\n\n"
            "🧠 Smart Finance Tracking\n"
            "• Automatically remember your businesses\n"
            "• Learn your spending patterns\n"
            "• Provide proactive insights\n\n"
            "📊 Intelligent Analysis\n"
            "• Generate smart financial insights\n"
            "• Predict patterns\n"
            "• Give personalized recommendations\n\n"
            "🎯 Context-Aware Memory\n"
            "• Remember important conversations\n"
            "• Recall past transactions\n"
            "• Understand your preferences\n\n"
            "Just talk to me naturally:\n"
            '"I lent Ahmad Rs 10,000 from Vidify"\n'
            '"Show me my insights"\n'
            '"What are my pending loans?"\n\n'
            "Commands:\n"
            "/insights - AI-powered insights\n"
            "/status - Check balances\n"
            "/help - Full command list"
        )
    
    elif command == "/status":
        from agents.router import main_agent
        result = await main_agent._get_status(user_id)
        return result.get("message", "Unable to fetch status")
    
    elif command == "/insights":
        from agents.router import main_agent
        result = await main_agent._generate_insights(user_id)
        return result.get("message", "No insights available yet. Start tracking to get intelligent analysis!")
    
    elif command == "/report":
        from agents.router import main_agent
        result = await main_agent._generate_insights(user_id)
        return result.get("message", "No data available yet!")
    
    elif command == "/help":
        return (
            "🤖 Zyana - Your JARVIS Assistant\n\n"
            "💬 Talk naturally:\n"
            "• 'Received 50k from milk sales today'\n"
            "• 'I gave Indian $130 for anime videos'\n"
            "• 'Ahmad owes me 10,000'\n"
            "• 'Show me my insights'\n"
            "• 'What did I spend on marketing?'\n\n"
            "🎯 Smart Commands:\n"
            "/start - Introduction\n"
            "/insights - AI-powered analysis 🧠\n"
            "/status - Quick balance check\n"
            "/report - Detailed financial report\n"
            "/help - This help message\n\n"
            "✨ I learn from every message and get smarter at helping you!"
        )
    
    elif command == "/add_business":
        return "To add a new business, just tell me: 'Start new business called [Name]'"
    
    elif command == "/sync_calendar":
        return "🗓️ Calendar sync coming soon! I'll let you know when it's ready."
    
    else:
        return "❓ Unknown command. Type /help to see what I can do!"

