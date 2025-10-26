"""Weekly Health Check Worker - Comprehensive system health check.

Runs every Sunday at 11 PM Pakistan time.
Performs full health check of all agents and logs results.
"""
import logging
import asyncio
from datetime import datetime, timedelta
import pytz

from services.health_monitor import health_monitor
from services.agent_registry import agent_registry
from services.telegram_bot import send_telegram_message
from config import settings

logger = logging.getLogger(__name__)

PAKISTAN_TZ = pytz.timezone(settings.default_timezone)


async def run_weekly_health_check(telegram_user_id: str = "5842356693"):
    """Run comprehensive weekly health check.
    
    Args:
        telegram_user_id: Telegram user ID for critical alerts
    """
    try:
        logger.info("🔍 Starting weekly health check...")
        
        # Run full health check
        report = await health_monitor.run_full_health_check()
        
        # Log all results
        for agent_name, result in report.get("agents", {}).items():
            await health_monitor.log_health_status(
                agent_name=agent_name,
                status=result.get("status", "unknown"),
                error=result.get("message") if result.get("status") == "failed" else None,
                auto_repair_attempted=False,
                auto_repair_success=None
            )
        
        # Check for critical failures
        critical_agents = agent_registry.get_critical_agents()
        critical_failures = []
        
        for agent_name in critical_agents:
            if agent_name in report.get("agents", {}):
                if report["agents"][agent_name].get("status") == "failed":
                    critical_failures.append(agent_name)
        
        # Send immediate alert if critical failures detected
        if critical_failures:
            alert_message = f"""🚨 **CRITICAL ALERT - Weekly Health Check**

⚠️  Critical system failures detected:

{chr(10).join(f'- {agent.capitalize()}' for agent in critical_failures)}

**Action Required:** Please check system logs immediately.

Timestamp: {datetime.now(PAKISTAN_TZ).strftime('%Y-%m-%d %H:%M:%S')} PKT"""
            
            await send_telegram_message(telegram_user_id, alert_message)
            logger.error(f"🚨 Critical failures detected: {critical_failures}")
        
        # Log summary
        summary = report.get("summary", {})
        logger.info(
            f"✅ Weekly health check complete: "
            f"{summary.get('healthy', 0)}/{summary.get('total', 0)} agents healthy"
        )
        
    except Exception as e:
        logger.error(f"❌ Error in weekly health check: {e}", exc_info=True)


async def run_weekly_worker():
    """Main function to run weekly health check worker."""
    logger.info("🕐 Starting Weekly Health Check Worker...")
    
    while True:
        try:
            # Get current time in Pakistan
            now = datetime.now(PAKISTAN_TZ)
            
            # Target: Next Sunday at 11 PM
            days_until_sunday = (6 - now.weekday()) % 7  # 6 = Sunday
            if days_until_sunday == 0 and now.hour >= 23:
                # If it's Sunday after 11 PM, schedule for next Sunday
                days_until_sunday = 7
            
            target = now + timedelta(days=days_until_sunday)
            target = target.replace(hour=23, minute=0, second=0, microsecond=0)
            
            # Calculate wait time
            wait_seconds = (target - now).total_seconds()
            
            logger.info(
                f"⏰ Next weekly health check at {target.strftime('%Y-%m-%d %H:%M:%S')} "
                f"({wait_seconds/3600:.1f} hours)"
            )
            
            # Wait until target time
            await asyncio.sleep(wait_seconds)
            
            # Run health check
            await run_weekly_health_check()
            
        except Exception as e:
            logger.error(f"❌ Error in weekly worker loop: {e}", exc_info=True)
            # Wait 1 hour before retry
            await asyncio.sleep(3600)


if __name__ == "__main__":
    # For testing
    asyncio.run(run_weekly_health_check())

