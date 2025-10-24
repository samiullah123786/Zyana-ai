"""Message parser service using Fal AI for intent extraction."""
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

from clients.fal_client import fal_client
from models.schemas import ParsedMessage
from services.prompts import get_prompt_json, get_prompt
from services.regex_parser import regex_parser

logger = logging.getLogger(__name__)


class MessageParser:
    """Parse natural language messages into structured data."""
    
    def __init__(self):
        """Initialize parser with prompts."""
        self.extraction_prompt = get_prompt_json("extract_transaction")
        self.system_prompt = get_prompt("system_zyana")
    
    async def parse(self, message: str, context: Optional[Dict[str, Any]] = None) -> ParsedMessage:
        """Parse a message into structured format using two-stage approach.
        
        Stage 1: Quick intent classification
        Stage 2: Structured data extraction
        
        Args:
            message: User message text
            context: Optional context (user habits, recent messages, etc.)
            
        Returns:
            ParsedMessage with extracted fields
        """
        # Stage 1: Quick intent classification
        intent = await self._classify_intent(message)
        logger.info(f"Classified intent: {intent}")
        
        # Stage 2: Extract structured data
        parsed_data = await self._extract_structured_data(message, intent, context)
        
        # Validate and create ParsedMessage
        try:
            parsed_message = ParsedMessage(**parsed_data)
            
            # Apply date inference
            parsed_message = self._infer_date(parsed_message)
            
            # Apply habit defaults if available
            if context and "habits" in context:
                parsed_message = self._apply_habits(parsed_message, context["habits"])
            
            return parsed_message
            
        except Exception as e:
            logger.error(f"Error creating ParsedMessage: {e}")
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
            response = await fal_client.chat_simple(
                prompt=classification_prompt,
                model="gpt-3.5-turbo",
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
        
        try:
            logger.info(f"Extracting structured data for: {message}")
            response = await fal_client.chat_simple(
                prompt=extraction_prompt,
                model="gpt-4",
                temperature=0.0
            )
            
            logger.info(f"Raw AI response: {response[:200]}...")
            
            # Parse JSON response
            # Remove markdown code blocks if present
            response = response.strip()
            if response.startswith("```"):
                response = response.split("```")[1]
                if response.startswith("json"):
                    response = response[4:]
            
            parsed_data = json.loads(response.strip())
            logger.info(f"Successfully parsed data: {parsed_data}")
            
            # Ensure raw_text is set
            parsed_data["raw_text"] = message
            
            return parsed_data
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {e}, response: {response if 'response' in locals() else 'No response'}")
            logger.warning("Falling back to regex parser")
            # Fallback to regex parser
            return regex_parser.parse(message)
        except Exception as e:
            logger.error(f"Extraction error: {e}", exc_info=True)
            logger.warning("Falling back to regex parser")
            # Fallback to regex parser
            return regex_parser.parse(message)
    
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

