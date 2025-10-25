"""Agent self-description module for Zyana.

Scans the repository to understand capabilities and stores agent profile
with owner information in the database.
"""
import logging
from pathlib import Path
from typing import List, Dict, Any
from clients.supabase_client import supabase_client
from config import settings

logger = logging.getLogger(__name__)


class AgentSelfDescribe:
    """Analyzes repository and creates agent self-description."""
    
    def __init__(self):
        """Initialize agent self-describe module."""
        self.agent_name = "Zyana"
        self.owner_name = settings.owner_name
        self.default_timezone = settings.default_timezone
        self.version = "2.0.0"
    
    async def initialize(self):
        """Initialize agent profile on startup."""
        try:
            logger.info("🤖 Initializing Zyana agent self-description...")
            
            # Scan capabilities
            capabilities = self._scan_capabilities()
            
            # Store profile in database
            profile_stored = await self._store_agent_profile(capabilities)
            
            if profile_stored:
                logger.info(
                    f"✅ Agent profile initialized: {self.agent_name} "
                    f"(Owner: {self.owner_name}, Timezone: {self.default_timezone})"
                )
                logger.info(f"📋 Capabilities: {len(capabilities)} features detected")
            else:
                logger.warning("⚠️  Agent profile already exists, skipping initialization")
            
        except Exception as e:
            logger.error(f"❌ Error initializing agent profile: {e}", exc_info=True)
    
    def _scan_capabilities(self) -> List[str]:
        """Scan repository to detect agent capabilities.
        
        Returns:
            List of capability descriptions
        """
        capabilities = []
        
        # Check agents directory
        agents_dir = Path(__file__).parent.parent / "agents"
        
        if agents_dir.exists():
            # Calendar agent
            if (agents_dir / "calendar.py").exists():
                capabilities.append("Schedule and manage calendar events with Google Calendar sync")
            
            # Finance agent
            if (agents_dir / "finance.py").exists():
                capabilities.append("Track financial transactions, loans, and repayments")
            
            # Invoice tracker
            if (agents_dir / "invoice_tracker.py").exists():
                capabilities.append("Generate and manage invoices for clients")
            
            # Client manager
            if (agents_dir / "client_manager.py").exists():
                capabilities.append("Manage client relationships and information")
            
            # Notification scheduler
            if (agents_dir / "notification_scheduler.py").exists():
                capabilities.append("Schedule reminders and notifications")
            
            # Habit learner
            if (agents_dir / "habit_learner.py").exists():
                capabilities.append("Learn user habits and preferences over time")
            
            # Routine optimizer
            if (agents_dir / "routine_optimizer.py").exists():
                capabilities.append("Optimize daily routines and work sessions")
            
            # Intent router
            if (agents_dir / "intent_router.py").exists():
                capabilities.append("Intelligent intent classification with GPT-5")
        
        # Check services directory
        services_dir = Path(__file__).parent.parent / "services"
        
        if services_dir.exists():
            # Voice transcription
            if (services_dir / "groq_transcriber.py").exists():
                capabilities.append("Transcribe voice messages via Groq Whisper")
            
            # Intelligence engine
            if (services_dir / "intelligence_engine.py").exists():
                capabilities.append("Provide intelligent insights and analysis")
            
            # Mirror mode
            if (services_dir / "mirror_mode.py").exists():
                capabilities.append("Mirror user communication style and tone")
            
            # Vector memory
            if (services_dir / "context_retriever.py").exists():
                capabilities.append("Store and retrieve memories with vector search")
            
            # Multi-turn clarification
            if (services_dir / "session_manager.py").exists():
                capabilities.append("Handle multi-turn clarification conversations")
            
            # Datetime parsing
            if (services_dir / "datetime_parser.py").exists():
                capabilities.append("Parse natural language dates and times robustly")
        
        # Check memory directory
        memory_dir = Path(__file__).parent.parent / "memory"
        
        if memory_dir.exists() and (memory_dir / "embed.py").exists():
            capabilities.append("Create semantic embeddings for intelligent search")
        
        # Always available
        capabilities.append("Natural conversation with context awareness")
        capabilities.append("Telegram bot integration for mobile access")
        
        return capabilities
    
    async def _store_agent_profile(self, capabilities: List[str]) -> bool:
        """Store agent profile in database.
        
        Args:
            capabilities: List of capability descriptions
            
        Returns:
            True if stored, False if already exists
        """
        try:
            # Check if profile already exists
            existing = supabase_client.admin.table("agent_profile").select("id").limit(1).execute()
            
            if existing.data and len(existing.data) > 0:
                # Update existing profile
                supabase_client.admin.table("agent_profile").update({
                    "name": self.agent_name,
                    "owner": self.owner_name,
                    "capabilities": capabilities,
                    "default_timezone": self.default_timezone,
                    "version": self.version,
                    "metadata": {
                        "features": [
                            "calendar_intelligence",
                            "multi_turn_clarification",
                            "vector_memory",
                            "voice_transcription",
                            "financial_tracking"
                        ],
                        "ai_models": [
                            "Fal AI GPT-5",
                            "Groq Whisper Turbo",
                            "OpenAI Embeddings"
                        ],
                        "integrations": [
                            "Google Calendar",
                            "Telegram",
                            "Supabase",
                            "Qdrant Vector DB",
                            "Redis Sessions"
                        ]
                    }
                }).eq("id", existing.data[0]["id"]).execute()
                
                logger.info("✅ Updated existing agent profile")
                return False
            else:
                # Insert new profile
                supabase_client.admin.table("agent_profile").insert({
                    "name": self.agent_name,
                    "owner": self.owner_name,
                    "capabilities": capabilities,
                    "default_timezone": self.default_timezone,
                    "version": self.version,
                    "metadata": {
                        "features": [
                            "calendar_intelligence",
                            "multi_turn_clarification",
                            "vector_memory",
                            "voice_transcription",
                            "financial_tracking"
                        ],
                        "ai_models": [
                            "Fal AI GPT-5",
                            "Groq Whisper Turbo",
                            "OpenAI Embeddings"
                        ],
                        "integrations": [
                            "Google Calendar",
                            "Telegram",
                            "Supabase",
                            "Qdrant Vector DB",
                            "Redis Sessions"
                        ]
                    }
                }).execute()
                
                logger.info("✅ Created new agent profile")
                return True
                
        except Exception as e:
            logger.error(f"❌ Error storing agent profile: {e}", exc_info=True)
            return False
    
    def get_capabilities_summary(self) -> str:
        """Get a text summary of agent capabilities.
        
        Returns:
            Human-readable capability summary
        """
        capabilities = self._scan_capabilities()
        
        summary = f"I'm {self.agent_name}, {self.owner_name}'s AI assistant. I can:\n\n"
        
        for i, capability in enumerate(capabilities, 1):
            summary += f"{i}. {capability}\n"
        
        summary += f"\nI operate in {self.default_timezone} timezone."
        
        return summary


# Global instance
agent_self_describe = AgentSelfDescribe()

