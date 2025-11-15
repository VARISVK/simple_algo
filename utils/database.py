"""
Database module for storing trade history.
Supports SQLite (default) and PostgreSQL.
"""

import sqlite3
import logging
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
import json

logger = logging.getLogger(__name__)


class TradeDatabase:
    """
    Database interface for storing trade history.
    """
    
    def __init__(self, db_path: str = "trades.db"):
        """
        Initialize database connection.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = Path(db_path)
        self.conn = None
        self._initialize_database()
    
    def _initialize_database(self):
        """Initialize database schema."""
        try:
            self.conn = sqlite3.connect(self.db_path)
            self.conn.row_factory = sqlite3.Row
            
            # Create trades table
            cursor = self.conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS trades (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    symbol TEXT NOT NULL,
                    position_type TEXT NOT NULL,
                    entry_price REAL NOT NULL,
                    exit_price REAL,
                    position_size REAL NOT NULL,
                    stop_loss_price REAL,
                    take_profit_price REAL,
                    pnl_pct REAL,
                    pnl_amount REAL,
                    reason TEXT,
                    entry_time TEXT,
                    exit_time TEXT,
                    duration_minutes REAL,
                    status TEXT DEFAULT 'open'
                )
            """)
            
            # Create signals table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS signals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    symbol TEXT NOT NULL,
                    signal TEXT NOT NULL,
                    reason TEXT,
                    oscillator REAL,
                    signal_line REAL,
                    close_price REAL,
                    indicators_json TEXT
                )
            """)
            
            self.conn.commit()
            logger.info(f"Database initialized: {self.db_path}")
        
        except Exception as e:
            logger.error(f"Error initializing database: {e}")
            raise
    
    def save_signal(self, signal_data: Dict):
        """
        Save trading signal to database.
        
        Args:
            signal_data: Dictionary containing signal information
        """
        try:
            cursor = self.conn.cursor()
            indicators = signal_data.get('indicators', {})
            
            cursor.execute("""
                INSERT INTO signals (
                    timestamp, symbol, signal, reason,
                    oscillator, signal_line, close_price, indicators_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                datetime.now().isoformat(),
                signal_data.get('symbol', ''),
                signal_data.get('signal', 'hold'),
                signal_data.get('reason', ''),
                indicators.get('oscillator'),
                indicators.get('signal_line'),
                indicators.get('close'),
                json.dumps(indicators)
            ))
            
            self.conn.commit()
            logger.debug("Signal saved to database")
        
        except Exception as e:
            logger.error(f"Error saving signal: {e}")
            self.conn.rollback()
    
    def save_trade(self, trade_data: Dict):
        """
        Save trade to database.
        
        Args:
            trade_data: Dictionary containing trade information
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                INSERT INTO trades (
                    timestamp, symbol, position_type, entry_price,
                    position_size, stop_loss_price, take_profit_price,
                    entry_time, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                datetime.now().isoformat(),
                trade_data.get('symbol', ''),
                trade_data.get('position_type', ''),
                trade_data.get('entry_price', 0),
                trade_data.get('position_size', 0),
                trade_data.get('stop_loss_price', 0),
                trade_data.get('take_profit_price', 0),
                trade_data.get('entry_time', datetime.now()).isoformat() if isinstance(trade_data.get('entry_time'), datetime) else trade_data.get('entry_time', ''),
                'open'
            ))
            
            self.conn.commit()
            logger.debug("Trade saved to database")
            return cursor.lastrowid
        
        except Exception as e:
            logger.error(f"Error saving trade: {e}")
            self.conn.rollback()
            return None
    
    def update_trade_close(self, trade_id: int, close_data: Dict):
        """
        Update trade with exit information.
        
        Args:
            trade_id: Trade ID
            close_data: Dictionary containing trade close information
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                UPDATE trades SET
                    exit_price = ?,
                    pnl_pct = ?,
                    pnl_amount = ?,
                    reason = ?,
                    exit_time = ?,
                    duration_minutes = ?,
                    status = 'closed'
                WHERE id = ?
            """, (
                close_data.get('exit_price', 0),
                close_data.get('pnl_pct', 0),
                close_data.get('pnl_amount', 0),
                close_data.get('reason', ''),
                close_data.get('exit_time', datetime.now()).isoformat() if isinstance(close_data.get('exit_time'), datetime) else close_data.get('exit_time', ''),
                close_data.get('duration', 0),
                trade_id
            ))
            
            self.conn.commit()
            logger.debug(f"Trade {trade_id} updated with close information")
        
        except Exception as e:
            logger.error(f"Error updating trade: {e}")
            self.conn.rollback()
    
    def get_trades(self, limit: int = 100) -> List[Dict]:
        """
        Get recent trades.
        
        Args:
            limit: Maximum number of trades to return
        
        Returns:
            List of trade dictionaries
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT * FROM trades
                ORDER BY timestamp DESC
                LIMIT ?
            """, (limit,))
            
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        
        except Exception as e:
            logger.error(f"Error fetching trades: {e}")
            return []
    
    def get_open_trades(self) -> List[Dict]:
        """Get all open trades."""
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT * FROM trades
                WHERE status = 'open'
                ORDER BY timestamp DESC
            """)
            
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        
        except Exception as e:
            logger.error(f"Error fetching open trades: {e}")
            return []
    
    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
            logger.info("Database connection closed")

