#!/bin/bash
# Complete AWS EC2 setup script for trading bot
# Run this script on a fresh Ubuntu EC2 instance

set -e

echo "=========================================="
echo "AWS Trading Bot Setup Script"
echo "=========================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
APP_DIR="/opt/trading-bot"
SERVICE_USER="ubuntu"

# Check if running as root or with sudo
if [ "$EUID" -ne 0 ]; then 
    echo -e "${RED}Please run as root or with sudo${NC}"
    exit 1
fi

echo -e "${GREEN}Step 1: Updating system packages...${NC}"
apt-get update
apt-get install -y python3 python3-pip python3-venv git build-essential curl wget unzip

echo -e "${GREEN}Step 2: Installing TA-Lib dependencies...${NC}"
apt-get install -y gcc g++ make

echo -e "${GREEN}Step 3: Installing TA-Lib library...${NC}"
cd /tmp
if [ ! -f "ta-lib-0.4.0-src.tar.gz" ]; then
    wget http://prdownloads.sourceforge.net/ta-lib/ta-lib-0.4.0-src.tar.gz
fi
tar -xzf ta-lib-0.4.0-src.tar.gz
cd ta-lib/
./configure --prefix=/usr
make
make install
cd /
rm -rf /tmp/ta-lib*

echo -e "${GREEN}Step 4: Creating application directory...${NC}"
mkdir -p $APP_DIR
chown $SERVICE_USER:$SERVICE_USER $APP_DIR

echo -e "${YELLOW}Step 5: Setting up Python environment...${NC}"
echo "Note: You need to copy your code to $APP_DIR"
echo "You can:"
echo "  1. Clone from Git: cd $APP_DIR && git clone <repo-url> ."
echo "  2. Upload via SCP from your local machine"
echo ""
read -p "Press Enter when code is in $APP_DIR..."

cd $APP_DIR

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
echo -e "${GREEN}Step 6: Installing Python dependencies...${NC}"
pip install --upgrade pip
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
else
    echo -e "${RED}requirements.txt not found!${NC}"
    exit 1
fi

# Create logs directory
mkdir -p logs
chown -R $SERVICE_USER:$SERVICE_USER $APP_DIR

echo -e "${GREEN}Step 7: Installing AWS CLI...${NC}"
if ! command -v aws &> /dev/null; then
    curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
    unzip awscliv2.zip
    ./aws/install
    rm -rf aws awscliv2.zip
else
    echo "AWS CLI already installed"
fi

echo -e "${GREEN}Step 8: Creating systemd service...${NC}"
cat > /etc/systemd/system/trading-bot.service <<EOF
[Unit]
Description=Linda Raschke Trading Bot
After=network.target

[Service]
Type=simple
User=$SERVICE_USER
WorkingDirectory=$APP_DIR
Environment="PATH=$APP_DIR/venv/bin"
Environment="PYTHONUNBUFFERED=1"
ExecStart=$APP_DIR/venv/bin/python $APP_DIR/main.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

# Reload systemd
systemctl daemon-reload

echo -e "${GREEN}Step 9: Setting up log rotation...${NC}"
cat > /etc/logrotate.d/trading-bot <<EOF
$APP_DIR/logs/*.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
    create 0640 $SERVICE_USER $SERVICE_USER
}
EOF

echo -e "${GREEN}Step 10: Configuring firewall...${NC}"
if command -v ufw &> /dev/null; then
    ufw allow 22/tcp
    echo "Firewall configured (SSH allowed)"
else
    echo "UFW not installed, skipping firewall setup"
fi

echo ""
echo -e "${GREEN}=========================================="
echo "Setup Complete!"
echo "==========================================${NC}"
echo ""
echo "Next steps:"
echo "1. Configure .env file:"
echo "   cd $APP_DIR"
echo "   nano .env"
echo "   (Add your Binance API keys)"
echo ""
echo "2. Configure config.json:"
echo "   cd $APP_DIR"
echo "   nano config/config.json"
echo "   (Set testnet: false for production)"
echo ""
echo "3. Test the bot:"
echo "   cd $APP_DIR"
echo "   source venv/bin/activate"
echo "   python main.py"
echo ""
echo "4. If test successful, start service:"
echo "   sudo systemctl enable trading-bot"
echo "   sudo systemctl start trading-bot"
echo ""
echo "5. Monitor logs:"
echo "   sudo journalctl -u trading-bot -f"
echo ""
echo -e "${YELLOW}IMPORTANT: Test on testnet first!${NC}"
echo "Set BINANCE_TESTNET=true in .env for initial testing"

