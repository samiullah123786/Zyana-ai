"""Mirror Mode Service for learning and replicating user communication style."""
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
import json
import re

from clients.supabase_client import supabase_client
from clients.qdrant_client import qdrant_client
from memory.embed import memory_service

logger = logging.getLogger(__name__)


class MirrorModeService:
    """Service for learning user communication style and applying it to responses."""
    
    SAMPLE_LIMIT = 100  # Maximum message samples to store
    MIN_SAMPLES = 20  # Minimum samples needed for style analysis
    
    async def enable_mirror_mode(self, user_id: int) -> Dict[str, Any]:
        """Enable mirror mode for a user.
        
        Args:
            user_id: User ID
            
        Returns:
            Response dict
        """
        try:
            # Update user record
            supabase_client.admin.table("users").update({
                "mirror_mode_enabled": True
            }).eq("id", user_id).execute()
            
            logger.info(f"Enabled mirror mode for user {user_id}")
            
            return {
                "success": True,
                "message": "✅ Mirror Mode activated! I'll start learning your communication style.\n\nI'll observe your messages to understand:\n• Your tone and formality level\n• Common phrases you use\n• Emoji preferences\n• Message length patterns"
            }
            
        except Exception as e:
            logger.error(f"Error enabling mirror mode: {e}", exc_info=True)
            return {
                "success": False,
                "message": f"Failed to enable mirror mode: {str(e)}"
            }
    
    async def disable_mirror_mode(self, user_id: int) -> Dict[str, Any]:
        """Disable mirror mode for a user.
        
        Args:
            user_id: User ID
            
        Returns:
            Response dict
        """
        try:
            # Update user record
            supabase_client.admin.table("users").update({
                "mirror_mode_enabled": False
            }).eq("id", user_id).execute()
            
            logger.info(f"Disabled mirror mode for user {user_id}")
            
            return {
                "success": True,
                "message": "✅ Mirror Mode deactivated. I'll use my default communication style."
            }
            
        except Exception as e:
            logger.error(f"Error disabling mirror mode: {e}", exc_info=True)
            return {
                "success": False,
                "message": f"Failed to disable mirror mode: {str(e)}"
            }
    
    async def is_mirror_mode_enabled(self, user_id: int) -> bool:
        """Check if mirror mode is enabled for a user.
        
        Args:
            user_id: User ID
            
        Returns:
            True if enabled
        """
        try:
            result = supabase_client.admin.table("users").select(
                "mirror_mode_enabled"
            ).eq("id", user_id).execute()
            
            if result.data:
                return result.data[0].get("mirror_mode_enabled", False)
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking mirror mode: {e}", exc_info=True)
            return False
    
    async def add_message_sample(
        self,
        user_id: int,
        message: str,
        intent: Optional[str] = None
    ):
        """Store a user message sample for style learning.
        
        Args:
            user_id: User ID
            message: User message
            intent: Message intent
        """
        try:
            # Embed message
            embedding_id = None
            try:
                # Create embedding in Qdrant
                points = await memory_service._embed_text(message)
                if points:
                    embedding_id = f"user_style_{user_id}_{datetime.utcnow().timestamp()}"
                    
                    # Store in Qdrant collection
                    qdrant_client.client.upsert(
                        collection_name="user_style",
                        points=[{
                            "id": embedding_id,
                            "vector": points[0],
                            "payload": {
                                "user_id": user_id,
                                "message": message,
                                "intent": intent,
                                "timestamp": datetime.utcnow().isoformat()
                            }
                        }]
                    )
            except Exception as embed_error:
                logger.error(f"Error embedding message sample: {embed_error}")
            
            # Store in database
            supabase_client.admin.table("user_message_samples").insert({
                "user_id": user_id,
                "message": message,
                "intent": intent,
                "embedding_id": embedding_id,
                "timestamp": datetime.utcnow().isoformat()
            }).execute()
            
            logger.debug(f"Stored message sample for user {user_id}")
            
            # Update style profile periodically
            await self._update_style_profile(user_id)
            
        except Exception as e:
            logger.error(f"Error adding message sample: {e}", exc_info=True)
    
    async def get_user_style(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get user's learned communication style.
        
        Args:
            user_id: User ID
            
        Returns:
            Style profile dict or None
        """
        try:
            # Get from habit_profiles
            result = supabase_client.admin.table("habit_profiles").select(
                "*"
            ).eq("user_id", user_id).eq("key", "communication_style").execute()
            
            if result.data:
                profile = result.data[0]
                return profile.get("style_profile", {})
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting user style: {e}", exc_info=True)
            return None
    
    async def apply_style_transformation(
        self,
        response: str,
        user_id: int
    ) -> str:
        """Transform a response to match user's communication style.
        
        Args:
            response: Original response
            user_id: User ID
            
        Returns:
            Transformed response
        """
        try:
            # Check if mirror mode is enabled
            if not await self.is_mirror_mode_enabled(user_id):
                return response
            
            # Get user style
            style = await self.get_user_style(user_id)
            
            if not style:
                logger.debug(f"No style profile for user {user_id} yet")
                return response
            
            # Apply transformations based on style profile
            transformed = response
            
            # 1. Adjust formality
            formality = style.get("formality", "neutral")
            if formality == "casual":
                transformed = self._casualize(transformed)
            elif formality == "formal":
                transformed = self._formalize(transformed)
            
            # 2. Adjust brevity
            brevity = style.get("brevity", "medium")
            if brevity == "short":
                transformed = self._shorten(transformed)
            
            # 3. Apply common phrases
            common_phrases = style.get("common_phrases", [])
            if common_phrases:
                transformed = self._apply_phrases(transformed, common_phrases)
            
            # 4. Adjust emoji usage
            emoji_level = style.get("emoji_level", "medium")
            if emoji_level == "low":
                transformed = self._reduce_emojis(transformed)
            elif emoji_level == "high":
                transformed = self._add_emojis(transformed)
            
            logger.debug(f"Applied style transformation for user {user_id}")
            
            return transformed
            
        except Exception as e:
            logger.error(f"Error applying style transformation: {e}", exc_info=True)
            return response  # Return original on error
    
    async def get_style_summary(self, user_id: int) -> Dict[str, Any]:
        """Get a summary of user's learned communication style.
        
        Args:
            user_id: User ID
            
        Returns:
            Style summary
        """
        try:
            # Get message samples
            samples = supabase_client.admin.table("user_message_samples").select(
                "*"
            ).eq("user_id", user_id).order("timestamp", desc=True).limit(50).execute()
            
            sample_count = len(samples.data) if samples.data else 0
            
            if sample_count < self.MIN_SAMPLES:
                return {
                    "success": False,
                    "message": f"Need {self.MIN_SAMPLES - sample_count} more messages to analyze your style.",
                    "data": {"sample_count": sample_count}
                }
            
            # Get style profile
            style = await self.get_user_style(user_id)
            
            if not style:
                return {
                    "success": False,
                    "message": "Style profile not yet analyzed.",
                    "data": {"sample_count": sample_count}
                }
            
            # Format summary
            message = (
                f"📝 Your Communication Style:\n\n"
                f"• Tone: {style.get('formality', 'neutral').title()}\n"
                f"• Brevity: {style.get('brevity', 'medium').title()} messages (avg {style.get('avg_words', 0)} words)\n"
                f"• Emoji usage: {style.get('emoji_level', 'medium').title()} ({style.get('emoji_per_message', 0):.1f} per message)\n"
            )
            
            common_phrases = style.get("common_phrases", [])
            if common_phrases:
                message += f"• Common phrases: {', '.join(common_phrases[:5])}\n"
            
            message += f"\nBased on {sample_count} messages"
            
            return {
                "success": True,
                "message": message,
                "data": {
                    "style": style,
                    "sample_count": sample_count
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting style summary: {e}", exc_info=True)
            return {
                "success": False,
                "message": f"Failed to get style summary: {str(e)}",
                "data": None
            }
    
    async def _update_style_profile(self, user_id: int):
        """Analyze message samples and update style profile.
        
        Args:
            user_id: User ID
        """
        try:
            # Get recent samples
            samples = supabase_client.admin.table("user_message_samples").select(
                "*"
            ).eq("user_id", user_id).order("timestamp", desc=True).limit(100).execute()
            
            if not samples.data or len(samples.data) < self.MIN_SAMPLES:
                return  # Not enough data
            
            messages = [s["message"] for s in samples.data]
            
            # Analyze style features
            style = self._analyze_style(messages)
            
            # Store in habit_profiles
            result = supabase_client.admin.table("habit_profiles").select("*").eq(
                "user_id", user_id
            ).eq("key", "communication_style").execute()
            
            data = {
                "style_profile": style,
                "updated_at": datetime.utcnow().isoformat()
            }
            
            if result.data:
                # Update
                supabase_client.admin.table("habit_profiles").update(data).eq(
                    "user_id", user_id
                ).eq("key", "communication_style").execute()
            else:
                # Create
                data.update({
                    "user_id": user_id,
                    "key": "communication_style",
                    "value": "learned",
                    "confidence_score": 0.7
                })
                supabase_client.admin.table("habit_profiles").insert(data).execute()
            
            logger.info(f"Updated style profile for user {user_id}")
            
        except Exception as e:
            logger.error(f"Error updating style profile: {e}", exc_info=True)
    
    def _analyze_style(self, messages: List[str]) -> Dict[str, Any]:
        """Analyze communication style from messages.
        
        Args:
            messages: List of user messages
            
        Returns:
            Style profile dict
        """
        # Word count
        word_counts = [len(msg.split()) for msg in messages]
        avg_words = sum(word_counts) / len(word_counts) if word_counts else 0
        
        # Emoji count
        emoji_pattern = re.compile("["
            u"\U0001F600-\U0001F64F"  # emoticons
            u"\U0001F300-\U0001F5FF"  # symbols & pictographs
            u"\U0001F680-\U0001F6FF"  # transport & map symbols
            u"\U0001F1E0-\U0001F1FF"  # flags
            "]+", flags=re.UNICODE)
        
        total_emojis = sum(len(emoji_pattern.findall(msg)) for msg in messages)
        emoji_per_message = total_emojis / len(messages) if messages else 0
        
        # Formality detection (simple heuristics)
        formal_indicators = ["please", "thank you", "would", "could", "kindly"]
        casual_indicators = ["bro", "yeah", "nah", "lol", "btw", "gonna", "wanna"]
        
        formal_count = sum(1 for msg in messages for word in formal_indicators if word in msg.lower())
        casual_count = sum(1 for msg in messages for word in casual_indicators if word in msg.lower())
        
        if casual_count > formal_count * 2:
            formality = "casual"
        elif formal_count > casual_count * 2:
            formality = "formal"
        else:
            formality = "neutral"
        
        # Brevity
        if avg_words < 10:
            brevity = "short"
        elif avg_words > 25:
            brevity = "long"
        else:
            brevity = "medium"
        
        # Emoji level
        if emoji_per_message < 0.5:
            emoji_level = "low"
        elif emoji_per_message > 2:
            emoji_level = "high"
        else:
            emoji_level = "medium"
        
        # Common phrases (extract frequent 2-3 word phrases)
        all_words = " ".join(messages).lower()
        common_phrases = []
        for word in casual_indicators + ["cool", "got it", "nice", "awesome"]:
            if all_words.count(word) >= 3:
                common_phrases.append(word)
        
        return {
            "formality": formality,
            "brevity": brevity,
            "avg_words": round(avg_words, 1),
            "emoji_level": emoji_level,
            "emoji_per_message": round(emoji_per_message, 1),
            "common_phrases": common_phrases[:10]
        }
    
    def _casualize(self, text: str) -> str:
        """Make text more casual."""
        replacements = {
            "Hello": "Hey",
            "Thank you": "Thanks",
            "I will": "I'll",
            "You are": "You're",
            "It is": "It's"
        }
        for formal, casual in replacements.items():
            text = text.replace(formal, casual)
        return text
    
    def _formalize(self, text: str) -> str:
        """Make text more formal."""
        replacements = {
            "Hey": "Hello",
            "Thanks": "Thank you",
            "I'll": "I will",
            "You're": "You are"
        }
        for casual, formal in replacements.items():
            text = text.replace(casual, formal)
        return text
    
    def _shorten(self, text: str) -> str:
        """Shorten message by removing extra details."""
        # Remove parenthetical explanations
        text = re.sub(r'\([^)]*\)', '', text)
        # Keep only first sentence if multiple
        sentences = text.split('. ')
        if len(sentences) > 2:
            return '. '.join(sentences[:2]) + '.'
        return text
    
    def _apply_phrases(self, text: str, phrases: List[str]) -> str:
        """Apply user's common phrases to response."""
        # Subtle integration of common phrases
        if "bro" in phrases and "!" in text and "bro" not in text.lower():
            text = text.replace("!", " bro!")
        return text
    
    def _reduce_emojis(self, text: str) -> str:
        """Reduce emoji usage."""
        emoji_pattern = re.compile("["
            u"\U0001F600-\U0001F64F"
            u"\U0001F300-\U0001F5FF"
            u"\U0001F680-\U0001F6FF"
            u"\U0001F1E0-\U0001F1FF"
            "]+", flags=re.UNICODE)
        # Remove every other emoji
        emojis = emoji_pattern.findall(text)
        for i, emoji in enumerate(emojis):
            if i % 2 == 1:
                text = text.replace(emoji, '', 1)
        return text
    
    def _add_emojis(self, text: str) -> str:
        """Add more emojis."""
        # Add contextual emojis
        if "success" in text.lower() or "✅" in text:
            text = text.replace("✅", "✅🎉")
        if "payment" in text.lower() or "paid" in text.lower():
            text = text.replace("paid", "paid 💰")
        return text


# Global instance
mirror_mode_service = MirrorModeService()

