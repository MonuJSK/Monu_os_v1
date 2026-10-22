"""
Unit tests for fetcher module.
"""

import pytest
import pandas as pd
import numpy as np
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from src.fetcher import MarketDataFetcher


class TestMarketDataFetcher:
    """Test cases for MarketDataFetcher class."""

    @pytest.fixture
    def fetcher(self):
        """Create fetcher instance with mocked credentials."""
        with patch('src.fetcher.TvDatafeed'):
            return MarketDataFetcher('test_user', 'test_pass')

    @pytest.fixture
    def sample_data(self):
        """Create sample OHLCV data for testing."""
        dates = pd.date_range('2023-01-01', periods=100, freq='D')
        np.random.seed(42)  # For reproducible results

        data = pd.DataFrame({
            'open': np.random.uniform(100, 110, 100),
            'high': np.random.uniform(110, 120, 100),
            'low': np.random.uniform(90, 100, 100),
            'close': np.random.uniform(95, 115, 100),
            'volume': np.random.randint(1000, 10000, 100)
        }, index=dates)

        # Ensure high >= close >= low and high >= open >= low
        for i in range(len(data)):
            high = max(data.iloc[i]['open'], data.iloc[i]['close'],
                      data.iloc[i]['high'], data.iloc[i]['low'])
            low = min(data.iloc[i]['open'], data.iloc[i]['close'],
                     data.iloc[i]['high'], data.iloc[i]['low'])

            data.iloc[i, data.columns.get_loc('high')] = high
            data.iloc[i, data.columns.get_loc('low')] = low

        return data

    def test_initialization(self, fetcher):
        """Test fetcher initialization."""
        assert fetcher.tv is not None
        assert fetcher.DEFAULT_SYMBOLS == ['NIFTY', 'BANKNIFTY', 'BTCUSDT', 'XAUUSD']
        assert fetcher.DEFAULT_EXCHANGES == ['NSE', 'NSE', 'BINANCE', 'FX_IDC']

    @patch('src.fetcher.TvDatafeed')
    def test_fetch_symbol_data_success(self, mock_tv_class, fetcher, sample_data):
        """Test successful data fetching."""
        mock_tv_instance = Mock()
        mock_tv_instance.get_hist.return_value = sample_data
        fetcher.tv = mock_tv_instance

        result = fetcher.fetch_symbol_data('NIFTY', 'NSE', n_bars=100)

        assert result is not None
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 100
        assert all(col in result.columns for col in ['open', 'high', 'low', 'close', 'volume'])

        mock_tv_instance.get_hist.assert_called_once_with(
            symbol='NIFTY', exchange='NSE', n_bars=100
        )

    @patch('src.fetcher.TvDatafeed')
    def test_fetch_symbol_data_failure(self, mock_tv_class, fetcher):
        """Test data fetching failure scenarios."""
        mock_tv_instance = Mock()
        fetcher.tv = mock_tv_instance

        # Test None return
        mock_tv_instance.get_hist.return_value = None
        result = fetcher.fetch_symbol_data('INVALID', 'NSE')
        assert result is None

        # Test empty DataFrame
        mock_tv_instance.get_hist.return_value = pd.DataFrame()
        result = fetcher.fetch_symbol_data('INVALID', 'NSE')
        assert result is None

        # Test missing columns
        mock_tv_instance.get_hist.return_value = pd.DataFrame({'invalid': [1, 2, 3]})
        result = fetcher.fetch_symbol_data('INVALID', 'NSE')
        assert result is None

    def test_calculate_indicators(self, fetcher, sample_data):
        """Test indicator calculations."""
        indicators = fetcher.calculate_indicators(sample_data)

        assert isinstance(indicators, dict)
        assert 'pct_change' in indicators
        assert 'vol_change_pct' in indicators
        assert 'ema_20' in indicators
        assert 'rsi_14' in indicators
        assert 'recent_high' in indicators
        assert 'recent_low' in indicators

        # Check types
        assert isinstance(indicators['pct_change'], float)
        assert isinstance(indicators['vol_change_pct'], float)
        assert isinstance(indicators['ema_20'], float)
        assert isinstance(indicators['rsi_14'], float)
        assert isinstance(indicators['recent_high'], float)
        assert isinstance(indicators['recent_low'], float)

    def test_calculate_indicators_insufficient_data(self, fetcher):
        """Test indicator calculations with insufficient data."""
        # Test with very small dataset
        small_data = pd.DataFrame({
            'open': [100],
            'high': [105],
            'low': [95],
            'close': [102],
            'volume': [1000]
        })

        indicators = fetcher.calculate_indicators(small_data)

        assert indicators['pct_change'] == 0.0  # Not enough data for comparison
        assert indicators['vol_change_pct'] == 0.0
        assert indicators['ema_20'] == 102.0  # Fallback to close price
        assert indicators['rsi_14'] == 50.0  # Neutral RSI
        assert indicators['recent_high'] == 105.0
        assert indicators['recent_low'] == 95.0

    def test_calculate_ema(self, fetcher):
        """Test EMA calculation."""
        prices = np.array([100.0, 102.0, 101.0, 103.0, 105.0])

        ema = fetcher._calculate_ema(prices, 3)

        # Manual calculation for verification
        multiplier = 2 / (3 + 1)
        expected_ema = prices[0]
        for price in prices[1:]:
            expected_ema = (price * multiplier) + (expected_ema * (1 - multiplier))

        assert abs(ema - expected_ema) < 0.001

    def test_calculate_rsi(self, fetcher):
        """Test RSI calculation."""
        # Create trending data for RSI test
        prices = np.array([100.0, 102.0, 104.0, 103.0, 105.0, 107.0, 106.0,
                          108.0, 110.0, 109.0, 111.0, 113.0, 112.0, 114.0, 116.0])

        rsi = fetcher._calculate_rsi(prices, 14)

        assert 0 <= rsi <= 100
        assert isinstance(rsi, float)

    def test_fetch_all_symbols(self, fetcher, sample_data):
        """Test fetching all symbols."""
        with patch.object(fetcher, 'fetch_symbol_data') as mock_fetch:
            mock_fetch.return_value = sample_data

            with patch.object(fetcher, 'calculate_indicators') as mock_calc:
                mock_calc.return_value = {
                    'pct_change': 1.5,
                    'vol_change_pct': 10.0,
                    'ema_20': 105.0,
                    'rsi_14': 65.0,
                    'recent_high': 110.0,
                    'recent_low': 95.0
                }

                result = fetcher.fetch_all_symbols()

                assert len(result) == 4  # Default symbols
                assert all(symbol in result for symbol in fetcher.DEFAULT_SYMBOLS)

                for symbol_data in result.values():
                    assert 'data' in symbol_data
                    assert 'indicators' in symbol_data
                    assert 'timestamp' in symbol_data
                    assert isinstance(symbol_data['timestamp'], datetime)

    def test_get_market_summary(self, fetcher):
        """Test market summary generation."""
        symbol_data = {
            'NIFTY': {
                'indicators': {'pct_change': 2.5, 'vol_change_pct': 60.0}
            },
            'BANKNIFTY': {
                'indicators': {'pct_change': -1.2, 'vol_change_pct': 8.0}
            },
            'BTCUSDT': {
                'indicators': {'pct_change': 5.0, 'vol_change_pct': 75.0}
            }
        }

        summary = fetcher.get_market_summary(symbol_data)

        assert summary['total_symbols'] == 3
        assert len(summary['gainers']) == 2  # NIFTY and BTCUSDT
        assert len(summary['losers']) == 1   # BANKNIFTY
        assert len(summary['high_volume']) == 2  # NIFTY and BTCUSDT (>50% volume change)

        # Check sorting
        assert summary['gainers'][0][1] >= summary['gainers'][1][1]  # Descending order
        assert summary['losers'][0][1] <= summary['losers'][0][1]   # Most negative first
