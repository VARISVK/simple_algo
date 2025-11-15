"""
Tests for Linda Raschke strategy.
"""

import pytest
import numpy as np
import pandas as pd
from datetime import datetime
from strategy.linda_raschke import LindaRaschkeStrategy


def create_sample_data(n=100):
    """Create sample OHLCV data."""
    np.random.seed(42)
    base_price = 100
    prices = base_price + np.cumsum(np.random.randn(n) * 0.5)
    
    timestamps = pd.date_range(start='2024-01-01', periods=n, freq='1H')
    
    data = pd.DataFrame({
        'timestamp': timestamps,
        'open': prices + np.random.randn(n) * 0.1,
        'high': prices + abs(np.random.randn(n) * 0.2),
        'low': prices - abs(np.random.randn(n) * 0.2),
        'close': prices,
        'volume': np.random.rand(n) * 1000
    })
    
    return data


def test_strategy_initialization():
    """Test strategy initialization."""
    strategy = LindaRaschkeStrategy(
        fast_period=3,
        slow_period=10,
        signal_period=16,
        use_trend_filter=True,
        trend_ema_period=50
    )
    
    assert strategy.fast_period == 3
    assert strategy.slow_period == 10
    assert strategy.signal_period == 16
    assert strategy.use_trend_filter is True
    assert strategy.position is None


def test_calculate_indicators():
    """Test indicator calculation."""
    strategy = LindaRaschkeStrategy()
    data = create_sample_data(100)
    
    indicators = strategy.calculate_indicators(data)
    
    assert 'fast_ema' in indicators
    assert 'slow_ema' in indicators
    assert 'oscillator' in indicators
    assert 'signal_line' in indicators
    assert 'trend_ema' in indicators  # If trend filter enabled


def test_generate_signal():
    """Test signal generation."""
    strategy = LindaRaschkeStrategy()
    data = create_sample_data(100)
    
    signal_data = strategy.generate_signal(data)
    
    assert 'signal' in signal_data
    assert 'reason' in signal_data
    assert 'indicators' in signal_data
    assert 'timestamp' in signal_data
    
    assert signal_data['signal'] in ['long', 'short', 'hold']


def test_should_exit_position():
    """Test exit condition checking."""
    strategy = LindaRaschkeStrategy()
    
    # Test long position stop loss
    should_exit, reason = strategy.should_exit_position(
        current_price=98.0,  # 2% below entry
        entry_price=100.0,
        position_type='long',
        stop_loss_pct=0.02,
        take_profit_pct=0.04
    )
    assert should_exit is True
    assert 'stop loss' in reason.lower()
    
    # Test long position take profit
    should_exit, reason = strategy.should_exit_position(
        current_price=104.0,  # 4% above entry
        entry_price=100.0,
        position_type='long',
        stop_loss_pct=0.02,
        take_profit_pct=0.04
    )
    assert should_exit is True
    assert 'take profit' in reason.lower()
    
    # Test short position stop loss
    should_exit, reason = strategy.should_exit_position(
        current_price=102.0,  # 2% above entry
        entry_price=100.0,
        position_type='short',
        stop_loss_pct=0.02,
        take_profit_pct=0.04
    )
    assert should_exit is True


def test_position_management():
    """Test position state management."""
    strategy = LindaRaschkeStrategy()
    
    assert strategy.position is None
    
    strategy.update_position('long', 100.0)
    assert strategy.position == 'long'
    assert strategy.entry_price == 100.0
    
    position_info = strategy.get_position()
    assert position_info['position'] == 'long'
    assert position_info['entry_price'] == 100.0
    
    strategy.update_position(None)
    assert strategy.position is None
    assert strategy.entry_price is None

