"""Simple regex-based parser as fallback when AI fails."""
import re
import logging
from datetime import datetime, timedelta, date
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class RegexParser:
    """Simple regex-based parser for financial transactions."""
    
    def parse(self, message: str) -> Dict[str, Any]:
        """Parse message using regex patterns.
        
        Args:
            message: User message
            
        Returns:
            Dict with extracted fields
        """
        message_lower = message.lower()
        
        # Extract amount (supports formats like: 10000, 10,000, 10k, 10K)
        amount = self._extract_amount(message)
        
        # Extract person name
        person = self._extract_person(message)
        
        # Extract business name
        business = self._extract_business(message)
        
        # Determine intent
        intent = self._determine_intent(message_lower, person, amount)
        
        # Determine transaction type
        trans_type = self._determine_type(message_lower, intent)
        
        # Extract currency
        currency = self._extract_currency(message)
        
        # Extract date
        extracted_date = self._extract_date(message_lower)
        
        # Handle date field based on intent
        if intent == "calendar":
            # Calendar events don't use the date field (they use event_time)
            extracted_date = None
        elif intent in ["transaction", "loan", "repayment"]:
            # Financial transactions: only set date if explicitly mentioned
            if not any(word in message_lower for word in ['today', 'yesterday', 'tomorrow', 'last week', 'this week']):
                extracted_date = None
        
        # Determine missing fields
        missing_fields = []
        if intent in ["transaction", "loan"] and not business:
            missing_fields.append("business")
        if intent in ["transaction", "loan", "repayment"] and not amount:
            missing_fields.append("amount")
        if intent in ["loan", "repayment"] and not person:
            missing_fields.append("person")
        
        return {
            "intent": intent,
            "business": business,
            "type": trans_type,
            "amount": amount,
            "currency": currency or "PKR",
            "category": self._extract_category(message_lower, trans_type),
            "person": person,
            "date": extracted_date,  # Can be date object or None
            "description": message,
            "tags": self._extract_tags(message_lower, intent),
            "raw_text": message,
            "missing_fields": missing_fields,
            "confidence": 0.7 if not missing_fields else 0.5
        }
    
    def _extract_amount(self, message: str) -> Optional[float]:
        """Extract amount from message."""
        # Pattern for amounts like: 10000, 10,000, 10k, $100, Rs 100
        patterns = [
            r'(?:rs\.?|pkr|usd|\$|€|£)\s*(\d{1,3}(?:,\d{3})*(?:\.\d+)?)',  # Rs 10,000
            r'(\d{1,3}(?:,\d{3})*(?:\.\d+)?)\s*(?:rs|pkr|usd|dollars?|rupees?)',  # 10,000 Rs
            r'(\d+(?:\.\d+)?)\s*k',  # 10k
            r'(\d{1,3}(?:,\d{3})*(?:\.\d+)?)',  # 10,000 or 10000
        ]
        
        for pattern in patterns:
            match = re.search(pattern, message.lower())
            if match:
                amount_str = match.group(1).replace(',', '')
                
                # Handle 'k' suffix
                if 'k' in message.lower()[match.end()-2:match.end()]:
                    return float(amount_str) * 1000
                
                return float(amount_str)
        
        return None
    
    def _extract_person(self, message: str) -> Optional[str]:
        """Extract person name from message."""
        # Patterns for person names
        patterns = [
            r'(?:lent|gave|paid)\s+([A-Z][a-zA-Z]+(?:\s+[A-Z][a-z]+)?)',  # After action: "gave Ahmad", "lent Indian"
            r'([A-Z][a-zA-Z]+)\s+(?:repaid|paid back)',  # Before action: "Ahmad repaid"
            r'(?:from|to)\s+([A-Z][a-zA-Z]+)',  # After preposition: "from Zain", "to Ahmad"
            r'(?:for)\s+([A-Z][a-zA-Z]+)',  # "for Indian"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, message)
            if match:
                name = match.group(1).strip()
                # Exclude business names and common words
                if name.lower() in ['vidify', 'milkbusiness', 'yazman', 'express', 'today', 'yesterday', 'tomorrow', 'from', 'with']:
                    continue
                # Include names like Indian, Zain, Ahmad, etc.
                return name
        
        # Try to extract capitalized names not caught by patterns
        words = message.split()
        for i, word in enumerate(words):
            # Clean word of punctuation
            clean_word = word.strip('.,!?;:')
            if len(clean_word) > 2 and clean_word[0].isupper():
                # Skip if it's the first word in sentence (might be "I")
                if i == 0 and clean_word.lower() == 'i':
                    continue
                # Skip business names and common words
                if clean_word.lower() not in ['vidify', 'milkbusiness', 'yazman', 'express', 'today', 'yesterday', 'tomorrow', 'rs', 'pkr', 'usd', 'the', 'from', 'with']:
                    return clean_word
        
        return None
    
    def _extract_business(self, message: str) -> Optional[str]:
        """Extract business name from message."""
        message_lower = message.lower()
        
        # Known business names
        businesses = {
            'vidify': 'Vidify',
            'milk': 'MilkBusiness',
            'milkbusiness': 'MilkBusiness',
            'yazman': 'Yazman Express',
            'yazman express': 'Yazman Express'
        }
        
        for key, value in businesses.items():
            if key in message_lower:
                return value
        
        return None
    
    def _determine_intent(self, message: str, person: Optional[str], amount: Optional[float]) -> str:
        """Determine message intent."""
        # Loan keywords
        if any(word in message for word in ['lent', 'loan', 'borrowed', 'lend']):
            return "loan"
        
        # Repayment keywords
        if any(word in message for word in ['repaid', 'repay', 'returned', 'paid back']):
            return "repayment"
        
        # Transaction keywords
        if any(word in message for word in ['gave', 'paid', 'received', 'income', 'expense', 'spent', 'bought']):
            return "transaction"
        
        # Query keywords
        if any(word in message for word in ['how much', 'what is', 'show me', 'tell me']):
            return "query"
        
        # Report keywords
        if any(word in message for word in ['report', 'summary', 'balance']):
            return "report"
        
        # Default to transaction if amount is present
        if amount:
            return "transaction"
        
        return "other"
    
    def _determine_type(self, message: str, intent: str) -> Optional[str]:
        """Determine transaction type."""
        if intent != "transaction":
            return None
        
        # Income keywords
        if any(word in message for word in ['received', 'income', 'earned', 'got', 'from']):
            return "income"
        
        # Expense keywords
        if any(word in message for word in ['paid', 'spent', 'bought', 'gave', 'expense', 'for']):
            return "expense"
        
        return "expense"  # Default
    
    def _extract_currency(self, message: str) -> Optional[str]:
        """Extract currency from message."""
        message_lower = message.lower()
        
        currencies = {
            'usd': 'USD',
            'dollar': 'USD',
            '$': 'USD',
            'pkr': 'PKR',
            'rs': 'PKR',
            'rupee': 'PKR',
            'eur': 'EUR',
            '€': 'EUR',
            'gbp': 'GBP',
            '£': 'GBP'
        }
        
        for key, value in currencies.items():
            if key in message_lower:
                return value
        
        return "PKR"  # Default
    
    def _extract_date(self, message: str) -> Optional[date]:
        """Extract date from message."""
        today = datetime.now().date()
        
        if "today" in message:
            return today
        elif "yesterday" in message:
            return today - timedelta(days=1)
        elif "tomorrow" in message:
            return today + timedelta(days=1)
        elif "last week" in message:
            return today - timedelta(days=7)
        elif "this week" in message:
            return today
        
        return None  # Return None if no date mentioned
    
    def _extract_category(self, message: str, trans_type: Optional[str]) -> str:
        """Extract category from message."""
        categories = {
            'software': ['software', 'subscription', 'saas'],
            'fuel': ['fuel', 'gas', 'petrol'],
            'food': ['food', 'lunch', 'dinner', 'breakfast', 'meal'],
            'supplies': ['supplies', 'equipment', 'materials'],
            'sales': ['sales', 'revenue', 'earned'],
            'salary': ['salary', 'wages', 'payroll'],
            'marketing': ['marketing', 'ads', 'advertising'],
            'rent': ['rent', 'lease'],
            'utilities': ['utility', 'utilities', 'electricity', 'water'],
        }
        
        for category, keywords in categories.items():
            if any(word in message for word in keywords):
                return category
        
        return "general"
    
    def _extract_tags(self, message: str, intent: str) -> list:
        """Extract relevant tags from message."""
        tags = [intent]
        
        tag_keywords = {
            'urgent': ['urgent', 'asap', 'important'],
            'recurring': ['monthly', 'weekly', 'daily', 'recurring'],
            'cash': ['cash'],
            'online': ['online', 'transfer', 'bank'],
        }
        
        for tag, keywords in tag_keywords.items():
            if any(word in message for word in keywords):
                tags.append(tag)
        
        return tags


# Global instance
regex_parser = RegexParser()

