"""Webhook router for receiving messages from Telegram and other platforms."""
from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
import logging
from datetime import datetime

from models.schemas import WebhookMessage, AgentResponse
from services.parser import message_parser
from agents.router import main_agent  # OLD router (legacy)
from agents.intent_router import intent_router  # NEW RAG-enabled router
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
    logger.info("=" * 80)
    logger.info(f"🔹 WEBHOOK START: user={webhook_msg.user_id}, platform={webhook_msg.platform}")
    logger.info(f"🔹 MESSAGE: {webhook_msg.message}")
    logger.info("=" * 80)
    
    try:
        # Quick pre-check for "remember" keyword (lightweight regex)
        is_memory_request = "remember" in webhook_msg.message.lower() and any(
            phrase in webhook_msg.message.lower() 
            for phrase in ["remember that", "remember this", "remember:", "don't forget"]
        )
        
        # Handle "remember" requests - save to long-term memory
        if is_memory_request:
            from memory.embed import memory_service
            try:
                # Remove "remember" from text for clean storage
                clean_text = webhook_msg.message.lower().replace("remember", "").replace("that", "").replace("this", "").strip()
                clean_text = clean_text if clean_text else webhook_msg.message
                
                # Save to memory
                await memory_service.add_memory(
                    content=clean_text,
                    metadata={
                        "type": "user_note",
                        "user_id": webhook_msg.user_id,
                        "intent": "memory",
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
        
        # Log activity for routine learning
        from agents.routine_optimizer import routine_optimizer
        from services.user_mapper import user_mapper
        user_id_int = await user_mapper.get_internal_user_id(webhook_msg.user_id)
        await routine_optimizer.observe_activity(user_id_int, datetime.now())
        
        # Store message sample for mirror mode learning (will be populated after intent routing)
        from services.mirror_mode import mirror_mode_service
        
        # Route to appropriate agent using NEW RAG-enabled intent router
        # The new intent_router automatically includes:
        # - RAG memory retrieval from Qdrant
        # - Mirror Mode style transformation
        # - User preferences and context
        # - Intelligent conversation handling
        logger.info("🤖 Routing through NEW intent_router (RAG + Mirror Mode enabled)")
        
        intent_result = await intent_router.route_intent(
            message=webhook_msg.message,
            user_id=webhook_msg.user_id
        )
        
        logger.info(f"✅ Intent router result: intent={intent_result.get('intent')}, confidence={intent_result.get('confidence', 0)}")
        
        # Store message for mirror mode learning
        if await mirror_mode_service.is_mirror_mode_enabled(user_id_int):
            await mirror_mode_service.add_message_sample(
                user_id_int,
                webhook_msg.message,
                intent_result.get('intent', 'unknown')
            )
            logger.info(f"📸 Stored message sample for Mirror Mode learning")
        
        # Extract response (already includes Mirror Mode transformation)
        response_message = intent_result.get('response', 'I received your message!')
        
        # If clarification is needed, the response will contain the clarification question
        if intent_result.get('needs_clarification'):
            logger.info(f"📝 Clarification needed: {intent_result.get('clarification_question')}")
        
        # Execute actions for specific intents (but always use intent_router's response)
        if intent_result['intent'] in ['schedule_meeting', 'reschedule_meeting', 'set_reminder']:
            # Calendar agent - execute the actual event creation
            if not intent_result.get('needs_clarification'):
                from agents.calendar import calendar_agent
                try:
                    event_result = await calendar_agent.create_event_from_intent(
                        intent_result,
                        webhook_msg.user_id
                    )
                    if event_result.get('success'):
                        # Use calendar's success message if available, otherwise keep intent_router's response
                        response_message = event_result.get('message', response_message)
                except Exception as e:
                    logger.error(f"Calendar execution error: {e}", exc_info=True)
                    # Keep intent_router's response even if execution fails
        
        elif intent_result['intent'] == 'check_weather':
            # Weather agent - fetch real-time weather data
            from agents.weather import weather_agent
            try:
                weather_result = await weather_agent.get_weather(
                    webhook_msg.message,
                    webhook_msg.user_id
                )
                if weather_result.get('success'):
                    # Use weather agent's formatted response
                    response_message = weather_result.get('message', response_message)
                    logger.info(f"🌤 Weather fetched for {weather_result.get('city')}: {weather_result.get('data', {}).get('temperature')}°C")
                else:
                    # Use weather agent's error message (e.g., "city not found")
                    response_message = weather_result.get('message', response_message)
            except Exception as e:
                logger.error(f"Weather execution error: {e}", exc_info=True)
                # Fallback to a generic error message
                response_message = "Couldn't fetch the weather right now. Please try again later! 🌦"
        
        # For ALL other intents (finance, chat, etc.), TRUST the intent_router's response
        # No need to fall back to old parser - intent_router handles everything
        
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
        
        # Build response data (agent_response might not exist for calendar/chat intents)
        response_data = {}
        if 'agent_response' in locals() and hasattr(agent_response, 'data'):
            response_data = agent_response.data
        
        return JSONResponse(content={
            "status": "success",
            "message": response_message,
            "data": response_data
        })
        
    except Exception as e:
        logger.error("=" * 80)
        logger.error(f"❌ CRITICAL ERROR in webhook processing!")
        logger.error(f"❌ Error type: {type(e).__name__}")
        logger.error(f"❌ Error message: {str(e)}")
        logger.error(f"❌ User: {webhook_msg.user_id}, Message: {webhook_msg.message[:100] if len(webhook_msg.message) > 100 else webhook_msg.message}")
        logger.error("=" * 80)
        logger.error(f"Full stack trace:", exc_info=True)
        
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
    """Handle voice message transcription using Groq Whisper API.
    
    Args:
        voice_data: Telegram voice message data
        user_id: Telegram user ID
        background_tasks: Background tasks manager
    """
    import tempfile
    import os
    import uuid
    from datetime import datetime
    from services.groq_transcriber import groq_transcriber
    from clients.supabase_client import supabase_client
    from config import settings
    import httpx
    
    temp_file = None
    
    try:
        # Get file from Telegram
        file_id = voice_data["file_id"]
        file_size = voice_data.get("file_size", 0)
        duration = voice_data.get("duration", 0)
        
        logger.info(f"🎙️ Processing voice message: {file_id} ({file_size} bytes, {duration}s)")
        
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
        
        # Save to temporary file (Groq API needs file path)
        with tempfile.NamedTemporaryFile(delete=False, suffix=".ogg") as temp:
            temp.write(audio_bytes)
            temp_file = temp.name
        
        logger.info(f"📥 Downloaded voice file: {temp_file}")
        
        # Transcribe with Groq
        transcription = await groq_transcriber.transcribe_telegram_voice(temp_file)
        
        if not transcription or not transcription.get("text"):
            await send_telegram_message(
                user_id,
                "❌ Sorry, I couldn't transcribe that voice message. Please try speaking more clearly or type your message."
            )
            return
        
        transcript_text = transcription["text"]
        detected_language = transcription.get("language", "unknown")
        
        logger.info(f"✅ Transcribed ({detected_language}): {transcript_text[:100]}...")
        
        # Get or create user in database
        try:
            user_result = supabase_client.admin.table("users").select("id").eq(
                "telegram_id", user_id
            ).limit(1).execute()
            
            if user_result.data:
                internal_user_id = user_result.data[0]["id"]
            else:
                # Create new user
                new_user = supabase_client.admin.table("users").insert({
                    "telegram_id": user_id,
                    "name": f"User {user_id[:8]}"
                }).execute()
                internal_user_id = new_user.data[0]["id"] if new_user.data else 1
        except Exception as e:
            logger.error(f"Error getting user: {e}")
            internal_user_id = 1  # Fallback
        
        # Save to voice_logs table
        try:
            voice_log = {
                "user_id": internal_user_id,
                "source": "telegram_voice",
                "file_url": None,  # TODO: Upload to Supabase Storage
                "file_size_bytes": file_size,
                "duration_seconds": duration,
                "transcription": transcript_text,
                "language": detected_language,
                "confidence": transcription.get("confidence"),
                "model_used": transcription.get("model_used", "whisper-large-v3-turbo"),
                "meta": {
                    "file_id": file_id,
                    "telegram_file_path": file_path,
                    "segments": transcription.get("segments", [])[:10],  # Store first 10 segments
                    "telegram_user_id": user_id
                }
            }
            
            supabase_client.admin.table("voice_logs").insert(voice_log).execute()
            logger.info(f"💾 Saved transcription to voice_logs")
        except Exception as e:
            logger.error(f"Error saving to voice_logs: {e}")
        
        # Send confirmation with transcript preview
        preview = transcript_text if len(transcript_text) <= 200 else transcript_text[:200] + "..."
        confirmation_msg = (
            f"✅ I transcribed your voice note:\n\n"
            f"\"{preview}\"\n\n"
            f"Processing your request..."
        )
        await send_telegram_message(user_id, confirmation_msg)
        
        # Process transcript through existing parser as regular message
        webhook_msg = WebhookMessage(
            user_id=user_id,
            message=transcript_text,
            platform="telegram",
            metadata={
                "from_voice": True,
                "language": detected_language,
                "duration": duration
            }
        )
        
        await receive_message(webhook_msg, background_tasks)
        
    except Exception as e:
        logger.error(f"❌ Error handling voice message: {e}", exc_info=True)
        await send_telegram_message(
            user_id,
            "❌ Sorry, there was an error processing your voice message. Please try again or type your message."
        )
    
    finally:
        # Clean up temporary file
        if temp_file and os.path.exists(temp_file):
            try:
                os.remove(temp_file)
                logger.info(f"🗑️ Cleaned up temp file: {temp_file}")
            except Exception as cleanup_error:
                logger.error(f"Error cleaning up temp file: {cleanup_error}")


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
            "I'm your intelligent companion with superpowers! 🚀\n\n"
            "✨ What I Can Do:\n\n"
            "💰 **Finance & Business**\n"
            "• Track transactions, loans, repayments\n"
            "• Manage multiple businesses\n"
            "• Generate invoices & track clients\n"
            "• Smart financial insights\n\n"
            "📅 **Calendar & Scheduling**\n"
            "• Book meetings automatically\n"
            "• Auto-sync to Google Calendar\n"
            "• Track work sessions\n\n"
            "🎙️ **Voice Messages**\n"
            "• Send voice notes - I transcribe them!\n"
            "• Powered by Groq Whisper AI\n\n"
            "🧠 **Smart Features**\n"
            "• Learn your patterns\n"
            "• Remember important info (use 'remember')\n"
            "• Context-aware responses\n"
            "• Mirror Mode - follow your workday\n\n"
            "💬 Talk to me naturally:\n"
            '"Book meeting tomorrow at 10am"\n'
            '"I gave Ali 5000 from Vidify"\n'
            '"remember my password is xyz"\n'
            '"Create invoice for ABC Corp"\n\n'
            "Type /help for all commands! 🎯"
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
            "💬 **Natural Language Examples:**\n"
            "• 'Received 50k from milk sales today'\n"
            "• 'Book meeting tomorrow at 3pm'\n"
            "• 'remember my API key is xyz123'\n"
            "• 'Create invoice for $5000'\n"
            "• Send voice messages (auto-transcribed!)\n\n"
            "📋 **All Commands:**\n\n"
            "🏠 General:\n"
            "/start - Welcome & introduction\n"
            "/help - This help message\n\n"
            "💰 Finance:\n"
            "/insights - AI-powered analysis 🧠\n"
            "/status - Quick balance check\n"
            "/report - Detailed financial report\n"
            "/list_invoices - View your invoices\n"
            "/list_clients - View your clients\n\n"
            "📅 Calendar:\n"
            "/sync_calendar - Connect Google Calendar\n"
            "Just say: 'Book meeting [when]'\n\n"
            "🎙️ Voice:\n"
            "Send any voice message - I'll transcribe it!\n\n"
            "⚙️ Settings:\n"
            "/toggle_mirror - Enable/disable mirror mode\n"
            "/my_notifications - View scheduled alerts\n\n"
            "✨ **Pro Tips:**\n"
            "• Use 'remember' to save important info\n"
            "• I learn from every interaction\n"
            "• Voice messages work in any language\n"
            "• Mirror mode tracks your workday automatically\n\n"
            "🔗 Auto-sync: Calendar events → Google Calendar\n"
            "Auth: https://zyana-backend.onrender.com/calendar/auth/google"
        )
    
    elif command == "/add_business":
        return "To add a new business, just tell me: 'Start new business called [Name]'"
    
    elif cmd == "/sync_calendar":
        from config import settings
        auth_url = f"{settings.backend_url}/calendar/auth/google"
        return (
            "🗓️ **Google Calendar Auto-Sync Setup**\n\n"
            "To enable automatic calendar syncing:\n\n"
            "1️⃣ Click this link to authenticate:\n"
            f"{auth_url}\n\n"
            "2️⃣ Sign in with your Google account\n"
            "3️⃣ Grant calendar permissions\n\n"
            "✅ After setup, all events will auto-sync!\n\n"
            "📌 Test it: 'Book meeting tomorrow at 10am'\n"
            "Your event will automatically appear in Google Calendar!"
        )
    
    elif cmd == "/list_invoices":
        from agents.invoice_tracker import invoice_tracker
        from services.user_mapper import user_mapper
        user_id_int = await user_mapper.get_internal_user_id(user_id)
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
        from services.user_mapper import user_mapper
        user_id_int = await user_mapper.get_internal_user_id(user_id)
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
        from services.user_mapper import user_mapper
        user_id_int = await user_mapper.get_internal_user_id(user_id)
        result = await mirror_mode_service.enable_mirror_mode(user_id_int)
        return result.get("message")
    
    elif cmd == "/mirror_mode_off":
        from services.mirror_mode import mirror_mode_service
        from services.user_mapper import user_mapper
        user_id_int = await user_mapper.get_internal_user_id(user_id)
        result = await mirror_mode_service.disable_mirror_mode(user_id_int)
        return result.get("message")
    
    elif cmd == "/my_style":
        from services.mirror_mode import mirror_mode_service
        from services.user_mapper import user_mapper
        user_id_int = await user_mapper.get_internal_user_id(user_id)
        result = await mirror_mode_service.get_style_summary(user_id_int)
        return result.get("message")
    
    else:
        return "❓ Unknown command. Type /help to see what I can do!"

