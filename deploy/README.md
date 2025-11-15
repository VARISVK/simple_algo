# Deployment Scripts

This directory contains scripts for deploying the trading bot to AWS EC2.

## Scripts

### `aws_setup.sh`
Complete setup script for a fresh Ubuntu EC2 instance. Installs all dependencies, TA-Lib, Python environment, and sets up systemd service.

**Usage:**
```bash
# On EC2 instance
sudo bash deploy/aws_setup.sh
```

### `quick_deploy.sh`
Quick deployment script for updating an existing installation. Use this after uploading new code.

**Usage:**
```bash
# On EC2 instance
sudo bash deploy/quick_deploy.sh
```

### `install.sh`
Original installation script. Similar to aws_setup.sh but with different structure.

### `update_secrets_manager.py`
Script to update AWS Secrets Manager with API credentials. Run from your local machine.

**Usage:**
```bash
# From local machine (with AWS CLI configured)
python deploy/update_secrets_manager.py
```

### `cloudwatch_logs.sh`
Script to send logs to AWS CloudWatch. Optional for advanced monitoring.

## Quick Start

1. **Launch EC2 instance** (Ubuntu 22.04, t3.small recommended)

2. **Connect to instance:**
```bash
ssh -i your-key.pem ubuntu@your-ec2-ip
```

3. **Upload code:**
```bash
# Option 1: Clone from Git
git clone <your-repo-url>
cd trading_bot

# Option 2: Upload via SCP (from local machine)
scp -i your-key.pem -r . ubuntu@your-ec2-ip:/opt/trading-bot
```

4. **Run setup:**
```bash
cd /opt/trading-bot
sudo bash deploy/aws_setup.sh
```

5. **Configure:**
```bash
nano .env  # Add API keys
nano config/config.json  # Set testnet: false
```

6. **Test:**
```bash
source venv/bin/activate
python main.py
```

7. **Start service:**
```bash
sudo systemctl enable trading-bot
sudo systemctl start trading-bot
```

8. **Monitor:**
```bash
sudo journalctl -u trading-bot -f
```

## AWS Secrets Manager Setup

For better security, store API keys in AWS Secrets Manager:

1. **Create secret (from local machine):**
```bash
python deploy/update_secrets_manager.py
```

2. **Attach IAM role to EC2** with Secrets Manager read permissions, OR

3. **Configure AWS credentials on EC2:**
```bash
aws configure
```

The bot will automatically use Secrets Manager if available.

## Troubleshooting

- **Service won't start:** Check logs with `sudo journalctl -u trading-bot -n 50`
- **TA-Lib errors:** Make sure TA-Lib C library is installed
- **API connection issues:** Verify API keys in .env or Secrets Manager
- **Permission errors:** Run `sudo chown -R ubuntu:ubuntu /opt/trading-bot`

See `AWS_DEPLOYMENT.md` for detailed instructions.

