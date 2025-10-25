"""Robust datetime parsing service using dateparser library.

This service provides production-grade datetime extraction from natural language,
with timezone awareness and ambiguity detection.
"""
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
import pytz
import dateparser
from config import settings

logger = logging.getLogger(__name__)


class DateTimeParser:
    """Production-ready datetime parser with timezone and ambiguity handling."""
    
    def __init__(self):
        """Initialize datetime parser with default settings."""
        self.timezone = pytz.timezone(settings.default_timezone)
        self.confidence_threshold = settings.confidence_threshold
        
        # Dateparser settings optimized for future dates
        self.parser_settings = {
            'PREFER_DATES_FROM': 'future',
            'TIMEZONE': settings.default_timezone,
            'RETURN_AS_TIMEZONE_AWARE': True,
            'RELATIVE_BASE': datetime.now(self.timezone),
            'PREFER_DAY_OF_MONTH': 'first',
        }
        
        logger.info(f"✅ DateTimeParser initialized with timezone: {settings.default_timezone}")
    
    def parse_datetime(
        self,
        text: str,
        reference_time: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Parse datetime from natural language text.
        
        Args:
            text: Natural language text containing date/time
            reference_time: Reference datetime for relative dates (defaults to now)
            
        Returns:
            Dict with:
                - iso_start: ISO8601 start time with timezone
                - iso_end: ISO8601 end time with timezone (start + 1 hour default)
                - duration_minutes: Duration in minutes
                - confidence: 0.0-1.0 confidence score
                - is_ambiguous: True if time/date is unclear
                - candidates: List of possible interpretations
                - raw_parsed: Raw dateparser result
        """
        if reference_time is None:
            reference_time = datetime.now(self.timezone)
        
        # Update parser settings with reference time
        parser_settings = self.parser_settings.copy()
        parser_settings['RELATIVE_BASE'] = reference_time
        
        try:
            # Parse with dateparser
            parsed_dt = dateparser.parse(
                text,
                settings=parser_settings,
                languages=['en']
            )
            
            if parsed_dt is None:
                logger.warning(f"❌ Failed to parse datetime from: {text}")
                return self._create_ambiguous_result(text, "No datetime found")
            
            # Ensure timezone-aware
            if parsed_dt.tzinfo is None:
                parsed_dt = self.timezone.localize(parsed_dt)
            
            # Detect ambiguity
            is_ambiguous, ambiguity_reasons = self._detect_ambiguity(text, parsed_dt)
            
            # Calculate confidence
            confidence = self._calculate_confidence(text, parsed_dt, is_ambiguous)
            
            # Generate candidates for ambiguous cases
            candidates = []
            if is_ambiguous:
                candidates = self._generate_candidates(text, parsed_dt, ambiguity_reasons)
            
            # Default duration: 1 hour
            duration_minutes = 60
            
            # Try to extract duration from text
            extracted_duration = self._extract_duration(text)
            if extracted_duration:
                duration_minutes = extracted_duration
            
            # Calculate end time
            end_dt = parsed_dt + timedelta(minutes=duration_minutes)
            
            result = {
                'iso_start': parsed_dt.isoformat(),
                'iso_end': end_dt.isoformat(),
                'duration_minutes': duration_minutes,
                'confidence': confidence,
                'is_ambiguous': is_ambiguous,
                'candidates': candidates,
                'raw_parsed': str(parsed_dt),
                'timezone': str(parsed_dt.tzinfo)
            }
            
            logger.info(
                f"✅ Parsed datetime: {text} → {parsed_dt.isoformat()} "
                f"(confidence: {confidence:.2f}, ambiguous: {is_ambiguous})"
            )
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Error parsing datetime: {e}", exc_info=True)
            return self._create_ambiguous_result(text, str(e))
    
    def _detect_ambiguity(
        self,
        text: str,
        parsed_dt: datetime
    ) -> tuple[bool, List[str]]:
        """Detect if the parsed datetime is ambiguous.
        
        Args:
            text: Original text
            parsed_dt: Parsed datetime
            
        Returns:
            Tuple of (is_ambiguous, list of reasons)
        """
        reasons = []
        text_lower = text.lower()
        
        # Check if no explicit time mentioned (defaulted to midnight or current time)
        time_keywords = ['am', 'pm', 'o\'clock', 'morning', 'afternoon', 'evening', 'night', ':']
        has_explicit_time = any(kw in text_lower for kw in time_keywords)
        
        # Check for time patterns
        import re
        time_pattern = r'\d{1,2}(?::\d{2})?\s*(?:am|pm)?'
        has_time_pattern = bool(re.search(time_pattern, text_lower))
        
        if not has_explicit_time and not has_time_pattern:
            # Check if parsed time is midnight or very close to now
            if parsed_dt.hour == 0 and parsed_dt.minute == 0:
                reasons.append("no_explicit_time")
            elif abs((parsed_dt - datetime.now(self.timezone)).total_seconds()) < 60:
                reasons.append("defaulted_to_now")
        
        # Check if date is too vague (e.g., just "meeting" without date)
        date_keywords = ['today', 'tomorrow', 'yesterday', 'monday', 'tuesday', 'wednesday',
                        'thursday', 'friday', 'saturday', 'sunday', 'next', 'this', 'week']
        has_explicit_date = any(kw in text_lower for kw in date_keywords)
        
        # Check for date patterns (YYYY-MM-DD, DD/MM, etc.)
        date_pattern = r'\d{1,4}[-/]\d{1,2}(?:[-/]\d{1,4})?'
        has_date_pattern = bool(re.search(date_pattern, text))
        
        if not has_explicit_date and not has_date_pattern:
            # If parsed date is today but not explicitly mentioned
            if parsed_dt.date() == datetime.now(self.timezone).date() and 'today' not in text_lower:
                reasons.append("date_not_specified")
        
        # Check for vague terms
        vague_terms = ['soon', 'later', 'sometime', 'eventually']
        if any(term in text_lower for term in vague_terms):
            reasons.append("vague_terms")
        
        # Check if it's just a generic word without context
        generic_calendar_words = ['meeting', 'call', 'appointment', 'event']
        word_count = len(text.split())
        if word_count <= 2 and any(word in text_lower for word in generic_calendar_words):
            reasons.append("insufficient_context")
        
        is_ambiguous = len(reasons) > 0
        
        return is_ambiguous, reasons
    
    def _calculate_confidence(
        self,
        text: str,
        parsed_dt: datetime,
        is_ambiguous: bool
    ) -> float:
        """Calculate confidence score for parsed datetime.
        
        Args:
            text: Original text
            parsed_dt: Parsed datetime
            is_ambiguous: Whether datetime is ambiguous
            
        Returns:
            Confidence score between 0.0 and 1.0
        """
        confidence = 1.0
        
        # Reduce confidence if ambiguous
        if is_ambiguous:
            confidence -= 0.4
        
        # Increase confidence for explicit patterns
        text_lower = text.lower()
        
        # Explicit time patterns increase confidence
        import re
        if re.search(r'\d{1,2}:\d{2}\s*(?:am|pm)', text_lower):
            confidence += 0.2
        elif re.search(r'\d{1,2}\s*(?:am|pm)', text_lower):
            confidence += 0.15
        
        # Explicit date patterns increase confidence
        if re.search(r'\d{4}-\d{2}-\d{2}', text):
            confidence += 0.2
        elif any(day in text_lower for day in ['monday', 'tuesday', 'wednesday', 'thursday', 'friday']):
            confidence += 0.1
        
        # "tomorrow" and "today" are very clear
        if 'tomorrow' in text_lower or 'today' in text_lower:
            confidence += 0.15
        
        # Clamp between 0.0 and 1.0
        confidence = max(0.0, min(1.0, confidence))
        
        return confidence
    
    def _generate_candidates(
        self,
        text: str,
        base_dt: datetime,
        ambiguity_reasons: List[str]
    ) -> List[Dict[str, str]]:
        """Generate candidate interpretations for ambiguous datetime.
        
        Args:
            text: Original text
            base_dt: Base parsed datetime
            ambiguity_reasons: List of ambiguity reasons
            
        Returns:
            List of candidate datetime interpretations
        """
        candidates = []
        
        # If no time specified, offer common times
        if "no_explicit_time" in ambiguity_reasons:
            common_times = [9, 10, 14, 15, 16, 17]  # 9am, 10am, 2pm, 3pm, 4pm, 5pm
            for hour in common_times:
                candidate_dt = base_dt.replace(hour=hour, minute=0, second=0, microsecond=0)
                candidates.append({
                    'iso': candidate_dt.isoformat(),
                    'description': candidate_dt.strftime('%I:%M %p on %A, %B %d')
                })
        
        # If date not specified, offer today/tomorrow
        if "date_not_specified" in ambiguity_reasons:
            today = datetime.now(self.timezone).replace(hour=base_dt.hour, minute=base_dt.minute)
            tomorrow = today + timedelta(days=1)
            
            candidates.append({
                'iso': today.isoformat(),
                'description': f"Today at {today.strftime('%I:%M %p')}"
            })
            candidates.append({
                'iso': tomorrow.isoformat(),
                'description': f"Tomorrow at {tomorrow.strftime('%I:%M %p')}"
            })
        
        # Limit to top 3 candidates
        return candidates[:3]
    
    def _extract_duration(self, text: str) -> Optional[int]:
        """Extract duration in minutes from text.
        
        Args:
            text: Text to extract duration from
            
        Returns:
            Duration in minutes, or None if not found
        """
        import re
        text_lower = text.lower()
        
        # Pattern: "for 30 minutes", "for 2 hours"
        duration_patterns = [
            (r'for\s+(\d+)\s*(?:hours?|hrs?)', 60),  # hours
            (r'for\s+(\d+)\s*(?:minutes?|mins?)', 1),  # minutes
            (r'(\d+)\s*(?:hours?|hrs?)\s+meeting', 60),
            (r'(\d+)\s*(?:minutes?|mins?)\s+meeting', 1),
        ]
        
        for pattern, multiplier in duration_patterns:
            match = re.search(pattern, text_lower)
            if match:
                return int(match.group(1)) * multiplier
        
        # Default durations based on keywords
        if 'lunch' in text_lower or 'dinner' in text_lower:
            return 60
        elif 'coffee' in text_lower:
            return 30
        elif 'quick' in text_lower or 'brief' in text_lower:
            return 15
        
        return None
    
    def _create_ambiguous_result(
        self,
        text: str,
        error_message: str
    ) -> Dict[str, Any]:
        """Create result for ambiguous/failed parse.
        
        Args:
            text: Original text
            error_message: Error or ambiguity message
            
        Returns:
            Ambiguous result dict
        """
        return {
            'iso_start': None,
            'iso_end': None,
            'duration_minutes': None,
            'confidence': 0.0,
            'is_ambiguous': True,
            'candidates': [],
            'raw_parsed': None,
            'timezone': settings.default_timezone,
            'error': error_message
        }
    
    def validate_iso_timestamp(self, iso_string: str) -> bool:
        """Validate ISO8601 timestamp with timezone.
        
        Args:
            iso_string: ISO8601 timestamp string
            
        Returns:
            True if valid, False otherwise
        """
        try:
            dt = datetime.fromisoformat(iso_string)
            # Must have timezone
            if dt.tzinfo is None:
                return False
            return True
        except (ValueError, TypeError):
            return False


# Global instance
datetime_parser = DateTimeParser()

