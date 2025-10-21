"""Background job definitions for Zyana."""
import logging
from datetime import datetime, timedelta, date
from typing import Optional

from clients.supabase_client import supabase_client
from memory.embed import memory_service
from services.telegram_bot import send_telegram_message

logger = logging.getLogger(__name__)


async def weekly_pl_summary_job(user_id: int = 1, telegram_chat_id: Optional[str] = None):
    """Generate and send weekly P&L summary.
    
    Args:
        user_id: User ID
        telegram_chat_id: Telegram chat ID to send summary to
    """
    logger.info("Running weekly P&L summary job")
    
    try:
        # Get date range (last 7 days)
        end_date = date.today()
        start_date = end_date - timedelta(days=7)
        
        # Get all businesses
        businesses_result = supabase_client.admin.table("businesses").select("*").execute()
        
        summary_lines = [f"📊 Weekly Summary ({start_date} to {end_date})\n"]
        
        for business in businesses_result.data:
            # Get transactions for this business
            transactions_result = supabase_client.admin.table("transactions").select(
                "type, amount"
            ).eq("business_id", business["id"]).gte(
                "date", start_date.isoformat()
            ).lte("date", end_date.isoformat()).execute()
            
            income = sum(
                t["amount"] for t in transactions_result.data if t["type"] == "income"
            )
            expenses = sum(
                t["amount"] for t in transactions_result.data if t["type"] == "expense"
            )
            
            if income > 0 or expenses > 0:
                summary_lines.append(
                    f"\n{business['name']}:\n"
                    f"  Income: PKR {income:,.0f}\n"
                    f"  Expenses: PKR {expenses:,.0f}\n"
                    f"  Net: PKR {income - expenses:,.0f}"
                )
        
        summary_text = "\n".join(summary_lines)
        
        # Send via Telegram if chat_id provided
        if telegram_chat_id:
            await send_telegram_message(telegram_chat_id, summary_text)
        
        logger.info("Weekly P&L summary completed")
        return summary_text
        
    except Exception as e:
        logger.error(f"Error in weekly P&L summary: {e}")
        raise


async def monthly_pl_summary_job(user_id: int = 1, telegram_chat_id: Optional[str] = None):
    """Generate and send monthly P&L summary.
    
    Args:
        user_id: User ID
        telegram_chat_id: Telegram chat ID to send summary to
    """
    logger.info("Running monthly P&L summary job")
    
    try:
        # Get date range (last 30 days)
        end_date = date.today()
        start_date = end_date - timedelta(days=30)
        
        businesses_result = supabase_client.admin.table("businesses").select("*").execute()
        
        summary_lines = [f"📈 Monthly Summary ({start_date} to {end_date})\n"]
        
        total_income = 0
        total_expenses = 0
        
        for business in businesses_result.data:
            transactions_result = supabase_client.admin.table("transactions").select(
                "type, amount, category"
            ).eq("business_id", business["id"]).gte(
                "date", start_date.isoformat()
            ).lte("date", end_date.isoformat()).execute()
            
            income = sum(
                t["amount"] for t in transactions_result.data if t["type"] == "income"
            )
            expenses = sum(
                t["amount"] for t in transactions_result.data if t["type"] == "expense"
            )
            
            total_income += income
            total_expenses += expenses
            
            if income > 0 or expenses > 0:
                summary_lines.append(
                    f"\n{business['name']}:\n"
                    f"  Income: PKR {income:,.0f}\n"
                    f"  Expenses: PKR {expenses:,.0f}\n"
                    f"  Net: PKR {income - expenses:,.0f}"
                )
        
        summary_lines.append(
            f"\n📊 TOTAL:\n"
            f"  Income: PKR {total_income:,.0f}\n"
            f"  Expenses: PKR {total_expenses:,.0f}\n"
            f"  Net: PKR {total_income - total_expenses:,.0f}"
        )
        
        summary_text = "\n".join(summary_lines)
        
        if telegram_chat_id:
            await send_telegram_message(telegram_chat_id, summary_text)
        
        logger.info("Monthly P&L summary completed")
        return summary_text
        
    except Exception as e:
        logger.error(f"Error in monthly P&L summary: {e}")
        raise


async def google_calendar_sync_job(user_id: int = 1):
    """Sync events from Google Calendar.
    
    Args:
        user_id: User ID
    """
    logger.info("Running Google Calendar sync job")
    
    try:
        from agents.calendar import calendar_agent
        
        result = await calendar_agent.sync_from_google()
        logger.info(f"Google Calendar sync completed: {result}")
        return result
        
    except Exception as e:
        logger.error(f"Error in Google Calendar sync: {e}")
        raise


async def nightly_summarizer_job(user_id: int = 1):
    """Create nightly summary of the day's activities.
    
    Args:
        user_id: User ID
    """
    logger.info("Running nightly summarizer job")
    
    try:
        # Summarize yesterday
        target_date = date.today() - timedelta(days=1)
        
        await memory_service.create_daily_summary(target_date, user_id)
        
        logger.info(f"Nightly summary completed for {target_date}")
        
    except Exception as e:
        logger.error(f"Error in nightly summarizer: {e}")
        raise


async def embed_batch_job(table: str, limit: int = 100):
    """Batch embed records from a table.
    
    Args:
        table: Table name (transactions, events, etc.)
        limit: Number of records to process
    """
    logger.info(f"Running batch embed job for {table}")
    
    try:
        # Get records without embeddings
        result = supabase_client.admin.table(table).select("*").limit(limit).execute()
        
        for record in result.data:
            # Create content string
            if table == "transactions":
                content = (
                    f"Transaction: {record['type']} {record['currency']} {record['amount']} "
                    f"- {record['description']} on {record['date']}"
                )
            elif table == "events":
                content = f"Event: {record['title']} on {record['start_time']}"
            else:
                content = str(record)
            
            # Add to memory
            await memory_service.add_memory(
                content=content,
                metadata={
                    "table": table,
                    "row_id": record["id"],
                    "date": record.get("date") or record.get("start_time"),
                    "business": None
                }
            )
        
        logger.info(f"Batch embedded {len(result.data)} records from {table}")
        
    except Exception as e:
        logger.error(f"Error in batch embed job: {e}")
        raise

