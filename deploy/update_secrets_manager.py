"""
Script to update AWS Secrets Manager with trading bot credentials.
Run this from your local machine with AWS CLI configured.
"""

import boto3
import json
import sys
from getpass import getpass


def update_secrets_manager():
    """Update or create secret in AWS Secrets Manager."""
    
    # Get region
    region = input("AWS Region (default: us-east-1): ").strip() or "us-east-1"
    secret_name = input("Secret name (default: trading-bot-secrets): ").strip() or "trading-bot-secrets"
    
    # Get credentials
    print("\nEnter Binance API credentials:")
    api_key = input("Binance API Key: ").strip()
    api_secret = getpass("Binance API Secret: ").strip()
    
    use_testnet = input("Use testnet? (y/n, default: n): ").strip().lower()
    testnet = "true" if use_testnet == "y" else "false"
    
    # Create secret value
    secret_value = {
        "BINANCE_API_KEY": api_key,
        "BINANCE_API_SECRET": api_secret,
        "BINANCE_TESTNET": testnet
    }
    
    # Initialize Secrets Manager client
    try:
        client = boto3.client('secretsmanager', region_name=region)
        
        # Try to get existing secret
        try:
            existing = client.get_secret_value(SecretId=secret_name)
            print(f"\nSecret '{secret_name}' exists. Updating...")
            
            # Update secret
            response = client.update_secret(
                SecretId=secret_name,
                SecretString=json.dumps(secret_value)
            )
            print(f"✓ Secret updated successfully!")
            print(f"  ARN: {response['ARN']}")
            
        except client.exceptions.ResourceNotFoundException:
            print(f"\nSecret '{secret_name}' not found. Creating...")
            
            # Create new secret
            response = client.create_secret(
                Name=secret_name,
                SecretString=json.dumps(secret_value),
                Description="Trading bot API credentials"
            )
            print(f"✓ Secret created successfully!")
            print(f"  ARN: {response['ARN']}")
        
        print(f"\nSecret stored in region: {region}")
        print(f"Testnet mode: {testnet}")
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        print("\nMake sure:")
        print("1. AWS CLI is configured (aws configure)")
        print("2. You have permissions for Secrets Manager")
        print("3. Region is correct")
        sys.exit(1)


if __name__ == "__main__":
    print("=" * 60)
    print("AWS Secrets Manager - Trading Bot Credentials")
    print("=" * 60)
    print()
    
    update_secrets_manager()
    
    print("\n" + "=" * 60)
    print("Next steps:")
    print("1. Attach IAM role to EC2 instance with Secrets Manager read permissions")
    print("2. Or configure AWS credentials on EC2 instance")
    print("3. Update config/settings.py to use Secrets Manager")
    print("=" * 60)

