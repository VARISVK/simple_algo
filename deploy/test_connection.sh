#!/bin/bash
# Test script to verify bot configuration and API connection
# Run this before starting the bot in production

set -e

APP_DIR="/opt/trading-bot"
cd $APP_DIR

echo "=========================================="
echo "Trading Bot Connection Test"
echo "=========================================="

# Activate virtual environment
source venv/bin/activate

echo ""
echo "1. Testing Python environment..."
python --version
echo "✓ Python OK"

echo ""
echo "2. Testing imports..."
python -c "
import sys
try:
    from config.settings import Settings
    from exchange.binance_client import BinanceClient
    from strategy.linda_raschke import LindaRaschkeStrategy
    print('✓ All imports successful')
except ImportError as e:
    print(f'✗ Import error: {e}')
    sys.exit(1)
"

echo ""
echo "3. Testing configuration loading..."
python -c "
from config.settings import Settings
try:
    settings = Settings()
    print('✓ Configuration loaded')
    print(f'  Symbol: {settings.get(\"trading.symbol\")}')
    print(f'  Timeframe: {settings.get(\"trading.timeframe\")}')
    print(f'  Testnet: {settings.testnet}')
except Exception as e:
    print(f'✗ Configuration error: {e}')
    sys.exit(1)
"

echo ""
echo "4. Testing API credentials..."
python -c "
from config.settings import Settings
settings = Settings()
api_key = settings.api_key
api_secret = settings.api_secret

if not api_key or not api_secret:
    print('✗ API credentials not found!')
    print('  Check .env file or AWS Secrets Manager')
    sys.exit(1)

if len(api_key) < 10:
    print('✗ API key seems invalid')
    sys.exit(1)

print('✓ API credentials found')
print(f'  API Key: {api_key[:10]}...')
print(f'  Using testnet: {settings.testnet}')
"

echo ""
echo "5. Testing Binance API connection..."
python -c "
from config.settings import Settings
from exchange.binance_client import BinanceClient
import sys

try:
    settings = Settings()
    client = BinanceClient(
        settings.api_key,
        settings.api_secret,
        testnet=settings.testnet
    )
    
    # Test connection by fetching balance
    balance = client.get_balance()
    print('✓ API connection successful')
    print(f'  Exchange: Binance ({\"Testnet\" if settings.testnet else \"Production\"})')
    
    # Show available balances
    non_zero = {k: v for k, v in balance.items() if v > 0}
    if non_zero:
        print('  Balances:')
        for currency, amount in list(non_zero.items())[:5]:
            print(f'    {currency}: {amount}')
    else:
        print('  No balances found (this is OK for testnet)')
        
except Exception as e:
    print(f'✗ API connection failed: {e}')
    print('  Check:')
    print('    - API keys are correct')
    print('    - API keys have trading permissions')
    print('    - Network connectivity')
    sys.exit(1)
"

echo ""
echo "6. Testing data fetching..."
python -c "
from config.settings import Settings
from exchange.binance_client import BinanceClient
import sys

try:
    settings = Settings()
    client = BinanceClient(
        settings.api_key,
        settings.api_secret,
        testnet=settings.testnet
    )
    
    symbol = settings.get('trading.symbol', 'BTC/USDT')
    timeframe = settings.get('trading.timeframe', '1h')
    
    ohlcv = client.fetch_ohlcv(symbol, timeframe, limit=10)
    print('✓ Data fetching successful')
    print(f'  Symbol: {symbol}')
    print(f'  Timeframe: {timeframe}')
    print(f'  Candles fetched: {len(ohlcv)}')
    if len(ohlcv) > 0:
        print(f'  Latest close: {ohlcv.iloc[-1][\"close\"]}')
        
except Exception as e:
    print(f'✗ Data fetching failed: {e}')
    sys.exit(1)
"

echo ""
echo "7. Testing strategy initialization..."
python -c "
from config.settings import Settings
from strategy.linda_raschke import LindaRaschkeStrategy
import sys

try:
    settings = Settings()
    strategy_config = settings.get_strategy_config()
    
    strategy = LindaRaschkeStrategy(
        fast_period=strategy_config.get('fast_period', 3),
        slow_period=strategy_config.get('slow_period', 10),
        signal_period=strategy_config.get('signal_period', 16),
        use_trend_filter=strategy_config.get('use_trend_filter', True),
        trend_ema_period=strategy_config.get('trend_ema_period', 50)
    )
    
    print('✓ Strategy initialized successfully')
    print(f'  Fast EMA: {strategy.fast_period}')
    print(f'  Slow EMA: {strategy.slow_period}')
    print(f'  Signal Period: {strategy.signal_period}')
    print(f'  Trend Filter: {strategy.use_trend_filter}')
    
except Exception as e:
    print(f'✗ Strategy initialization failed: {e}')
    sys.exit(1)
"

echo ""
echo "=========================================="
echo "All Tests Passed! ✓"
echo "=========================================="
echo ""
echo "The bot is ready to run. You can now:"
echo "  1. Start manually: python main.py"
echo "  2. Start as service: sudo systemctl start trading-bot"
echo ""

