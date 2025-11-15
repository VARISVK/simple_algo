"""
Binance exchange client wrapper using CCXT.
Handles API communication, rate limiting, and error handling.
"""

import ccxt
import time
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
import pandas as pd

logger = logging.getLogger(__name__)


class BinanceClient:
    """
    Binance exchange client with rate limiting and error handling.
    """
    
    def __init__(
        self,
        api_key: str,
        api_secret: str,
        testnet: bool = True,
        sandbox: bool = True
    ):
        """
        Initialize Binance client.
        
        Args:
            api_key: Binance API key
            api_secret: Binance API secret
            testnet: Use testnet (default: True)
            sandbox: Use sandbox mode (default: True)
        """
        self.api_key = api_key
        self.api_secret = api_secret
        self.testnet = testnet
        
        # Initialize CCXT exchange
        exchange_config = {
            'apiKey': api_key,
            'secret': api_secret,
            'enableRateLimit': True,
            'options': {
                'defaultType': 'spot'  # or 'future' for futures
            }
        }
        
        if testnet or sandbox:
            exchange_config['options']['sandboxMode'] = True
        
        try:
            self.exchange = ccxt.binance(exchange_config)
            logger.info(f"Initialized Binance client (testnet: {testnet})")
        except Exception as e:
            logger.error(f"Failed to initialize Binance client: {e}")
            raise
    
    def fetch_ohlcv(
        self,
        symbol: str,
        timeframe: str = '1h',
        since: Optional[int] = None,
        limit: int = 100
    ) -> pd.DataFrame:
        """
        Fetch OHLCV (candlestick) data.
        
        Args:
            symbol: Trading pair symbol (e.g., 'BTC/USDT')
            timeframe: Timeframe (e.g., '1h', '4h', '1d')
            since: Timestamp in milliseconds (optional)
            limit: Number of candles to fetch (default: 100)
        
        Returns:
            DataFrame with columns: ['timestamp', 'open', 'high', 'low', 'close', 'volume']
        """
        max_retries = 3
        retry_delay = 1
        
        for attempt in range(max_retries):
            try:
                ohlcv = self.exchange.fetch_ohlcv(
                    symbol,
                    timeframe,
                    since=since,
                    limit=limit
                )
                
                # Convert to DataFrame
                df = pd.DataFrame(
                    ohlcv,
                    columns=['timestamp', 'open', 'high', 'low', 'close', 'volume']
                )
                
                # Convert timestamp to datetime
                df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
                
                logger.debug(
                    f"Fetched {len(df)} candles for {symbol} "
                    f"({timeframe})"
                )
                
                return df
            
            except ccxt.NetworkError as e:
                logger.warning(f"Network error fetching OHLCV (attempt {attempt + 1}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay * (attempt + 1))
                else:
                    raise
            
            except ccxt.ExchangeError as e:
                logger.error(f"Exchange error fetching OHLCV: {e}")
                raise
            
            except Exception as e:
                logger.error(f"Unexpected error fetching OHLCV: {e}")
                raise
        
        raise Exception("Failed to fetch OHLCV after retries")
    
    def get_ticker(self, symbol: str) -> Dict[str, Any]:
        """
        Get current ticker information.
        
        Args:
            symbol: Trading pair symbol
        
        Returns:
            Dictionary with ticker information
        """
        try:
            ticker = self.exchange.fetch_ticker(symbol)
            return {
                'symbol': symbol,
                'last': ticker['last'],
                'bid': ticker['bid'],
                'ask': ticker['ask'],
                'volume': ticker['quoteVolume'],
                'timestamp': datetime.now()
            }
        except Exception as e:
            logger.error(f"Error fetching ticker for {symbol}: {e}")
            raise
    
    def get_balance(self) -> Dict[str, float]:
        """
        Get account balance.
        
        Returns:
            Dictionary with balances for each currency
        """
        try:
            balance = self.exchange.fetch_balance()
            return balance['total']  # Return total balance (excluding free/used breakdown)
        except Exception as e:
            logger.error(f"Error fetching balance: {e}")
            raise
    
    def create_market_order(
        self,
        symbol: str,
        side: str,
        amount: float
    ) -> Dict[str, Any]:
        """
        Create a market order.
        
        Args:
            symbol: Trading pair symbol
            side: 'buy' or 'sell'
            amount: Order amount in base currency
        
        Returns:
            Order information
        """
        try:
            logger.info(f"Creating {side} market order: {amount} {symbol}")
            order = self.exchange.create_market_order(symbol, side, amount)
            
            logger.info(
                f"Order executed: {order['id']} - "
                f"{side} {amount} {symbol} at {order.get('price', 'market')}"
            )
            
            return order
        except ccxt.InsufficientFunds as e:
            logger.error(f"Insufficient funds for order: {e}")
            raise
        except ccxt.InvalidOrder as e:
            logger.error(f"Invalid order: {e}")
            raise
        except Exception as e:
            logger.error(f"Error creating market order: {e}")
            raise
    
    def create_limit_order(
        self,
        symbol: str,
        side: str,
        amount: float,
        price: float
    ) -> Dict[str, Any]:
        """
        Create a limit order.
        
        Args:
            symbol: Trading pair symbol
            side: 'buy' or 'sell'
            amount: Order amount in base currency
            price: Limit price
        
        Returns:
            Order information
        """
        try:
            logger.info(
                f"Creating {side} limit order: {amount} {symbol} at {price}"
            )
            order = self.exchange.create_limit_order(symbol, side, amount, price)
            
            logger.info(f"Limit order placed: {order['id']}")
            
            return order
        except Exception as e:
            logger.error(f"Error creating limit order: {e}")
            raise
    
    def cancel_order(self, order_id: str, symbol: str) -> Dict[str, Any]:
        """
        Cancel an order.
        
        Args:
            order_id: Order ID
            symbol: Trading pair symbol
        
        Returns:
            Cancellation result
        """
        try:
            result = self.exchange.cancel_order(order_id, symbol)
            logger.info(f"Order cancelled: {order_id}")
            return result
        except Exception as e:
            logger.error(f"Error cancelling order {order_id}: {e}")
            raise
    
    def get_open_orders(self, symbol: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get open orders.
        
        Args:
            symbol: Trading pair symbol (optional, None for all symbols)
        
        Returns:
            List of open orders
        """
        try:
            orders = self.exchange.fetch_open_orders(symbol)
            return orders
        except Exception as e:
            logger.error(f"Error fetching open orders: {e}")
            raise
    
    def get_order_status(self, order_id: str, symbol: str) -> Dict[str, Any]:
        """
        Get order status.
        
        Args:
            order_id: Order ID
            symbol: Trading pair symbol
        
        Returns:
            Order status information
        """
        try:
            order = self.exchange.fetch_order(order_id, symbol)
            return order
        except Exception as e:
            logger.error(f"Error fetching order status: {e}")
            raise

