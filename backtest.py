"""
Backtesting module for the Linda Raschke 3-10 Oscillator strategy.
Tests strategy on historical data and calculates performance metrics.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from datetime import datetime
import logging
import ccxt

from strategy.linda_raschke import LindaRaschkeStrategy
from risk.position_manager import PositionManager

logger = logging.getLogger(__name__)


def fetch_historical_data_public(
    symbol: str,
    timeframe: str = '1h',
    limit: int = 500
) -> pd.DataFrame:
    """
    Fetch historical OHLCV data from Binance public API (no authentication required).
    Uses real production data, not testnet.
    
    Args:
        symbol: Trading pair symbol (e.g., 'BTC/USDT')
        timeframe: Timeframe (e.g., '1h', '4h', '1d')
        limit: Number of candles to fetch
    
    Returns:
        DataFrame with OHLCV data
    """
    try:
        # Create exchange instance without authentication (public API)
        exchange = ccxt.binance({
            'enableRateLimit': True,
            'options': {
                'defaultType': 'spot'
            }
        })
        
        # Fetch OHLCV data
        ohlcv = exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
        
        # Convert to DataFrame
        df = pd.DataFrame(
            ohlcv,
            columns=['timestamp', 'open', 'high', 'low', 'close', 'volume']
        )
        
        # Convert timestamp to datetime
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        
        logger.info(f"Fetched {len(df)} candles for {symbol} ({timeframe})")
        
        return df
    
    except Exception as e:
        logger.error(f"Error fetching historical data: {e}")
        raise


def load_data_from_csv(file_path: str) -> pd.DataFrame:
    """
    Load OHLCV data from CSV file.
    
    CSV should have columns: timestamp, open, high, low, close, volume
    Or: date, open, high, low, close, volume
    
    Args:
        file_path: Path to CSV file
    
    Returns:
        DataFrame with OHLCV data
    """
    try:
        df = pd.read_csv(file_path)
        
        # Handle different timestamp column names
        if 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'])
        elif 'date' in df.columns:
            df['timestamp'] = pd.to_datetime(df['date'])
            df = df.drop('date', axis=1)
        else:
            raise ValueError("CSV must have 'timestamp' or 'date' column")
        
        # Ensure required columns exist
        required_cols = ['open', 'high', 'low', 'close', 'volume']
        missing = [col for col in required_cols if col not in df.columns]
        if missing:
            raise ValueError(f"Missing required columns: {missing}")
        
        # Sort by timestamp
        df = df.sort_values('timestamp').reset_index(drop=True)
        
        logger.info(f"Loaded {len(df)} candles from {file_path}")
        
        return df
    
    except Exception as e:
        logger.error(f"Error loading CSV data: {e}")
        raise


class Backtester:
    """
    Backtesting engine for trading strategies.
    """
    
    def __init__(
        self,
        strategy: LindaRaschkeStrategy,
        initial_balance: float = 10000.0,
        risk_per_trade: float = 0.02,
        stop_loss_pct: float = 0.02,
        take_profit_pct: float = 0.04
    ):
        """
        Initialize backtester.
        
        Args:
            strategy: Strategy instance
            initial_balance: Starting balance
            risk_per_trade: Risk per trade percentage
            stop_loss_pct: Stop loss percentage
            take_profit_pct: Take profit percentage
        """
        self.strategy = strategy
        self.position_manager = PositionManager(
            account_balance=initial_balance,
            risk_per_trade=risk_per_trade,
            stop_loss_pct=stop_loss_pct,
            take_profit_pct=take_profit_pct,
            max_daily_loss=1.0  # Disable daily loss limit for backtesting
        )
        
        self.trades = []
        self.equity_curve = []
    
    def run(
        self,
        ohlcv_data: pd.DataFrame,
        symbol: str = "BTC/USDT"
    ) -> Dict:
        """
        Run backtest on historical data.
        
        Args:
            ohlcv_data: DataFrame with OHLCV data
            symbol: Trading pair symbol
        
        Returns:
            Dictionary with backtest results
        """
        logger.info(f"Starting backtest on {len(ohlcv_data)} candles")
        
        # Calculate indicators once for the entire dataset
        indicators = self.strategy.calculate_indicators(ohlcv_data)
        
        # Iterate through data
        for i in range(50, len(ohlcv_data)):  # Start from index 50 to ensure indicators are calculated
            current_data = ohlcv_data.iloc[:i+1]
            current_price = ohlcv_data.iloc[i]['close']
            current_time = ohlcv_data.iloc[i]['timestamp']
            
            # Get current indicators for this point
            current_indicators = {
                key: values[i] if i < len(values) else None
                for key, values in indicators.items()
            }
            
            # Check for NaN values
            if any(np.isnan(v) if v is not None else True for v in current_indicators.values()):
                continue
            
            # Check existing position
            position_info = self.position_manager.get_position_info()
            
            if position_info['has_position']:
                # Check stop loss
                should_exit, reason = self.position_manager.check_stop_loss(current_price)
                if should_exit:
                    self._close_position(current_price, current_time, reason)
                    continue
                
                # Check take profit
                should_exit, reason = self.position_manager.check_take_profit(current_price)
                if should_exit:
                    self._close_position(current_price, current_time, reason)
                    continue
            
            # Generate signal
            try:
                signal_data = self.strategy.generate_signal(current_data, indicators=None)
                signal_type = signal_data.get('signal', 'hold')
                
                # Handle new position entry
                if signal_type in ['long', 'short'] and not position_info['has_position']:
                    self._open_position(
                        signal_type,
                        current_price,
                        current_time,
                        symbol
                    )
                
                # Handle opposite signal exit
                elif position_info['has_position']:
                    current_position = position_info['position']
                    if (signal_type == 'long' and current_position == 'short') or \
                       (signal_type == 'short' and current_position == 'long'):
                        self._close_position(
                            current_price,
                            current_time,
                            "Opposite signal generated"
                        )
            
            except Exception as e:
                logger.warning(f"Error processing signal at index {i}: {e}")
                continue
            
            # Record equity
            account_info = self.position_manager.get_account_info()
            self.equity_curve.append({
                'timestamp': current_time,
                'equity': account_info['current_balance'],
                'price': current_price
            })
        
        # Close any open positions
        position_info = self.position_manager.get_position_info()
        if position_info['has_position']:
            final_price = ohlcv_data.iloc[-1]['close']
            final_time = ohlcv_data.iloc[-1]['timestamp']
            self._close_position(final_price, final_time, "End of backtest")
        
        # Calculate performance metrics
        results = self._calculate_metrics(ohlcv_data)
        
        return results
    
    def _open_position(
        self,
        signal_type: str,
        entry_price: float,
        entry_time: datetime,
        symbol: str
    ):
        """Open a position in backtest."""
        try:
            stop_loss_price, take_profit_price = \
                self.position_manager.calculate_stop_loss_and_take_profit(
                    entry_price,
                    signal_type
                )
            
            position_size = self.position_manager.calculate_position_size(
                entry_price,
                stop_loss_price
            )
            
            if position_size <= 0:
                return
            
            trade_data = self.position_manager.open_position(
                signal_type,
                entry_price,
                position_size
            )
            
            trade_data['symbol'] = symbol
            trade_data['entry_time'] = entry_time
            self.trades.append(trade_data)
            
            self.strategy.update_position(signal_type, entry_price)
        
        except Exception as e:
            logger.warning(f"Error opening position: {e}")
    
    def _close_position(
        self,
        exit_price: float,
        exit_time: datetime,
        reason: str
    ):
        """Close a position in backtest."""
        try:
            close_data = self.position_manager.close_position(exit_price, reason)
            close_data['exit_time'] = exit_time
            
            # Update last trade
            if self.trades:
                last_trade = self.trades[-1]
                last_trade.update(close_data)
            
            self.strategy.update_position(None)
        
        except Exception as e:
            logger.warning(f"Error closing position: {e}")
    
    def _calculate_metrics(self, ohlcv_data: pd.DataFrame) -> Dict:
        """Calculate performance metrics."""
        if not self.trades:
            return {
                'total_trades': 0,
                'message': 'No trades executed'
            }
        
        # Filter completed trades
        completed_trades = [t for t in self.trades if 'exit_price' in t and t.get('exit_price') is not None]
        
        if not completed_trades:
            return {
                'total_trades': len(self.trades),
                'open_trades': len(self.trades),
                'message': 'No completed trades'
            }
        
        # Calculate metrics
        pnl_amounts = [t['pnl_amount'] for t in completed_trades]
        pnl_pcts = [t['pnl_pct'] for t in completed_trades]
        
        winning_trades = [t for t in completed_trades if t['pnl_amount'] > 0]
        losing_trades = [t for t in completed_trades if t['pnl_amount'] < 0]
        
        total_pnl = sum(pnl_amounts)
        total_pnl_pct = (total_pnl / self.position_manager.initial_balance) * 100
        
        win_rate = len(winning_trades) / len(completed_trades) * 100 if completed_trades else 0
        
        avg_win = np.mean([t['pnl_amount'] for t in winning_trades]) if winning_trades else 0
        avg_loss = np.mean([t['pnl_amount'] for t in losing_trades]) if losing_trades else 0
        
        profit_factor = abs(sum([t['pnl_amount'] for t in winning_trades]) / 
                           sum([t['pnl_amount'] for t in losing_trades])) if losing_trades else float('inf')
        
        # Calculate equity curve metrics
        equity_values = [e['equity'] for e in self.equity_curve]
        if equity_values:
            peak = equity_values[0]
            max_drawdown = 0
            max_drawdown_pct = 0
            
            for equity in equity_values:
                if equity > peak:
                    peak = equity
                drawdown = peak - equity
                drawdown_pct = (drawdown / peak) * 100
                
                if drawdown > max_drawdown:
                    max_drawdown = drawdown
                if drawdown_pct > max_drawdown_pct:
                    max_drawdown_pct = drawdown_pct
        else:
            max_drawdown = 0
            max_drawdown_pct = 0
        
        # Calculate Sharpe ratio (simplified)
        if len(pnl_pcts) > 1:
            returns = np.array(pnl_pcts)
            sharpe_ratio = np.mean(returns) / np.std(returns) * np.sqrt(252) if np.std(returns) > 0 else 0
        else:
            sharpe_ratio = 0
        
        account_info = self.position_manager.get_account_info()
        
        return {
            'total_trades': len(completed_trades),
            'winning_trades': len(winning_trades),
            'losing_trades': len(losing_trades),
            'win_rate': win_rate,
            'total_pnl': total_pnl,
            'total_pnl_pct': total_pnl_pct,
            'initial_balance': self.position_manager.initial_balance,
            'final_balance': account_info['current_balance'],
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'profit_factor': profit_factor,
            'max_drawdown': max_drawdown,
            'max_drawdown_pct': max_drawdown_pct,
            'sharpe_ratio': sharpe_ratio,
            'trades': completed_trades,
            'equity_curve': self.equity_curve
        }


def run_backtest(
    ohlcv_data: pd.DataFrame,
    fast_period: int = 3,
    slow_period: int = 10,
    signal_period: int = 16,
    use_trend_filter: bool = True,
    trend_ema_period: int = 50,
    initial_balance: float = 10000.0,
    risk_per_trade: float = 0.02,
    stop_loss_pct: float = 0.02,
    take_profit_pct: float = 0.04
) -> Dict:
    """
    Run a backtest with specified parameters.
    
    Args:
        ohlcv_data: Historical OHLCV data
        fast_period: Fast EMA period
        slow_period: Slow EMA period
        signal_period: Signal line SMA period
        use_trend_filter: Use trend filter
        trend_ema_period: Trend EMA period
        initial_balance: Starting balance
        risk_per_trade: Risk per trade
        stop_loss_pct: Stop loss percentage
        take_profit_pct: Take profit percentage
    
    Returns:
        Backtest results dictionary
    """
    strategy = LindaRaschkeStrategy(
        fast_period=fast_period,
        slow_period=slow_period,
        signal_period=signal_period,
        use_trend_filter=use_trend_filter,
        trend_ema_period=trend_ema_period
    )
    
    backtester = Backtester(
        strategy=strategy,
        initial_balance=initial_balance,
        risk_per_trade=risk_per_trade,
        stop_loss_pct=stop_loss_pct,
        take_profit_pct=take_profit_pct
    )
    
    return backtester.run(ohlcv_data)


if __name__ == "__main__":
    """
    Run backtest when script is executed directly.
    Uses Binance public API (no authentication required) for real historical data.
    """
    import sys
    import argparse
    from config.settings import Settings
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Backtest Linda Raschke 3-10 Oscillator Strategy')
    parser.add_argument('--csv', type=str, help='Path to CSV file with historical data')
    parser.add_argument('--symbol', type=str, help='Trading pair symbol (default: from config)')
    parser.add_argument('--timeframe', type=str, help='Timeframe (default: from config)')
    parser.add_argument('--limit', type=int, default=500, help='Number of candles to fetch (default: 500)')
    args = parser.parse_args()
    
    print("=" * 60)
    print("Linda Raschke 3-10 Oscillator Backtest")
    print("=" * 60)
    print()
    
    try:
        # Load configuration
        settings = Settings()
        trading_config = settings.get_trading_config()
        strategy_config = settings.get_strategy_config()
        risk_config = settings.get_risk_config()
        
        symbol = args.symbol or trading_config.get("symbol", "BTC/USDT")
        timeframe = args.timeframe or trading_config.get("timeframe", "1h")
        
        print(f"Configuration:")
        print(f"  Symbol: {symbol}")
        print(f"  Timeframe: {timeframe}")
        print(f"  Fast EMA: {strategy_config.get('fast_period', 3)}")
        print(f"  Slow EMA: {strategy_config.get('slow_period', 10)}")
        print(f"  Signal Period: {strategy_config.get('signal_period', 16)}")
        print()
        
        # Load data
        if args.csv:
            # Load from CSV file
            print(f"Loading data from CSV: {args.csv}")
            ohlcv_data = load_data_from_csv(args.csv)
        else:
            # Fetch from Binance public API (no authentication needed)
            print(f"Fetching historical data from Binance public API...")
            print(f"  Symbol: {symbol}")
            print(f"  Timeframe: {timeframe}")
            print(f"  Limit: {args.limit} candles")
            print()
            print("Note: Using Binance production data (not testnet)")
            print("      No API credentials required for historical data")
            print()
            
            ohlcv_data = fetch_historical_data_public(symbol, timeframe, limit=args.limit)
        
        print(f"Data loaded: {len(ohlcv_data)} candles")
        print(f"Date range: {ohlcv_data['timestamp'].iloc[0]} to {ohlcv_data['timestamp'].iloc[-1]}")
        print(f"Price range: ${ohlcv_data['close'].min():.2f} - ${ohlcv_data['close'].max():.2f}")
        print()
        
        # Run backtest
        print("Running backtest...")
        print("-" * 60)
        
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
        
        # Display results
        print()
        print("=" * 60)
        print("BACKTEST RESULTS")
        print("=" * 60)
        print(f"Total Trades: {results.get('total_trades', 0)}")
        print(f"Winning Trades: {results.get('winning_trades', 0)}")
        print(f"Losing Trades: {results.get('losing_trades', 0)}")
        print(f"Win Rate: {results.get('win_rate', 0):.2f}%")
        print()
        print(f"Initial Balance: ${results.get('initial_balance', 0):,.2f}")
        print(f"Final Balance: ${results.get('final_balance', 0):,.2f}")
        print(f"Total P&L: {results.get('total_pnl_pct', 0):.2f}% (${results.get('total_pnl', 0):,.2f})")
        print()
        print(f"Average Win: ${results.get('avg_win', 0):,.2f}")
        print(f"Average Loss: ${results.get('avg_loss', 0):,.2f}")
        print(f"Profit Factor: {results.get('profit_factor', 0):.2f}")
        print()
        print(f"Max Drawdown: {results.get('max_drawdown_pct', 0):.2f}% (${results.get('max_drawdown', 0):,.2f})")
        print(f"Sharpe Ratio: {results.get('sharpe_ratio', 0):.2f}")
        print("=" * 60)
        
        if results.get('message'):
            print(f"\nNote: {results['message']}")
    
    except KeyboardInterrupt:
        print("\n\nBacktest interrupted by user")
        sys.exit(0)
    
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
