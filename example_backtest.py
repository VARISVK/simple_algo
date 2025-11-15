"""
Example script for running backtests.
This demonstrates how to use the backtesting functionality.
"""

import pandas as pd
from backtest import run_backtest
from exchange.binance_client import BinanceClient
from config.settings import Settings
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def example_backtest_with_historical_data():
    """
    Example: Run backtest using historical data from Binance.
    """
    # Initialize settings
    settings = Settings()
    
    # Initialize exchange client (testnet)
    exchange = BinanceClient(
        api_key=settings.api_key,
        api_secret=settings.api_secret,
        testnet=True
    )
    
    # Fetch historical data
    trading_config = settings.get_trading_config()
    symbol = trading_config.get("symbol", "BTC/USDT")
    timeframe = trading_config.get("timeframe", "1h")
    
    logger.info(f"Fetching historical data for {symbol} on {timeframe} timeframe...")
    ohlcv_data = exchange.fetch_ohlcv(symbol, timeframe, limit=500)
    
    # Run backtest
    strategy_config = settings.get_strategy_config()
    risk_config = settings.get_risk_config()
    
    logger.info("Running backtest...")
    results = run_backtest(
        ohlcv_data=ohlcv_data,
        fast_period=strategy_config.get("fast_period", 3),
        slow_period=strategy_config.get("slow_period", 10),
        signal_period=strategy_config.get("signal_period", 16),
        use_trend_filter=strategy_config.get("use_trend_filter", True),
        trend_ema_period=strategy_config.get("trend_ema_period", 50),
        initial_balance=10000.0,
        risk_per_trade=risk_config.get("risk_per_trade", 0.02),
        stop_loss_pct=risk_config.get("stop_loss_pct", 0.02),
        take_profit_pct=risk_config.get("take_profit_pct", 0.04)
    )
    
    # Print results
    print("\n" + "=" * 60)
    print("BACKTEST RESULTS")
    print("=" * 60)
    print(f"Total Trades: {results.get('total_trades', 0)}")
    print(f"Winning Trades: {results.get('winning_trades', 0)}")
    print(f"Losing Trades: {results.get('losing_trades', 0)}")
    print(f"Win Rate: {results.get('win_rate', 0):.2f}%")
    print(f"\nInitial Balance: ${results.get('initial_balance', 0):.2f}")
    print(f"Final Balance: ${results.get('final_balance', 0):.2f}")
    print(f"Total P&L: {results.get('total_pnl_pct', 0):.2f}% (${results.get('total_pnl', 0):.2f})")
    print(f"\nAverage Win: ${results.get('avg_win', 0):.2f}")
    print(f"Average Loss: ${results.get('avg_loss', 0):.2f}")
    print(f"Profit Factor: {results.get('profit_factor', 0):.2f}")
    print(f"\nMax Drawdown: {results.get('max_drawdown_pct', 0):.2f}% (${results.get('max_drawdown', 0):.2f})")
    print(f"Sharpe Ratio: {results.get('sharpe_ratio', 0):.2f}")
    print("=" * 60)
    
    return results


def example_backtest_with_csv():
    """
    Example: Run backtest using CSV file with historical data.
    CSV should have columns: timestamp, open, high, low, close, volume
    """
    # Load data from CSV
    df = pd.read_csv('historical_data.csv')
    
    # Ensure timestamp column is datetime
    if 'timestamp' in df.columns:
        df['timestamp'] = pd.to_datetime(df['timestamp'])
    else:
        # If no timestamp, create one
        df['timestamp'] = pd.date_range(start='2024-01-01', periods=len(df), freq='1H')
    
    # Run backtest
    results = run_backtest(
        ohlcv_data=df,
        fast_period=3,
        slow_period=10,
        signal_period=16,
        use_trend_filter=True,
        trend_ema_period=50,
        initial_balance=10000.0,
        risk_per_trade=0.02,
        stop_loss_pct=0.02,
        take_profit_pct=0.04
    )
    
    print(f"Backtest completed: {results.get('total_trades', 0)} trades")
    return results


if __name__ == "__main__":
    # Run example backtest
    try:
        example_backtest_with_historical_data()
    except Exception as e:
        logger.error(f"Error running backtest: {e}")
        print("\nNote: Make sure you have:")
        print("1. Set up .env file with Binance API credentials")
        print("2. Installed all dependencies (pip install -r requirements.txt)")
        print("3. TA-Lib library installed")

