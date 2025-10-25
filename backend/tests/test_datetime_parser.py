"""Tests for datetime parser service."""
import pytest
from datetime import datetime, timedelta
from services.datetime_parser import datetime_parser


class TestDateTimeParser:
    """Test datetime parsing with various natural language inputs."""
    
    def test_parse_explicit_time_tomorrow(self):
        """Test parsing 'tomorrow at 3pm'."""
        result = datetime_parser.parse_datetime("tomorrow at 3pm")
        
        assert result['iso_start'] is not None
        assert result['iso_end'] is not None
        assert result['confidence'] > 0.7
        assert not result['is_ambiguous']
        
        # Verify it's actually tomorrow
        start_dt = datetime.fromisoformat(result['iso_start'])
        tomorrow = datetime.now(datetime_parser.timezone) + timedelta(days=1)
        assert start_dt.date() == tomorrow.date()
        assert start_dt.hour == 15  # 3pm
    
    def test_parse_explicit_time_with_minutes(self):
        """Test parsing '10:30am tomorrow'."""
        result = datetime_parser.parse_datetime("10:30am tomorrow")
        
        assert result['iso_start'] is not None
        assert result['confidence'] > 0.8
        
        start_dt = datetime.fromisoformat(result['iso_start'])
        assert start_dt.hour == 10
        assert start_dt.minute == 30
    
    def test_parse_relative_time(self):
        """Test parsing 'in 2 hours'."""
        result = datetime_parser.parse_datetime("in 2 hours")
        
        assert result['iso_start'] is not None
        assert result['confidence'] > 0.7
        
        start_dt = datetime.fromisoformat(result['iso_start'])
        now = datetime.now(datetime_parser.timezone)
        
        # Should be roughly 2 hours from now (within 5 minute tolerance)
        time_diff = abs((start_dt - now).total_seconds() - 7200)
        assert time_diff < 300
    
    def test_parse_ambiguous_no_time(self):
        """Test ambiguous input 'schedule a meeting'."""
        result = datetime_parser.parse_datetime("schedule a meeting")
        
        assert result['is_ambiguous']
        assert result['confidence'] < 0.7
    
    def test_parse_vague_date(self):
        """Test vague date 'next week'."""
        result = datetime_parser.parse_datetime("next week")
        
        # Should parse but may be ambiguous if no time specified
        assert result['iso_start'] is not None or result['is_ambiguous']
    
    def test_parse_named_day(self):
        """Test parsing 'next Friday at 2pm'."""
        result = datetime_parser.parse_datetime("next Friday at 2pm")
        
        assert result['iso_start'] is not None
        assert result['confidence'] > 0.7
        
        start_dt = datetime.fromisoformat(result['iso_start'])
        assert start_dt.weekday() == 4  # Friday
        assert start_dt.hour == 14  # 2pm
    
    def test_parse_morning_afternoon(self):
        """Test parsing 'tomorrow morning'."""
        result = datetime_parser.parse_datetime("tomorrow morning")
        
        assert result['iso_start'] is not None
        
        start_dt = datetime.fromisoformat(result['iso_start'])
        # Morning should be before noon
        assert start_dt.hour < 12
    
    def test_timezone_included(self):
        """Test that timezone is included in ISO strings."""
        result = datetime_parser.parse_datetime("tomorrow at 3pm")
        
        assert result['iso_start'] is not None
        
        # Check that timezone info is present
        start_dt = datetime.fromisoformat(result['iso_start'])
        assert start_dt.tzinfo is not None
        assert result['timezone'] == 'Asia/Karachi'
    
    def test_duration_extraction(self):
        """Test duration extraction from 'meeting for 30 minutes'."""
        result = datetime_parser.parse_datetime("meeting tomorrow at 3pm for 30 minutes")
        
        # Should extract 30 minute duration
        if result['duration_minutes']:
            assert result['duration_minutes'] == 30
    
    def test_validate_iso_timestamp(self):
        """Test ISO timestamp validation."""
        valid_iso = "2025-10-26T15:00:00+05:00"
        invalid_iso_no_tz = "2025-10-26T15:00:00"
        invalid_format = "not a timestamp"
        
        assert datetime_parser.validate_iso_timestamp(valid_iso)
        assert not datetime_parser.validate_iso_timestamp(invalid_iso_no_tz)
        assert not datetime_parser.validate_iso_timestamp(invalid_format)
    
    def test_candidates_for_ambiguous(self):
        """Test that ambiguous parses generate candidates."""
        result = datetime_parser.parse_datetime("schedule meeting")
        
        if result['is_ambiguous'] and result['candidates']:
            # Should have candidate interpretations
            assert len(result['candidates']) > 0
            assert 'iso' in result['candidates'][0]
            assert 'description' in result['candidates'][0]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

