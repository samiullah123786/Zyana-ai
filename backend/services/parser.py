"""Message parser service using AI for intent extraction with regex fallback."""
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

from clients.fal_client import fal_client
from models.schemas import ParsedMessage
from services.prompts import get_prompt_json, get_prompt
from services.regex_parser import regex_parser

logger = logging.getLogger(__name__)

# Try to import OpenAI
try:
    from clients.openai_client import openai_client
    HAS_OPENAI = openai_client.enabled
except:
    HAS_OPENAI = False
    logger.warning("OpenAI client not available")


class MessageParser:
    """Parse natural language messages into structured data."""
    
    def __init__(self):
        """Initialize parser with prompts."""
        self.extraction_prompt = get_prompt_json("extract_transaction")
        self.system_prompt = get_prompt("system_zyana")
    
    async def parse(self, message: str, context: Optional[Dict[str, Any]] = None) -> ParsedMessage:
        """Parse a message into structured format using FAST regex-first approach.
        
        STRATEGY: Use instant regex parser as primary method for speed.
        FAL AI is too slow (30+ seconds) for real-time chat.
        
        Args:
            message: User message text
            context: Optional context (user habits, recent messages, etc.)
            
        Returns:
            ParsedMessage with extracted fields
        """
        logger.info(f"⚡ Parsing message (regex-first approach): {message[:50]}...")
        
        try:
            # Use FAST regex parser (instant response)
            parsed_data = regex_parser.parse(message)
            logger.info(f"✅ Regex parser succeeded: intent={parsed_data.get('intent')}, confidence={parsed_data.get('confidence')}")
            
            # Validate and create ParsedMessage
            parsed_message = ParsedMessage(**parsed_data)
            
            # Apply date inference
            parsed_message = self._infer_date(parsed_message)
            
            # Apply habit defaults if available
            if context and "habits" in context:
                parsed_message = self._apply_habits(parsed_message, context["habits"])
            
            return parsed_message
            
        except Exception as e:
            logger.error(f"Error in regex parser: {e}", exc_info=True)
            # Return basic structure on error
            return ParsedMessage(
                intent="other",
                raw_text=message,
                missing_fields=["all"],
                confidence=0.0
            )
    
    async def _classify_intent(self, message: str) -> str:
        """Classify message intent (stage 1 - quick classification).
        
        Args:
            message: User message
            
        Returns:
            Intent string
        """
        classification_prompt = f"""Classify the intent of this message. Reply with ONLY ONE WORD from this list:
- transaction (for income, expense, payment)
- loan (lending money)
- repayment (receiving money back)
- calendar (scheduling, meetings, events)
- goal (targets, objectives)
- create_business (creating new business)
- query (asking questions)
- report (requesting reports/summaries)
- status (checking status)
- other (anything else)

Message: "{message}"

Intent:"""
        
        try:
            # Use FAL AI with fast model for classification
            response = await fal_client.chat_simple(
                prompt=classification_prompt,
                model="google/gemini-2.5-flash-lite",  # Fast model for classification
                temperature=0.0
            )
            
            intent = response.strip().lower()
            
            # Validate intent
            valid_intents = [
                "transaction", "loan", "repayment", "calendar", "goal",
                "create_business", "query", "report", "status", "other"
            ]
            
            return intent if intent in valid_intents else "other"
            
        except Exception as e:
            logger.error(f"Intent classification error: {e}")
            return "other"
    
    async def _extract_structured_data(
        self,
        message: str,
        intent: str,
        context: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Extract structured data from message (stage 2).
        
        Args:
            message: User message
            intent: Classified intent
            context: Optional context
            
        Returns:
            Dict with extracted fields
        """
        # Build extraction prompt with examples
        examples_text = "\n\n".join([
            f"Input: {ex['input']}\nOutput: {json.dumps(ex['output'], indent=2)}"
            for ex in self.extraction_prompt["examples"][:5]
        ])
        
        extraction_prompt = f"""{self.extraction_prompt['system']}

Schema:
{json.dumps(self.extraction_prompt['schema'], indent=2)}

Examples:
{examples_text}

Now extract from this message:
Input: "{message}"
Output (JSON only):"""
        
        # Try OpenAI first (most reliable)
        if HAS_OPENAI:
            try:
                logger.info(f"Using OpenAI for extraction: {message[:50]}...")
                response = await openai_client.chat_simple(
                    prompt=extraction_prompt,
                    model="gpt-3.5-turbo",
                    temperature=0.0
                )
                
                logger.info(f"OpenAI response received")
                parsed_data = self._parse_ai_response(response, message)
                if parsed_data:
                    return parsed_data
                    
            except Exception as e:
                logger.warning(f"OpenAI failed: {e}, trying FAL AI")
        
        # Try FAL AI as backup
        try:
            logger.info(f"Using FAL AI (GPT-5) for extraction: {message[:50]}...")
            response = await fal_client.chat_simple(
                prompt=extraction_prompt,
                model="openai/gpt-5-chat",  # Using GPT-5 via FAL AI
                temperature=0.0
            )
            
            logger.info(f"FAL AI response received")
            parsed_data = self._parse_ai_response(response, message)
            if parsed_data:
                return parsed_data
                
        except Exception as e:
            logger.warning(f"FAL AI failed: {e}")
        
        # Fallback to regex parser (always works)
        logger.info("Using regex parser fallback")
        return regex_parser.parse(message)
    
    def _parse_ai_response(self, response: str, message: str) -> Optional[Dict[str, Any]]:
        """Parse AI response JSON.
        
        Args:
            response: AI response text
            message: Original message
            
        Returns:
            Parsed data dict or None if parsing fails
        """
        try:
            # Remove markdown code blocks if present
            response = response.strip()
            if response.startswith("```"):
                parts = response.split("```")
                if len(parts) >= 2:
                    response = parts[1]
                    if response.startswith("json"):
                        response = response[4:]
            
            parsed_data = json.loads(response.strip())
            logger.info(f"Successfully parsed AI response")
            
            # Ensure raw_text is set
            parsed_data["raw_text"] = message
            
            return parsed_data
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {e}")
            return None
        except Exception as e:
            logger.error(f"Error parsing AI response: {e}")
            return None
    
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

