"""
Risk management and position sizing module.
Handles position sizing, stop loss, take profit, and risk limits.
"""

from typing import Dict, Optional, Tuple, Any
from datetime import datetime, timedelta
import logging


logger = logging.getLogger(__name__)


class PositionManager:
    """
    Manages position sizing and risk management for trades.
    
    Calculates position sizes based on:
    - Account balance
    - Risk per trade percentage
    - Stop loss distance
    """
    
    def __init__(
        self,
        account_balance: float,
        risk_per_trade: float = 0.02,
        stop_loss_pct: float = 0.02,
        take_profit_pct: float = 0.04,
        max_daily_loss: float = 0.05,
        max_position_size: float = 1000.0
    ):
        """
        Initialize position manager.
        
        Args:
            account_balance: Starting account balance
            risk_per_trade: Risk percentage per trade (default: 0.02 = 2%)
            stop_loss_pct: Stop loss percentage (default: 0.02 = 2%)
            take_profit_pct: Take profit percentage (default: 0.04 = 4%)
            max_daily_loss: Maximum daily loss percentage (default: 0.05 = 5%)
            max_position_size: Maximum position size in base currency (default: 1000.0)
        """
        self.initial_balance = account_balance
        self.current_balance = account_balance
        self.risk_per_trade = risk_per_trade
        self.stop_loss_pct = stop_loss_pct
        self.take_profit_pct = take_profit_pct
        self.max_daily_loss = max_daily_loss
        self.max_position_size = max_position_size
        
        # Track daily P&L
        self.daily_start_balance = account_balance
        self.daily_start_date = datetime.now().date()
        self.daily_pnl = 0.0
        
        # Track current position
        self.current_position = None  # 'long' or 'short'
        self.entry_price = None
        self.position_size = None
        self.stop_loss_price = None
        self.take_profit_price = None
        self.entry_time = None
    
    def calculate_position_size(
        self,
        entry_price: float,
        stop_loss_price: float
    ) -> float:
        """
        Calculate position size based on risk management rules.
        
        Formula: Position Size = (Account Balance × Risk%) / Stop Loss Distance
        
        Args:
            entry_price: Entry price for the trade
            stop_loss_price: Stop loss price
        
        Returns:
            Position size in base currency (e.g., BTC amount for BTC/USDT)
        """
        # Calculate risk amount (dollar amount to risk)
        risk_amount = self.current_balance * self.risk_per_trade
        
        # Calculate stop loss distance (absolute price difference)
        stop_loss_distance = abs(entry_price - stop_loss_price)
        
        if stop_loss_distance == 0:
            logger.warning("Stop loss distance is zero, using minimum position size")
            return 0.0
        
        # Calculate position size
        # Position size = Risk amount / Stop loss distance per unit
        position_size = risk_amount / stop_loss_distance
        
        # Apply maximum position size limit
        position_size = min(position_size, self.max_position_size / entry_price)
        
        logger.info(
            f"Calculated position size: {position_size:.6f} "
            f"(risk: ${risk_amount:.2f}, stop distance: ${stop_loss_distance:.2f})"
        )
        
        return position_size
    
    def calculate_stop_loss_and_take_profit(
        self,
        entry_price: float,
        position_type: str
    ) -> Tuple[float, float]:
        """
        Calculate stop loss and take profit prices.
        
        Args:
            entry_price: Entry price
            position_type: 'long' or 'short'
        
        Returns:
            Tuple of (stop_loss_price, take_profit_price)
        """
        if position_type == 'long':
            stop_loss_price = entry_price * (1 - self.stop_loss_pct)
            take_profit_price = entry_price * (1 + self.take_profit_pct)
        elif position_type == 'short':
            stop_loss_price = entry_price * (1 + self.stop_loss_pct)
            take_profit_price = entry_price * (1 - self.take_profit_pct)
        else:
            raise ValueError(f"Invalid position type: {position_type}")
        
        return stop_loss_price, take_profit_price
    
    def open_position(
        self,
        position_type: str,
        entry_price: float,
        position_size: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Open a new position.
        
        Args:
            position_type: 'long' or 'short'
            entry_price: Entry price
            position_size: Position size (if None, will be calculated)
        
        Returns:
            Dictionary with position details
        """
        if self.current_position is not None:
            raise ValueError(
                f"Cannot open new position. Current position: {self.current_position}"
            )
        
        # Check daily loss limit
        if not self.check_daily_loss_limit():
            raise ValueError("Daily loss limit reached. Trading stopped for today.")
        
        # Calculate stop loss and take profit
        stop_loss_price, take_profit_price = self.calculate_stop_loss_and_take_profit(
            entry_price,
            position_type
        )
        
        # Calculate position size if not provided
        if position_size is None:
            position_size = self.calculate_position_size(entry_price, stop_loss_price)
        
        # Store position details
        self.current_position = position_type
        self.entry_price = entry_price
        self.position_size = position_size
        self.stop_loss_price = stop_loss_price
        self.take_profit_price = take_profit_price
        self.entry_time = datetime.now()
        
        logger.info(
            f"Opened {position_type} position: "
            f"Entry: {entry_price:.2f}, Size: {position_size:.6f}, "
            f"Stop Loss: {stop_loss_price:.2f}, Take Profit: {take_profit_price:.2f}"
        )
        
        return {
            'position_type': position_type,
            'entry_price': entry_price,
            'position_size': position_size,
            'stop_loss_price': stop_loss_price,
            'take_profit_price': take_profit_price,
            'entry_time': self.entry_time
        }
    
    def close_position(
        self,
        exit_price: float,
        reason: str = "Manual close"
    ) -> Dict[str, Any]:
        """
        Close current position and calculate P&L.
        
        Args:
            exit_price: Exit price
            reason: Reason for closing position
        
        Returns:
            Dictionary with trade results including P&L
        """
        if self.current_position is None:
            raise ValueError("No position to close")
        
        # Calculate P&L
        if self.current_position == 'long':
            pnl_pct = (exit_price - self.entry_price) / self.entry_price
        else:  # short
            pnl_pct = (self.entry_price - exit_price) / self.entry_price
        
        pnl_amount = self.current_balance * self.risk_per_trade * (pnl_pct / self.stop_loss_pct)
        
        # Update balance
        self.current_balance += pnl_amount
        
        # Update daily P&L
        self.daily_pnl += pnl_amount
        
        # Store trade details
        trade_result = {
            'position_type': self.current_position,
            'entry_price': self.entry_price,
            'exit_price': exit_price,
            'position_size': self.position_size,
            'pnl_pct': pnl_pct,
            'pnl_amount': pnl_amount,
            'reason': reason,
            'entry_time': self.entry_time,
            'exit_time': datetime.now(),
            'duration': (datetime.now() - self.entry_time).total_seconds() / 60  # minutes
        }
        
        logger.info(
            f"Closed {self.current_position} position: "
            f"Entry: {self.entry_price:.2f}, Exit: {exit_price:.2f}, "
            f"P&L: {pnl_pct*100:.2f}% (${pnl_amount:.2f})"
        )
        
        # Reset position
        self.current_position = None
        self.entry_price = None
        self.position_size = None
        self.stop_loss_price = None
        self.take_profit_price = None
        self.entry_time = None
        
        return trade_result
    
    def check_stop_loss(self, current_price: float) -> Tuple[bool, str]:
        """
        Check if stop loss should be triggered.
        
        Args:
            current_price: Current market price
        
        Returns:
            Tuple of (should_trigger: bool, reason: str)
        """
        if self.current_position is None:
            return False, "No position"
        
        if self.current_position == 'long':
            if current_price <= self.stop_loss_price:
                return True, f"Stop loss triggered at {current_price:.2f}"
        else:  # short
            if current_price >= self.stop_loss_price:
                return True, f"Stop loss triggered at {current_price:.2f}"
        
        return False, "Stop loss not triggered"
    
    def check_take_profit(self, current_price: float) -> Tuple[bool, str]:
        """
        Check if take profit should be triggered.
        
        Args:
            current_price: Current market price
        
        Returns:
            Tuple of (should_trigger: bool, reason: str)
        """
        if self.current_position is None:
            return False, "No position"
        
        if self.current_position == 'long':
            if current_price >= self.take_profit_price:
                return True, f"Take profit triggered at {current_price:.2f}"
        else:  # short
            if current_price <= self.take_profit_price:
                return True, f"Take profit triggered at {current_price:.2f}"
        
        return False, "Take profit not triggered"
    
    def check_daily_loss_limit(self) -> bool:
        """
        Check if daily loss limit has been reached.
        
        Returns:
            True if trading is allowed, False if daily loss limit reached
        """
        # Reset daily tracking if new day
        current_date = datetime.now().date()
        if current_date != self.daily_start_date:
            self.daily_start_balance = self.current_balance
            self.daily_start_date = current_date
            self.daily_pnl = 0.0
        
        # Calculate daily loss percentage
        daily_loss_pct = abs(self.daily_pnl) / self.daily_start_balance if self.daily_pnl < 0 else 0
        
        if daily_loss_pct >= self.max_daily_loss:
            logger.warning(
                f"Daily loss limit reached: {daily_loss_pct*100:.2f}% "
                f"(limit: {self.max_daily_loss*100:.2f}%)"
            )
            return False
        
        return True
    
    def get_position_info(self) -> Dict[str, Any]:
        """Get current position information."""
        if self.current_position is None:
            return {
                'position': None,
                'has_position': False
            }
        
        return {
            'position': self.current_position,
            'has_position': True,
            'entry_price': self.entry_price,
            'position_size': self.position_size,
            'stop_loss_price': self.stop_loss_price,
            'take_profit_price': self.take_profit_price,
            'entry_time': self.entry_time
        }
    
    def get_account_info(self) -> Dict[str, Any]:
        """Get current account information."""
        return {
            'current_balance': self.current_balance,
            'initial_balance': self.initial_balance,
            'total_pnl': self.current_balance - self.initial_balance,
            'total_pnl_pct': (self.current_balance - self.initial_balance) / self.initial_balance * 100,
            'daily_pnl': self.daily_pnl,
            'daily_pnl_pct': (self.daily_pnl / self.daily_start_balance * 100) if self.daily_start_balance > 0 else 0
        }
    
    def update_balance(self, new_balance: float):
        """Update account balance (e.g., from exchange)."""
        self.current_balance = new_balance

