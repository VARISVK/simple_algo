# AWS Deployment Checklist

Use this checklist to ensure a smooth deployment to AWS.

## Pre-Deployment

- [ ] AWS account created and configured
- [ ] AWS CLI installed and configured locally
- [ ] Binance production API keys obtained
- [ ] API keys have trading permissions (not just read-only)
- [ ] Tested bot on local machine with testnet
- [ ] Backtested strategy on historical data
- [ ] Reviewed and adjusted risk parameters
- [ ] Decided on initial capital allocation

## EC2 Setup

- [ ] EC2 instance launched (Ubuntu 22.04 LTS)
- [ ] Instance type selected (t3.small recommended)
- [ ] Security group configured (SSH only from your IP)
- [ ] Key pair downloaded and secured
- [ ] Can SSH into instance successfully

## Code Deployment

- [ ] Code uploaded to EC2 (Git clone or SCP)
- [ ] Code is in `/opt/trading-bot` directory
- [ ] All files present and permissions correct

## Installation

- [ ] Ran `sudo bash deploy/aws_setup.sh` successfully
- [ ] TA-Lib installed and working
- [ ] Python virtual environment created
- [ ] All dependencies installed (`pip install -r requirements.txt`)
- [ ] Systemd service file created

## Configuration

- [ ] `.env` file created with API credentials
- [ ] `config/config.json` updated for production
- [ ] `testnet: false` set in config.json
- [ ] Risk parameters reviewed and set appropriately
- [ ] Trading symbol and timeframe configured
- [ ] Check interval set appropriately

## AWS Secrets Manager (Optional but Recommended)

- [ ] Secrets Manager secret created
- [ ] API keys stored in Secrets Manager
- [ ] IAM role attached to EC2 with Secrets Manager permissions
- [ ] OR AWS credentials configured on EC2
- [ ] Tested secret retrieval

## Testing

- [ ] Tested API connection manually
- [ ] Verified bot can fetch market data
- [ ] Tested signal generation (without trading)
- [ ] Ran bot manually (`python main.py`) for a few minutes
- [ ] Verified logs are being written
- [ ] Checked database is working

## Service Setup

- [ ] Systemd service enabled (`sudo systemctl enable trading-bot`)
- [ ] Service started (`sudo systemctl start trading-bot`)
- [ ] Service status is "active (running)"
- [ ] Service auto-restarts on failure

## Monitoring Setup

- [ ] Logs directory created and writable
- [ ] Log rotation configured
- [ ] CloudWatch agent installed (optional)
- [ ] CloudWatch logs configured (optional)
- [ ] Monitoring alerts set up (optional)

## Security

- [ ] `.env` file permissions set (chmod 600)
- [ ] Firewall configured (UFW)
- [ ] SSH key secured
- [ ] No unnecessary ports open
- [ ] Regular security updates scheduled

## Final Verification

- [ ] Bot is running (`sudo systemctl status trading-bot`)
- [ ] Logs show successful startup
- [ ] No errors in logs
- [ ] API connection successful
- [ ] Can see signals being generated
- [ ] Database is recording trades (when they occur)

## Go-Live

- [ ] Start with minimal position sizes
- [ ] Monitor closely for first 24 hours
- [ ] Set up daily review schedule
- [ ] Have emergency stop procedure ready
- [ ] Document any issues encountered

## Post-Deployment

- [ ] Set up daily log review
- [ ] Monitor account balance daily
- [ ] Review trades weekly
- [ ] Adjust parameters based on performance
- [ ] Keep bot and system updated

## Emergency Procedures

- [ ] Know how to stop bot: `sudo systemctl stop trading-bot`
- [ ] Know how to check status: `sudo systemctl status trading-bot`
- [ ] Know how to view logs: `sudo journalctl -u trading-bot -f`
- [ ] Have backup of configuration files
- [ ] Know how to rollback if needed

## Notes

- Start with testnet even on AWS to verify everything works
- Use small position sizes initially
- Monitor closely for the first week
- Keep detailed logs of any issues
- Review and adjust strategy parameters regularly

---

**Remember:** Start small, test thoroughly, and scale gradually!

