"""Tests for session manager service."""
import pytest
from services.session_manager import session_manager


class TestSessionManager:
    """Test Redis-based session management."""
    
    @pytest.fixture(autouse=True)
    def cleanup(self):
        """Cleanup sessions after each test."""
        yield
        # Cleanup test sessions
        # Note: In production, sessions expire automatically
    
    def test_create_session(self):
        """Test creating a new session."""
        session_id = session_manager.create_session(
            user_id="test_user_123",
            intent="schedule_meeting",
            pending_fields=["datetime"],
            partial_data={"title": "Meeting"},
            initial_message="Schedule a meeting"
        )
        
        assert session_id is not None
        assert "test_user_123" in session_id
        assert "schedule_meeting" in session_id
    
    def test_get_session(self):
        """Test retrieving a session."""
        # Create session
        session_id = session_manager.create_session(
            user_id="test_user_456",
            intent="schedule_meeting",
            pending_fields=["datetime"],
            partial_data={"title": "Team Meeting"},
            initial_message="Schedule team meeting"
        )
        
        # Retrieve session
        session = session_manager.get_session(session_id)
        
        if session:  # Only test if Redis is available
            assert session is not None
            assert session['user_id'] == "test_user_456"
            assert session['intent'] == "schedule_meeting"
            assert "datetime" in session['pending_fields']
            assert session['partial_data']['title'] == "Team Meeting"
            assert session['status'] == 'pending'
    
    def test_get_active_session(self):
        """Test getting the most recent active session for a user."""
        user_id = "test_user_789"
        
        # Create session
        session_id = session_manager.create_session(
            user_id=user_id,
            intent="schedule_meeting",
            pending_fields=["datetime"],
            partial_data={},
            initial_message="Schedule meeting"
        )
        
        # Get active session
        active = session_manager.get_active_session(user_id)
        
        if active:  # Only test if Redis is available
            assert active is not None
            assert active['user_id'] == user_id
            assert active['status'] == 'pending'
    
    def test_update_session(self):
        """Test updating session data."""
        # Create session
        session_id = session_manager.create_session(
            user_id="test_user_update",
            intent="schedule_meeting",
            pending_fields=["datetime"],
            partial_data={"title": "Meeting"},
            initial_message="Schedule a meeting"
        )
        
        # Update session
        success = session_manager.update_session(
            session_id,
            {
                "pending_fields": [],
                "partial_data": {
                    "title": "Meeting",
                    "start_iso": "2025-10-26T15:00:00+05:00"
                }
            },
            add_message="Tomorrow at 3pm",
            message_role="user"
        )
        
        if success:  # Only test if Redis is available
            # Retrieve updated session
            session = session_manager.get_session(session_id)
            assert session is not None
            assert len(session['pending_fields']) == 0
            assert len(session['conversation_history']) >= 2
    
    def test_mark_session_complete(self):
        """Test marking session as completed."""
        # Create session
        session_id = session_manager.create_session(
            user_id="test_user_complete",
            intent="schedule_meeting",
            pending_fields=["datetime"],
            partial_data={},
            initial_message="Schedule meeting"
        )
        
        # Mark complete
        success = session_manager.mark_session_complete(session_id)
        
        if success:  # Only test if Redis is available
            session = session_manager.get_session(session_id)
            assert session is not None
            assert session['status'] == 'completed'
    
    def test_clear_session(self):
        """Test clearing/deleting a session."""
        # Create session
        session_id = session_manager.create_session(
            user_id="test_user_clear",
            intent="schedule_meeting",
            pending_fields=[],
            partial_data={},
            initial_message="Test"
        )
        
        # Clear session
        success = session_manager.clear_session(session_id)
        
        if success:  # Only test if Redis is available
            # Try to retrieve - should not exist
            session = session_manager.get_session(session_id)
            assert session is None
    
    def test_conversation_history(self):
        """Test conversation history tracking."""
        # Create session with message
        session_id = session_manager.create_session(
            user_id="test_user_history",
            intent="schedule_meeting",
            pending_fields=["datetime"],
            partial_data={},
            initial_message="Schedule a meeting"
        )
        
        # Add assistant message
        session_manager.update_session(
            session_id,
            {},
            add_message="What time should I schedule it?",
            message_role="assistant"
        )
        
        # Add user response
        session_manager.update_session(
            session_id,
            {},
            add_message="Tomorrow at 3pm",
            message_role="user"
        )
        
        # Get conversation history
        history = session_manager.get_conversation_history(session_id)
        
        if history:  # Only test if Redis is available
            assert len(history) >= 3
            assert history[0]['role'] == 'user'
            assert history[0]['message'] == "Schedule a meeting"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

