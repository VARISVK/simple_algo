"""
Tests for risk management.
"""

import pytest
from risk.position_manager import PositionManager


def test_position_manager_initialization():
    """Test position manager initialization."""
    pm = PositionManager(
        account_balance=10000.0,
        risk_per_trade=0.02,
        stop_loss_pct=0.02,
        take_profit_pct=0.04
    )
    
    assert pm.current_balance == 10000.0
    assert pm.risk_per_trade == 0.02
    assert pm.current_position is None


def test_calculate_position_size():
    """Test position size calculation."""
    pm = PositionManager(account_balance=10000.0, risk_per_trade=0.02)
    
    entry_price = 100.0
    stop_loss_price = 98.0  # 2% stop loss
    
    position_size = pm.calculate_position_size(entry_price, stop_loss_price)
    
    # Risk amount = 10000 * 0.02 = 200
    # Stop loss distance = 2.0
    # Position size = 200 / 2.0 = 100 units
    expected_size = (10000.0 * 0.02) / 2.0
    assert abs(position_size - expected_size) < 0.01


def test_calculate_stop_loss_and_take_profit():
    """Test stop loss and take profit calculation."""
    pm = PositionManager(account_balance=10000.0)
    
    entry_price = 100.0
    
    # Long position
    stop_loss, take_profit = pm.calculate_stop_loss_and_take_profit(
        entry_price, 'long'
    )
    assert stop_loss == 98.0  # 2% below
    assert take_profit == 104.0  # 4% above
    
    # Short position
    stop_loss, take_profit = pm.calculate_stop_loss_and_take_profit(
        entry_price, 'short'
    )
    assert stop_loss == 102.0  # 2% above
    assert take_profit == 96.0  # 4% below


def test_open_position():
    """Test opening a position."""
    pm = PositionManager(account_balance=10000.0)
    
    trade_data = pm.open_position('long', 100.0)
    
    assert pm.current_position == 'long'
    assert pm.entry_price == 100.0
    assert trade_data['position_type'] == 'long'
    assert 'stop_loss_price' in trade_data
    assert 'take_profit_price' in trade_data


def test_close_position():
    """Test closing a position."""
    pm = PositionManager(account_balance=10000.0)
    
    # Open position
    pm.open_position('long', 100.0)
    
    # Close at profit
    close_data = pm.close_position(104.0, "Take profit")
    
    assert pm.current_position is None
    assert close_data['pnl_pct'] > 0
    assert close_data['pnl_amount'] > 0


def test_check_stop_loss():
    """Test stop loss checking."""
    pm = PositionManager(account_balance=10000.0)
    
    pm.open_position('long', 100.0)
    
    # Price hits stop loss
    should_exit, reason = pm.check_stop_loss(98.0)
    assert should_exit is True
    
    # Price above stop loss
    pm.open_position('long', 100.0)
    should_exit, reason = pm.check_stop_loss(99.0)
    assert should_exit is False


def test_check_take_profit():
    """Test take profit checking."""
    pm = PositionManager(account_balance=10000.0)
    
    pm.open_position('long', 100.0)
    
    # Price hits take profit
    should_exit, reason = pm.check_take_profit(104.0)
    assert should_exit is True
    
    # Price below take profit
    pm.open_position('long', 100.0)
    should_exit, reason = pm.check_take_profit(103.0)
    assert should_exit is False


def test_daily_loss_limit():
    """Test daily loss limit."""
    pm = PositionManager(
        account_balance=10000.0,
        max_daily_loss=0.05
    )
    
    # Open and close losing trades
    pm.open_position('long', 100.0)
    pm.close_position(98.0, "Stop loss")  # -2%
    
    pm.open_position('long', 100.0)
    pm.close_position(98.0, "Stop loss")  # -2% more
    
    # Should still be under limit (4% < 5%)
    assert pm.check_daily_loss_limit() is True
    
    # One more loss
    pm.open_position('long', 100.0)
    pm.close_position(98.0, "Stop loss")  # -2% more (total 6%)
    
    # Should hit daily loss limit
    assert pm.check_daily_loss_limit() is False

