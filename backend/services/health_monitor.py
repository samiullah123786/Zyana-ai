"""Health Monitor - Self-healing system with auto-repair capabilities.

Monitors agent health, attempts automatic repairs, and logs issues for reporting.
"""
import logging
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import pytz

from clients.supabase_client import supabase_client
from services.agent_registry import agent_registry
from config import settings

logger = logging.getLogger(__name__)

PAKISTAN_TZ = pytz.timezone(settings.default_timezone)


class HealthMonitor:
    """Monitors system health and performs auto-repair."""
    
    def __init__(self):
        """Initialize Health Monitor."""
        self.enable_auto_repair = getattr(settings, 'enable_auto_repair', True)
        logger.info(f"✅ HealthMonitor initialized (auto-repair: {self.enable_auto_repair})")
    
    async def check_agent_health(
        self,
        agent_name: str
    ) -> Dict[str, Any]:
        """Check health of a specific agent.
        
        Args:
            agent_name: Agent name
            
        Returns:
            Dict with health status
        """
        agent = agent_registry.get_agent(agent_name)
        
        if not agent:
            return {
                "status": "unknown",
                "message": f"Agent '{agent_name}' not found in registry",
                "dependencies": {}
            }
        
        health_check_func = agent.get("health_check")
        
        if not health_check_func:
            return {
                "status": "unknown",
                "message": "No health check function defined",
                "dependencies": {}
            }
        
        try:
            # Run health check
            result = await health_check_func()
            
            # Update registry
            status = result.get("status", "unknown")
            agent_registry.update_health_status(
                agent_name,
                status,
                datetime.now(PAKISTAN_TZ)
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error checking {agent_name} health: {e}", exc_info=True)
            
            # Mark as failed
            agent_registry.update_health_status(
                agent_name,
                "failed",
                datetime.now(PAKISTAN_TZ)
            )
            
            return {
                "status": "failed",
                "message": str(e),
                "dependencies": {}
            }
    
    async def run_full_health_check(self) -> Dict[str, Any]:
        """Run health check on all registered agents.
        
        Returns:
            Dict with overall status and individual agent statuses
        """
        logger.info("🏥 Running full system health check...")
        
        start_time = datetime.now(PAKISTAN_TZ)
        results = {}
        errors = []
        
        # Check all agents
        for agent_name in agent_registry.agents.keys():
            try:
                result = await self.check_agent_health(agent_name)
                results[agent_name] = result
                
                if result["status"] == "failed":
                    errors.append({
                        "agent": agent_name,
                        "error": result.get("message", "Unknown error"),
                        "timestamp": datetime.now(PAKISTAN_TZ).isoformat()
                    })
            
            except Exception as e:
                logger.error(f"Error checking {agent_name}: {e}", exc_info=True)
                errors.append({
                    "agent": agent_name,
                    "error": str(e),
                    "timestamp": datetime.now(PAKISTAN_TZ).isoformat()
                })
        
        # Get overall status
        system_status = agent_registry.get_system_status()
        
        duration = (datetime.now(PAKISTAN_TZ) - start_time).total_seconds()
        
        logger.info(f"✅ Health check complete ({duration:.2f}s): {system_status['overall_status']}")
        
        return {
            "status": system_status["overall_status"],
            "duration_seconds": duration,
            "timestamp": datetime.now(PAKISTAN_TZ).isoformat(),
            "agents": results,
            "errors": errors,
            "summary": {
                "total": system_status["total_agents"],
                "healthy": system_status["healthy"],
                "degraded": system_status["degraded"],
                "failed": system_status["failed"],
                "unknown": system_status["unknown"]
            }
        }
    
    async def auto_repair_agent(
        self,
        agent_name: str,
        error: str
    ) -> Dict[str, Any]:
        """Attempt automatic repair of a failed agent.
        
        Args:
            agent_name: Agent name
            error: Error message
            
        Returns:
            Dict with repair result
        """
        if not self.enable_auto_repair:
            logger.info(f"⚠️  Auto-repair disabled, skipping {agent_name}")
            return {"success": False, "message": "Auto-repair disabled"}
        
        logger.info(f"🔧 Attempting auto-repair for {agent_name}: {error}")
        
        repair_strategies = []
        
        # Strategy 1: Retry with exponential backoff
        repair_strategies.append(self._strategy_retry)
        
        # Strategy 2: Clear cache (if Redis-related)
        if "redis" in error.lower() or "cache" in error.lower():
            repair_strategies.append(self._strategy_clear_cache)
        
        # Strategy 3: Refresh OAuth tokens (if auth-related)
        if "oauth" in error.lower() or "auth" in error.lower() or "token" in error.lower():
            repair_strategies.append(self._strategy_refresh_auth)
        
        # Strategy 4: Reconnect (if connection-related)
        if "connection" in error.lower() or "timeout" in error.lower():
            repair_strategies.append(self._strategy_reconnect)
        
        # Try each strategy
        for strategy in repair_strategies:
            try:
                result = await strategy(agent_name, error)
                if result.get("success"):
                    logger.info(f"✅ Auto-repair successful for {agent_name}: {result.get('message')}")
                    return result
            except Exception as e:
                logger.warning(f"Auto-repair strategy failed: {e}")
        
        logger.error(f"❌ All auto-repair strategies failed for {agent_name}")
        return {
            "success": False,
            "message": "All repair strategies failed",
            "strategies_tried": len(repair_strategies)
        }
    
    async def _strategy_retry(
        self,
        agent_name: str,
        error: str
    ) -> Dict[str, Any]:
        """Repair strategy: Retry with exponential backoff.
        
        Args:
            agent_name: Agent name
            error: Error message
            
        Returns:
            Dict with result
        """
        logger.info(f"🔄 Strategy: Retry with backoff for {agent_name}")
        
        max_retries = 3
        base_delay = 1  # seconds
        
        for attempt in range(max_retries):
            await asyncio.sleep(base_delay * (2 ** attempt))
            
            health_result = await self.check_agent_health(agent_name)
            
            if health_result.get("status") == "healthy":
                return {
                    "success": True,
                    "message": f"Recovered after {attempt + 1} retries",
                    "strategy": "retry"
                }
        
        return {"success": False, "message": "Retry strategy exhausted"}
    
    async def _strategy_clear_cache(
        self,
        agent_name: str,
        error: str
    ) -> Dict[str, Any]:
        """Repair strategy: Clear Redis cache.
        
        Args:
            agent_name: Agent name
            error: Error message
            
        Returns:
            Dict with result
        """
        logger.info(f"🗑️  Strategy: Clear cache for {agent_name}")
        
        try:
            # Import Redis client if available
            from redis import asyncio as aioredis
            redis_url = getattr(settings, 'redis_url', None)
            
            if redis_url:
                redis = await aioredis.from_url(redis_url)
                # Clear keys related to agent
                pattern = f"*{agent_name}*"
                keys = await redis.keys(pattern)
                if keys:
                    await redis.delete(*keys)
                    await redis.close()
                    
                    return {
                        "success": True,
                        "message": f"Cleared {len(keys)} cache keys",
                        "strategy": "clear_cache"
                    }
            
            return {"success": False, "message": "Redis not available"}
            
        except Exception as e:
            logger.error(f"Cache clear strategy failed: {e}")
            return {"success": False, "message": str(e)}
    
    async def _strategy_refresh_auth(
        self,
        agent_name: str,
        error: str
    ) -> Dict[str, Any]:
        """Repair strategy: Refresh OAuth tokens.
        
        Args:
            agent_name: Agent name
            error: Error message
            
        Returns:
            Dict with result
        """
        logger.info(f"🔑 Strategy: Refresh OAuth for {agent_name}")
        
        try:
            # Attempt to refresh tokens for calendar/sheets agents
            if agent_name in ["calendar", "sheets"]:
                from agents.calendar import calendar_agent
                
                if calendar_agent.credentials:
                    if calendar_agent.credentials.expired and calendar_agent.credentials.refresh_token:
                        from google.auth.transport.requests import Request
                        calendar_agent.credentials.refresh(Request())
                        calendar_agent._save_credentials(calendar_agent.credentials)
                        
                        return {
                            "success": True,
                            "message": "OAuth tokens refreshed",
                            "strategy": "refresh_auth"
                        }
            
            return {"success": False, "message": "No OAuth refresh available for this agent"}
            
        except Exception as e:
            logger.error(f"Auth refresh strategy failed: {e}")
            return {"success": False, "message": str(e)}
    
    async def _strategy_reconnect(
        self,
        agent_name: str,
        error: str
    ) -> Dict[str, Any]:
        """Repair strategy: Reconnect to service.
        
        Args:
            agent_name: Agent name
            error: Error message
            
        Returns:
            Dict with result
        """
        logger.info(f"🔌 Strategy: Reconnect for {agent_name}")
        
        # For now, just wait and retry
        await asyncio.sleep(2)
        
        health_result = await self.check_agent_health(agent_name)
        
        if health_result.get("status") == "healthy":
            return {
                "success": True,
                "message": "Reconnected successfully",
                "strategy": "reconnect"
            }
        
        return {"success": False, "message": "Reconnect failed"}
    
    async def log_health_status(
        self,
        agent_name: str,
        status: str,
        error: Optional[str] = None,
        auto_repair_attempted: bool = False,
        auto_repair_success: Optional[bool] = None
    ):
        """Log health status to database.
        
        Args:
            agent_name: Agent name
            status: Health status
            error: Optional error message
            auto_repair_attempted: Whether auto-repair was attempted
            auto_repair_success: Whether auto-repair succeeded
        """
        try:
            supabase_client.admin.table("system_health_log").insert({
                "agent_name": agent_name,
                "status": status,
                "error_message": error,
                "auto_repair_attempted": auto_repair_attempted,
                "auto_repair_success": auto_repair_success,
                "timestamp": datetime.now(PAKISTAN_TZ).isoformat()
            }).execute()
            
            logger.debug(f"💾 Logged health status for {agent_name}: {status}")
            
        except Exception as e:
            logger.error(f"Error logging health status: {e}", exc_info=True)
    
    async def generate_daily_summary(self) -> Dict[str, Any]:
        """Generate daily health summary from last 24 hours.
        
        Returns:
            Dict with summary data
        """
        try:
            # Get logs from last 24 hours
            since = (datetime.now(PAKISTAN_TZ) - timedelta(days=1)).isoformat()
            
            result = supabase_client.admin.table("system_health_log").select(
                "*"
            ).gte("timestamp", since).execute()
            
            logs = result.data if result.data else []
            
            # Count by status
            total_checks = len(logs)
            failed_checks = sum(1 for log in logs if log.get("status") == "failed")
            degraded_checks = sum(1 for log in logs if log.get("status") == "degraded")
            
            # Group issues by agent
            issues_by_agent = {}
            for log in logs:
                if log.get("status") in ["failed", "degraded"]:
                    agent = log.get("agent_name")
                    if agent not in issues_by_agent:
                        issues_by_agent[agent] = []
                    issues_by_agent[agent].append({
                        "status": log.get("status"),
                        "error": log.get("error_message"),
                        "auto_repaired": log.get("auto_repair_success", False),
                        "timestamp": log.get("timestamp")
                    })
            
            # Format issues for summary
            issues = []
            for agent, agent_issues in issues_by_agent.items():
                count = len(agent_issues)
                auto_repaired = sum(1 for issue in agent_issues if issue.get("auto_repaired"))
                
                issues.append({
                    "agent": agent,
                    "count": count,
                    "auto_repaired": auto_repaired,
                    "sample_error": agent_issues[0].get("error", "Unknown error")
                })
            
            summary = {
                "date": datetime.now(PAKISTAN_TZ).date().isoformat(),
                "total_checks": total_checks,
                "failed_checks": failed_checks,
                "degraded_checks": degraded_checks,
                "issues": issues,
                "overall_status": "healthy" if failed_checks == 0 else ("degraded" if failed_checks < 5 else "critical")
            }
            
            logger.info(f"📊 Generated daily summary: {total_checks} checks, {len(issues)} issues")
            
            return summary
            
        except Exception as e:
            logger.error(f"Error generating daily summary: {e}", exc_info=True)
            return {
                "date": datetime.now(PAKISTAN_TZ).date().isoformat(),
                "error": str(e)
            }


# Global instance
health_monitor = HealthMonitor()

