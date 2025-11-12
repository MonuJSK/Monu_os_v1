"""
Google Sheets integration module for Monu OS v1.
"""

import gspread
from oauth2client.service_account import ServiceAccountCredentials
from typing import Dict, List, Any, Optional, Tuple
import logging
from datetime import datetime

from .utils import logger

class GoogleSheetsManager:
    """
    Manages Google Sheets operations for storing market data.
    """

    SCOPE = [
        'https://spreadsheets.google.com/feeds',
        'https://www.googleapis.com/auth/drive'
    ]

    def __init__(self, service_account_path: str, spreadsheet_id: str):
        """
        Initialize Google Sheets manager.

        Args:
            service_account_path: Path to service account JSON file
            spreadsheet_id: Google Sheets spreadsheet ID
        """
        self.service_account_path = service_account_path
        self.spreadsheet_id = spreadsheet_id
        self.gc = None
        self.sheet = None
        self._connect()

    def _connect(self) -> None:
        """
        Establish connection to Google Sheets.
        """
        try:
            creds = ServiceAccountCredentials.from_json_keyfile_name(
                self.service_account_path, self.SCOPE
            )
            self.gc = gspread.authorize(creds)
            self.sheet = self.gc.open_by_key(self.spreadsheet_id)
            logger.info("Successfully connected to Google Sheets")
        except Exception as e:
            logger.error(f"Failed to connect to Google Sheets: {str(e)}")
            raise

    def append_raw(self, symbol: str, row: Dict[str, Any]) -> bool:
        """
        Append a raw data row to the RawData worksheet.

        Args:
            symbol: Symbol name
            row: Dictionary containing row data

        Returns:
            True if successful, False otherwise
        """
        try:
            # Get or create RawData worksheet
            raw_sheet = self._get_or_create_worksheet("RawData")

            # Prepare row data
            timestamp = datetime.now().isoformat()
            row_data = [
                timestamp,
                symbol,
                row.get('open', 0),
                row.get('high', 0),
                row.get('low', 0),
                row.get('close', 0),
                row.get('volume', 0),
                row.get('pct_change', 0),
                row.get('vol_change_pct', 0),
                row.get('ema_20', 0),
                row.get('rsi_14', 0),
                row.get('recent_high', 0),
                row.get('recent_low', 0)
            ]

            # Append to sheet
            raw_sheet.append_row(row_data)
            logger.info(f"Appended raw data for {symbol}")
            return True

        except Exception as e:
            logger.error(f"Failed to append raw data for {symbol}: {str(e)}")
            return False

    def update_summary(self, date: str, summary_obj: Dict[str, Any]) -> bool:
        """
        Update the Summary worksheet with daily summary data.

        Args:
            date: Date string (YYYY-MM-DD)
            summary_obj: Summary data dictionary

        Returns:
            True if successful, False otherwise
        """
        try:
            # Get or create Summary worksheet
            summary_sheet = self._get_or_create_worksheet("Summary")

            # Prepare summary data
            row_data = [
                date,
                summary_obj.get('total_symbols', 0),
                self._format_list(summary_obj.get('gainers', [])),
                self._format_list(summary_obj.get('losers', [])),
                self._format_list(summary_obj.get('high_volume', [])),
                summary_obj.get('timestamp', datetime.now().isoformat())
            ]

            # Check if date already exists, update or append
            existing_rows = summary_sheet.get_all_values()
            date_column = [row[0] for row in existing_rows]

            if date in date_column:
                # Update existing row
                row_index = date_column.index(date) + 1  # +1 because sheets are 1-indexed
                for col, value in enumerate(row_data, 1):
                    summary_sheet.update_cell(row_index, col, value)
                logger.info(f"Updated summary for date {date}")
            else:
                # Append new row
                summary_sheet.append_row(row_data)
                logger.info(f"Appended summary for date {date}")

            return True

        except Exception as e:
            logger.error(f"Failed to update summary for {date}: {str(e)}")
            return False

    def read_config(self) -> Dict[str, Any]:
        """
        Read configuration from Config worksheet.

        Returns:
            Configuration dictionary
        """
        try:
            config_sheet = self._get_or_create_worksheet("Config")

            # Get all config data
            config_data = config_sheet.get_all_records()

            if not config_data:
                logger.warning("No configuration data found in Config sheet")
                return {}

            # Convert to dictionary (assuming first row has headers)
            config = {}
            for record in config_data:
                for key, value in record.items():
                    config[key.lower().replace(' ', '_')] = value

            logger.info("Successfully read configuration from Google Sheets")
            return config

        except Exception as e:
            logger.error(f"Failed to read config: {str(e)}")
            return {}

    def _get_or_create_worksheet(self, name: str) -> gspread.Worksheet:
        """
        Get existing worksheet or create new one.

        Args:
            name: Worksheet name

        Returns:
            Worksheet object
        """
        try:
            return self.sheet.worksheet(name)
        except gspread.WorksheetNotFound:
            logger.info(f"Creating new worksheet: {name}")
            return self.sheet.add_worksheet(title=name, rows=1000, cols=20)

    def _format_list(self, items: List[Tuple[str, float]]) -> str:
        """
        Format list of tuples for sheet storage.

        Args:
            items: List of (symbol, value) tuples

        Returns:
            Formatted string
        """
        if not items:
            return ""

        formatted_items = []
        for symbol, value in items:
            if isinstance(value, float):
                formatted_items.append(f"{symbol}: {value:.2f}%")
            else:
                formatted_items.append(f"{symbol}: {value}")

        return "; ".join(formatted_items)

    def get_recent_data(self, symbol: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get recent raw data for a symbol.

        Args:
            symbol: Symbol name
            limit: Number of recent records to retrieve

        Returns:
            List of data dictionaries
        """
        try:
            raw_sheet = self._get_or_create_worksheet("RawData")

            # Get all data and filter by symbol
            all_data = raw_sheet.get_all_records()
            symbol_data = [row for row in all_data if row.get('symbol') == symbol]

            # Sort by timestamp and get most recent
            symbol_data.sort(key=lambda x: x.get('timestamp', ''), reverse=True)

            return symbol_data[:limit]

        except Exception as e:
            logger.error(f"Failed to get recent data for {symbol}: {str(e)}")
            return []

    def initialize_sheets(self) -> bool:
        """
        Initialize worksheets with headers if they don't exist.

        Returns:
            True if successful, False otherwise
        """
        try:
            # Initialize RawData sheet
            raw_sheet = self._get_or_create_worksheet("RawData")
            raw_headers = [
                "timestamp", "symbol", "open", "high", "low", "close", "volume",
                "pct_change", "vol_change_pct", "ema_20", "rsi_14", "recent_high", "recent_low"
            ]

            if raw_sheet.row_count == 0 or not raw_sheet.get('A1'):
                raw_sheet.append_row(raw_headers)
                logger.info("Initialized RawData sheet headers")

            # Initialize Summary sheet
            summary_sheet = self._get_or_create_worksheet("Summary")
            summary_headers = [
                "date", "total_symbols", "gainers", "losers", "high_volume", "timestamp"
            ]

            if summary_sheet.row_count == 0 or not summary_sheet.get('A1'):
                summary_sheet.append_row(summary_headers)
                logger.info("Initialized Summary sheet headers")

            # Initialize Config sheet
            config_sheet = self._get_or_create_worksheet("Config")
            config_headers = ["key", "value"]

            if config_sheet.row_count == 0 or not config_sheet.get('A1'):
                config_sheet.append_row(config_headers)
                logger.info("Initialized Config sheet headers")

            return True

        except Exception as e:
            logger.error(f"Failed to initialize sheets: {str(e)}")
            return False
