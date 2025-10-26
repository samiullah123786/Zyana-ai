"""Agent Registry - Central registry of all AI agents with health monitoring.

Maintains a catalog of all agents, their capabilities, dependencies, and health status.
Enables self-awareness by providing a comprehensive view of system capabilities.
"""
import logging
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime

logger = logging.getLogger(__name__)


class AgentRegistry:
    """Central registry for all AI agents with health monitoring."""
    
    def __init__(self):
        """Initialize Agent Registry."""
        self.agents: Dict[str, Dict[str, Any]] = {}
        logger.info("✅ AgentRegistry initialized")
    
    def register_agent(
        self,
        name: str,
        description: str,
        dependencies: List[str],
        health_check: Optional[Callable] = None,
        critical: bool = False,
        **kwargs
    ):
        """Register an agent in the system.
        
        Args:
            name: Agent name (unique identifier)
            description: Human-readable description of agent's purpose
            dependencies: List of dependencies (e.g., ["Google OAuth", "Supabase"])
            health_check: Async function to check agent health
            critical: Whether this agent is critical to system operation
            **kwargs: Additional metadata
        """
        self.agents[name] = {
            "name": name,
            "description": description,
            "dependencies": dependencies,
            "health_check": health_check,
            "critical": critical,
            "last_health_check": None,
            "last_status": "unknown",
            "registered_at": datetime.now().isoformat(),
            **kwargs
        }
        
        logger.info(f"📝 Registered agent: {name} ({'CRITICAL' if critical else 'optional'})")
    
    def get_agent(self, name: str) -> Optional[Dict[str, Any]]:
        """Get agent metadata by name.
        
        Args:
            name: Agent name
            
        Returns:
            Agent metadata dict or None
        """
        return self.agents.get(name)
    
    def list_agents(
        self,
        include_health: bool = False
    ) -> List[Dict[str, Any]]:
        """List all registered agents.
        
        Args:
            include_health: Whether to include health check status
            
        Returns:
            List of agent metadata dicts
        """
        agents_list = []
        
        for name, agent in self.agents.items():
            agent_info = {
                "name": agent["name"],
                "description": agent["description"],
                "dependencies": agent["dependencies"],
                "critical": agent["critical"]
            }
            
            if include_health:
                agent_info.update({
                    "last_status": agent.get("last_status", "unknown"),
                    "last_health_check": agent.get("last_health_check")
                })
            
            agents_list.append(agent_info)
        
        return agents_list
    
    def get_capabilities_summary(self) -> str:
        """Get a human-readable summary of system capabilities.
        
        Returns:
            Formatted string of capabilities
        """
        capabilities = []
        
        for agent in self.agents.values():
            status_emoji = "✅" if agent.get("last_status") == "healthy" else "❓"
            capabilities.append(f"{status_emoji} {agent['description']}")
        
        return "\n".join(capabilities)
    
    def get_critical_agents(self) -> List[str]:
        """Get list of critical agent names.
        
        Returns:
            List of critical agent names
        """
        return [name for name, agent in self.agents.items() if agent.get("critical", False)]
    
    def update_health_status(
        self,
        agent_name: str,
        status: str,
        last_check: datetime
    ):
        """Update an agent's health status.
        
        Args:
            agent_name: Agent name
            status: Health status ('healthy', 'degraded', 'failed')
            last_check: Timestamp of last health check
        """
        if agent_name in self.agents:
            self.agents[agent_name]["last_status"] = status
            self.agents[agent_name]["last_health_check"] = last_check.isoformat()
            logger.debug(f"💊 Updated health status for {agent_name}: {status}")
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get overall system status based on agent health.
        
        Returns:
            Dict with overall status and details
        """
        total_agents = len(self.agents)
        healthy = sum(1 for a in self.agents.values() if a.get("last_status") == "healthy")
        failed = sum(1 for a in self.agents.values() if a.get("last_status") == "failed")
        degraded = sum(1 for a in self.agents.values() if a.get("last_status") == "degraded")
        unknown = sum(1 for a in self.agents.values() if a.get("last_status") == "unknown")
        
        # Determine overall status
        if failed > 0:
            # Check if any critical agents failed
            critical_failed = any(
                a.get("last_status") == "failed" and a.get("critical")
                for a in self.agents.values()
            )
            overall_status = "critical" if critical_failed else "degraded"
        elif degraded > 0:
            overall_status = "degraded"
        elif healthy == total_agents:
            overall_status = "healthy"
        else:
            overall_status = "unknown"
        
        return {
            "overall_status": overall_status,
            "total_agents": total_agents,
            "healthy": healthy,
            "degraded": degraded,
            "failed": failed,
            "unknown": unknown,
            "agents": self.list_agents(include_health=True)
        }


# Global instance
agent_registry = AgentRegistry()


# Register all agents (called during startup)
def register_all_agents():
    """Register all agents in the system."""
    
    # Calendar Agent
    agent_registry.register_agent(
        name="calendar",
        description="Schedule meetings and manage Google Calendar events",
        dependencies=["Google OAuth", "Supabase", "Qdrant"],
        critical=True,
        category="productivity"
    )
    
    # Finance Agent
    agent_registry.register_agent(
        name="finance",
        description="Track expenses, income, and financial analytics",
        dependencies=["Supabase"],
        critical=False,
        category="finance"
    )
    
    # Google Sheets Agent
    agent_registry.register_agent(
        name="sheets",
        description="Automatic expense logging and financial summaries in Google Sheets",
        dependencies=["Google OAuth", "Google Sheets API", "Google Drive API"],
        critical=False,
        category="finance"
    )
    
    # Weather Agent
    agent_registry.register_agent(
        name="weather",
        description="Real-time weather forecasts via Open-Meteo API",
        dependencies=["Open-Meteo API"],
        critical=False,
        category="information"
    )
    
    # Invoice Tracker Agent
    agent_registry.register_agent(
        name="invoice",
        description="Client invoice management and payment tracking",
        dependencies=["Supabase"],
        critical=False,
        category="finance"
    )
    
    # Client Manager Agent
    agent_registry.register_agent(
        name="client",
        description="Client relationship management and project tracking",
        dependencies=["Supabase"],
        critical=False,
        category="business"
    )
    
    # Notification Scheduler Agent
    agent_registry.register_agent(
        name="notification",
        description="Schedule and manage future notifications",
        dependencies=["Supabase", "Redis", "Telegram Bot API"],
        critical=False,
        category="productivity"
    )
    
    # Routine Optimizer Agent
    agent_registry.register_agent(
        name="routine",
        description="Learn work patterns and suggest optimal break times",
        dependencies=["Supabase"],
        critical=False,
        category="productivity"
    )
    
    # Habit Learner Agent
    agent_registry.register_agent(
        name="habit",
        description="Learn user habits and preferences over time",
        dependencies=["Supabase", "Qdrant"],
        critical=False,
        category="learning"
    )
    
    # Mirror Mode Agent
    agent_registry.register_agent(
        name="mirror",
        description="Learn and replicate user communication style",
        dependencies=["Supabase", "Qdrant", "OpenAI Embeddings"],
        critical=False,
        category="learning"
    )
    
    # Voice Transcription Agent
    agent_registry.register_agent(
        name="voice",
        description="Transcribe voice messages using Groq Whisper",
        dependencies=["Groq API", "Telegram Bot API"],
        critical=False,
        category="communication"
    )
    
    # Intent Router (Brain)
    agent_registry.register_agent(
        name="intent_router",
        description="Core AI brain for understanding and routing user requests",
        dependencies=["OpenAI GPT-4o", "Supabase", "Redis"],
        critical=True,
        category="core"
    )
    
    # Memory System
    agent_registry.register_agent(
        name="memory",
        description="Multi-layer memory system for context-aware conversations",
        dependencies=["Supabase", "Qdrant", "OpenAI Embeddings", "Redis"],
        critical=True,
        category="core"
    )
    
    logger.info(f"✅ Registered {len(agent_registry.agents)} agents")

