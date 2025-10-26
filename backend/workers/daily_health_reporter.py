"""Daily Health Reporter - Sends daily health summary to user via Telegram.

Runs every day at 11:30 PM Pakistan time.
"""
import logging
import asyncio
from datetime import datetime
import pytz

from services.health_monitor import health_monitor
from services.telegram_bot import send_telegram_message
from clients.supabase_client import supabase_client
from config import settings

logger = logging.getLogger(__name__)

PAKISTAN_TZ = pytz.timezone(settings.default_timezone)


async def send_daily_health_report(telegram_user_id: str = "5842356693"):
    """Generate and send daily health report via Telegram.
    
    Args:
        telegram_user_id: Telegram user ID to send report to (default: Sami's ID)
    """
    try:
        logger.info("🏥 Generating daily health report...")
        
        # Generate summary
        summary = await health_monitor.generate_daily_summary()
        
        # Check if already sent today
        today = datetime.now(PAKISTAN_TZ).date().isoformat()
        existing = supabase_client.admin.table("daily_health_summary").select(
            "summary_sent"
        ).eq("date", today).execute()
        
        if existing.data and existing.data[0].get("summary_sent"):
            logger.info(f"✅ Health report already sent today ({today})")
            return
        
        # Format message
        message = format_health_report(summary)
        
        # Send via Telegram
        await send_telegram_message(telegram_user_id, message)
        
        # Save summary to database
        supabase_client.admin.table("daily_health_summary").upsert({
            "date": today,
            "total_checks": summary.get("total_checks", 0),
            "failed_checks": summary.get("failed_checks", 0),
            "issues": summary.get("issues", []),
            "summary_sent": True
        }).execute()
        
        logger.info(f"✅ Daily health report sent successfully")
        
    except Exception as e:
        logger.error(f"❌ Error sending daily health report: {e}", exc_info=True)


def format_health_report(summary: dict) -> str:
    """Format health summary into human-readable message.
    
    Args:
        summary: Health summary dict
        
    Returns:
        Formatted message string
    """
    date_str = summary.get("date", datetime.now(PAKISTAN_TZ).date().isoformat())
    total_checks = summary.get("total_checks", 0)
    failed_checks = summary.get("failed_checks", 0)
    overall_status = summary.get("overall_status", "unknown")
    issues = summary.get("issues", [])
    
    # Status emoji
    if overall_status == "healthy":
        status_emoji = "✅"
        status_text = "Healthy"
    elif overall_status == "degraded":
        status_emoji = "⚠️ "
        status_text = "Degraded"
    else:
        status_emoji = "🔴"
        status_text = "Critical"
    
    # Build message
    message = f"""🏥 **Daily Health Report - {date_str}**

{status_emoji} **System Status:** {status_text}
📊 **Checks:** {total_checks} performed, {failed_checks} issues"""
    
    if issues:
        message += "\n\n**⚠️  Issues Detected:**"
        for i, issue in enumerate(issues, 1):
            agent = issue.get("agent", "Unknown")
            count = issue.get("count", 0)
            auto_repaired = issue.get("auto_repaired", 0)
            error = issue.get("sample_error", "Unknown error")[:50]
            
            repair_status = "✅" if auto_repaired > 0 else "❌"
            
            message += f"\n{i}. **{agent.capitalize()}:** {error}... ({count}x) - Auto-repaired: {repair_status}"
    else:
        message += "\n\n✨ **No issues detected!**"
    
    message += "\n\nAll systems operational. Sleep well, Sami! 😊"
    
    return message


async def run_daily_reporter():
    """Main function to run daily health reporter."""
    logger.info("🕐 Starting Daily Health Reporter...")
    
    while True:
        try:
            # Get current time in Pakistan
            now = datetime.now(PAKISTAN_TZ)
            
            # Target time: 11:30 PM
            target_hour = int(getattr(settings, 'daily_summary_time', '23:30').split(':')[0])
            target_minute = int(getattr(settings, 'daily_summary_time', '23:30').split(':')[1])
            
            # If past target time today, wait until tomorrow
            target = now.replace(hour=target_hour, minute=target_minute, second=0, microsecond=0)
            
            if now > target:
                # Add one day
                from datetime import timedelta
                target += timedelta(days=1)
            
            # Calculate wait time
            wait_seconds = (target - now).total_seconds()
            
            logger.info(f"⏰ Next health report at {target.strftime('%Y-%m-%d %H:%M:%S')} ({wait_seconds/3600:.1f} hours)")
            
            # Wait until target time
            await asyncio.sleep(wait_seconds)
            
            # Send report
            await send_daily_health_report()
            
        except Exception as e:
            logger.error(f"❌ Error in daily reporter loop: {e}", exc_info=True)
            # Wait 1 hour before retry
            await asyncio.sleep(3600)


if __name__ == "__main__":
    # For testing
    asyncio.run(send_daily_health_report())

