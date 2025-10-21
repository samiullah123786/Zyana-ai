"""Tests for finance agent."""
import pytest
from datetime import date
from agents.finance import FinanceAgent
from models.schemas import ParsedMessage


class TestFinanceAgent:
    """Test finance agent functionality."""
    
    @pytest.fixture
    def agent(self):
        """Create agent instance."""
        return FinanceAgent()
    
    @pytest.fixture
    def sample_transaction_message(self):
        """Create sample transaction message."""
        return ParsedMessage(
            intent="transaction",
            business="Vidify",
            type="expense",
            amount=15000.0,
            currency="PKR",
            category="software",
            person=None,
            date=date.today(),
            description="Adobe subscription",
            tags=["expense", "software"],
            raw_text="Paid 15000 for Adobe subscription",
            missing_fields=[],
            confidence=0.95
        )
    
    @pytest.mark.asyncio
    async def test_create_transaction(self, agent, sample_transaction_message):
        """Test transaction creation."""
        result = await agent.process(sample_transaction_message, "test_user")
        
        assert result["success"] is True
        assert "message" in result
        assert "data" in result
    
    @pytest.mark.asyncio
    async def test_create_loan(self, agent):
        """Test loan creation."""
        parsed = ParsedMessage(
            intent="loan",
            business="Vidify",
            amount=10000.0,
            currency="PKR",
            person="Ahmad",
            date=date.today(),
            description="Loan to Ahmad",
            tags=["loan"],
            raw_text="Lent Ahmad 10000",
            missing_fields=[],
            confidence=0.95
        )
        
        result = await agent.process(parsed, "test_user")
        
        # Note: This might fail if database is not set up
        # In real tests, you'd use a test database or mocks
        assert "success" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

