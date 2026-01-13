#!/usr/bin/env python3
"""
Red Dragon Trading Bot - Deployment Helper
Helps set up environment variables for cloud deployment
"""

import os
import json
import sys

def setup_deployment():
    """Interactive setup for deployment environment variables"""

    print("🚀 Red Dragon Trading Bot - Deployment Setup")
    print("=" * 50)

    # Check if config.json exists
    config_file = "config.json"
    config = {}

    if os.path.exists(config_file):
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
            print("✅ Found existing config.json")
        except:
            print("⚠️  Could not read config.json")

    # Get Telegram Bot Token
    bot_token = input("Enter your Telegram Bot Token (from @BotFather): ").strip()
    if not bot_token:
        bot_token = config.get('bot_token', '')
    if not bot_token:
        print("❌ Bot token is required!")
        return False

    # Get Binance API Keys
    api_key = input("Enter your Binance API Key: ").strip()
    if not api_key:
        api_key = config.get('api_key', '')
    if not api_key:
        print("❌ Binance API Key is required!")
        return False

    api_secret = input("Enter your Binance API Secret: ").strip()
    if not api_secret:
        api_secret = config.get('api_secret', '')
    if not api_secret:
        print("❌ Binance API Secret is required!")
        return False

    # Web app settings
    web_app = input("Enable web dashboard? (y/N): ").strip().lower()
    web_app_enabled = web_app in ['y', 'yes']

    # Generate environment variables
    env_vars = f"""# Environment Variables for Deployment
BOT_TOKEN={bot_token}
BINANCE_API_KEY={api_key}
BINANCE_API_SECRET={api_secret}
WEB_APP_ENABLED={str(web_app_enabled).lower()}
"""

    # Save to .env file
    with open('.env', 'w') as f:
        f.write(env_vars)

    print("\n✅ Environment variables saved to .env")
    print("\n📋 Copy these to your hosting platform:")
    print("-" * 40)
    print(env_vars)
    print("-" * 40)

    # Platform-specific instructions
    print("\n🌐 Deployment Instructions:")
    print("1. Railway: Copy variables to 'Variables' tab")
    print("2. Render: Add as environment variables")
    print("3. Heroku: Use 'heroku config:set KEY=value'")
    print("4. Fly.io: Use 'fly secrets set KEY=value'")

    return True

def check_requirements():
    """Check if all requirements are met for deployment"""

    print("🔍 Checking deployment requirements...")

    # Check Python version
    python_version = sys.version_info
    if python_version.major < 3 or (python_version.major == 3 and python_version.minor < 8):
        print("❌ Python 3.8+ required")
        return False
    print(f"✅ Python {python_version.major}.{python_version.minor}.{python_version.micro}")

    # Check required files
    required_files = ['Procfile', 'requirements.txt', 'runtime.txt', 'pythonbot.py']
    for file in required_files:
        if os.path.exists(file):
            print(f"✅ {file}")
        else:
            print(f"❌ {file} missing")
            return False

    # Check if config exists
    if os.path.exists('config.json'):
        print("✅ config.json found")
    else:
        print("⚠️  config.json not found (will be created)")

    print("✅ All requirements met!")
    return True

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "check":
        check_requirements()
    else:
        if check_requirements():
            setup_deployment()
        else:
            print("❌ Fix requirements before proceeding")