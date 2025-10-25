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
        """Extract amount from message (supports natural language numbers)."""
        message_lower = message.lower()
        
        # Natural language numbers
        word_to_number = {
            'zero': 0, 'one': 1, 'two': 2, 'three': 3, 'four': 4, 'five': 5,
            'six': 6, 'seven': 7, 'eight': 8, 'nine': 9, 'ten': 10,
            'eleven': 11, 'twelve': 12, 'thirteen': 13, 'fourteen': 14, 'fifteen': 15,
            'sixteen': 16, 'seventeen': 17, 'eighteen': 18, 'nineteen': 19, 'twenty': 20,
            'thirty': 30, 'forty': 40, 'fifty': 50, 'sixty': 60, 'seventy': 70,
            'eighty': 80, 'ninety': 90, 'hundred': 100, 'thousand': 1000,
            'lakh': 100000, 'lac': 100000, 'million': 1000000
        }
        
        # Try natural language patterns first
        # e.g., "ten thousand", "five hundred", "fifty thousand"
        for word_mult in ['lakh', 'lac', 'thousand', 'hundred', 'million']:
            pattern = r'(' + '|'.join(word_to_number.keys()) + r')?\s*' + word_mult
            match = re.search(pattern, message_lower)
            if match:
                multiplier = word_to_number.get(word_mult, 1)
                base = word_to_number.get(match.group(1), 1) if match.group(1) else 1
                return float(base * multiplier)
        
        # Pattern for amounts like: 10000, 10,000, 10k, $100, Rs 100
        patterns = [
            r'(?:rs\.?|pkr|usd|\$|€|£)\s*(\d{1,3}(?:,\d{3})*(?:\.\d+)?)',  # Rs 10,000
            r'(\d{1,3}(?:,\d{3})*(?:\.\d+)?)\s*(?:rs|pkr|usd|dollars?|rupees?)',  # 10,000 Rs
            r'(\d+(?:\.\d+)?)\s*k',  # 10k
            r'(\d{1,3}(?:,\d{3})*(?:\.\d+)?)',  # 10,000 or 10000
        ]
        
        for pattern in patterns:
            match = re.search(pattern, message_lower)
            if match:
                amount_str = match.group(1).replace(',', '')
                
                # Handle 'k' suffix
                if 'k' in message_lower[match.end()-2:match.end()]:
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
        """Determine message intent - SMART pattern matching."""
        message_lower = message.lower()
        
        # Calendar keywords - check FIRST (highest priority)
        calendar_keywords = ['meeting', 'book', 'schedule', 'appointment', 'call', 'event', 'remind', 'calendar']
        if any(word in message_lower for word in calendar_keywords):
            return "calendar"
        
        # Loan keywords - expanded for natural language
        loan_keywords = ['lent', 'loan', 'borrowed', 'lend', 'owe', 'owes', 'debt', 'gave.*loan', 'borrowed from']
        if any(word in message_lower for word in loan_keywords):
            return "loan"
        
        # Repayment keywords
        repay_keywords = ['repaid', 'repay', 'returned', 'paid back', 'got back', 'received back']
        if any(word in message_lower for word in repay_keywords):
            return "repayment"
        
        # Transaction keywords - expanded for natural language
        transaction_keywords = [
            'gave', 'paid', 'received', 'income', 'expense', 'spent', 'bought',
            'got', 'from', 'for', 'to', 'given', 'taken', 'collected', 'earned',
            'salary', 'purchase', 'sold', 'sale'
        ]
        if any(word in message_lower for word in transaction_keywords):
            return "transaction"
        
        # Query keywords
        query_keywords = ['how much', 'what is', 'show me', 'tell me', 'check', 'status']
        if any(word in message_lower for word in query_keywords):
            return "query"
        
        # Report keywords
        report_keywords = ['report', 'summary', 'balance', 'total', 'overview']
        if any(word in message_lower for word in report_keywords):
            return "report"
        
        # Default to transaction if amount AND person present
        if amount and person:
            return "transaction"
        
        # Default to transaction if amount is present
        if amount:
            return "transaction"
        
        return "other"
    
    def _determine_type(self, message: str, intent: str) -> Optional[str]:
        """Determine transaction type - SMART pattern matching."""
        if intent != "transaction":
            return None
        
        message_lower = message.lower()
        
        # Income patterns - receiving money
        income_patterns = [
            'received', 'income', 'earned', 'got', 'collected', 
            'i got', 'i received', 'received from', 'got from',
            'came in', 'incoming', 'payment from', 'paid by',
            'salary', 'wage', 'profit', 'revenue', 'sales'
        ]
        if any(pattern in message_lower for pattern in income_patterns):
            return "income"
        
        # Expense patterns - giving money
        expense_patterns = [
            'paid', 'spent', 'bought', 'gave', 'expense', 
            'i gave', 'i paid', 'paid for', 'gave to',
            'purchased', 'spending', 'cost', 'fee',
            'bill', 'subscription', 'rent'
        ]
        if any(pattern in message_lower for pattern in expense_patterns):
            return "expense"
        
        # Smart detection: if "from" appears, likely income
        if ' from ' in message_lower:
            return "income"
        
        # Smart detection: if "to" or "for" appears, likely expense  
        if ' to ' in message_lower or ' for ' in message_lower:
            return "expense"
        
        return "expense"  # Default to expense if unclear
    
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
        """Extract date from message (supports natural language)."""
        today = datetime.now().date()
        message_lower = message.lower()
        
        # Relative day keywords
        if "today" in message_lower:
            return today
        elif "yesterday" in message_lower:
            return today - timedelta(days=1)
        elif "tomorrow" in message_lower:
            return today + timedelta(days=1)
        elif "day after tomorrow" in message_lower:
            return today + timedelta(days=2)
        elif "day before yesterday" in message_lower:
            return today - timedelta(days=2)
        
        # Week-based patterns
        elif "last week" in message_lower:
            return today - timedelta(days=7)
        elif "next week" in message_lower:
            return today + timedelta(days=7)
        elif "this week" in message_lower:
            return today
        
        # "in X days" pattern
        match = re.search(r'in\s+(\d+)\s+days?', message_lower)
        if match:
            days = int(match.group(1))
            return today + timedelta(days=days)
        
        # Day of week patterns (e.g., "next Monday", "this Friday")
        weekdays = {
            'monday': 0, 'tuesday': 1, 'wednesday': 2, 'thursday': 3,
            'friday': 4, 'saturday': 5, 'sunday': 6
        }
        
        for day_name, day_num in weekdays.items():
            if f"next {day_name}" in message_lower:
                days_ahead = day_num - today.weekday()
                if days_ahead <= 0:  # Target day already passed this week
                    days_ahead += 7
                return today + timedelta(days=days_ahead)
            elif f"this {day_name}" in message_lower:
                days_ahead = day_num - today.weekday()
                if days_ahead < 0:  # Already passed, use next week
                    days_ahead += 7
                return today + timedelta(days=days_ahead)
        
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

