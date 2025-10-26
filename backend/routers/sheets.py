"""Google Sheets router for Smart Finance Assistant.

Provides endpoints for:
- Creating monthly finance sheets
- Logging expenses/income
- Reading and summarizing financial data
- Testing Google Sheets integration
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Optional, List
from datetime import datetime
import logging

from services.google_sheets_service import google_sheets_service
from pydantic import BaseModel

logger = logging.getLogger(__name__)
router = APIRouter()


class ExpenseEntry(BaseModel):
    """Expense/Income entry model."""
    date: str
    category: str
    transaction_type: str  # "expense" or "income"
    amount: float
    description: Optional[str] = ""
    business: Optional[str] = ""


@router.get("/test")
async def test_google_sheets():
    """Test Google Sheets integration.
    
    Creates a test sheet and appends a sample entry.
    
    Returns:
        Test results with sheet URL
    """
    try:
        logger.info("🧪 Testing Google Sheets integration...")
        
        # Test 1: Create monthly sheet
        sheet_result = await google_sheets_service.create_monthly_sheet(
            month_name="Test",
            year=2025
        )
        
        logger.info(f"✅ Test sheet created: {sheet_result['sheet_url']}")
        
        # Test 2: Append sample entry
        entry_result = await google_sheets_service.append_expense_entry(
            sheet_id=sheet_result['sheet_id'],
            date_str=datetime.now().strftime("%Y-%m-%d"),
            category="Test",
            transaction_type="expense",
            amount=100.0,
            description="Test expense from Zyana API",
            business="Testing"
        )
        
        logger.info(f"✅ Test entry appended: {entry_result['updated_range']}")
        
        # Test 3: Read expenses
        expenses = await google_sheets_service.read_expenses(
            sheet_id=sheet_result['sheet_id']
        )
        
        logger.info(f"✅ Read {len(expenses)} entries from test sheet")
        
        # Test 4: Get summary
        summary = await google_sheets_service.get_monthly_summary(
            sheet_id=sheet_result['sheet_id']
        )
        
        logger.info(f"✅ Generated summary: {summary['summary_text']}")
        
        return {
            "success": True,
            "message": "Google Sheets integration test passed! ✅",
            "sheet": sheet_result,
            "test_entry": entry_result,
            "expenses": expenses,
            "summary": summary
        }
        
    except Exception as e:
        logger.error(f"❌ Google Sheets test failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sheets/create")
async def create_monthly_sheet(
    month_name: Optional[str] = None,
    year: Optional[int] = None
):
    """Create a new monthly finance sheet.
    
    Args:
        month_name: Month name (e.g., "October"). Defaults to current month.
        year: Year (e.g., 2025). Defaults to current year.
        
    Returns:
        Sheet information with URL
    """
    try:
        result = await google_sheets_service.create_monthly_sheet(
            month_name=month_name,
            year=year
        )
        
        return {
            "success": True,
            "message": f"✅ Created finance sheet for {result['month']} {result['year']}",
            "sheet": result
        }
        
    except Exception as e:
        logger.error(f"Error creating monthly sheet: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/expenses/add")
async def add_expense(entry: ExpenseEntry, background_tasks: BackgroundTasks):
    """Add an expense or income entry to the current month's sheet.
    
    Args:
        entry: Expense/income entry data
        background_tasks: Background tasks for async processing
        
    Returns:
        Success status and entry details
    """
    try:
        # Get or create current month's sheet
        now = datetime.now()
        month_name = now.strftime("%B")
        year = now.year
        
        sheet_result = await google_sheets_service.create_monthly_sheet(
            month_name=month_name,
            year=year
        )
        
        # Append entry
        result = await google_sheets_service.append_expense_entry(
            sheet_id=sheet_result['sheet_id'],
            date_str=entry.date,
            category=entry.category,
            transaction_type=entry.transaction_type,
            amount=entry.amount,
            description=entry.description,
            business=entry.business
        )
        
        logger.info(f"✅ Added {entry.transaction_type}: {entry.category} - Rs {entry.amount}")
        
        return {
            "success": True,
            "message": f"✅ Logged {entry.transaction_type} of Rs {entry.amount} in {entry.category}",
            "sheet_url": sheet_result['sheet_url'],
            "entry": result['row_data']
        }
        
    except Exception as e:
        logger.error(f"Error adding expense: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/expenses")
async def get_expenses(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    category: Optional[str] = None,
    month_name: Optional[str] = None,
    year: Optional[int] = None
):
    """Get expenses from a specific month with optional filters.
    
    Args:
        start_date: Filter by start date (YYYY-MM-DD)
        end_date: Filter by end date (YYYY-MM-DD)
        category: Filter by category
        month_name: Month name (defaults to current month)
        year: Year (defaults to current year)
        
    Returns:
        List of expenses
    """
    try:
        # Default to current month
        now = datetime.now()
        if not month_name:
            month_name = now.strftime("%B")
        if not year:
            year = now.year
        
        # Find sheet
        sheet_name = f"Finance_{month_name}_{year}"
        sheet_info = await google_sheets_service.find_sheet_by_name(sheet_name)
        
        if not sheet_info:
            return {
                "success": False,
                "message": f"No finance sheet found for {month_name} {year}",
                "expenses": []
            }
        
        # Read expenses
        expenses = await google_sheets_service.read_expenses(
            sheet_id=sheet_info['sheet_id'],
            start_date=start_date,
            end_date=end_date,
            category=category
        )
        
        return {
            "success": True,
            "message": f"Found {len(expenses)} transactions",
            "sheet_url": sheet_info['sheet_url'],
            "expenses": expenses,
            "count": len(expenses)
        }
        
    except Exception as e:
        logger.error(f"Error getting expenses: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/summary")
async def get_monthly_summary(
    month_name: Optional[str] = None,
    year: Optional[int] = None
):
    """Get monthly financial summary with insights.
    
    Args:
        month_name: Month name (defaults to current month)
        year: Year (defaults to current year)
        
    Returns:
        Financial summary with totals and insights
    """
    try:
        # Default to current month
        now = datetime.now()
        if not month_name:
            month_name = now.strftime("%B")
        if not year:
            year = now.year
        
        # Find sheet
        sheet_name = f"Finance_{month_name}_{year}"
        sheet_info = await google_sheets_service.find_sheet_by_name(sheet_name)
        
        if not sheet_info:
            return {
                "success": False,
                "message": f"No finance sheet found for {month_name} {year}",
                "summary": None
            }
        
        # Get summary
        summary = await google_sheets_service.get_monthly_summary(
            sheet_id=sheet_info['sheet_id']
        )
        
        logger.info(f"📊 Generated summary for {month_name} {year}")
        
        return {
            "success": True,
            "message": f"Summary for {month_name} {year}",
            "sheet_url": sheet_info['sheet_url'],
            "summary": summary
        }
        
    except Exception as e:
        logger.error(f"Error getting summary: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sheets/list")
async def list_finance_sheets():
    """List all finance sheets in the Zyana Finance Logs folder.
    
    Returns:
        List of all finance sheets
    """
    try:
        if not google_sheets_service.drive_service:
            raise HTTPException(
                status_code=503,
                detail="Google Drive not connected. Please authorize Google account first."
            )
        
        # Get folder ID
        folder_id = await google_sheets_service.ensure_finance_folder()
        
        # List all sheets in folder
        query = f"'{folder_id}' in parents and mimeType='application/vnd.google-apps.spreadsheet' and trashed=false"
        response = google_sheets_service.drive_service.files().list(
            q=query,
            spaces='drive',
            fields='files(id, name, webViewLink, createdTime, modifiedTime)',
            orderBy='modifiedTime desc'
        ).execute()
        
        files = response.get('files', [])
        
        return {
            "success": True,
            "message": f"Found {len(files)} finance sheets",
            "sheets": files,
            "count": len(files)
        }
        
    except Exception as e:
        logger.error(f"Error listing sheets: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

