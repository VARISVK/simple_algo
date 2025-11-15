#!/bin/bash
# Installation script for AWS EC2 deployment

set -e

echo "Installing Linda Raschke Trading Bot..."

# Update system
sudo apt-get update
sudo apt-get install -y python3 python3-pip python3-venv git

# Install TA-Lib dependencies
sudo apt-get install -y gcc g++ make wget

# Download and install TA-Lib
cd /tmp
wget http://prdownloads.sourceforge.net/ta-lib/ta-lib-0.4.0-src.tar.gz
tar -xzf ta-lib-0.4.0-src.tar.gz
cd ta-lib/
./configure --prefix=/usr
make
sudo make install
cd ..
rm -rf ta-lib ta-lib-0.4.0-src.tar.gz

# Create application directory
sudo mkdir -p /opt/trading-bot
sudo chown $USER:$USER /opt/trading-bot

# Clone or copy application
# Assuming code is already in /opt/trading-bot
cd /opt/trading-bot

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Create logs directory
mkdir -p logs

# Create systemd service
sudo tee /etc/systemd/system/trading-bot.service > /dev/null <<EOF
[Unit]
Description=Linda Raschke Trading Bot
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=/opt/trading-bot
Environment="PATH=/opt/trading-bot/venv/bin"
ExecStart=/opt/trading-bot/venv/bin/python main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Reload systemd
sudo systemctl daemon-reload

echo "Installation complete!"
echo "To start the bot: sudo systemctl start trading-bot"
echo "To enable auto-start: sudo systemctl enable trading-bot"
echo "To view logs: sudo journalctl -u trading-bot -f"

