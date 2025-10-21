"""Tests for message parser."""
import pytest
from datetime import date
from services.parser import MessageParser
from models.schemas import ParsedMessage


class TestMessageParser:
    """Test message parser functionality."""
    
    @pytest.fixture
    def parser(self):
        """Create parser instance."""
        return MessageParser()
    
    @pytest.mark.asyncio
    async def test_parse_transaction_income(self, parser):
        """Test parsing income transaction."""
        message = "Received 50k from milk sales today"
        parsed = await parser.parse(message)
        
        assert parsed.intent == "transaction"
        assert parsed.type == "income"
        assert parsed.amount == 50000
        assert parsed.currency == "PKR"
        assert parsed.category == "sales"
    
    @pytest.mark.asyncio
    async def test_parse_loan(self, parser):
        """Test parsing loan."""
        message = "I lent Ahmad Rs 10000 from Vidify yesterday"
        parsed = await parser.parse(message)
        
        assert parsed.intent == "loan"
        assert parsed.person == "Ahmad"
        assert parsed.amount == 10000
        assert parsed.business == "Vidify"
    
    @pytest.mark.asyncio
    async def test_parse_calendar_event(self, parser):
        """Test parsing calendar event."""
        message = "Meeting with team tomorrow at 3pm"
        parsed = await parser.parse(message)
        
        assert parsed.intent == "calendar"
        assert parsed.description is not None
        assert "meeting" in parsed.description.lower()
    
    @pytest.mark.asyncio
    async def test_parse_query(self, parser):
        """Test parsing query."""
        message = "How much did I lend Ahmad?"
        parsed = await parser.parse(message)
        
        assert parsed.intent == "query"
        assert parsed.person == "Ahmad"
    
    @pytest.mark.asyncio
    async def test_missing_fields(self, parser):
        """Test detection of missing fields."""
        message = "Paid someone 3000"
        parsed = await parser.parse(message)
        
        assert len(parsed.missing_fields) > 0
        assert parsed.confidence < 0.8


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

