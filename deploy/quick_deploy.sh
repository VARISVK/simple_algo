#!/bin/bash
# Quick deployment script - Run this on your EC2 instance after uploading code

set -e

APP_DIR="/opt/trading-bot"
SERVICE_NAME="trading-bot"

echo "=========================================="
echo "Quick Trading Bot Deployment"
echo "=========================================="

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "Please run with sudo"
    exit 1
fi

cd $APP_DIR

echo "1. Activating virtual environment..."
source venv/bin/activate

echo "2. Installing/updating dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

echo "3. Creating necessary directories..."
mkdir -p logs
chown -R ubuntu:ubuntu $APP_DIR

echo "4. Setting up systemd service..."
cat > /etc/systemd/system/$SERVICE_NAME.service <<EOF
[Unit]
Description=Linda Raschke Trading Bot
After=network.target

[Service]
Type=simple
User=ubuntu
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

systemctl daemon-reload

echo "5. Checking configuration..."
if [ ! -f ".env" ]; then
    echo "WARNING: .env file not found!"
    echo "Create .env file with your API credentials"
fi

if [ ! -f "config/config.json" ]; then
    echo "WARNING: config/config.json not found!"
    exit 1
fi

echo ""
echo "=========================================="
echo "Deployment Complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo ""
echo "1. Configure .env file:"
echo "   nano $APP_DIR/.env"
echo ""
echo "2. Update config/config.json for production:"
echo "   nano $APP_DIR/config/config.json"
echo "   Set 'testnet': false"
echo ""
echo "3. Test the bot manually:"
echo "   cd $APP_DIR"
echo "   source venv/bin/activate"
echo "   python main.py"
echo ""
echo "4. If test successful, start service:"
echo "   sudo systemctl enable $SERVICE_NAME"
echo "   sudo systemctl start $SERVICE_NAME"
echo ""
echo "5. Monitor logs:"
echo "   sudo journalctl -u $SERVICE_NAME -f"
echo ""

