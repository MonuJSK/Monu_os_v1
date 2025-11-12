"""
Unit tests for sheets module.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock, mock_open
import pandas as pd
from datetime import datetime

from src.sheets import GoogleSheetsManager


class TestGoogleSheetsManager:
    """Test cases for GoogleSheetsManager class."""

    @pytest.fixture
    def sheets_manager(self):
        """Create sheets manager instance."""
        with patch('src.sheets.ServiceAccountCredentials'):
            with patch('src.sheets.gspread'):
                return GoogleSheetsManager('fake_path.json', 'fake_sheet_id')

    def test_initialization(self, sheets_manager):
        """Test sheets manager initialization."""
        assert sheets_manager.service_account_path == 'fake_path.json'
        assert sheets_manager.spreadsheet_id == 'fake_sheet_id'
        assert sheets_manager.gc is not None
        assert sheets_manager.sheet is not None

    @patch('src.sheets.gspread')
    def test_connect_success(self, mock_gspread, sheets_manager):
        """Test successful connection to Google Sheets."""
        mock_gc = Mock()
        mock_sheet = Mock()
        mock_gspread.authorize.return_value = mock_gc
        mock_gc.open_by_key.return_value = mock_sheet

        sheets_manager._connect()

        mock_gspread.authorize.assert_called_once()
        mock_gc.open_by_key.assert_called_once_with('fake_sheet_id')

    @patch('src.sheets.gspread')
    def test_connect_failure(self, mock_gspread, sheets_manager):
        """Test connection failure."""
        mock_gspread.authorize.side_effect = Exception("Connection failed")

        with pytest.raises(Exception):
            sheets_manager._connect()

    def test_append_raw_success(self, sheets_manager):
        """Test successful raw data append."""
        mock_raw_sheet = Mock()
        mock_raw_sheet.append_row.return_value = None

        with patch.object(sheets_manager, '_get_or_create_worksheet') as mock_get:
            mock_get.return_value = mock_raw_sheet

            row_data = {
                'open': 100.0,
                'high': 105.0,
                'low': 95.0,
                'close': 102.0,
                'volume': 10000,
                'pct_change': 2.5,
                'vol_change_pct': 10.0,
                'ema_20': 101.0,
                'rsi_14': 65.0,
                'recent_high': 110.0,
                'recent_low': 90.0
            }

            result = sheets_manager.append_raw('NIFTY', row_data)

            assert result is True
            mock_raw_sheet.append_row.assert_called_once()
            args = mock_raw_sheet.append_row.call_args[0][0]

            # Check that timestamp is included and data is correct
            assert len(args) == 13  # timestamp + 12 data fields
            assert args[1] == 'NIFTY'  # symbol
            assert args[2] == 100.0   # open
            assert args[3] == 105.0   # high
            assert args[4] == 95.0    # low
            assert args[5] == 102.0   # close
            assert args[6] == 10000   # volume

    def test_append_raw_failure(self, sheets_manager):
        """Test raw data append failure."""
        mock_raw_sheet = Mock()
        mock_raw_sheet.append_row.side_effect = Exception("Append failed")

        with patch.object(sheets_manager, '_get_or_create_worksheet') as mock_get:
            mock_get.return_value = mock_raw_sheet

            row_data = {'open': 100.0, 'close': 102.0}
            result = sheets_manager.append_raw('NIFTY', row_data)

            assert result is False

    def test_update_summary_new_date(self, sheets_manager):
        """Test summary update for new date."""
        mock_summary_sheet = Mock()
        mock_summary_sheet.get_all_values.return_value = [['date', 'total_symbols']]  # Only headers

        with patch.object(sheets_manager, '_get_or_create_worksheet') as mock_get:
            mock_get.return_value = mock_summary_sheet

            summary_data = {
                'total_symbols': 4,
                'gainers': [('NIFTY', 2.5)],
                'losers': [('BANKNIFTY', -1.2)],
                'high_volume': [('BTCUSDT', 25.0)],
                'timestamp': '2023-01-01T10:00:00'
            }

            result = sheets_manager.update_summary('2023-01-01', summary_data)

            assert result is True
            mock_summary_sheet.append_row.assert_called_once()
            args = mock_summary_sheet.append_row.call_args[0][0]

            assert args[0] == '2023-01-01'
            assert args[1] == 4
            assert 'NIFTY: 2.50%' in args[2]
            assert 'BANKNIFTY: -1.20%' in args[3]
            assert 'BTCUSDT: 25.00%' in args[4]

    def test_update_summary_existing_date(self, sheets_manager):
        """Test summary update for existing date."""
        mock_summary_sheet = Mock()
        # Headers + existing data for 2023-01-01
        mock_summary_sheet.get_all_values.return_value = [
            ['date', 'total_symbols', 'gainers', 'losers', 'high_volume', 'timestamp'],
            ['2023-01-01', '3', 'OLD', 'OLD', 'OLD', 'OLD']
        ]

        with patch.object(sheets_manager, '_get_or_create_worksheet') as mock_get:
            mock_get.return_value = mock_summary_sheet

            summary_data = {
                'total_symbols': 4,
                'gainers': [('NIFTY', 2.5)],
                'losers': [('BANKNIFTY', -1.2)],
                'high_volume': [('BTCUSDT', 25.0)],
                'timestamp': '2023-01-01T10:00:00'
            }

            result = sheets_manager.update_summary('2023-01-01', summary_data)

            assert result is True
            mock_summary_sheet.update_cell.assert_called()
            # Should update row 2 (1-indexed, after header)
            assert mock_summary_sheet.update_cell.call_count == 5  # 5 columns to update

    def test_update_summary_failure(self, sheets_manager):
        """Test summary update failure."""
        mock_summary_sheet = Mock()
        mock_summary_sheet.get_all_values.side_effect = Exception("Sheet error")

        with patch.object(sheets_manager, '_get_or_create_worksheet') as mock_get:
            mock_get.return_value = mock_summary_sheet

            result = sheets_manager.update_summary('2023-01-01', {})

            assert result is False

    def test_read_config_success(self, sheets_manager):
        """Test successful config reading."""
        mock_config_sheet = Mock()
        mock_config_sheet.get_all_records.return_value = [
            {'key': 'symbol_1', 'value': 'NIFTY'},
            {'key': 'exchange_1', 'value': 'NSE'},
            {'key': 'update_interval', 'value': '3600'}
        ]

        with patch.object(sheets_manager, '_get_or_create_worksheet') as mock_get:
            mock_get.return_value = mock_config_sheet

            config = sheets_manager.read_config()

            assert config['symbol_1'] == 'NIFTY'
            assert config['exchange_1'] == 'NSE'
            assert config['update_interval'] == '3600'

    def test_read_config_empty(self, sheets_manager):
        """Test config reading with empty sheet."""
        mock_config_sheet = Mock()
        mock_config_sheet.get_all_records.return_value = []

        with patch.object(sheets_manager, '_get_or_create_worksheet') as mock_get:
            mock_get.return_value = mock_config_sheet

            config = sheets_manager.read_config()

            assert config == {}

    def test_read_config_failure(self, sheets_manager):
        """Test config reading failure."""
        mock_config_sheet = Mock()
        mock_config_sheet.get_all_records.side_effect = Exception("Read failed")

        with patch.object(sheets_manager, '_get_or_create_worksheet') as mock_get:
            mock_get.return_value = mock_config_sheet

            config = sheets_manager.read_config()

            assert config == {}

    def test_get_or_create_worksheet_existing(self, sheets_manager):
        """Test getting existing worksheet."""
        mock_worksheet = Mock()
        sheets_manager.sheet.worksheet.return_value = mock_worksheet

        result = sheets_manager._get_or_create_worksheet('ExistingSheet')

        assert result == mock_worksheet
        sheets_manager.sheet.worksheet.assert_called_once_with('ExistingSheet')

    def test_get_or_create_worksheet_new(self, sheets_manager):
        """Test creating new worksheet."""
        sheets_manager.sheet.worksheet.side_effect = Exception("Worksheet not found")
        mock_new_sheet = Mock()
        sheets_manager.sheet.add_worksheet.return_value = mock_new_sheet

        result = sheets_manager._get_or_create_worksheet('NewSheet')

        assert result == mock_new_sheet
        sheets_manager.sheet.add_worksheet.assert_called_once_with(
            title='NewSheet', rows=1000, cols=20
        )

    def test_format_list(self, sheets_manager):
        """Test list formatting for sheets."""
        items = [('NIFTY', 2.5), ('BANKNIFTY', -1.2), ('BTCUSDT', 5.0)]

        result = sheets_manager._format_list(items)

        assert 'NIFTY: 2.50%' in result
        assert 'BANKNIFTY: -1.20%' in result
        assert 'BTCUSDT: 5.00%' in result
        assert '; ' in result  # Separator

    def test_format_list_empty(self, sheets_manager):
        """Test formatting empty list."""
        result = sheets_manager._format_list([])
        assert result == ""

    def test_get_recent_data(self, sheets_manager):
        """Test getting recent data."""
        mock_raw_sheet = Mock()
        mock_raw_sheet.get_all_records.return_value = [
            {'timestamp': '2023-01-02T10:00:00', 'symbol': 'NIFTY', 'close': '102.0'},
            {'timestamp': '2023-01-01T10:00:00', 'symbol': 'NIFTY', 'close': '100.0'},
            {'timestamp': '2023-01-02T10:00:00', 'symbol': 'BANKNIFTY', 'close': '105.0'}
        ]

        with patch.object(sheets_manager, '_get_or_create_worksheet') as mock_get:
            mock_get.return_value = mock_raw_sheet

            result = sheets_manager.get_recent_data('NIFTY', limit=5)

            assert len(result) == 2
            assert result[0]['symbol'] == 'NIFTY'
            assert result[1]['symbol'] == 'NIFTY'
            # Should be sorted by timestamp descending
            assert result[0]['timestamp'] >= result[1]['timestamp']

    def test_initialize_sheets(self, sheets_manager):
        """Test sheets initialization."""
        mock_raw_sheet = Mock()
        mock_summary_sheet = Mock()
        mock_config_sheet = Mock()

        # Mock get calls
        call_count = 0
        def mock_get_side_effect(name):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return mock_raw_sheet
            elif call_count == 2:
                return mock_summary_sheet
            else:
                return mock_config_sheet

        with patch.object(sheets_manager, '_get_or_create_worksheet') as mock_get:
            mock_get.side_effect = mock_get_side_effect

            result = sheets_manager.initialize_sheets()

            assert result is True
            assert mock_get.call_count == 3

            # Check that append_row was called for headers
            assert mock_raw_sheet.append_row.called
            assert mock_summary_sheet.append_row.called
            assert mock_config_sheet.append_row.called

    def test_initialize_sheets_failure(self, sheets_manager):
        """Test sheets initialization failure."""
        with patch.object(sheets_manager, '_get_or_create_worksheet') as mock_get:
            mock_get.side_effect = Exception("Init failed")

            result = sheets_manager.initialize_sheets()

            assert result is False
