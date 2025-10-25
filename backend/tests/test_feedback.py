"""Tests for feedback system."""
import pytest
from fastapi.testclient import TestClient
from main import app


client = TestClient(app)


class TestFeedbackAPI:
    """Test feedback API endpoints."""
    
    def test_submit_feedback(self):
        """Test submitting feedback."""
        feedback_data = {
            "user_id": "test_user",
            "source_type": "message",
            "source_id": "msg_123",
            "rating": 5,
            "comment": "Great response!"
        }
        
        response = client.post("/feedback/", json=feedback_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "feedback_id" in data
    
    def test_submit_feedback_invalid_rating(self):
        """Test submitting feedback with invalid rating."""
        feedback_data = {
            "user_id": "test_user",
            "source_type": "message",
            "rating": 10,  # Invalid: > 5
        }
        
        response = client.post("/feedback/", json=feedback_data)
        
        assert response.status_code == 422  # Validation error
    
    def test_get_recent_feedback(self):
        """Test getting recent feedback."""
        response = client.get("/feedback/recent?limit=10")
        
        assert response.status_code == 200
        data = response.json()
        assert "feedback" in data
        assert "count" in data
    
    def test_get_feedback_stats(self):
        """Test getting feedback statistics."""
        response = client.get("/feedback/stats")
        
        assert response.status_code == 200
        data = response.json()
        assert "stats" in data
        stats = data["stats"]
        assert "total" in stats
        assert "avg_rating" in stats
        assert "rating_distribution" in stats
    
    def test_update_feedback_reviewed_status(self):
        """Test updating feedback reviewed status."""
        # First create a feedback
        feedback_data = {
            "user_id": "test_user",
            "source_type": "message",
            "rating": 4
        }
        create_response = client.post("/feedback/", json=feedback_data)
        feedback_id = create_response.json()["feedback_id"]
        
        # Update reviewed status
        response = client.put(f"/feedback/{feedback_id}?reviewed=true")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

