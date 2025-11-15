"""
Main entry point for the Linda Raschke 3-10 Oscillator Trading Bot.
"""

import time
import signal
import sys
import logging
from datetime import datetime
from typing import Optional

from config.settings import Settings
from strategy.linda_raschke import LindaRaschkeStrategy
from exchange.binance_client import BinanceClient
from exchange.order_executor import OrderExecutor
from risk.position_manager import PositionManager
from utils.logger import setup_logger, log_signal, log_trade, log_trade_close
from utils.database import TradeDatabase
from data_manager import DataManager


class TradingBot:
    """
    Main trading bot class that orchestrates all components.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize trading bot.
        
        Args:
            config_path: Path to configuration file (optional)
        """
        # Load configuration
        self.settings = Settings(config_path)
        
        # Setup logging
        log_level = self.settings.get("execution.log_level", "INFO")
        log_file = self.settings.get("execution.log_file", "logs/trading_bot.log")
        self.logger = setup_logger("trading_bot", log_level, log_file)
        
        self.logger.info("=" * 60)
        self.logger.info("Linda Raschke 3-10 Oscillator Trading Bot")
        self.logger.info("=" * 60)
        
        # Initialize components
        self._initialize_components()
        
        # Running flag
        self.running = True
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _initialize_components(self):
        """Initialize all bot components."""
        try:
            # Initialize exchange client
            self.exchange = BinanceClient(
                api_key=self.settings.api_key,
                api_secret=self.settings.api_secret,
                testnet=self.settings.testnet
            )
            
            # Initialize data manager
            self.data_manager = DataManager(self.exchange)
            
            # Initialize order executor
            self.order_executor = OrderExecutor(self.exchange)
            
            # Initialize strategy
            strategy_config = self.settings.get_strategy_config()
            self.strategy = LindaRaschkeStrategy(
                fast_period=strategy_config.get("fast_period", 3),
                slow_period=strategy_config.get("slow_period", 10),
                signal_period=strategy_config.get("signal_period", 16),
                use_trend_filter=strategy_config.get("use_trend_filter", True),
                trend_ema_period=strategy_config.get("trend_ema_period", 50)
            )
            
            # Initialize risk manager
            risk_config = self.settings.get_risk_config()
            account_balance = risk_config.get("account_balance", 1000.0)
            
            # Try to get actual balance from exchange
            try:
                balances = self.exchange.get_balance()
                # Find USDT balance (or base currency)
                trading_config = self.settings.get_trading_config()
                symbol = trading_config.get("symbol", "BTC/USDT")
                quote_currency = symbol.split('/')[1]  # e.g., USDT from BTC/USDT
                
                if quote_currency in balances and balances[quote_currency] > 0:
                    account_balance = balances[quote_currency]
                    self.logger.info(f"Using exchange balance: {account_balance} {quote_currency}")
            except Exception as e:
                self.logger.warning(f"Could not fetch exchange balance: {e}. Using config value.")
            
            self.position_manager = PositionManager(
                account_balance=account_balance,
                risk_per_trade=risk_config.get("risk_per_trade", 0.02),
                stop_loss_pct=risk_config.get("stop_loss_pct", 0.02),
                take_profit_pct=risk_config.get("take_profit_pct", 0.04),
                max_daily_loss=risk_config.get("max_daily_loss", 0.05),
                max_position_size=risk_config.get("max_position_size", 1000.0)
            )
            
            # Initialize database
            self.database = TradeDatabase()
            
            self.logger.info("All components initialized successfully")
        
        except Exception as e:
            self.logger.error(f"Error initializing components: {e}")
            raise
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        self.logger.info("Shutdown signal received. Closing positions and exiting...")
        self.running = False
    
    def run(self):
        """Main trading loop."""
        trading_config = self.settings.get_trading_config()
        execution_config = self.settings.get_execution_config()
        risk_config = self.settings.get_risk_config()
        
        symbol = trading_config.get("symbol", "BTC/USDT")
        timeframe = trading_config.get("timeframe", "1h")
        check_interval = execution_config.get("check_interval", 60)
        stop_loss_pct = risk_config.get("stop_loss_pct", 0.02)
        take_profit_pct = risk_config.get("take_profit_pct", 0.04)
        
        self.logger.info(f"Starting trading bot for {symbol} on {timeframe} timeframe")
        self.logger.info(f"Check interval: {check_interval} seconds")
        
        while self.running:
            try:
                # Fetch current market data
                ohlcv_data = self.data_manager.get_ohlcv_data(
                    symbol,
                    timeframe,
                    limit=200
                )
                
                # Get current price
                current_price = self.data_manager.get_current_price(symbol)
                
                # Check existing position for exit conditions
                position_info = self.position_manager.get_position_info()
                
                if position_info['has_position']:
                    # Check stop loss
                    should_exit, reason = self.position_manager.check_stop_loss(current_price)
                    if should_exit:
                        self._close_position(current_price, reason)
                        continue
                    
                    # Check take profit
                    should_exit, reason = self.position_manager.check_take_profit(current_price)
                    if should_exit:
                        self._close_position(current_price, reason)
                        continue
                
                # Generate trading signal
                signal_data = self.strategy.generate_signal(ohlcv_data)
                signal_data['symbol'] = symbol
                
                # Log signal
                log_signal(self.logger, signal_data)
                self.database.save_signal(signal_data)
                
                signal_type = signal_data.get('signal', 'hold')
                
                # Handle new position entry
                if signal_type in ['long', 'short'] and not position_info['has_position']:
                    # Open new position
                    self._open_position(signal_type, current_price, symbol)
                
                # Handle position exit on opposite signal
                elif position_info['has_position']:
                    current_position = position_info['position']
                    opposite_signal = False
                    
                    if (signal_type == 'long' and current_position == 'short') or \
                       (signal_type == 'short' and current_position == 'long'):
                        opposite_signal = True
                    
                    if opposite_signal:
                        should_exit, reason = self.strategy.should_exit_position(
                            current_price,
                            position_info['entry_price'],
                            current_position,
                            stop_loss_pct,
                            take_profit_pct,
                            opposite_signal=True
                        )
                        
                        if should_exit:
                            self._close_position(current_price, reason)
                
                # Log account status
                account_info = self.position_manager.get_account_info()
                self.logger.info(
                    f"Account Balance: ${account_info['current_balance']:.2f} | "
                    f"Total P&L: {account_info['total_pnl_pct']:.2f}% | "
                    f"Daily P&L: {account_info['daily_pnl_pct']:.2f}%"
                )
                
                # Wait before next iteration
                time.sleep(check_interval)
            
            except KeyboardInterrupt:
                self.logger.info("Keyboard interrupt received. Shutting down...")
                self.running = False
                break
            
            except Exception as e:
                self.logger.error(f"Error in trading loop: {e}", exc_info=True)
                time.sleep(check_interval)
        
        # Cleanup
        self._cleanup()
    
    def _open_position(self, signal_type: str, entry_price: float, symbol: str):
        """Open a new position."""
        try:
            # Calculate position size
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
                self.logger.warning("Position size is zero or negative. Skipping trade.")
                return
            
            # Open position in position manager
            trade_data = self.position_manager.open_position(
                signal_type,
                entry_price,
                position_size
            )
            
            # Execute order on exchange
            order_result = self.order_executor.execute_trade(
                symbol,
                signal_type,
                position_size,
                order_type='market'
            )
            
            if order_result['success']:
                # Update strategy position
                self.strategy.update_position(signal_type, entry_price)
                
                # Save to database
                trade_data['symbol'] = symbol
                trade_id = self.database.save_trade(trade_data)
                
                # Log trade
                log_trade(self.logger, trade_data)
                
                self.logger.info(f"Position opened successfully. Trade ID: {trade_id}")
            else:
                self.logger.error(f"Failed to execute order: {order_result.get('error')}")
                # Reset position manager if order failed
                self.position_manager.current_position = None
        
        except Exception as e:
            self.logger.error(f"Error opening position: {e}", exc_info=True)
    
    def _close_position(self, exit_price: float, reason: str):
        """Close current position."""
        try:
            position_info = self.position_manager.get_position_info()
            
            if not position_info['has_position']:
                return
            
            # Close position in position manager
            close_data = self.position_manager.close_position(exit_price, reason)
            
            # Execute close order on exchange
            trading_config = self.settings.get_trading_config()
            symbol = trading_config.get("symbol", "BTC/USDT")
            
            order_result = self.order_executor.close_position(
                symbol,
                position_info['position'],
                position_info['position_size'],
                order_type='market'
            )
            
            if order_result['success']:
                # Update strategy position
                self.strategy.update_position(None)
                
                # Update database
                open_trades = self.database.get_open_trades()
                if open_trades:
                    trade_id = open_trades[0]['id']  # Get most recent open trade
                    self.database.update_trade_close(trade_id, close_data)
                
                # Log trade close
                log_trade_close(self.logger, close_data)
                
                self.logger.info("Position closed successfully")
            else:
                self.logger.error(f"Failed to execute close order: {order_result.get('error')}")
        
        except Exception as e:
            self.logger.error(f"Error closing position: {e}", exc_info=True)
    
    def _cleanup(self):
        """Cleanup resources."""
        self.logger.info("Cleaning up resources...")
        
        # Close database connection
        if hasattr(self, 'database'):
            self.database.close()
        
        self.logger.info("Trading bot stopped.")


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Linda Raschke 3-10 Oscillator Trading Bot")
    parser.add_argument(
        "--config",
        type=str,
        help="Path to configuration file"
    )
    
    args = parser.parse_args()
    
    try:
        bot = TradingBot(config_path=args.config)
        bot.run()
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

