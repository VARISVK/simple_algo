"""
Linda Raschke 3-10 Oscillator Trading Strategy Implementation.

This module implements the Linda Raschke 3-10 Oscillator strategy:
- Fast EMA: 3-period
- Slow EMA: 10-period
- Oscillator: Fast EMA - Slow EMA
- Signal Line: 16-period SMA of oscillator
- Trend Filter: Optional 50 or 200-period EMA
"""

import numpy as np
import pandas as pd
from typing import Dict, Optional, Tuple, Any
from datetime import datetime

from strategy.indicators import (
    calculate_linda_raschke_oscillator,
    calculate_trend_filter,
    detect_crossover,
    validate_indicators
)


class LindaRaschkeStrategy:
    """
    Linda Raschke 3-10 Oscillator Trading Strategy.
    
    Entry Rules:
    - LONG: Oscillator crosses above signal line + price above trend EMA
    - SHORT: Oscillator crosses below signal line + price below trend EMA
    
    Exit Rules:
    - Fixed stop loss: 2% from entry
    - Fixed take profit: 4% from entry
    - Or exit on opposite crossover signal
    """
    
    def __init__(
        self,
        fast_period: int = 3,
        slow_period: int = 10,
        signal_period: int = 16,
        use_trend_filter: bool = True,
        trend_ema_period: int = 50
    ):
        """
        Initialize the Linda Raschke strategy.
        
        Args:
            fast_period: Fast EMA period (default: 3)
            slow_period: Slow EMA period (default: 10)
            signal_period: Signal line SMA period (default: 16)
            use_trend_filter: Whether to use trend filter (default: True)
            trend_ema_period: Trend filter EMA period (default: 50)
        """
        self.fast_period = fast_period
        self.slow_period = slow_period
        self.signal_period = signal_period
        self.use_trend_filter = use_trend_filter
        self.trend_ema_period = trend_ema_period
        
        # Store previous values for crossover detection
        self.previous_oscillator = None
        self.previous_signal = None
        
        # Current position state
        self.position = None  # 'long', 'short', or None
        self.entry_price = None
        self.entry_time = None
    
    def calculate_indicators(self, ohlcv_data: pd.DataFrame) -> Dict[str, np.ndarray]:
        """
        Calculate all indicators for the strategy.
        
        Args:
            ohlcv_data: DataFrame with columns ['timestamp', 'open', 'high', 'low', 'close', 'volume']
        
        Returns:
            Dictionary containing all calculated indicators
        """
        close_prices = ohlcv_data['close'].values
        
        # Calculate main oscillator indicators
        indicators = calculate_linda_raschke_oscillator(
            close_prices,
            fast_period=self.fast_period,
            slow_period=self.slow_period,
            signal_period=self.signal_period
        )
        
        # Calculate trend filter if enabled
        if self.use_trend_filter:
            indicators['trend_ema'] = calculate_trend_filter(
                close_prices,
                period=self.trend_ema_period
            )
        
        # Validate indicators
        validate_indicators(indicators)
        
        return indicators
    
    def generate_signal(
        self,
        ohlcv_data: pd.DataFrame,
        indicators: Optional[Dict[str, np.ndarray]] = None
    ) -> Dict[str, Any]:
        """
        Generate trading signal based on current market conditions.
        
        Args:
            ohlcv_data: DataFrame with OHLCV data
            indicators: Pre-calculated indicators (optional)
        
        Returns:
            Dictionary containing:
            - signal: 'long', 'short', or 'hold'
            - reason: Explanation of the signal
            - indicators: Current indicator values
            - timestamp: Signal generation time
        """
        if indicators is None:
            indicators = self.calculate_indicators(ohlcv_data)
        
        # Get current and previous values
        current_idx = len(ohlcv_data) - 1
        previous_idx = current_idx - 1 if current_idx > 0 else 0
        
        # Extract current values
        current_close = ohlcv_data['close'].iloc[current_idx]
        current_oscillator = indicators['oscillator'][current_idx]
        current_signal = indicators['signal_line'][current_idx]
        
        # Extract previous values (for crossover detection)
        if previous_idx >= 0:
            previous_oscillator = indicators['oscillator'][previous_idx]
            previous_signal = indicators['signal_line'][previous_idx]
        else:
            previous_oscillator = self.previous_oscillator
            previous_signal = self.previous_signal
        
        # Check for NaN values
        if (np.isnan(current_oscillator) or np.isnan(current_signal) or
            np.isnan(previous_oscillator) or np.isnan(previous_signal)):
            return {
                'signal': 'hold',
                'reason': 'Insufficient data for signal generation',
                'indicators': {
                    'oscillator': current_oscillator,
                    'signal_line': current_signal,
                    'close': current_close
                },
                'timestamp': datetime.now()
            }
        
        # Detect crossover
        crossover = detect_crossover(
            current_oscillator,
            previous_oscillator,
            current_signal,
            previous_signal
        )
        
        # Check trend filter if enabled
        trend_ok = True
        if self.use_trend_filter and 'trend_ema' in indicators:
            current_trend_ema = indicators['trend_ema'][current_idx]
            if np.isnan(current_trend_ema):
                trend_ok = False
            else:
                # For long: price must be above trend EMA
                # For short: price must be below trend EMA
                if crossover == 'bullish':
                    trend_ok = current_close > current_trend_ema
                elif crossover == 'bearish':
                    trend_ok = current_close < current_trend_ema
        
        # Generate signal based on crossover and trend filter
        signal = 'hold'
        reason = 'No crossover signal'
        
        if crossover == 'bullish' and trend_ok:
            signal = 'long'
            reason = 'Bullish crossover: Oscillator crossed above signal line'
            if self.use_trend_filter:
                reason += f' and price above trend EMA ({current_trend_ema:.2f})'
        
        elif crossover == 'bearish' and trend_ok:
            signal = 'short'
            reason = 'Bearish crossover: Oscillator crossed below signal line'
            if self.use_trend_filter:
                reason += f' and price below trend EMA ({current_trend_ema:.2f})'
        
        # Store current values as previous for next iteration
        self.previous_oscillator = current_oscillator
        self.previous_signal = current_signal
        
        return {
            'signal': signal,
            'reason': reason,
            'indicators': {
                'oscillator': current_oscillator,
                'signal_line': current_signal,
                'close': current_close,
                'fast_ema': indicators['fast_ema'][current_idx],
                'slow_ema': indicators['slow_ema'][current_idx],
                'trend_ema': indicators.get('trend_ema', [None])[current_idx] if self.use_trend_filter else None
            },
            'timestamp': datetime.now(),
            'crossover': crossover
        }
    
    def should_exit_position(
        self,
        current_price: float,
        entry_price: float,
        position_type: str,
        stop_loss_pct: float = 0.02,
        take_profit_pct: float = 0.04,
        opposite_signal: bool = False
    ) -> Tuple[bool, str]:
        """
        Check if current position should be exited.
        
        Args:
            current_price: Current market price
            entry_price: Entry price of the position
            position_type: 'long' or 'short'
            stop_loss_pct: Stop loss percentage (default: 0.02 = 2%)
            take_profit_pct: Take profit percentage (default: 0.04 = 4%)
            opposite_signal: Whether opposite signal was generated
        
        Returns:
            Tuple of (should_exit: bool, reason: str)
        """
        if position_type is None or entry_price is None:
            return False, "No position to exit"
        
        # Calculate price change
        if position_type == 'long':
            price_change_pct = (current_price - entry_price) / entry_price
            stop_loss_price = entry_price * (1 - stop_loss_pct)
            take_profit_price = entry_price * (1 + take_profit_pct)
        else:  # short
            price_change_pct = (entry_price - current_price) / entry_price
            stop_loss_price = entry_price * (1 + stop_loss_pct)
            take_profit_price = entry_price * (1 - take_profit_pct)
        
        # Check stop loss
        if position_type == 'long' and current_price <= stop_loss_price:
            return True, f"Stop loss hit at {current_price:.2f} (entry: {entry_price:.2f})"
        
        if position_type == 'short' and current_price >= stop_loss_price:
            return True, f"Stop loss hit at {current_price:.2f} (entry: {entry_price:.2f})"
        
        # Check take profit
        if position_type == 'long' and current_price >= take_profit_price:
            return True, f"Take profit hit at {current_price:.2f} (entry: {entry_price:.2f})"
        
        if position_type == 'short' and current_price <= take_profit_price:
            return True, f"Take profit hit at {current_price:.2f} (entry: {entry_price:.2f})"
        
        # Check opposite signal
        if opposite_signal:
            return True, "Opposite signal generated"
        
        return False, "Hold position"
    
    def update_position(self, position: Optional[str], entry_price: Optional[float] = None):
        """
        Update current position state.
        
        Args:
            position: 'long', 'short', or None
            entry_price: Entry price (optional)
        """
        self.position = position
        self.entry_price = entry_price
        if entry_price is not None:
            self.entry_time = datetime.now()
        else:
            self.entry_time = None
    
    def get_position(self) -> Dict[str, Any]:
        """Get current position information."""
        return {
            'position': self.position,
            'entry_price': self.entry_price,
            'entry_time': self.entry_time
        }

