# AWS Deployment Guide

Complete guide for deploying the Linda Raschke Trading Bot to AWS EC2.

## Prerequisites

1. **AWS Account** with EC2 access
2. **AWS CLI** installed and configured
3. **SSH Key Pair** for EC2 access
4. **Binance API Credentials** (production keys for live trading)

## Step 1: Launch EC2 Instance

### 1.1 Create EC2 Instance

1. Go to AWS Console → EC2 → Launch Instance
2. **Name**: `trading-bot-production`
3. **AMI**: Ubuntu 22.04 LTS (or latest)
4. **Instance Type**: 
   - **t3.micro** (free tier, for testing)
   - **t3.small** (recommended for production, ~$15/month)
   - **t3.medium** (for multiple symbols/timeframes)
5. **Key Pair**: Select or create a new key pair (download .pem file)
6. **Network Settings**: 
   - Allow SSH (port 22) from your IP
   - Optionally allow HTTP/HTTPS if you add a dashboard later
7. **Storage**: 20 GB should be sufficient
8. **Launch Instance**

### 1.2 Configure Security Group

Add rules to security group:
- **SSH (22)**: Your IP only
- **Custom TCP (optional)**: For monitoring dashboard if needed

## Step 2: Connect to EC2 Instance

```bash
# Replace with your key and instance IP
chmod 400 your-key.pem
ssh -i your-key.pem ubuntu@your-ec2-ip-address
```

## Step 3: Install Dependencies

Run the installation script:

```bash
# Clone or upload your code to the instance
# Option 1: Clone from Git
git clone <your-repo-url>
cd trading_bot

# Option 2: Upload via SCP
# From your local machine:
# scp -i your-key.pem -r . ubuntu@your-ec2-ip:/opt/trading-bot

# Run installation
bash deploy/install.sh
```

Or install manually:

```bash
# Update system
sudo apt-get update
sudo apt-get install -y python3 python3-pip python3-venv git build-essential

# Install TA-Lib dependencies
sudo apt-get install -y gcc g++ make wget

# Install TA-Lib
cd /tmp
wget http://prdownloads.sourceforge.net/ta-lib/ta-lib-0.4.0-src.tar.gz
tar -xzf ta-lib-0.4.0-src.tar.gz
cd ta-lib/
./configure --prefix=/usr
make
sudo make install
cd /opt/trading-bot

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

## Step 4: Configure AWS Secrets Manager (Recommended)

### 4.1 Store API Keys in Secrets Manager

From your local machine (with AWS CLI configured):

```bash
# Create secret
aws secretsmanager create-secret \
    --name trading-bot-secrets \
    --secret-string '{
        "BINANCE_API_KEY": "your_production_api_key",
        "BINANCE_API_SECRET": "your_production_api_secret",
        "BINANCE_TESTNET": "false"
    }' \
    --region us-east-1
```

Or use AWS Console:
1. Go to AWS Secrets Manager
2. Click "Store a new secret"
3. Select "Other type of secret"
4. Add key-value pairs:
   - `BINANCE_API_KEY`: your key
   - `BINANCE_API_SECRET`: your secret
   - `BINANCE_TESTNET`: false
5. Secret name: `trading-bot-secrets`
6. Click "Store"

### 4.2 Update Settings to Use Secrets Manager

The bot will automatically try to fetch from Secrets Manager if configured. Update `config/settings.py` if needed.

## Step 5: Configure the Bot

### 5.1 Create Environment File

```bash
cd /opt/trading-bot
nano .env
```

Add configuration:

```env
# If using Secrets Manager, these can be empty
BINANCE_API_KEY=
BINANCE_API_SECRET=
BINANCE_TESTNET=false

# Or if not using Secrets Manager, add directly:
# BINANCE_API_KEY=your_production_key
# BINANCE_API_SECRET=your_production_secret
# BINANCE_TESTNET=false

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/trading_bot.log

# AWS Configuration
AWS_REGION=us-east-1
AWS_SECRETS_MANAGER_SECRET_NAME=trading-bot-secrets

# Trading Configuration
ACCOUNT_BALANCE=1000.0
MAX_DAILY_LOSS=0.05
```

### 5.2 Configure Strategy

Edit `config/config.json`:

```json
{
  "strategy": {
    "name": "linda_raschke_3_10",
    "fast_period": 3,
    "slow_period": 10,
    "signal_period": 16,
    "signal_ma_type": "SMA",
    "use_trend_filter": true,
    "trend_ema_period": 50
  },
  "trading": {
    "symbol": "BTC/USDT",
    "timeframe": "1h",
    "exchange": "binance",
    "testnet": false
  },
  "risk": {
    "risk_per_trade": 0.02,
    "stop_loss_pct": 0.02,
    "take_profit_pct": 0.04,
    "max_daily_loss": 0.05,
    "max_position_size": 1000
  },
  "execution": {
    "check_interval": 60,
    "order_type": "market",
    "slippage_tolerance": 0.001
  }
}
```

**Important**: Set `"testnet": false` for production!

### 5.3 Set Up AWS Credentials (for Secrets Manager)

```bash
# Install AWS CLI if not installed
sudo apt-get install -y awscli

# Configure AWS credentials
aws configure
# Enter your AWS Access Key ID
# Enter your AWS Secret Access Key
# Enter region (e.g., us-east-1)
# Enter output format (json)
```

Or attach an IAM role to EC2 instance with Secrets Manager read permissions.

## Step 6: Set Up Systemd Service

The installation script should have created the service, but verify:

```bash
# Check service file
cat /etc/systemd/system/trading-bot.service

# Reload systemd
sudo systemctl daemon-reload

# Enable service (auto-start on boot)
sudo systemctl enable trading-bot

# Start service
sudo systemctl start trading-bot

# Check status
sudo systemctl status trading-bot

# View logs
sudo journalctl -u trading-bot -f
```

## Step 7: Set Up CloudWatch Logs (Optional)

### 7.1 Install CloudWatch Agent

```bash
wget https://s3.amazonaws.com/amazoncloudwatch-agent/ubuntu/amd64/latest/amazon-cloudwatch-agent.deb
sudo dpkg -i -E ./amazon-cloudwatch-agent.deb
```

### 7.2 Configure CloudWatch

Create config file:

```bash
sudo nano /opt/aws/amazon-cloudwatch-agent/etc/amazon-cloudwatch-agent.json
```

```json
{
    "logs": {
        "logs_collected": {
            "files": {
                "collect_list": [
                    {
                        "file_path": "/opt/trading-bot/logs/trading_bot.log",
                        "log_group_name": "/trading-bot/linda-raschke",
                        "log_stream_name": "bot-{instance_id}",
                        "retention_in_days": 30
                    }
                ]
            }
        }
    }
}
```

### 7.3 Start CloudWatch Agent

```bash
sudo /opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-ctl \
    -a fetch-config -m ec2 -c file:/opt/aws/amazon-cloudwatch-agent/etc/amazon-cloudwatch-agent.json -s
```

## Step 8: Verify Deployment

### 8.1 Check Service Status

```bash
sudo systemctl status trading-bot
```

Should show: `Active: active (running)`

### 8.2 Check Logs

```bash
# Systemd logs
sudo journalctl -u trading-bot -n 50

# Application logs
tail -f /opt/trading-bot/logs/trading_bot.log
```

### 8.3 Test API Connection

```bash
cd /opt/trading-bot
source venv/bin/activate
python -c "from exchange.binance_client import BinanceClient; from config.settings import Settings; s = Settings(); c = BinanceClient(s.api_key, s.api_secret, testnet=False); print('Balance:', c.get_balance())"
```

## Step 9: Monitoring and Maintenance

### 9.1 Monitor Logs

```bash
# Real-time logs
sudo journalctl -u trading-bot -f

# Last 100 lines
sudo journalctl -u trading-bot -n 100

# Logs from today
sudo journalctl -u trading-bot --since today
```

### 9.2 Check Bot Status

```bash
# Check if running
sudo systemctl is-active trading-bot

# Restart if needed
sudo systemctl restart trading-bot

# Stop bot
sudo systemctl stop trading-bot

# Start bot
sudo systemctl start trading-bot
```

### 9.3 View Trade History

```bash
cd /opt/trading-bot
source venv/bin/activate
python -c "from utils.database import TradeDatabase; db = TradeDatabase(); trades = db.get_trades(10); [print(t) for t in trades]"
```

### 9.4 Set Up Alarms (Optional)

Create CloudWatch alarms for:
- Bot process down
- High error rate
- Unusual trading activity

## Step 10: Security Best Practices

### 10.1 IAM Role for EC2

Create IAM role with minimal permissions:
- `secretsmanager:GetSecretValue` (for Secrets Manager)
- `logs:CreateLogGroup`, `logs:CreateLogStream`, `logs:PutLogEvents` (for CloudWatch)

Attach role to EC2 instance.

### 10.2 Secure .env File

```bash
# Set restrictive permissions
chmod 600 /opt/trading-bot/.env
chown ubuntu:ubuntu /opt/trading-bot/.env
```

### 10.3 Firewall Rules

```bash
# Only allow SSH from your IP
sudo ufw allow from YOUR_IP_ADDRESS to any port 22
sudo ufw enable
```

### 10.4 Regular Updates

```bash
# Update system packages
sudo apt-get update && sudo apt-get upgrade -y

# Update bot code
cd /opt/trading-bot
git pull  # If using Git
# Or upload new files via SCP
```

## Troubleshooting

### Bot Not Starting

```bash
# Check service status
sudo systemctl status trading-bot

# Check logs for errors
sudo journalctl -u trading-bot -n 50

# Check Python environment
cd /opt/trading-bot
source venv/bin/activate
python --version
pip list
```

### API Connection Issues

```bash
# Test API connection
python -c "from exchange.binance_client import BinanceClient; from config.settings import Settings; s = Settings(); print('API Key:', s.api_key[:10] + '...')"

# Check network connectivity
ping api.binance.com
```

### Permission Issues

```bash
# Fix ownership
sudo chown -R ubuntu:ubuntu /opt/trading-bot
sudo chmod +x /opt/trading-bot/main.py
```

### High Memory Usage

```bash
# Check memory
free -h

# Restart service
sudo systemctl restart trading-bot
```

## Cost Estimation

- **EC2 t3.small**: ~$15/month
- **Data Transfer**: Minimal (~$1/month)
- **CloudWatch Logs**: First 5GB free, then $0.50/GB
- **Secrets Manager**: $0.40/month per secret

**Total**: ~$17-20/month for basic setup

## Production Checklist

Before going live:

- [ ] Tested on Binance testnet
- [ ] Backtested strategy on historical data
- [ ] Configured production API keys
- [ ] Set `testnet: false` in config
- [ ] Verified risk parameters (start small!)
- [ ] Set up monitoring and alerts
- [ ] Configured CloudWatch logging
- [ ] Set up automated backups
- [ ] Documented deployment process
- [ ] Tested service restart/recovery
- [ ] Verified security settings

## Quick Commands Reference

```bash
# Start bot
sudo systemctl start trading-bot

# Stop bot
sudo systemctl stop trading-bot

# Restart bot
sudo systemctl restart trading-bot

# View logs
sudo journalctl -u trading-bot -f

# Check status
sudo systemctl status trading-bot

# View application logs
tail -f /opt/trading-bot/logs/trading_bot.log

# Access database
cd /opt/trading-bot && source venv/bin/activate
python -c "from utils.database import TradeDatabase; db = TradeDatabase(); print(db.get_trades(5))"
```

## Support

For issues:
1. Check logs: `sudo journalctl -u trading-bot -n 100`
2. Check application logs: `tail -100 /opt/trading-bot/logs/trading_bot.log`
3. Verify configuration: `cat /opt/trading-bot/config/config.json`
4. Test API connection manually

