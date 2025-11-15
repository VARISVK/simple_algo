# Quick Start Guide

## Prerequisites

1. **Python 3.11+** installed
2. **TA-Lib library** installed (see installation instructions below)
3. **Binance API credentials** (get from Binance account)

## Installation Steps

### 1. Install TA-Lib

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
Download pre-compiled wheel from: https://www.lfd.uci.edu/~gohlke/pythonlibs/#ta-lib
Then install: `pip install TA_Lib-0.4.XX-cpXX-cpXX-win_amd64.whl`

### 2. Install Python Dependencies

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install packages
pip install -r requirements.txt
```

### 3. Configure Environment

```bash
# Copy example environment file
cp .env.example .env

# Edit .env and add your Binance API credentials
# BINANCE_API_KEY=your_key_here
# BINANCE_API_SECRET=your_secret_here
# BINANCE_TESTNET=true  # Start with testnet!
```

### 4. Configure Strategy (Optional)

Edit `config/config.json` to adjust:
- Trading pair (symbol)
- Timeframe
- Strategy parameters
- Risk settings

## Running the Bot

### Test Mode (Testnet)

```bash
# Make sure BINANCE_TESTNET=true in .env
python main.py
```

### Backtesting

```bash
python example_backtest.py
```

### Run Tests

```bash
pytest tests/
```

## First Steps

1. **Start with Testnet**: Always test on Binance testnet first
   - Set `BINANCE_TESTNET=true` in `.env`
   - Get testnet API keys from: https://testnet.binance.vision/

2. **Use Small Position Sizes**: Start with minimal risk
   - Set `risk_per_trade` to 0.01 (1%) in `config/config.json`
   - Use small account balance for testing

3. **Monitor Closely**: Watch the bot during initial runs
   - Check logs in `logs/trading_bot.log`
   - Monitor console output

4. **Backtest First**: Test strategy on historical data
   - Run `python example_backtest.py`
   - Analyze results before live trading

## Common Issues

### TA-Lib Installation Issues

**Error: "TA-Lib not available"**
- Make sure TA-Lib C library is installed first
- Then install Python bindings: `pip install TA-Lib`

**Error: "Cannot find ta-lib"**
- Linux: Check `/usr/lib` for `libta_lib.so`
- macOS: Check `/usr/local/lib` for `libta_lib.dylib`
- Windows: Ensure DLL is in PATH

### API Connection Issues

**Error: "Invalid API key"**
- Verify API keys in `.env` file
- Check if testnet keys are used for testnet mode
- Ensure API keys have trading permissions

**Error: "Rate limit exceeded"**
- Bot includes rate limiting, but if you see this:
  - Increase `check_interval` in `config/config.json`
  - Reduce API call frequency

## Next Steps

1. **Review Strategy**: Understand the Linda Raschke 3-10 Oscillator strategy
2. **Backtest**: Test on historical data with different parameters
3. **Paper Trade**: Run on testnet for extended period
4. **Monitor**: Watch performance and adjust risk parameters
5. **Deploy**: When confident, deploy to AWS or run on VPS

## Safety Reminders

⚠️ **IMPORTANT:**
- Never risk more than you can afford to lose
- Always start with testnet
- Use small position sizes initially
- Monitor the bot regularly
- Cryptocurrency trading is risky

## Getting Help

- Check logs: `logs/trading_bot.log`
- Review configuration: `config/config.json`
- Run tests: `pytest tests/ -v`
- Check README.md for detailed documentation

