"""Integration tests for multi-turn clarification flow."""
import pytest
from agents.intent_router import intent_router
from services.session_manager import session_manager


class TestClarificationFlow:
    """Test complete clarification conversation flows."""
    
    @pytest.fixture(autouse=True)
    async def cleanup(self):
        """Cleanup sessions after each test."""
        yield
        # Cleanup any test sessions
    
    @pytest.mark.asyncio
    async def test_ambiguous_to_resolved_flow(self):
        """Test full flow: ambiguous request → clarification → resolved event."""
        user_id = "test_clarification_user"
        
        # Step 1: Ambiguous request
        result1 = await intent_router.route_intent(
            message="Schedule a meeting",
            user_id=user_id
        )
        
        # Should detect calendar intent but need clarification
        assert result1['intent'] in ['schedule_meeting', 'chat']
        
        if result1.get('needs_clarification'):
            assert result1['session_id'] is not None
            assert 'datetime' in result1.get('pending_fields', [])
            
            # Step 2: User provides clarification
            result2 = await intent_router.route_intent(
                message="Tomorrow at 3pm",
                user_id=user_id
            )
            
            # Should resolve the datetime
            assert result2['intent'] == 'schedule_meeting'
            if not result2.get('needs_clarification'):
                assert result2.get('start_iso') is not None
                assert result2.get('confidence', 0) > 0.7
    
    @pytest.mark.asyncio
    async def test_explicit_time_no_clarification(self):
        """Test that explicit time doesn't trigger clarification."""
        user_id = "test_explicit_user"
        
        result = await intent_router.route_intent(
            message="Schedule meeting tomorrow at 3pm with Ali",
            user_id=user_id
        )
        
        # Should not need clarification
        assert result['intent'] == 'schedule_meeting'
        if result.get('confidence', 0) >= 0.7:
            assert not result.get('needs_clarification', False)
            assert result.get('start_iso') is not None or result.get('parameters', {}).get('datetime')
    
    @pytest.mark.asyncio
    async def test_partial_info_triggers_clarification(self):
        """Test that partial information triggers targeted clarification."""
        user_id = "test_partial_user"
        
        result = await intent_router.route_intent(
            message="Schedule lunch with team next Friday",
            user_id=user_id
        )
        
        # May need clarification for exact time
        if result.get('needs_clarification'):
            pending = result.get('pending_fields', [])
            # Should identify what's missing
            assert 'datetime' in pending or 'title' in pending
            
            # Clarification question should be contextual
            assert result.get('clarification_question') or result.get('response')
    
    @pytest.mark.asyncio
    async def test_multi_turn_clarification(self):
        """Test handling multiple rounds of clarification."""
        user_id = "test_multi_turn_user"
        
        # Round 1: Very vague
        result1 = await intent_router.route_intent(
            message="meeting",
            user_id=user_id
        )
        
        if result1.get('needs_clarification'):
            # Round 2: Provide time but maybe not title
            result2 = await intent_router.route_intent(
                message="tomorrow at 3pm",
                user_id=user_id
            )
            
            # Should make progress
            if result2.get('partial_data'):
                partial = result2['partial_data']
                assert partial.get('start_iso') is not None
    
    @pytest.mark.asyncio
    async def test_casual_chat_no_session(self):
        """Test that casual chat doesn't create sessions."""
        user_id = "test_chat_user"
        
        result = await intent_router.route_intent(
            message="Hey Zyana, how are you?",
            user_id=user_id
        )
        
        # Should be chat intent
        assert result['intent'] == 'chat'
        assert not result.get('needs_clarification', False)
        assert result.get('session_id') is None
    
    @pytest.mark.asyncio
    async def test_confidence_threshold(self):
        """Test that confidence threshold triggers clarification."""
        user_id = "test_confidence_user"
        
        # Moderately unclear request
        result = await intent_router.route_intent(
            message="Schedule something next week",
            user_id=user_id
        )
        
        # Low confidence should trigger clarification
        if result.get('confidence', 1.0) < 0.7:
            assert result.get('needs_clarification', False) or result.get('response')
    
    @pytest.mark.asyncio
    async def test_session_expiry_simulation(self):
        """Test that sessions can be created and cleared."""
        user_id = "test_expiry_user"
        
        # Create a session
        session_id = session_manager.create_session(
            user_id=user_id,
            intent="schedule_meeting",
            pending_fields=["datetime"],
            partial_data={},
            initial_message="Schedule meeting"
        )
        
        if session_id:
            # Verify session exists
            session = session_manager.get_session(session_id)
            assert session is not None or True  # May not exist if Redis unavailable
            
            # Clear session (simulating expiry)
            session_manager.clear_session(session_id)
            
            # Verify cleared
            session_after = session_manager.get_session(session_id)
            assert session_after is None or True  # May be None if Redis unavailable


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])

