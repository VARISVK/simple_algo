"""
Configuration management for the trading bot.
Handles loading configuration from JSON files and environment variables.
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Try to import boto3 for AWS Secrets Manager (optional)
try:
    import boto3
    BOTO3_AVAILABLE = True
except ImportError:
    BOTO3_AVAILABLE = False


class Settings:
    """Manages configuration settings for the trading bot."""
    
    def __init__(self, config_path: str = None):
        """
        Initialize settings from config file and environment variables.
        
        Args:
            config_path: Path to config.json file. If None, uses default path.
        """
        if config_path is None:
            # Default to config/config.json relative to project root
            project_root = Path(__file__).parent.parent
            config_path = project_root / "config" / "config.json"
        
        self.config_path = Path(config_path)
        self.config = self._load_config()
        self._override_with_env()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from JSON file."""
        try:
            with open(self.config_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            raise FileNotFoundError(
                f"Configuration file not found: {self.config_path}"
            )
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in config file: {e}")
    
    def _load_secrets_from_aws(self) -> Optional[Dict[str, str]]:
        """
        Load secrets from AWS Secrets Manager.
        
        Returns:
            Dictionary with secrets or None if not available
        """
        if not BOTO3_AVAILABLE:
            return None
        
        secret_name = os.getenv("AWS_SECRETS_MANAGER_SECRET_NAME", "trading-bot-secrets")
        region = os.getenv("AWS_REGION", "us-east-1")
        
        try:
            client = boto3.client('secretsmanager', region_name=region)
            response = client.get_secret_value(SecretId=secret_name)
            secrets = json.loads(response['SecretString'])
            return secrets
        except Exception:
            # Secrets Manager not available or not configured
            return None
    
    def _override_with_env(self):
        """Override config values with environment variables if present."""
        # Try to load from AWS Secrets Manager first
        aws_secrets = self._load_secrets_from_aws()
        
        # Override testnet setting
        testnet_value = None
        if aws_secrets and "BINANCE_TESTNET" in aws_secrets:
            testnet_value = aws_secrets["BINANCE_TESTNET"]
        elif os.getenv("BINANCE_TESTNET"):
            testnet_value = os.getenv("BINANCE_TESTNET")
        
        if testnet_value:
            self.config["trading"]["testnet"] = (
                str(testnet_value).lower() == "true"
            )
        
        # Override account balance
        if os.getenv("ACCOUNT_BALANCE"):
            try:
                self.config["risk"]["account_balance"] = float(
                    os.getenv("ACCOUNT_BALANCE")
                )
            except ValueError:
                pass
        
        # Override max daily loss
        if os.getenv("MAX_DAILY_LOSS"):
            try:
                self.config["risk"]["max_daily_loss"] = float(
                    os.getenv("MAX_DAILY_LOSS")
                )
            except ValueError:
                pass
    
    def get(self, key_path: str, default: Any = None) -> Any:
        """
        Get configuration value using dot notation.
        
        Args:
            key_path: Dot-separated path to config value (e.g., "strategy.fast_period")
            default: Default value if key not found
        
        Returns:
            Configuration value or default
        """
        keys = key_path.split('.')
        value = self.config
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        
        return value
    
    def get_strategy_config(self) -> Dict[str, Any]:
        """Get strategy configuration."""
        return self.config.get("strategy", {})
    
    def get_trading_config(self) -> Dict[str, Any]:
        """Get trading configuration."""
        return self.config.get("trading", {})
    
    def get_risk_config(self) -> Dict[str, Any]:
        """Get risk management configuration."""
        return self.config.get("risk", {})
    
    def get_execution_config(self) -> Dict[str, Any]:
        """Get execution configuration."""
        return self.config.get("execution", {})
    
    @property
    def api_key(self) -> str:
        """Get Binance API key from environment or AWS Secrets Manager."""
        # Try AWS Secrets Manager first
        aws_secrets = self._load_secrets_from_aws()
        if aws_secrets and "BINANCE_API_KEY" in aws_secrets:
            return aws_secrets["BINANCE_API_KEY"]
        # Fallback to environment variable
        return os.getenv("BINANCE_API_KEY", "")
    
    @property
    def api_secret(self) -> str:
        """Get Binance API secret from environment or AWS Secrets Manager."""
        # Try AWS Secrets Manager first
        aws_secrets = self._load_secrets_from_aws()
        if aws_secrets and "BINANCE_API_SECRET" in aws_secrets:
            return aws_secrets["BINANCE_API_SECRET"]
        # Fallback to environment variable
        return os.getenv("BINANCE_API_SECRET", "")
    
    @property
    def testnet(self) -> bool:
        """Check if testnet mode is enabled."""
        return self.config.get("trading", {}).get("testnet", True)

