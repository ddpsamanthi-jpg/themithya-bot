
"""
Red Dragon - Binance Trading Bot Mini App
Provides a web dashboard to monitor and control the Red Dragon trading bot
"""

from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
from datetime import datetime
import json
import threading
import time

app = Flask(__name__)
CORS(app)

# Shared data dictionary (will be updated by the main bot)
BOT_DATA = {
    "balance": {},
    "active_trades": {},
    "trading_config": {
        "enabled": False,
        "mode": "spot",
        "leverage": 1,
        "trade_amount": 0.001,
        "stop_loss_percent": 2,
        "take_profit_percent": 5
    },
    "trade_stats": {
        "total_trades": 0,
        "winning_trades": 0,
        "losing_trades": 0,
        "total_profit": 0,
        "total_loss": 0
    }
}

# Commands to be executed by bot
PENDING_COMMANDS = []

@app.route('/')
def index():
    """Serve the welcome page"""
    return render_template('welcome.html')

@app.route('/dashboard')
def dashboard():
    """Serve the main dashboard"""
    return render_template('dashboard.html')

@app.route('/api/status')
def get_status():
    """Get current bot status"""
    return jsonify({
        "trading_enabled": BOT_DATA["trading_config"]["enabled"],
        "mode": BOT_DATA["trading_config"]["mode"],
        "leverage": BOT_DATA["trading_config"]["leverage"],
        "active_trades": len(BOT_DATA["active_trades"]),
        "timestamp": datetime.now().isoformat()
    })

@app.route('/api/balance')
def get_balance():
    """Get account balance"""
    return jsonify(BOT_DATA["balance"])

@app.route('/api/trades')
def get_trades():
    """Get active trades"""
    return jsonify(BOT_DATA["active_trades"])

@app.route('/api/stats')
def get_stats():
    """Get trading statistics"""
    stats = BOT_DATA["trade_stats"].copy()
    stats["win_rate"] = (stats["winning_trades"] / stats["total_trades"] * 100) if stats["total_trades"] > 0 else 0
    return jsonify(stats)

@app.route('/api/config')
def get_config():
    """Get trading configuration"""
    return jsonify(BOT_DATA["trading_config"])

@app.route('/api/command', methods=['POST'])
def execute_command():
    """Queue a command to be executed by the bot"""
    data = request.json
    command = data.get('command')
    args = data.get('args', [])
    
    PENDING_COMMANDS.append({
        'command': command,
        'args': args,
        'timestamp': datetime.now().isoformat()
    })
    
    return jsonify({"status": "queued", "command": command})

@app.route('/api/commands/pending')
def get_pending_commands():
    """Get pending commands (for bot to consume)"""
    commands = PENDING_COMMANDS.copy()
    PENDING_COMMANDS.clear()
    return jsonify(commands)

@app.route('/api/sync', methods=['POST'])
def sync_bot_data():
    """Receive data updates from bot"""
    global BOT_DATA
    try:
        data = request.json
        BOT_DATA.update(data)
        return jsonify({"status": "ok"})
    except Exception as e:
        return jsonify({"error": str(e)}), 400

if __name__ == '__main__':
    # Run on localhost:5000
    app.run(debug=False, host='0.0.0.0', port=5000)
