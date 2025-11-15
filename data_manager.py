"""
Data manager for fetching and processing market data.
"""

import pandas as pd
import logging
from typing import Optional
from exchange.binance_client import BinanceClient

logger = logging.getLogger(__name__)


class DataManager:
    """
    Manages fetching and processing of market data.
    """
    
    def __init__(self, exchange_client: BinanceClient):
        """
        Initialize data manager.
        
        Args:
            exchange_client: Exchange client instance
        """
        self.exchange = exchange_client
    
    def get_ohlcv_data(
        self,
        symbol: str,
        timeframe: str,
        limit: int = 200
    ) -> pd.DataFrame:
        """
        Fetch OHLCV data for strategy calculations.
        
        Args:
            symbol: Trading pair symbol
            timeframe: Timeframe (e.g., '1h', '4h')
            limit: Number of candles to fetch (default: 200)
        
        Returns:
            DataFrame with OHLCV data
        """
        try:
            # Fetch more data than needed to ensure we have enough for indicators
            df = self.exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
            
            # Validate data
            if df.empty:
                raise ValueError(f"No data returned for {symbol} {timeframe}")
            
            if len(df) < 50:
                logger.warning(
                    f"Limited data available: {len(df)} candles. "
                    f"Some indicators may not be calculated."
                )
            
            logger.debug(
                f"Fetched {len(df)} candles for {symbol} "
                f"({timeframe})"
            )
            
            return df
        
        except Exception as e:
            logger.error(f"Error fetching OHLCV data: {e}")
            raise
    
    def get_current_price(self, symbol: str) -> float:
        """
        Get current market price.
        
        Args:
            symbol: Trading pair symbol
        
        Returns:
            Current price
        """
        try:
            ticker = self.exchange.get_ticker(symbol)
            return ticker['last']
        except Exception as e:
            logger.error(f"Error fetching current price: {e}")
            raise

