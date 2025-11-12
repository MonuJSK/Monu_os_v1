"""
Data fetching and indicator calculation module for Monu OS v1.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from tvDatafeed import TvDatafeed
from datetime import datetime, timedelta
import logging

from .utils import logger, safe_float, calculate_percentage_change

class MarketDataFetcher:
    """
    Fetches market data and calculates technical indicators.
    """

    DEFAULT_SYMBOLS = ['NIFTY', 'BANKNIFTY', 'BTCUSDT', 'XAUUSD']
    DEFAULT_EXCHANGES = ['NSE', 'NSE', 'BINANCE', 'FX_IDC']

    def __init__(self, username: str, password: str):
        """
        Initialize the data fetcher.

        Args:
            username: TradingView username
            password: TradingView password
        """
        self.tv = TvDatafeed(username=username, password=password)
        logger.info("MarketDataFetcher initialized")

    def fetch_symbol_data(self, symbol: str, exchange: str, n_bars: int = 100) -> Optional[pd.DataFrame]:
        """
        Fetch historical data for a symbol.

        Args:
            symbol: Symbol name
            exchange: Exchange name
            n_bars: Number of bars to fetch

        Returns:
            DataFrame with OHLCV data or None if failed
        """
        try:
            data = self.tv.get_hist(symbol=symbol, exchange=exchange, n_bars=n_bars)
            if data is None or data.empty:
                logger.warning(f"No data fetched for {symbol} on {exchange}")
                return None

            # Ensure we have the required columns
            required_cols = ['open', 'high', 'low', 'close', 'volume']
            if not all(col in data.columns for col in required_cols):
                logger.error(f"Missing required columns for {symbol}")
                return None

            logger.info(f"Successfully fetched {len(data)} bars for {symbol}")
            return data

        except Exception as e:
            logger.error(f"Error fetching data for {symbol}: {str(e)}")
            return None

    def calculate_indicators(self, data: pd.DataFrame) -> Dict[str, float]:
        """
        Calculate technical indicators for the given data.

        Args:
            data: OHLCV DataFrame

        Returns:
            Dictionary of calculated indicators
        """
        indicators = {}

        try:
            close_prices = data['close'].values
            volumes = data['volume'].values

            # Percentage change (latest vs previous)
            if len(close_prices) >= 2:
                indicators['pct_change'] = calculate_percentage_change(
                    close_prices[-1], close_prices[-2]
                )
            else:
                indicators['pct_change'] = 0.0

            # Volume change percentage
            if len(volumes) >= 2:
                indicators['vol_change_pct'] = calculate_percentage_change(
                    volumes[-1], volumes[-2]
                )
            else:
                indicators['vol_change_pct'] = 0.0

            # EMA 20
            if len(close_prices) >= 20:
                ema_20 = self._calculate_ema(close_prices, 20)
                indicators['ema_20'] = ema_20
            else:
                indicators['ema_20'] = close_prices[-1] if len(close_prices) > 0 else 0.0

            # RSI 14
            if len(close_prices) >= 15:  # Need at least 15 for RSI calculation
                rsi = self._calculate_rsi(close_prices, 14)
                indicators['rsi_14'] = rsi
            else:
                indicators['rsi_14'] = 50.0  # Neutral RSI

            # Recent high/low (last 20 periods)
            lookback = min(20, len(data))
            recent_data = data.tail(lookback)
            indicators['recent_high'] = recent_data['high'].max()
            indicators['recent_low'] = recent_data['low'].min()

        except Exception as e:
            logger.error(f"Error calculating indicators: {str(e)}")
            # Return default values
            indicators = {
                'pct_change': 0.0,
                'vol_change_pct': 0.0,
                'ema_20': data['close'].iloc[-1] if not data.empty else 0.0,
                'rsi_14': 50.0,
                'recent_high': data['high'].max() if not data.empty else 0.0,
                'recent_low': data['low'].min() if not data.empty else 0.0
            }

        return indicators

    def _calculate_ema(self, prices: np.ndarray, period: int) -> float:
        """
        Calculate Exponential Moving Average.

        Args:
            prices: Array of prices
            period: EMA period

        Returns:
            EMA value
        """
        if len(prices) < period:
            return prices[-1]

        multiplier = 2 / (period + 1)
        ema = prices[0]

        for price in prices[1:]:
            ema = (price * multiplier) + (ema * (1 - multiplier))

        return ema

    def _calculate_rsi(self, prices: np.ndarray, period: int = 14) -> float:
        """
        Calculate Relative Strength Index.

        Args:
            prices: Array of prices
            period: RSI period

        Returns:
            RSI value
        """
        if len(prices) < period + 1:
            return 50.0

        deltas = np.diff(prices)
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)

        avg_gain = np.mean(gains[:period])
        avg_loss = np.mean(losses[:period])

        for i in range(period, len(gains)):
            avg_gain = (avg_gain * (period - 1) + gains[i]) / period
            avg_loss = (avg_loss * (period - 1) + losses[i]) / period

        if avg_loss == 0:
            return 100.0

        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))

        return rsi

    def fetch_all_symbols(self, symbols: Optional[List[str]] = None,
                         exchanges: Optional[List[str]] = None) -> Dict[str, Dict]:
        """
        Fetch data and calculate indicators for all symbols.

        Args:
            symbols: List of symbols (default: DEFAULT_SYMBOLS)
            exchanges: List of exchanges (default: DEFAULT_EXCHANGES)

        Returns:
            Dictionary with symbol data and indicators
        """
        if symbols is None:
            symbols = self.DEFAULT_SYMBOLS
        if exchanges is None:
            exchanges = self.DEFAULT_EXCHANGES

        if len(symbols) != len(exchanges):
            raise ValueError("Symbols and exchanges lists must have the same length")

        results = {}

        for symbol, exchange in zip(symbols, exchanges):
            logger.info(f"Fetching data for {symbol} on {exchange}")

            data = self.fetch_symbol_data(symbol, exchange)
            if data is None:
                logger.warning(f"Skipping {symbol} due to data fetch failure")
                continue

            indicators = self.calculate_indicators(data)

            results[symbol] = {
                'data': data,
                'indicators': indicators,
                'timestamp': datetime.now()
            }

        logger.info(f"Successfully processed {len(results)} symbols")
        return results

    def get_market_summary(self, symbol_data: Dict[str, Dict]) -> Dict[str, any]:
        """
        Generate market summary from symbol data.

        Args:
            symbol_data: Dictionary with symbol data from fetch_all_symbols

        Returns:
            Market summary dictionary
        """
        summary = {
            'total_symbols': len(symbol_data),
            'gainers': [],
            'losers': [],
            'high_volume': [],
            'timestamp': datetime.now().isoformat()
        }

        for symbol, data in symbol_data.items():
            pct_change = data['indicators']['pct_change']
            vol_change = data['indicators']['vol_change_pct']

            if pct_change > 0:
                summary['gainers'].append((symbol, pct_change))
            elif pct_change < 0:
                summary['losers'].append((symbol, pct_change))

            if vol_change > 50:  # Arbitrary threshold for high volume
                summary['high_volume'].append((symbol, vol_change))

        # Sort by absolute change
        summary['gainers'].sort(key=lambda x: x[1], reverse=True)
        summary['losers'].sort(key=lambda x: abs(x[1]), reverse=True)
        summary['high_volume'].sort(key=lambda x: x[1], reverse=True)

        return summary
