"""
Tests for indicator calculations.
"""

import pytest
import numpy as np
import pandas as pd
from strategy.indicators import (
    calculate_ema,
    calculate_sma,
    calculate_linda_raschke_oscillator,
    detect_crossover,
    validate_indicators
)


def test_calculate_ema():
    """Test EMA calculation."""
    data = np.array([100, 101, 102, 103, 104, 105, 106, 107, 108, 109])
    ema = calculate_ema(data, period=3)
    
    assert len(ema) == len(data)
    assert not np.isnan(ema[-1])  # Last value should be calculated


def test_calculate_sma():
    """Test SMA calculation."""
    data = np.array([100, 101, 102, 103, 104, 105, 106, 107, 108, 109])
    sma = calculate_sma(data, period=3)
    
    assert len(sma) == len(data)
    # SMA of last 3 values should be approximately 108
    assert abs(sma[-1] - 108) < 1


def test_calculate_linda_raschke_oscillator():
    """Test Linda Raschke oscillator calculation."""
    # Generate sample price data
    np.random.seed(42)
    close_prices = 100 + np.cumsum(np.random.randn(100) * 0.5)
    
    indicators = calculate_linda_raschke_oscillator(
        close_prices,
        fast_period=3,
        slow_period=10,
        signal_period=16
    )
    
    assert 'fast_ema' in indicators
    assert 'slow_ema' in indicators
    assert 'oscillator' in indicators
    assert 'signal_line' in indicators
    
    # Oscillator should be fast_ema - slow_ema
    oscillator_calc = indicators['fast_ema'] - indicators['slow_ema']
    np.testing.assert_array_almost_equal(
        indicators['oscillator'],
        oscillator_calc,
        decimal=5
    )
    
    # Validate indicators
    validate_indicators(indicators)


def test_detect_crossover():
    """Test crossover detection."""
    # Bullish crossover
    result = detect_crossover(
        current_value=1.0,
        previous_value=0.5,
        current_signal=0.8,
        previous_signal=0.9
    )
    assert result == 'bullish'
    
    # Bearish crossover
    result = detect_crossover(
        current_value=0.5,
        previous_value=1.0,
        current_signal=0.8,
        previous_signal=0.7
    )
    assert result == 'bearish'
    
    # No crossover
    result = detect_crossover(
        current_value=1.0,
        previous_value=1.1,
        current_signal=0.8,
        previous_signal=0.7
    )
    assert result == 'none'


def test_insufficient_data():
    """Test handling of insufficient data."""
    data = np.array([100, 101, 102])  # Only 3 data points
    
    with pytest.raises(ValueError):
        calculate_linda_raschke_oscillator(data, fast_period=3, slow_period=10, signal_period=16)

