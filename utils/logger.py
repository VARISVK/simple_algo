"""
Logging configuration for the trading bot.
Provides comprehensive logging for debugging and monitoring.
"""

import logging
import sys
from pathlib import Path
from datetime import datetime
import os


def setup_logger(
    name: str = "trading_bot",
    log_level: str = "INFO",
    log_file: str = None
) -> logging.Logger:
    """
    Set up logger with console and file handlers.
    
    Args:
        name: Logger name
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Path to log file (optional)
    
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # Remove existing handlers to avoid duplicates
    logger.handlers.clear()
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, log_level.upper()))
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler (if log_file is specified)
    if log_file:
        # Create logs directory if it doesn't exist
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)  # File logs everything
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger


def log_signal(logger: logging.Logger, signal_data: dict):
    """
    Log trading signal in a structured format.
    
    Args:
        logger: Logger instance
        signal_data: Dictionary containing signal information
    """
    logger.info("=" * 60)
    logger.info("TRADING SIGNAL GENERATED")
    logger.info(f"Signal: {signal_data.get('signal', 'N/A').upper()}")
    logger.info(f"Reason: {signal_data.get('reason', 'N/A')}")
    
    indicators = signal_data.get('indicators', {})
    logger.info(f"Current Price: {indicators.get('close', 'N/A')}")
    logger.info(f"Oscillator: {indicators.get('oscillator', 'N/A'):.6f}")
    logger.info(f"Signal Line: {indicators.get('signal_line', 'N/A'):.6f}")
    logger.info(f"Fast EMA: {indicators.get('fast_ema', 'N/A'):.6f}")
    logger.info(f"Slow EMA: {indicators.get('slow_ema', 'N/A'):.6f}")
    
    if indicators.get('trend_ema'):
        logger.info(f"Trend EMA: {indicators.get('trend_ema', 'N/A'):.6f}")
    
    logger.info("=" * 60)


def log_trade(logger: logging.Logger, trade_data: dict):
    """
    Log trade execution in a structured format.
    
    Args:
        logger: Logger instance
        trade_data: Dictionary containing trade information
    """
    logger.info("=" * 60)
    logger.info("TRADE EXECUTED")
    logger.info(f"Position: {trade_data.get('position_type', 'N/A').upper()}")
    logger.info(f"Entry Price: {trade_data.get('entry_price', 'N/A')}")
    logger.info(f"Position Size: {trade_data.get('position_size', 'N/A')}")
    logger.info(f"Stop Loss: {trade_data.get('stop_loss_price', 'N/A')}")
    logger.info(f"Take Profit: {trade_data.get('take_profit_price', 'N/A')}")
    logger.info("=" * 60)


def log_trade_close(logger: logging.Logger, close_data: dict):
    """
    Log trade closure in a structured format.
    
    Args:
        logger: Logger instance
        close_data: Dictionary containing trade close information
    """
    logger.info("=" * 60)
    logger.info("POSITION CLOSED")
    logger.info(f"Position: {close_data.get('position_type', 'N/A').upper()}")
    logger.info(f"Entry Price: {close_data.get('entry_price', 'N/A')}")
    logger.info(f"Exit Price: {close_data.get('exit_price', 'N/A')}")
    logger.info(f"P&L: {close_data.get('pnl_pct', 0) * 100:.2f}%")
    logger.info(f"P&L Amount: ${close_data.get('pnl_amount', 0):.2f}")
    logger.info(f"Reason: {close_data.get('reason', 'N/A')}")
    logger.info(f"Duration: {close_data.get('duration', 0):.2f} minutes")
    logger.info("=" * 60)

