"""
Order execution logic.
Handles order placement, monitoring, and execution.
"""

import logging
from typing import Dict, Optional, Tuple, Any
from exchange.binance_client import BinanceClient

logger = logging.getLogger(__name__)


class OrderExecutor:
    """
    Handles order execution and monitoring.
    """
    
    def __init__(self, exchange_client: BinanceClient):
        """
        Initialize order executor.
        
        Args:
            exchange_client: Exchange client instance
        """
        self.exchange = exchange_client
    
    def execute_trade(
        self,
        symbol: str,
        signal: str,
        position_size: float,
        order_type: str = 'market'
    ) -> Dict[str, Any]:
        """
        Execute a trade based on signal.
        
        Args:
            symbol: Trading pair symbol
            signal: 'long' or 'short'
            position_size: Position size in base currency
            order_type: 'market' or 'limit' (default: 'market')
        
        Returns:
            Dictionary with order execution details
        """
        if signal not in ['long', 'short']:
            raise ValueError(f"Invalid signal: {signal}. Must be 'long' or 'short'")
        
        # Map signal to order side
        side = 'buy' if signal == 'long' else 'sell'
        
        try:
            if order_type == 'market':
                order = self.exchange.create_market_order(symbol, side, position_size)
            else:
                # For limit orders, we'd need a price
                # This is a simplified version - in production, you'd calculate limit price
                raise NotImplementedError("Limit orders require price calculation")
            
            return {
                'success': True,
                'order_id': order.get('id'),
                'side': side,
                'amount': position_size,
                'symbol': symbol,
                'order_type': order_type,
                'order': order
            }
        
        except Exception as e:
            logger.error(f"Error executing trade: {e}")
            return {
                'success': False,
                'error': str(e),
                'side': side,
                'amount': position_size,
                'symbol': symbol
            }
    
    def close_position(
        self,
        symbol: str,
        position_type: str,
        position_size: float,
        order_type: str = 'market'
    ) -> Dict[str, Any]:
        """
        Close an existing position.
        
        Args:
            symbol: Trading pair symbol
            position_type: 'long' or 'short'
            position_size: Position size to close
            order_type: 'market' or 'limit' (default: 'market')
        
        Returns:
            Dictionary with order execution details
        """
        # Opposite side to close position
        side = 'sell' if position_type == 'long' else 'buy'
        
        try:
            if order_type == 'market':
                order = self.exchange.create_market_order(symbol, side, position_size)
            else:
                raise NotImplementedError("Limit orders require price calculation")
            
            return {
                'success': True,
                'order_id': order.get('id'),
                'side': side,
                'amount': position_size,
                'symbol': symbol,
                'order_type': order_type,
                'order': order
            }
        
        except Exception as e:
            logger.error(f"Error closing position: {e}")
            return {
                'success': False,
                'error': str(e),
                'side': side,
                'amount': position_size,
                'symbol': symbol
            }
    
    def check_order_status(
        self,
        order_id: str,
        symbol: str
    ) -> Optional[Dict[str, Any]]:
        """
        Check the status of an order.
        
        Args:
            order_id: Order ID
            symbol: Trading pair symbol
        
        Returns:
            Order status dictionary or None if error
        """
        try:
            order = self.exchange.get_order_status(order_id, symbol)
            return order
        except Exception as e:
            logger.error(f"Error checking order status: {e}")
            return None

