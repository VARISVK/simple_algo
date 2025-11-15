#!/bin/bash
# Script to send logs to AWS CloudWatch

# Install CloudWatch agent (if not already installed)
if ! command -v aws &> /dev/null; then
    echo "Installing AWS CLI..."
    curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
    unzip awscliv2.zip
    sudo ./aws/install
fi

# Configure CloudWatch logs
LOG_GROUP_NAME="/trading-bot/linda-raschke"

# Create log group if it doesn't exist
aws logs create-log-group --log-group-name $LOG_GROUP_NAME 2>/dev/null || true

# Configure log stream
LOG_STREAM_NAME="bot-$(hostname)-$(date +%Y%m%d)"

aws logs create-log-stream \
    --log-group-name $LOG_GROUP_NAME \
    --log-stream-name $LOG_STREAM_NAME 2>/dev/null || true

# Function to send log to CloudWatch
send_log() {
    local message="$1"
    local timestamp=$(date +%s)000
    
    aws logs put-log-events \
        --log-group-name $LOG_GROUP_NAME \
        --log-stream-name $LOG_STREAM_NAME \
        --log-events timestamp=$timestamp,message="$message" \
        --sequence-token $(aws logs describe-log-streams \
            --log-group-name $LOG_GROUP_NAME \
            --log-stream-name-prefix $LOG_STREAM_NAME \
            --query 'logStreams[0].uploadSequenceToken' \
            --output text) 2>/dev/null || \
    aws logs put-log-events \
        --log-group-name $LOG_GROUP_NAME \
        --log-stream-name $LOG_STREAM_NAME \
        --log-events timestamp=$timestamp,message="$message"
}

# Monitor log file and send to CloudWatch
tail -f /opt/trading-bot/logs/trading_bot.log | while read line; do
    send_log "$line"
done

