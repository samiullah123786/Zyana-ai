"""Google Sheets Service for Smart Finance Assistant.

Extends the existing Google OAuth system to support Sheets and Drive APIs.
Automatically creates monthly finance sheets and logs expenses/income.
"""
import logging
import json
from datetime import datetime, date
from typing import Dict, Any, Optional, List, Tuple
from pathlib import Path
import pytz

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from clients.supabase_client import supabase_client
from config import settings

logger = logging.getLogger(__name__)

# Google API Scopes (extends calendar scopes)
SCOPES = [
    'https://www.googleapis.com/auth/calendar',
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive.file'
]

# Default timezone
PAKISTAN_TZ = pytz.timezone(settings.default_timezone)


class GoogleSheetsFinanceService:
    """Service for managing finance data in Google Sheets."""
    
    def __init__(self):
        """Initialize Google Sheets Finance Service."""
        self.credentials = None
        self.sheets_service = None
        self.drive_service = None
        self.folder_id = getattr(settings, 'google_sheets_folder_id', None)
        self._load_credentials()
    
    def _load_credentials(self, user_id: int = 1):
        """Load Google OAuth credentials from Supabase.
        
        Args:
            user_id: User ID to load credentials for
        """
        try:
            # Load from Supabase (same as calendar agent)
            result = supabase_client.admin.table("users").select(
                "google_credentials, google_calendar_connected"
            ).eq("id", user_id).execute()
            
            if result.data and result.data[0].get("google_credentials"):
                creds_json = result.data[0]["google_credentials"]
                self.credentials = Credentials.from_authorized_user_info(
                    json.loads(creds_json), SCOPES
                )
                
                # Refresh if expired
                if self.credentials and self.credentials.expired and self.credentials.refresh_token:
                    self.credentials.refresh(Request())
                    self._save_credentials(self.credentials, user_id)
                
                # Build services
                self.sheets_service = build('sheets', 'v4', credentials=self.credentials)
                self.drive_service = build('drive', 'v3', credentials=self.credentials)
                
                logger.info(f"✅ Loaded Google Sheets credentials from Supabase for user {user_id}")
                return
            
            # Fallback: Try to find any user with credentials
            logger.warning(f"⚠️  No credentials for user {user_id}, checking for any available credentials...")
            fallback_result = supabase_client.admin.table("users").select(
                "id, google_credentials, google_calendar_connected"
            ).eq("google_calendar_connected", True).limit(1).execute()
            
            if fallback_result.data and fallback_result.data[0].get("google_credentials"):
                creds_json = fallback_result.data[0]["google_credentials"]
                self.credentials = Credentials.from_authorized_user_info(
                    json.loads(creds_json), SCOPES
                )
                
                # Refresh if expired
                if self.credentials and self.credentials.expired and self.credentials.refresh_token:
                    self.credentials.refresh(Request())
                
                # Build services
                self.sheets_service = build('sheets', 'v4', credentials=self.credentials)
                self.drive_service = build('drive', 'v3', credentials=self.credentials)
                
                fallback_user_id = fallback_result.data[0]["id"]
                logger.info(f"✅ Using fallback Google Sheets credentials from user {fallback_user_id}")
            else:
                logger.info(f"ℹ️  No Google Sheets credentials found in system")
                self.credentials = None
                
        except Exception as e:
            logger.error(f"Error loading credentials from Supabase: {e}", exc_info=True)
            self.credentials = None
    
    def _save_credentials(self, creds: Credentials, user_id: int = 1):
        """Save credentials to Supabase.
        
        Args:
            creds: Google OAuth credentials
            user_id: User ID to save credentials for
        """
        try:
            creds_json = creds.to_json()
            
            supabase_client.admin.table("users").update({
                "google_credentials": creds_json,
                "google_calendar_connected": True,
                "google_sheets_connected": True
            }).eq("id", user_id).execute()
            
            logger.info(f"✅ Saved Google Sheets credentials to Supabase for user {user_id}")
            
        except Exception as e:
            logger.error(f"Error saving credentials to Supabase: {e}", exc_info=True)
    
    async def ensure_finance_folder(self) -> str:
        """Ensure the 'Zyana Finance Logs' folder exists in Google Drive.
        
        Returns:
            Folder ID
        """
        if not self.drive_service:
            raise Exception("Google Drive service not initialized. Please connect Google account first.")
        
        try:
            # If folder ID is set in environment, use it
            if self.folder_id:
                logger.info(f"✅ Using configured folder ID: {self.folder_id}")
                return self.folder_id
            
            # Search for existing folder
            query = "name='Zyana Finance Logs' and mimeType='application/vnd.google-apps.folder' and trashed=false"
            response = self.drive_service.files().list(
                q=query,
                spaces='drive',
                fields='files(id, name)'
            ).execute()
            
            files = response.get('files', [])
            
            if files:
                folder_id = files[0]['id']
                logger.info(f"✅ Found existing Zyana Finance Logs folder: {folder_id}")
                return folder_id
            
            # Create new folder
            folder_metadata = {
                'name': 'Zyana Finance Logs',
                'mimeType': 'application/vnd.google-apps.folder'
            }
            
            folder = self.drive_service.files().create(
                body=folder_metadata,
                fields='id'
            ).execute()
            
            folder_id = folder.get('id')
            logger.info(f"✅ Created Zyana Finance Logs folder: {folder_id}")
            
            # Cache folder ID
            self.folder_id = folder_id
            
            return folder_id
            
        except HttpError as e:
            logger.error(f"❌ Error ensuring finance folder: {e}")
            raise
    
    async def create_monthly_sheet(
        self,
        month_name: str = None,
        year: int = None
    ) -> Dict[str, Any]:
        """Create a new monthly finance sheet.
        
        Args:
            month_name: Month name (e.g., "October"). Defaults to current month.
            year: Year (e.g., 2025). Defaults to current year.
            
        Returns:
            Dict with sheet_id, sheet_url, and sheet_name
        """
        if not self.sheets_service:
            raise Exception("Google Sheets service not initialized. Please connect Google account first.")
        
        try:
            # Default to current month/year
            now = datetime.now(PAKISTAN_TZ)
            if not month_name:
                month_name = now.strftime("%B")  # Full month name
            if not year:
                year = now.year
            
            sheet_name = f"Finance_{month_name}_{year}"
            
            # Check if sheet already exists
            existing_sheet = await self.find_sheet_by_name(sheet_name)
            if existing_sheet:
                logger.info(f"✅ Sheet already exists: {sheet_name}")
                return existing_sheet
            
            # Ensure folder exists
            folder_id = await self.ensure_finance_folder()
            
            # Create spreadsheet
            spreadsheet = {
                'properties': {
                    'title': sheet_name
                },
                'sheets': [{
                    'properties': {
                        'title': 'Expenses',
                        'gridProperties': {
                            'frozenRowCount': 1  # Freeze header row
                        }
                    }
                }]
            }
            
            spreadsheet_response = self.sheets_service.spreadsheets().create(
                body=spreadsheet
            ).execute()
            
            sheet_id = spreadsheet_response['spreadsheetId']
            sheet_url = spreadsheet_response['spreadsheetUrl']
            
            logger.info(f"✅ Created new finance sheet: {sheet_name} ({sheet_id})")
            
            # Move to folder
            if folder_id:
                self.drive_service.files().update(
                    fileId=sheet_id,
                    addParents=folder_id,
                    fields='id, parents'
                ).execute()
                logger.info(f"✅ Moved sheet to Zyana Finance Logs folder")
            
            # Initialize with header row
            header_values = [
                ['Date', 'Category', 'Type', 'Amount', 'Description', 'Business', 'Added At']
            ]
            
            self.sheets_service.spreadsheets().values().update(
                spreadsheetId=sheet_id,
                range='Expenses!A1:G1',
                valueInputOption='RAW',
                body={'values': header_values}
            ).execute()
            
            # Format header row (bold, background color)
            format_request = {
                'requests': [
                    {
                        'repeatCell': {
                            'range': {
                                'sheetId': 0,
                                'startRowIndex': 0,
                                'endRowIndex': 1
                            },
                            'cell': {
                                'userEnteredFormat': {
                                    'backgroundColor': {
                                        'red': 0.2,
                                        'green': 0.6,
                                        'blue': 0.9
                                    },
                                    'textFormat': {
                                        'bold': True,
                                        'foregroundColor': {
                                            'red': 1.0,
                                            'green': 1.0,
                                            'blue': 1.0
                                        }
                                    }
                                }
                            },
                            'fields': 'userEnteredFormat(backgroundColor,textFormat)'
                        }
                    }
                ]
            }
            
            self.sheets_service.spreadsheets().batchUpdate(
                spreadsheetId=sheet_id,
                body=format_request
            ).execute()
            
            logger.info(f"✅ Initialized sheet with headers and formatting")
            
            # Store in Supabase for quick lookup
            await self._store_sheet_metadata(sheet_id, sheet_name, sheet_url, month_name, year)
            
            return {
                'sheet_id': sheet_id,
                'sheet_url': sheet_url,
                'sheet_name': sheet_name,
                'month': month_name,
                'year': year
            }
            
        except HttpError as e:
            logger.error(f"❌ Error creating monthly sheet: {e}")
            raise
    
    async def append_expense_entry(
        self,
        sheet_id: str,
        date_str: str,
        category: str,
        transaction_type: str,
        amount: float,
        description: str = "",
        business: str = ""
    ) -> Dict[str, Any]:
        """Append an expense/income entry to the sheet.
        
        Args:
            sheet_id: Google Sheet ID
            date_str: Date string (e.g., "2025-10-26")
            category: Category (e.g., "Food", "Travel", "Salary")
            transaction_type: "expense" or "income"
            amount: Amount
            description: Optional description
            business: Optional business name
            
        Returns:
            Dict with success status and row number
        """
        if not self.sheets_service:
            raise Exception("Google Sheets service not initialized. Please connect Google account first.")
        
        try:
            # Prepare row data
            now_str = datetime.now(PAKISTAN_TZ).strftime("%Y-%m-%d %H:%M:%S")
            row_data = [[
                date_str,
                category,
                transaction_type.capitalize(),
                amount,
                description,
                business,
                now_str
            ]]
            
            # Append to sheet
            result = self.sheets_service.spreadsheets().values().append(
                spreadsheetId=sheet_id,
                range='Expenses!A:G',
                valueInputOption='USER_ENTERED',
                insertDataOption='INSERT_ROWS',
                body={'values': row_data}
            ).execute()
            
            updated_range = result.get('updates', {}).get('updatedRange', '')
            logger.info(f"✅ Appended entry to sheet: {updated_range}")
            
            return {
                'success': True,
                'updated_range': updated_range,
                'row_data': row_data[0]
            }
            
        except HttpError as e:
            logger.error(f"❌ Error appending entry: {e}")
            raise
    
    async def read_expenses(
        self,
        sheet_id: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        category: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Read expenses from sheet with optional filters.
        
        Args:
            sheet_id: Google Sheet ID
            start_date: Optional start date filter (YYYY-MM-DD)
            end_date: Optional end date filter (YYYY-MM-DD)
            category: Optional category filter
            
        Returns:
            List of expense/income entries
        """
        if not self.sheets_service:
            raise Exception("Google Sheets service not initialized. Please connect Google account first.")
        
        try:
            # Read all data (skip header)
            result = self.sheets_service.spreadsheets().values().get(
                spreadsheetId=sheet_id,
                range='Expenses!A2:G'
            ).execute()
            
            values = result.get('values', [])
            
            if not values:
                logger.info("📊 No data found in sheet")
                return []
            
            # Parse into structured format
            expenses = []
            for row in values:
                if len(row) < 4:  # Skip incomplete rows
                    continue
                
                entry = {
                    'date': row[0] if len(row) > 0 else '',
                    'category': row[1] if len(row) > 1 else '',
                    'type': row[2] if len(row) > 2 else '',
                    'amount': float(row[3]) if len(row) > 3 and row[3] else 0,
                    'description': row[4] if len(row) > 4 else '',
                    'business': row[5] if len(row) > 5 else '',
                    'added_at': row[6] if len(row) > 6 else ''
                }
                
                # Apply filters
                if start_date and entry['date'] < start_date:
                    continue
                if end_date and entry['date'] > end_date:
                    continue
                if category and entry['category'].lower() != category.lower():
                    continue
                
                expenses.append(entry)
            
            logger.info(f"📊 Read {len(expenses)} entries from sheet (filtered from {len(values)} total)")
            
            return expenses
            
        except HttpError as e:
            logger.error(f"❌ Error reading expenses: {e}")
            raise
    
    async def get_monthly_summary(self, sheet_id: str) -> Dict[str, Any]:
        """Get monthly summary with category-wise totals and insights.
        
        Args:
            sheet_id: Google Sheet ID
            
        Returns:
            Dict with summary statistics
        """
        try:
            # Read all expenses
            expenses = await self.read_expenses(sheet_id)
            
            if not expenses:
                return {
                    'total_expenses': 0,
                    'total_income': 0,
                    'net': 0,
                    'by_category': {},
                    'by_business': {},
                    'transaction_count': 0,
                    'summary_text': "No transactions recorded this month."
                }
            
            # Calculate totals
            total_expenses = sum(e['amount'] for e in expenses if e['type'].lower() == 'expense')
            total_income = sum(e['amount'] for e in expenses if e['type'].lower() == 'income')
            net = total_income - total_expenses
            
            # Group by category
            by_category = {}
            for e in expenses:
                cat = e['category'] or 'Uncategorized'
                if cat not in by_category:
                    by_category[cat] = {'expense': 0, 'income': 0, 'count': 0}
                
                if e['type'].lower() == 'expense':
                    by_category[cat]['expense'] += e['amount']
                else:
                    by_category[cat]['income'] += e['amount']
                
                by_category[cat]['count'] += 1
            
            # Group by business
            by_business = {}
            for e in expenses:
                bus = e['business'] or 'Personal'
                if bus not in by_business:
                    by_business[bus] = {'expense': 0, 'income': 0, 'count': 0}
                
                if e['type'].lower() == 'expense':
                    by_business[bus]['expense'] += e['amount']
                else:
                    by_business[bus]['income'] += e['amount']
                
                by_business[bus]['count'] += 1
            
            # Top spending category
            top_category = max(by_category.items(), key=lambda x: x[1]['expense'])[0] if by_category else "N/A"
            top_category_amount = by_category[top_category]['expense'] if by_category else 0
            
            # Generate summary text
            summary_text = (
                f"💰 Monthly Summary:\n"
                f"• Total Expenses: Rs {total_expenses:,.0f}\n"
                f"• Total Income: Rs {total_income:,.0f}\n"
                f"• Net: Rs {net:,.0f}\n"
                f"• Top Category: {top_category} (Rs {top_category_amount:,.0f})\n"
                f"• Transactions: {len(expenses)}"
            )
            
            return {
                'total_expenses': total_expenses,
                'total_income': total_income,
                'net': net,
                'by_category': by_category,
                'by_business': by_business,
                'transaction_count': len(expenses),
                'summary_text': summary_text
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting monthly summary: {e}", exc_info=True)
            raise
    
    async def find_sheet_by_name(self, sheet_name: str) -> Optional[Dict[str, Any]]:
        """Find a sheet by name.
        
        Args:
            sheet_name: Sheet name to search for
            
        Returns:
            Sheet info dict or None
        """
        if not self.drive_service:
            return None
        
        try:
            query = f"name='{sheet_name}' and mimeType='application/vnd.google-apps.spreadsheet' and trashed=false"
            response = self.drive_service.files().list(
                q=query,
                spaces='drive',
                fields='files(id, name, webViewLink)'
            ).execute()
            
            files = response.get('files', [])
            
            if files:
                file = files[0]
                return {
                    'sheet_id': file['id'],
                    'sheet_name': file['name'],
                    'sheet_url': file.get('webViewLink', ''),
                }
            
            return None
            
        except HttpError as e:
            logger.error(f"❌ Error finding sheet: {e}")
            return None
    
    async def _store_sheet_metadata(
        self,
        sheet_id: str,
        sheet_name: str,
        sheet_url: str,
        month: str,
        year: int
    ):
        """Store sheet metadata in Supabase for quick lookup.
        
        Args:
            sheet_id: Google Sheet ID
            sheet_name: Sheet name
            sheet_url: Sheet URL
            month: Month name
            year: Year
        """
        try:
            supabase_client.admin.table("finance_sheets").upsert({
                'sheet_id': sheet_id,
                'sheet_name': sheet_name,
                'sheet_url': sheet_url,
                'month': month,
                'year': year,
                'created_at': datetime.now(PAKISTAN_TZ).isoformat()
            }).execute()
            
            logger.info(f"✅ Stored sheet metadata in Supabase")
            
        except Exception as e:
            logger.warning(f"⚠️  Could not store sheet metadata: {e}")


# Global instance
google_sheets_service = GoogleSheetsFinanceService()

