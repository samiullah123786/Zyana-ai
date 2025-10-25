"""
INTELLIGENT AI Parser with Claude Sonnet 3.5
=============================================
TRUE INTELLIGENCE: Understands ANY natural language sentence
NO SYNTAX REQUIRED: Just talk naturally

Features:
- 🧠 Claude AI for deep understanding
- 💾 "Remember" keyword for memory storage  
- 📚 Context learning from interactions
- 🎯 Extracts structured data from any sentence
"""
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

from models.schemas import ParsedMessage
from services.prompts import get_prompt_json, get_prompt
from services.regex_parser import regex_parser

logger = logging.getLogger(__name__)

# Try to import Claude (primary AI parser)
try:
    from clients.claude_client import claude_client
    HAS_CLAUDE = claude_client.enabled
    if HAS_CLAUDE:
        logger.info("✅ Claude AI enabled for intelligent parsing")
    else:
        logger.warning("⚠️  Claude AI not available - using regex fallback")
except Exception as e:
    HAS_CLAUDE = False
    logger.warning(f"⚠️  Claude AI import failed: {e}")


class MessageParser:
    """Parse natural language messages into structured data."""
    
    def __init__(self):
        """Initialize parser with prompts."""
        self.extraction_prompt = get_prompt_json("extract_transaction")
        self.system_prompt = get_prompt("system_zyana")
    
    async def parse(self, message: str, context: Optional[Dict[str, Any]] = None) -> ParsedMessage:
        """
        INTELLIGENT AI PARSER
        =====================
        Understands ANY natural language - no specific syntax required!
        
        Strategy:
        1. Check for "remember" keyword → save to memory
        2. Try Claude AI for intelligent understanding
        3. Fall back to regex if Claude unavailable
        
        Args:
            message: User message text (ANY natural language!)
            context: Optional context (user habits, recent messages, etc.)
            
        Returns:
            ParsedMessage with extracted fields
        """
        start_time = datetime.now()
        logger.info(f"🧠 Intelligent parsing: '{message[:60]}...'")
        
        try:
            # Check for "remember" keyword - save to memory
            is_memory = "remember" in message.lower()
            if is_memory:
                logger.info("💾 Memory request detected - will save to long-term memory")
            
            # Use FAST regex parser (Claude via FAL AI is too slow - 10s timeouts)
            # TODO: Re-enable Claude when we have direct Anthropic API (not via FAL AI)
            parsed_data = regex_parser.parse(message)
            parsed_data["is_memory_request"] = is_memory
            logger.info(f"✅ Regex parser (instant, reliable)")
            
            # SAFETY: Force date=None for calendar events
            if parsed_data.get("intent") == "calendar" and parsed_data.get("date"):
                logger.info(f"🗓️  Calendar event detected - clearing date field")
                parsed_data["date"] = None
            
            # Validate and create ParsedMessage
            parsed_message = ParsedMessage(**parsed_data)
            
            # Apply date inference (skip for calendar events)
            if parsed_message.intent != "calendar":
                parsed_message = self._infer_date(parsed_message)
            
            # Apply habit defaults if available
            if context and "habits" in context:
                parsed_message = self._apply_habits(parsed_message, context["habits"])
            
            elapsed = (datetime.now() - start_time).total_seconds()
            logger.info(
                f"✅ Parsed in {elapsed:.3f}s | "
                f"Intent: {parsed_message.intent} | "
                f"Confidence: {parsed_message.confidence:.2f} | "
                f"Memory: {is_memory}"
            )
            
            return parsed_message
            
        except Exception as e:
            logger.error(f"❌ Parser error: {e}", exc_info=True)
            # Return safe fallback
            return ParsedMessage(
                intent="other",
                raw_text=message,
                missing_fields=["all"],
                confidence=0.0
            )
    
    async def _parse_with_claude(self, message: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Use Claude AI to intelligently parse any natural language message.
        
        Claude understands:
        - "I got 50k from my client yesterday" → transaction
        - "Ahmad owes me ten thousand" → loan
        - "Got payment from Vidify today" → transaction  
        - "Meeting with boss tomorrow 3pm" → calendar
        - ANY natural way of speaking!
        
        Args:
            message: Natural language message
            context: User context (habits, history)
            
        Returns:
            Parsed data dictionary
        """
        # Build intelligent prompt for Claude
        system_prompt = """You are an AI assistant that extracts structured financial and calendar data from natural language.

Your job: Parse ANY sentence into structured JSON, no matter how it's written.

Extract these fields:
- intent: transaction, loan, repayment, calendar, query, other
- amount: numeric value (if mentioned)
- currency: PKR, USD, etc. (default PKR if in Pakistan)
- business: company/business name
- person: person's name  
- type: income or expense (for transactions)
- category: what it's for (salary, fuel, software, etc.)
- description: brief summary
- date: only if EXPLICITLY mentioned (today, yesterday, tomorrow, etc.)

IMPORTANT RULES:
1. Be flexible - understand ANY way of saying things
2. If date not mentioned, leave it null
3. Infer intent from context (money = transaction, owe = loan, etc.)
4. Extract person names even if casual ("got money from Ali")
5. Understand Pakistani/Urdu English mix
6. Currency defaults to PKR if not specified

Examples:
"I got 50k from my client yesterday" → {"intent":"transaction","type":"income","amount":50000,"currency":"PKR","date":"yesterday"}
"Ahmad owes me ten thousand" → {"intent":"loan","amount":10000,"person":"Ahmad","currency":"PKR"}
"Meeting with boss tomorrow at 3" → {"intent":"calendar","person":"boss","description":"Meeting"}
"Paid 3000 for fuel today" → {"intent":"transaction","type":"expense","amount":3000,"category":"fuel","date":"today"}"""

        user_prompt = f"""Parse this message into JSON:

"{message}"

Return ONLY valid JSON, no explanation."""

        try:
            # Call Claude via FAL AI
            response = await claude_client.chat_simple(
                prompt=user_prompt,
                system_prompt=system_prompt,
                temperature=0.1,  # Low temperature for consistent extraction
                max_tokens=500
            )
            
            # Clean and parse response
            response_clean = response.strip()
            if response_clean.startswith("```"):
                # Remove markdown code blocks
                lines = response_clean.split("\n")
                response_clean = "\n".join([l for l in lines if not l.startswith("```")])
                response_clean = response_clean.replace("json", "").strip()
            
            # Parse JSON
            parsed_data = json.loads(response_clean)
            
            # Ensure required fields
            parsed_data.setdefault("raw_text", message)
            parsed_data.setdefault("confidence", 0.9)  # High confidence from Claude
            parsed_data.setdefault("missing_fields", [])
            
            logger.info(f"🧠 Claude extracted: {parsed_data}")
            return parsed_data
            
        except json.JSONDecodeError as e:
            logger.error(f"❌ Claude returned invalid JSON: {response}")
            raise
        except Exception as e:
            logger.error(f"❌ Claude parsing error: {e}")
            raise
    
    def _infer_date(self, parsed: ParsedMessage) -> ParsedMessage:
        """Infer date from relative terms if not set.
        
        Args:
            parsed: ParsedMessage
            
        Returns:
            ParsedMessage with inferred date
        """
        if parsed.date:
            return parsed
        
        message_lower = parsed.raw_text.lower()
        today = datetime.now().date()
        
        if "today" in message_lower:
            parsed.date = today
        elif "yesterday" in message_lower:
            parsed.date = today - timedelta(days=1)
        elif "tomorrow" in message_lower:
            parsed.date = today + timedelta(days=1)
        elif "last week" in message_lower:
            parsed.date = today - timedelta(days=7)
        elif "this week" in message_lower:
            parsed.date = today
        
        return parsed
    
    def _apply_habits(self, parsed: ParsedMessage, habits: Dict[str, Any]) -> ParsedMessage:
        """Apply user habits to fill missing fields.
        
        Args:
            parsed: ParsedMessage
            habits: User habit profile
            
        Returns:
            ParsedMessage with habits applied
        """
        # Apply default currency
        if not parsed.currency and "preferred_currency" in habits:
            parsed.currency = habits["preferred_currency"]
        
        # Apply default business if only one business mentioned frequently
        if not parsed.business and "default_business" in habits:
            parsed.business = habits["default_business"]
        
        # More habit applications can be added here
        
        return parsed


# Global parser instance
message_parser = MessageParser()

