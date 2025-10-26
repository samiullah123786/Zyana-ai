"""Smart Finance Agent for Google Sheets integration.

Handles natural language commands for:
- Logging expenses/income to Google Sheets
- Reading and filtering financial data
- Generating monthly summaries
"""
import logging
from datetime import datetime
from typing import Dict, Any, Optional
import pytz

from services.google_sheets_service import google_sheets_service
from config import settings

logger = logging.getLogger(__name__)

PAKISTAN_TZ = pytz.timezone(settings.default_timezone)


class SmartFinanceAgent:
    """Agent for managing finances with Google Sheets."""
    
    def __init__(self):
        """Initialize Smart Finance Agent."""
        logger.info("✅ SmartFinanceAgent initialized")
    
    async def log_expense(
        self,
        intent_result: Dict[str, Any],
        user_id: str
    ) -> Dict[str, Any]:
        """Log an expense to Google Sheets.
        
        Args:
            intent_result: Parsed intent with parameters
            user_id: User identifier
            
        Returns:
            Result dict with success status and message
        """
        try:
            params = intent_result.get('parameters', {})
            
            # Extract parameters
            amount = params.get('amount')
            category = params.get('category', 'Uncategorized')
            description = params.get('description', '')
            business = params.get('business', '')
            
            if not amount:
                return {
                    'success': False,
                    'message': "I need the amount to log the expense. How much was it?"
                }
            
            # Get current date
            now = datetime.now(PAKISTAN_TZ)
            date_str = now.strftime("%Y-%m-%d")
            
            # Get or create current month's sheet
            month_name = now.strftime("%B")
            year = now.year
            
            sheet_result = await google_sheets_service.create_monthly_sheet(
                month_name=month_name,
                year=year
            )
            
            # Append entry
            await google_sheets_service.append_expense_entry(
                sheet_id=sheet_result['sheet_id'],
                date_str=date_str,
                category=category,
                transaction_type="expense",
                amount=amount,
                description=description,
                business=business
            )
            
            logger.info(f"✅ Logged expense: {category} - Rs {amount}")
            
            message = f"✅ Logged expense of Rs {amount:,.0f} in {category}"
            if business:
                message += f" ({business})"
            message += f"\n\n📊 View sheet: {sheet_result['sheet_url']}"
            
            return {
                'success': True,
                'message': message,
                'sheet_url': sheet_result['sheet_url']
            }
            
        except Exception as e:
            logger.error(f"❌ Error logging expense: {e}", exc_info=True)
            return {
                'success': False,
                'message': "Sorry, I couldn't log the expense to Google Sheets. Please try again or check your Google connection."
            }
    
    async def log_income(
        self,
        intent_result: Dict[str, Any],
        user_id: str
    ) -> Dict[str, Any]:
        """Log income to Google Sheets.
        
        Args:
            intent_result: Parsed intent with parameters
            user_id: User identifier
            
        Returns:
            Result dict with success status and message
        """
        try:
            params = intent_result.get('parameters', {})
            
            # Extract parameters
            amount = params.get('amount')
            category = params.get('category', 'Income')
            description = params.get('description', '')
            business = params.get('business', '')
            
            if not amount:
                return {
                    'success': False,
                    'message': "I need the amount to log the income. How much was it?"
                }
            
            # Get current date
            now = datetime.now(PAKISTAN_TZ)
            date_str = now.strftime("%Y-%m-%d")
            
            # Get or create current month's sheet
            month_name = now.strftime("%B")
            year = now.year
            
            sheet_result = await google_sheets_service.create_monthly_sheet(
                month_name=month_name,
                year=year
            )
            
            # Append entry
            await google_sheets_service.append_expense_entry(
                sheet_id=sheet_result['sheet_id'],
                date_str=date_str,
                category=category,
                transaction_type="income",
                amount=amount,
                description=description,
                business=business
            )
            
            logger.info(f"✅ Logged income: {category} - Rs {amount}")
            
            message = f"✅ Logged income of Rs {amount:,.0f}"
            if category and category != 'Income':
                message += f" ({category})"
            if business:
                message += f" from {business}"
            message += f"\n\n📊 View sheet: {sheet_result['sheet_url']}"
            
            return {
                'success': True,
                'message': message,
                'sheet_url': sheet_result['sheet_url']
            }
            
        except Exception as e:
            logger.error(f"❌ Error logging income: {e}", exc_info=True)
            return {
                'success': False,
                'message': "Sorry, I couldn't log the income to Google Sheets. Please try again or check your Google connection."
            }
    
    async def show_expenses(
        self,
        intent_result: Dict[str, Any],
        user_id: str
    ) -> Dict[str, Any]:
        """Show expenses from Google Sheets.
        
        Args:
            intent_result: Parsed intent with parameters
            user_id: User identifier
            
        Returns:
            Result dict with expenses list
        """
        try:
            params = intent_result.get('parameters', {})
            category = params.get('category')
            
            # Default to current month
            now = datetime.now(PAKISTAN_TZ)
            month_name = now.strftime("%B")
            year = now.year
            
            # Find sheet
            sheet_name = f"Finance_{month_name}_{year}"
            sheet_info = await google_sheets_service.find_sheet_by_name(sheet_name)
            
            if not sheet_info:
                return {
                    'success': False,
                    'message': f"No finance sheet found for {month_name} {year}. Start logging expenses and I'll create one!"
                }
            
            # Read expenses
            expenses = await google_sheets_service.read_expenses(
                sheet_id=sheet_info['sheet_id'],
                category=category
            )
            
            if not expenses:
                message = f"No expenses found"
                if category:
                    message += f" in {category}"
                message += f" for {month_name} {year}"
                
                return {
                    'success': True,
                    'message': message,
                    'expenses': []
                }
            
            # Format message
            message = f"📊 **Expenses for {month_name} {year}**"
            if category:
                message += f" ({category})"
            message += f"\n\nFound {len(expenses)} transactions:\n\n"
            
            # Show first 5 expenses
            for i, exp in enumerate(expenses[:5], 1):
                message += f"{i}. {exp['date']} - {exp['category']}: Rs {exp['amount']:,.0f}"
                if exp['description']:
                    message += f" ({exp['description']})"
                message += "\n"
            
            if len(expenses) > 5:
                message += f"\n...and {len(expenses) - 5} more"
            
            message += f"\n\n📊 View full sheet: {sheet_info['sheet_url']}"
            
            return {
                'success': True,
                'message': message,
                'expenses': expenses,
                'sheet_url': sheet_info['sheet_url']
            }
            
        except Exception as e:
            logger.error(f"❌ Error showing expenses: {e}", exc_info=True)
            return {
                'success': False,
                'message': "Sorry, I couldn't fetch expenses from Google Sheets. Please try again or check your Google connection."
            }
    
    async def summarize_finances(
        self,
        intent_result: Dict[str, Any],
        user_id: str
    ) -> Dict[str, Any]:
        """Generate financial summary from Google Sheets.
        
        Args:
            intent_result: Parsed intent with parameters
            user_id: User identifier
            
        Returns:
            Result dict with summary
        """
        try:
            # Default to current month
            now = datetime.now(PAKISTAN_TZ)
            month_name = now.strftime("%B")
            year = now.year
            
            # Find sheet
            sheet_name = f"Finance_{month_name}_{year}"
            sheet_info = await google_sheets_service.find_sheet_by_name(sheet_name)
            
            if not sheet_info:
                return {
                    'success': False,
                    'message': f"No finance sheet found for {month_name} {year}. Start logging expenses and I'll create one!"
                }
            
            # Get summary
            summary = await google_sheets_service.get_monthly_summary(
                sheet_id=sheet_info['sheet_id']
            )
            
            if summary['transaction_count'] == 0:
                return {
                    'success': True,
                    'message': f"No transactions recorded for {month_name} {year} yet.",
                    'summary': summary
                }
            
            # Format detailed message
            message = summary['summary_text']
            
            # Add category breakdown
            if summary['by_category']:
                message += "\n\n**By Category:**"
                for cat, data in sorted(summary['by_category'].items(), key=lambda x: x[1]['expense'], reverse=True)[:5]:
                    if data['expense'] > 0:
                        message += f"\n• {cat}: Rs {data['expense']:,.0f}"
            
            message += f"\n\n📊 View full sheet: {sheet_info['sheet_url']}"
            
            logger.info(f"📊 Generated summary for {month_name} {year}")
            
            return {
                'success': True,
                'message': message,
                'summary': summary,
                'sheet_url': sheet_info['sheet_url']
            }
            
        except Exception as e:
            logger.error(f"❌ Error generating summary: {e}", exc_info=True)
            return {
                'success': False,
                'message': "Sorry, I couldn't generate the financial summary. Please try again or check your Google connection."
            }


# Global instance
smart_finance_agent = SmartFinanceAgent()

