#!/usr/bin/env python3
"""
Simple launcher for Red Dragon - Binance Trading Bot with Telegram Mini App
Runs both the web app and bot in one command
"""

import subprocess
import time
import os
import signal
import sys

def main():
    print("=" * 60)
    print("🐉 Red Dragon - Binance Trading Bot with Telegram Mini App")
    print("=" * 60)
    print()
    
    # Get the directory where this script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    webapp_path = os.path.join(script_dir, 'webapp.py')
    botpath = os.path.join(script_dir, 'pythonbot.py')
    
    print(f"📁 Working Directory: {script_dir}")
    print()
    
    # Start web app
    print("🌐 Starting Web App (Flask)...")
    print("   → Access at: http://localhost:5000")
    print()
    
    try:
        webapp_process = subprocess.Popen(
            [sys.executable, webapp_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=script_dir
        )
        print("✅ Web App Started (PID: {})".format(webapp_process.pid))
    except Exception as e:
        print(f"❌ Failed to start web app: {e}")
        sys.exit(1)
    
    # Wait for web app to initialize
    time.sleep(3)
    
    # Start bot
    print("🤖 Starting Telegram Bot...")
    print("   → Send /start to activate mini app")
    print()
    
    try:
        bot_process = subprocess.Popen(
            [sys.executable, botpath],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=script_dir
        )
        print("✅ Bot Started (PID: {})".format(bot_process.pid))
    except Exception as e:
        print(f"❌ Failed to start bot: {e}")
        webapp_process.terminate()
        sys.exit(1)
    
    print()
    print("=" * 60)
    print("✨ Both services are running!")
    print("=" * 60)
    print()
    print("📱 Dashboard:")
    print("   → Browser: http://localhost:5000")
    print("   → Telegram: Send /start to your bot")
    print()
    print("Press CTRL+C to stop both services...")
    print()
    
    try:
        # Keep both processes running
        while True:
            time.sleep(1)
            if webapp_process.poll() is not None:
                print("⚠️  Web App stopped!")
            if bot_process.poll() is not None:
                print("⚠️  Bot stopped!")
    except KeyboardInterrupt:
        print()
        print("🛑 Shutting down...")
        
        # Terminate both processes
        webapp_process.terminate()
        bot_process.terminate()
        
        # Wait for graceful shutdown
        try:
            webapp_process.wait(timeout=5)
            bot_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            print("Force killing processes...")
            webapp_process.kill()
            bot_process.kill()
        
        print("✅ Shutdown complete")

if __name__ == "__main__":
    main()
