"""Webhook router for receiving messages from Telegram and other platforms."""
from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
import logging
from datetime import datetime

from models.schemas import WebhookMessage, AgentResponse
from services.parser import message_parser
from agents.router import main_agent
from services.telegram_bot import send_telegram_message

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/telegram/status")
async def telegram_status():
    """Check Telegram webhook status and bot configuration.
    
    Use this endpoint to debug if your bot isn't receiving messages.
    Returns: Webhook info from Telegram API
    """
    try:
        from config import settings
        import httpx
        
        url = f"https://api.telegram.org/bot{settings.telegram_bot_token}/getWebhookInfo"
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            data = response.json()
            
        return {
            "status": "ok",
            "message": "Webhook status fetched successfully",
            "webhook_info": data.get("result", {}),
            "backend_webhook_url": f"{settings.webhook_url}/webhook/telegram" if settings.webhook_url else "NOT CONFIGURED"
        }
    except Exception as e:
        logger.error(f"Error fetching webhook status: {e}")
        return {
            "status": "error",
            "message": str(e)
        }


@router.post("/telegram/set")
async def set_webhook_manual():
    """Manually set Telegram webhook.
    
    Use this if the bot isn't receiving messages.
    This will configure Telegram to send updates to your backend.
    """
    try:
        from services.telegram_bot import set_telegram_webhook
        from config import settings
        
        if not settings.webhook_url:
            return {
                "status": "error",
                "message": "WEBHOOK_URL not configured in environment variables"
            }
        
        webhook_url = f"{settings.webhook_url}/webhook/telegram"
        result = await set_telegram_webhook(webhook_url)
        
        logger.info(f"✅ Webhook manually set to: {webhook_url}")
        
        return {
            "status": "success",
            "message": "Webhook set successfully",
            "webhook_url": webhook_url,
            "telegram_response": result
        }
    except Exception as e:
        logger.error(f"Error setting webhook: {e}")
        return {
            "status": "error",
            "message": str(e)
        }


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
        
        logger.info(f"Parsed message: intent={parsed.intent}, confidence={parsed.confidence}, memory={parsed.is_memory_request}")
        
        # Handle "remember" requests - save to long-term memory
        if parsed.is_memory_request:
            from memory.embed import memory_service
            try:
                # Remove "remember" from text for clean storage
                clean_text = parsed.raw_text.lower().replace("remember", "").replace("that", "").strip()
                clean_text = clean_text if clean_text else parsed.raw_text
                
                # Save to memory
                await memory_service.add_memory(
                    content=clean_text,
                    metadata={
                        "type": "user_note",
                        "user_id": webhook_msg.user_id,
                        "intent": parsed.intent,
                        "timestamp": datetime.now().isoformat()
                    }
                )
                logger.info(f"💾 Saved to long-term memory: {clean_text[:50]}...")
                
                # Send confirmation
                memory_response = f"✅ Got it! I'll remember: \"{clean_text}\"\n\nI've saved this to my long-term memory."
                if webhook_msg.platform == "telegram":
                    background_tasks.add_task(
                        send_telegram_message,
                        webhook_msg.user_id,
                        memory_response
                    )
                
                return JSONResponse(content={
                    "status": "success",
                    "message": memory_response,
                    "memory_saved": True
                })
            except Exception as e:
                logger.error(f"Error saving memory: {e}")
                # Continue processing normally if memory save fails
        
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
        
        # Log activity for routine learning
        from agents.routine_optimizer import routine_optimizer
        user_id_int = 1  # TODO: Map telegram_id to internal user_id
        await routine_optimizer.observe_activity(user_id_int, datetime.now())
        
        # Store message sample for mirror mode learning
        from services.mirror_mode import mirror_mode_service
        if await mirror_mode_service.is_mirror_mode_enabled(user_id_int):
            await mirror_mode_service.add_message_sample(
                user_id_int,
                parsed.raw_text,
                parsed.intent
            )
        
        # Route to appropriate agent
        agent_response = await main_agent.route(parsed, user_id=webhook_msg.user_id)
        
        # Apply mirror mode style transformation
        response_message = agent_response.message
        if await mirror_mode_service.is_mirror_mode_enabled(user_id_int):
            response_message = await mirror_mode_service.apply_style_transformation(
                response_message,
                user_id_int
            )
        
        # Check for break suggestion
        break_suggestion = await routine_optimizer.suggest_break(user_id_int)
        if break_suggestion:
            response_message = break_suggestion + "\n\n" + response_message
        
        # Send confirmation back to user
        if webhook_msg.platform == "telegram":
            background_tasks.add_task(
                send_telegram_message,
                webhook_msg.user_id,
                response_message
            )
        
        return JSONResponse(content={
            "status": "success",
            "message": response_message,
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
    # CRITICAL: Use INFO not DEBUG for production visibility
    logger.info(f"📨 Telegram webhook received: update_id={data.get('update_id')}")
    
    try:
        # Extract message from Telegram update
        if "message" not in data:
            logger.info("⏭️  No message in update, skipping")
            return {"ok": True}
        
        message = data["message"]
        user_id = str(message["from"]["id"])
        
        # Handle voice messages
        if "voice" in message:
            logger.info(f"Received voice message from telegram user: {user_id}")
            background_tasks.add_task(
                _handle_voice_message,
                message["voice"],
                user_id,
                background_tasks
            )
            
            # Send immediate feedback
            background_tasks.add_task(
                send_telegram_message,
                user_id,
                "🎙️ Transcribing your voice message..."
            )
            return {"ok": True}
        
        # Handle text messages
        if "text" in message:
            text = message["text"]
            logger.info(f"Received message from telegram: {text}")
            
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


async def _handle_voice_message(voice_data: dict, user_id: str, background_tasks: BackgroundTasks):
    """Handle voice message transcription.
    
    Args:
        voice_data: Telegram voice message data
        user_id: Telegram user ID
        background_tasks: Background tasks manager
    """
    try:
        from services.voice_transcriber import voice_transcriber
        from config import settings
        import httpx
        
        # Get file from Telegram
        file_id = voice_data["file_id"]
        
        # Get file path from Telegram API
        async with httpx.AsyncClient() as client:
            file_response = await client.get(
                f"https://api.telegram.org/bot{settings.telegram_bot_token}/getFile?file_id={file_id}",
                timeout=30.0
            )
            file_data = file_response.json()
            
            if not file_data.get("ok"):
                raise Exception("Failed to get file from Telegram")
            
            file_path = file_data["result"]["file_path"]
            
            # Download file
            file_url = f"https://api.telegram.org/file/bot{settings.telegram_bot_token}/{file_path}"
            download_response = await client.get(file_url, timeout=30.0)
            audio_bytes = download_response.content
        
        # Transcribe
        transcript = await voice_transcriber.transcribe_telegram_voice(audio_bytes)
        
        if not transcript:
            await send_telegram_message(
                user_id,
                "❌ Sorry, I couldn't transcribe that voice message. Please try again or type your message."
            )
            return
        
        logger.info(f"Transcribed voice message: {transcript}")
        
        # Process transcript as regular message
        webhook_msg = WebhookMessage(
            user_id=user_id,
            message=transcript,
            platform="telegram",
            metadata={"from_voice": True}
        )
        
        await receive_message(webhook_msg, background_tasks)
        
    except Exception as e:
        logger.error(f"Error handling voice message: {e}", exc_info=True)
        await send_telegram_message(
            user_id,
            "❌ Sorry, there was an error processing your voice message. Please try again."
        )


async def _handle_telegram_command(command: str, user_id: str) -> str:
    """Handle Telegram bot commands.
    
    Args:
        command: Command string (e.g., "/start")
        user_id: Telegram user ID
        
    Returns:
        Response message
    """
    # Split command and args
    parts = command.split(maxsplit=1)
    cmd = parts[0].lower()
    args = parts[1] if len(parts) > 1 else ""
    
    if cmd == "/start":
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
    
    elif cmd == "/sync_calendar":
        return "🗓️ Calendar sync coming soon! I'll let you know when it's ready."
    
    elif cmd == "/list_invoices":
        from agents.invoice_tracker import invoice_tracker
        user_id_int = 1  # TODO: Map telegram_id to user_id
        invoices = await invoice_tracker.list_invoices(user_id=user_id_int)
        
        if not invoices:
            return "📋 No invoices found."
        
        message = "📋 Your Invoices:\n\n"
        for inv in invoices[:10]:  # Show first 10
            status_emoji = "✅" if inv["status"] == "paid" else "⚠️" if inv["status"] == "overdue" else "⏳"
            client_name = inv.get("clients", {}).get("name", "Unknown")
            message += f"{status_emoji} #{inv['invoice_number']} - {client_name} - {inv['currency']} {inv['amount']:,.0f}\n"
        
        return message
    
    elif cmd == "/add_client":
        return "To add a client, please use the dashboard or tell me:\n'Add client [Name] for [Business]'"
    
    elif cmd == "/list_clients":
        from agents.client_manager import client_manager
        clients = await client_manager.list_clients()
        
        if not clients:
            return "👥 No clients found."
        
        message = "👥 Your Clients:\n\n"
        for client in clients[:20]:
            business_name = client.get("businesses", {}).get("name", "")
            message += f"• {client['name']}"
            if client.get("contact"):
                message += f" - {client['contact']}"
            if business_name:
                message += f" ({business_name})"
            message += "\n"
        
        return message
    
    elif cmd == "/client_status":
        from agents.client_manager import client_manager
        
        if not args:
            return "Please specify client name: /client_status [Client Name]"
        
        # Find client by name
        client = await client_manager.get_client_by_name(args)
        
        if not client:
            return f"Client '{args}' not found."
        
        # Get status
        result = await client_manager.get_client_status(client["id"])
        return result.get("message", "Unable to get client status")
    
    elif cmd == "/list_reminders":
        from agents.notification_scheduler import notification_scheduler
        user_id_int = 1  # TODO: Map telegram_id to user_id
        notifications = await notification_scheduler.list_scheduled(user_id_int)
        
        if not notifications:
            return "⏰ No pending reminders."
        
        message = "⏰ Your Scheduled Reminders:\n\n"
        for notif in notifications[:10]:
            scheduled_time = datetime.fromisoformat(notif["scheduled_time"])
            message += f"#{notif['id']} - \"{notif['message']}\"\n"
            message += f"   📅 {scheduled_time.strftime('%b %d, %I:%M %p')}\n\n"
        
        return message
    
    elif cmd == "/cancel_reminder":
        from agents.notification_scheduler import notification_scheduler
        
        if not args:
            return "Please specify reminder ID: /cancel_reminder [ID]"
        
        try:
            notification_id = int(args)
            result = await notification_scheduler.cancel_notification(notification_id)
            return result.get("message", "Failed to cancel reminder")
        except ValueError:
            return "Invalid reminder ID. Please provide a number."
    
    elif cmd == "/mirror_mode_on":
        from services.mirror_mode import mirror_mode_service
        user_id_int = 1  # TODO: Map telegram_id to user_id
        result = await mirror_mode_service.enable_mirror_mode(user_id_int)
        return result.get("message")
    
    elif cmd == "/mirror_mode_off":
        from services.mirror_mode import mirror_mode_service
        user_id_int = 1  # TODO: Map telegram_id to user_id
        result = await mirror_mode_service.disable_mirror_mode(user_id_int)
        return result.get("message")
    
    elif cmd == "/my_style":
        from services.mirror_mode import mirror_mode_service
        user_id_int = 1  # TODO: Map telegram_id to user_id
        result = await mirror_mode_service.get_style_summary(user_id_int)
        return result.get("message")
    
    else:
        return "❓ Unknown command. Type /help to see what I can do!"

