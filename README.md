# Linda Raschke 3-10 Oscillator Trading Bot

A production-ready cryptocurrency trading bot implementing Linda Raschke's 3-10 Oscillator strategy for automated trading on Binance.

## Strategy Overview

The Linda Raschke 3-10 Oscillator strategy uses:
- **Fast EMA:** 3-period exponential moving average
- **Slow EMA:** 10-period exponential moving average
- **Oscillator:** Difference between fast and slow EMA (Fast EMA - Slow EMA)
- **Signal Line:** 16-period Simple Moving Average (SMA) of the oscillator
- **Trend Filter:** Optional 50 or 200-period EMA to filter trades with overall trend

### Entry Rules
- **LONG:** Oscillator crosses above signal line + price above trend EMA
- **SHORT:** Oscillator crosses below signal line + price below trend EMA

### Exit Rules
- Fixed stop loss: 2% from entry
- Fixed take profit: 4% from entry (2:1 risk-reward ratio)
- Or exit on opposite crossover signal

### Risk Management
- Risk 2% of account balance per trade
- Position size calculated as: (Account Balance × Risk%) / Stop Loss Distance
- Maximum daily loss limit: 5% (configurable)

## Installation

### Prerequisites
- Python 3.11+
- TA-Lib library (C library + Python bindings)
- Binance API credentials

### Setup

1. **Clone the repository:**
```bash
git clone https://github.com/VARISVK/simple_algo.git
cd simple_algo
```

2. **Create virtual environment:**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install TA-Lib:**

**Linux:**
```bash
wget http://prdownloads.sourceforge.net/ta-lib/ta-lib-0.4.0-src.tar.gz
tar -xzf ta-lib-0.4.0-src.tar.gz
cd ta-lib/
./configure --prefix=/usr
make
sudo make install
cd ..
```

**macOS:**
```bash
brew install ta-lib
```

**Windows:**
Download pre-compiled TA-Lib from: https://www.lfd.uci.edu/~gohlke/pythonlibs/#ta-lib

4. **Install Python dependencies:**
```bash
pip install -r requirements.txt
```

5. **Configure environment:**
```bash
cp .env.example .env
# Edit .env with your API keys
```

6. **Configure strategy:**
Edit `config/config.json` to adjust strategy parameters, trading pairs, and risk settings.

## Configuration

### Environment Variables (.env)
```env
BINANCE_API_KEY=your_api_key_here
BINANCE_API_SECRET=your_api_secret_here
BINANCE_TESTNET=true
LOG_LEVEL=INFO
ACCOUNT_BALANCE=1000.0
MAX_DAILY_LOSS=0.05
```

### Strategy Configuration (config/config.json)
```json
{
  "strategy": {
    "fast_period": 3,
    "slow_period": 10,
    "signal_period": 16,
    "use_trend_filter": true,
    "trend_ema_period": 50
  },
  "trading": {
    "symbol": "BTC/USDT",
    "timeframe": "1h",
    "testnet": true
  },
  "risk": {
    "risk_per_trade": 0.02,
    "stop_loss_pct": 0.02,
    "take_profit_pct": 0.04,
    "max_daily_loss": 0.05
  }
}
```

## Usage

### Running the Bot

```bash
python main.py
```

Or with custom config:
```bash
python main.py --config path/to/config.json
```

### Backtesting

```bash
# Backtest using Binance public API (no credentials needed)
python backtest.py

# Or with options
python backtest.py --symbol BTC/USDT --timeframe 4h --limit 1000

# Or from CSV file
python backtest.py --csv data/historical_data.csv
```

## Docker Deployment

### Build and Run
```bash
docker-compose up -d
```

### View Logs
```bash
docker-compose logs -f trading-bot
```

## AWS Deployment

See [AWS_DEPLOYMENT.md](AWS_DEPLOYMENT.md) for complete AWS deployment guide.

## Project Structure

```
simple_algo/
├── main.py                 # Entry point
├── backtest.py             # Backtesting engine
├── data_manager.py         # Data fetching and processing
├── config/
│   ├── settings.py         # Configuration management
│   └── config.json         # Strategy parameters
├── strategy/
│   ├── linda_raschke.py    # Strategy implementation
│   └── indicators.py      # Indicator calculations
├── exchange/
│   ├── binance_client.py   # Binance API wrapper
│   └── order_executor.py   # Order execution
├── risk/
│   └── position_manager.py # Risk management
├── utils/
│   ├── logger.py           # Logging configuration
│   └── database.py         # Trade history storage
├── deploy/                 # AWS deployment scripts
├── tests/                  # Unit tests
├── requirements.txt
├── Dockerfile
└── README.md
```

## Safety Features

- **Daily Loss Limit:** Stops trading if daily loss exceeds configured limit
- **Position Size Limits:** Maximum position size to prevent over-leveraging
- **Stop Loss/Take Profit:** Automatic exit at predefined levels
- **Error Handling:** Graceful handling of API errors and network issues
- **Rate Limiting:** Built-in rate limiting to avoid API bans
- **Testnet Mode:** Test on Binance testnet before live trading

## Logging

Logs are written to:
- Console (stdout)
- File: `logs/trading_bot.log`

Log levels: DEBUG, INFO, WARNING, ERROR, CRITICAL

## Database

Trade history is stored in SQLite database (`trades.db`):
- **trades table:** All executed trades
- **signals table:** All generated signals

## Testing

Run tests:
```bash
pytest tests/
```

## Important Notes

⚠️ **WARNING:** 
- Always test on Binance testnet before live trading
- Start with small position sizes
- Monitor the bot closely during initial runs
- Never risk more than you can afford to lose
- Cryptocurrency trading involves significant risk

## License

MIT License

## Support

For issues and questions, please open an issue on GitHub.

## Disclaimer

This software is for educational purposes only. Trading cryptocurrencies involves substantial risk of loss. The authors and contributors are not responsible for any financial losses incurred from using this software.
