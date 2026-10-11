"""Google Sheets client for syncing CSV data."""
import os
import pandas as pd
from typing import List, Optional

try:
    import gspread
    from google.oauth2.service_account import Credentials
    SHEETS_AVAILABLE = True
except ImportError:
    SHEETS_AVAILABLE = False
    gspread = None
    Credentials = None


class SheetsClient:
    """Client for interacting with Google Sheets."""
    
    def __init__(self, service_account_json_path: str, sheet_url: str):
        """
        Initialize Google Sheets client.
        
        Args:
            service_account_json_path: Path to service account JSON credentials.
            sheet_url: URL of the Google Sheet.
        """
        if not SHEETS_AVAILABLE:
            raise ImportError(
                "gspread and google-auth are required for Google Sheets sync. "
                "Install with: pip install gspread google-auth"
            )
        
        # Resolve relative paths
        if not os.path.isabs(service_account_json_path):
            project_root = os.path.dirname(os.path.abspath(__file__))
            service_account_json_path = os.path.join(
                project_root, service_account_json_path
            )
        
        # Authenticate
        scope = [
            "https://spreadsheets.google.com/feeds",
            "https://www.googleapis.com/auth/drive"
        ]
        creds = Credentials.from_service_account_file(
            service_account_json_path, scopes=scope
        )
        self.client = gspread.authorize(creds)
        
        # Open spreadsheet
        self.spreadsheet = self.client.open_by_url(sheet_url)
    
    def get_or_create_worksheet(self, tab_name: str, headers: List[str]):
        """
        Get existing worksheet or create new one with headers.
        
        Args:
            tab_name: Name of the worksheet tab.
            headers: List of header column names.
        
        Returns:
            Worksheet object.
        """
        try:
            worksheet = self.spreadsheet.worksheet(tab_name)
            # Ensure headers match
            existing_headers = worksheet.row_values(1)
            if existing_headers != headers:
                # Clear and set new headers
                worksheet.clear()
                worksheet.append_row(headers)
            return worksheet
        except gspread.exceptions.WorksheetNotFound:
            # Create new worksheet
            worksheet = self.spreadsheet.add_worksheet(
                title=tab_name, rows=1000, cols=len(headers)
            )
            worksheet.append_row(headers)
            return worksheet
    
    def append_rows(self, tab_name: str, rows: List[List]) -> None:
        """
        Append rows to a worksheet.
        
        Args:
            tab_name: Name of the worksheet tab.
            rows: List of lists, where each inner list is a row.
        """
        if not rows:
            return
        
        worksheet = self.spreadsheet.worksheet(tab_name)
        worksheet.append_rows(rows)
    
    def sync_csv_to_sheet(
        self,
        csv_path: str,
        tab_name: str,
        key_columns: Optional[List[str]] = None
    ) -> None:
        """
        Sync CSV file to Google Sheet tab.
        
        Uses simple approach: clear tab and re-upload full DataFrame.
        For upsert functionality, this can be extended later.
        
        Args:
            csv_path: Path to CSV file.
            tab_name: Name of the worksheet tab.
            key_columns: Optional list of key columns for future upsert logic.
        """
        # Resolve relative paths
        if not os.path.isabs(csv_path):
            project_root = os.path.dirname(os.path.abspath(__file__))
            csv_path = os.path.join(project_root, csv_path)
        
        if not os.path.exists(csv_path):
            print(f"CSV file not found: {csv_path}")
            return
        
        # Load CSV
        df = pd.read_csv(csv_path)
        
        if df.empty:
            print(f"CSV is empty: {csv_path}")
            return
        
        # Get headers
        headers = list(df.columns)
        
        # Get or create worksheet
        worksheet = self.get_or_create_worksheet(tab_name, headers)
        
        # Clear existing data (except headers)
        worksheet.clear()
        worksheet.append_row(headers)
        
        # Convert DataFrame to list of lists
        rows = df.values.tolist()
        
        # Batch append (gspread has limits, so we'll do in chunks)
        batch_size = 1000
        for i in range(0, len(rows), batch_size):
            batch = rows[i:i + batch_size]
            worksheet.append_rows(batch)
        
        print(f"Synced {len(rows)} rows to '{tab_name}' tab")


def get_sheets_client() -> Optional[SheetsClient]:
    """
    Create SheetsClient from environment variables.
    
    Returns:
        SheetsClient instance or None if env vars not set.
    """
    service_account_json = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")
    sheet_url = os.getenv("GOOGLE_SHEET_URL")
    
    if not service_account_json or not sheet_url:
        return None
    
    return SheetsClient(service_account_json, sheet_url)

