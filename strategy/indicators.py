"""
Technical indicator calculations using TA-Lib.
Implements EMA, SMA, and oscillator calculations for the Linda Raschke strategy.
"""

import numpy as np
import pandas as pd
from typing import Dict
try:
    import talib
    TALIB_AVAILABLE = True
except ImportError:
    TALIB_AVAILABLE = False
    print("Warning: TA-Lib not available. Using fallback implementations.")


def calculate_ema(data: np.ndarray, period: int) -> np.ndarray:
    """
    Calculate Exponential Moving Average (EMA).
    
    Args:
        data: Array of closing prices
        period: EMA period
    
    Returns:
        Array of EMA values
    """
    if TALIB_AVAILABLE:
        return talib.EMA(data, timeperiod=period)
    else:
        # Fallback implementation
        return pd.Series(data).ewm(span=period, adjust=False).mean().values


def calculate_sma(data: np.ndarray, period: int) -> np.ndarray:
    """
    Calculate Simple Moving Average (SMA).
    
    Args:
        data: Array of values
        period: SMA period
    
    Returns:
        Array of SMA values
    """
    if TALIB_AVAILABLE:
        return talib.SMA(data, timeperiod=period)
    else:
        # Fallback implementation
        return pd.Series(data).rolling(window=period).mean().values


def calculate_linda_raschke_oscillator(
    close_prices: np.ndarray,
    fast_period: int = 3,
    slow_period: int = 10,
    signal_period: int = 16
) -> Dict[str, np.ndarray]:
    """
    Calculate Linda Raschke 3-10 Oscillator indicators.
    
    This function calculates:
    1. Fast EMA (3-period)
    2. Slow EMA (10-period)
    3. Oscillator (Fast EMA - Slow EMA)
    4. Signal Line (16-period SMA of oscillator)
    
    Args:
        close_prices: Array of closing prices
        fast_period: Fast EMA period (default: 3)
        slow_period: Slow EMA period (default: 10)
        signal_period: Signal line SMA period (default: 16)
    
    Returns:
        Dictionary containing:
        - fast_ema: Fast EMA values
        - slow_ema: Slow EMA values
        - oscillator: Oscillator values (fast_ema - slow_ema)
        - signal_line: Signal line values (SMA of oscillator)
    """
    if len(close_prices) < max(fast_period, slow_period, signal_period) + 10:
        raise ValueError(
            f"Insufficient data points. Need at least "
            f"{max(fast_period, slow_period, signal_period) + 10} points, "
            f"got {len(close_prices)}"
        )
    
    # Calculate EMAs
    fast_ema = calculate_ema(close_prices, fast_period)
    slow_ema = calculate_ema(close_prices, slow_period)
    
    # Calculate oscillator (difference between fast and slow EMA)
    oscillator = fast_ema - slow_ema
    
    # Calculate signal line (SMA of oscillator, NOT EMA)
    signal_line = calculate_sma(oscillator, signal_period)
    
    return {
        "fast_ema": fast_ema,
        "slow_ema": slow_ema,
        "oscillator": oscillator,
        "signal_line": signal_line
    }


def calculate_trend_filter(
    close_prices: np.ndarray,
    period: int = 50
) -> np.ndarray:
    """
    Calculate trend filter EMA.
    
    Args:
        close_prices: Array of closing prices
        period: EMA period for trend filter (default: 50)
    
    Returns:
        Array of trend EMA values
    """
    if len(close_prices) < period + 5:
        raise ValueError(
            f"Insufficient data points for trend filter. "
            f"Need at least {period + 5} points, got {len(close_prices)}"
        )
    
    return calculate_ema(close_prices, period)


def detect_crossover(
    current_value: float,
    previous_value: float,
    current_signal: float,
    previous_signal: float
) -> str:
    """
    Detect crossover between oscillator and signal line.
    
    Args:
        current_value: Current oscillator value
        previous_value: Previous oscillator value
        current_signal: Current signal line value
        previous_signal: Previous signal line value
    
    Returns:
        'bullish' if oscillator crosses above signal line
        'bearish' if oscillator crosses below signal line
        'none' if no crossover
    """
    # Check for bullish crossover (oscillator crosses above signal line)
    if (previous_value <= previous_signal and current_value > current_signal):
        return 'bullish'
    
    # Check for bearish crossover (oscillator crosses below signal line)
    if (previous_value >= previous_signal and current_value < current_signal):
        return 'bearish'
    
    return 'none'


def validate_indicators(indicators: Dict[str, np.ndarray]) -> bool:
    """
    Validate that indicators are calculated correctly.
    
    Args:
        indicators: Dictionary of indicator arrays
    
    Returns:
        True if valid, raises ValueError if invalid
    """
    required_keys = ['fast_ema', 'slow_ema', 'oscillator', 'signal_line']
    
    for key in required_keys:
        if key not in indicators:
            raise ValueError(f"Missing required indicator: {key}")
        
        if indicators[key] is None or len(indicators[key]) == 0:
            raise ValueError(f"Indicator {key} is empty")
        
        # Check for NaN values (except at the beginning where indicators may not be calculated)
        nan_count = np.isnan(indicators[key]).sum()
        if nan_count == len(indicators[key]):
            raise ValueError(f"Indicator {key} contains only NaN values")
    
    return True

