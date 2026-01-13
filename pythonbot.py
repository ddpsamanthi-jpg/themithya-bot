import os
from telegram.ext import Updater, CommandHandler, Application, ContextTypes
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from binance.client import Client
import logging
from datetime import datetime
import pandas as pd
import numpy as np
import json
from decimal import Decimal
import asyncio
import threading
import time
from flask import Flask, request, jsonify

# Configuration
BOT_TOKEN = "8251943750:AAGNKIaeUgq020N0jutrOVAOOFPcRUbThi8"
CONFIG_FILE = "config.json"

# Load configuration from file or environment
def load_config():
    global BINANCE_API_KEY, BINANCE_API_SECRET
    try:
        with open(CONFIG_FILE, 'r') as f:
            config = json.load(f)
            BINANCE_API_KEY = config.get('api_key')
            BINANCE_API_SECRET = config.get('api_secret')
    except FileNotFoundError:
        # Try environment variables
        BINANCE_API_KEY = os.getenv('BINANCE_API_KEY')
        BINANCE_API_SECRET = os.getenv('BINANCE_API_SECRET')
        # Save to file if found
        if BINANCE_API_KEY and BINANCE_API_SECRET:
            save_config()

def save_config():
    config = {
        'api_key': BINANCE_API_KEY,
        'api_secret': BINANCE_API_SECRET
    }
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=4)

# Load config on startup
load_config()

# Web app configuration
WEB_APP_URL = os.getenv('WEB_APP_URL', 'https://yourserver.com/bot')  # Use environment variable or default
WEB_APP_ENABLED = os.getenv('WEB_APP_ENABLED', 'false').lower() == 'true'

# Trading Configuration
TRADING_CONFIG = {
    "enabled": False,  # Set to True to enable auto-trading
    "trade_amount": 0.6,  # Amount to trade (in BTC for BTCUSDT) - set to 0.6 as requested
    "stop_loss_percent": 0,  # Stop loss percentage - set to 0 to disable
    "take_profit_percent": 0,  # Take profit percentage - set to 0 to disable
    "leverage": 15,  # Trading leverage (1 = no leverage, 15 = 15x leverage)
    "mode": "futures",  # Trading mode: "spot" or "futures" (default to futures)
    "position_mode": "one_way",  # Futures position mode: "one_way" or "hedge" (default: one_way)
    "max_positions": 6,  # Maximum number of active positions
}

# Active trades tracking
ACTIVE_TRADES = {}

# Trade history and statistics
TRADE_HISTORY = []
TRADE_STATS = {
    "total_trades": 0,
    "winning_trades": 0,
    "losing_trades": 0,
    "total_profit": 0.0,
    "total_loss": 0.0,
    "win_rate": 0.0
}

# Enable logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global Binance client
binance_client = None

def get_binance_client():
    """Get or create Binance client with current API credentials"""
    global binance_client, BINANCE_API_KEY, BINANCE_API_SECRET
    if binance_client is None and BINANCE_API_KEY and BINANCE_API_SECRET:
        try:
            binance_client = Client(BINANCE_API_KEY, BINANCE_API_SECRET)
        except Exception as e:
            logger.error(f"Failed to create Binance client: {e}")
            return None
    return binance_client

def get_public_client():
    """Get Binance client for public endpoints (no API key needed)"""
    try:
        return Client("", "")  # Public client
    except:
        return None

def calculate_qqe(closes, period=14, smoothing=5):
    """Calculate QQE (Qualitative Quantitative Estimation) signal"""
    try:
        # Calculate RSI
        delta = pd.Series(closes).diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        # Smooth RSI
        smoothed_rsi = rsi.rolling(window=smoothing).mean()
        
        # Calculate fast and slow ATR
        high_low = pd.Series(closes).rolling(window=period).max() - pd.Series(closes).rolling(window=period).min()
        fast_atr = high_low.rolling(window=smoothing).mean()
        
        # QQE bands
        qqe_upper = smoothed_rsi + fast_atr
        qqe_lower = smoothed_rsi - fast_atr
        
        return rsi.iloc[-1], smoothed_rsi.iloc[-1], qqe_upper.iloc[-1], qqe_lower.iloc[-1]
    except Exception as e:
        logger.error(f"QQE calculation error: {e}")
        return None, None, None, None

# --- Fibonacci retracement calculation ---
def calculate_fibonacci_levels(closes):
    """Calculate Fibonacci retracement levels from recent closes (high to low)"""
    if len(closes) < 2:
        return None
    high = max(closes)
    low = min(closes)
    diff = high - low
    levels = {
        '0.0%': high,
        '23.6%': high - 0.236 * diff,
        '38.2%': high - 0.382 * diff,
        '50.0%': high - 0.5 * diff,
        '61.8%': high - 0.618 * diff,
        '78.6%': high - 0.786 * diff,
        '100.0%': low
    }
    return levels, high, low

async def analyze_market(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Analyze whole market for trading signals"""
    client = get_binance_client()
    if client is None:
        await update.message.reply_text("❌ Binance API credentials not set. Use /setapikey and /setapisecret to configure.")
        return
    
    try:
        await update.message.reply_text("📊 Scanning 65+ markets... This may take a moment...")
        
        # 65+ Popular trading pairs to scan
        trading_pairs = [
            # Top 15 by market cap
            "BTCUSDT", "ETHUSDT", "BNBUSDT", "XRPUSDT", "ADAUSDT",
            "DOGEUSDT", "SOLUSDT", "MATICUSDT", "AVAXUSDT", "LINKUSDT",
            "LTCUSDT", "XLMUSDT", "UNIUSDT", "DOTUSDT", "ATOMUSDT",
            # Additional 50+ coins
            "TRXUSDT", "FDUSUDT", "TUSDUSDT", "PEPEUSDT", "SUIUSDT",
            "WBTCUSDT", "OKBUSDT", "VETUSDT", "FILUSDT", "GRTUSDT",
            "ALGOUSDT", "ARBUSDT", "OPUSDT", "LDOBUSDT", "IOTIUSDT",
            "NEARUSDT", "ICPUSDT", "MKRUSDT", "AAVEUSDT", "SHIBUSDT",
            "INJUSDT", "APTUSDT", "RUNEUSDT", "LDOUSDT", "THETAUSDT",
            "JTOESDT", "JUPUSDT", "FLOKIUSDT", "EOSUSDT", "XTZUSDT",
            "COSMOSUSDT", "FLOWUSDT", "MANAUSDT", "SANDUSDT", "ENAUSDT",
            "BTGUSDT", "ETHWUSDT", "CAKEUSDT", "SSVUSDT", "QNTUSDT",
            "OCEANUSDT", "CVXUSDT", "BALANCEUSDT", "GNSUSDT", "WIFUSDT",
            "BONKUSDT", "STGUSDT", "PHBUSDT", "POLYUSDT", "POLYXUSDT"
        ]
        
        buy_signals = []
        sell_signals = []
        neutral_signals = []
        
        for symbol in trading_pairs:
            try:
                # Get historical data
                klines = client.get_historical_klines(
                    symbol, Client.KLINE_INTERVAL_1HOUR, "100 hours ago UTC"
                )
                closes = [float(k[4]) for k in klines]
                
                rsi, smooth_rsi, upper, lower = calculate_qqe(closes)
                
                if rsi is None:
                    continue
                
                current_price = closes[-1]
                
                # Determine signal strength
                if smooth_rsi < lower:
                    signal_strength = lower - smooth_rsi
                    buy_signals.append((symbol, current_price, signal_strength, smooth_rsi))
                elif smooth_rsi > upper:
                    signal_strength = smooth_rsi - upper
                    sell_signals.append((symbol, current_price, signal_strength, smooth_rsi))
                else:
                    neutral_signals.append((symbol, current_price, smooth_rsi))
            except Exception as e:
                logger.error(f"Error scanning {symbol}: {e}")
                continue
        
        # Sort by signal strength
        buy_signals.sort(key=lambda x: x[2], reverse=True)
        sell_signals.sort(key=lambda x: x[2], reverse=True)
        
        # Create response
        response = "📈 MARKET ANALYSIS RESULTS (65+ Pairs)\n"
        response += f"{'='*50}\n\n"
        
        if buy_signals:
            response += "🟢 BUY SIGNALS (Top 10 Strongest):\n"
            for i, (symbol, price, strength, rsi) in enumerate(buy_signals[:10], 1):
                response += f"{i}. {symbol} @ ${price:,.2f}\n"
                response += f"   Strength: {strength:.2f} | RSI: {rsi:.2f}\n"
        else:
            response += "🟢 BUY SIGNALS: None found\n\n"
        
        if sell_signals:
            response += "\n🔴 SELL SIGNALS (Top 10 Strongest):\n"
            for i, (symbol, price, strength, rsi) in enumerate(sell_signals[:10], 1):
                response += f"{i}. {symbol} @ ${price:,.2f}\n"
                response += f"   Strength: {strength:.2f} | RSI: {rsi:.2f}\n"
        else:
            response += "\n🔴 SELL SIGNALS: None found\n"
        
        response += f"\n{'='*50}\n"
        response += f"📊 Summary:\n"
        response += f"   Total BUY Signals: {len(buy_signals)}\n"
        response += f"   Total SELL Signals: {len(sell_signals)}\n"
        response += f"   NEUTRAL: {len(neutral_signals)}\n"
        response += f"⏱️  Scanned: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        await update.message.reply_text(response)
        
    except Exception as e:
        await update.message.reply_text(f"❌ Market analysis error: {str(e)}")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start command handler"""
    # Create keyboard with web app button
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(
            text="📱 Open Dashboard", 
            web_app={"url": WEB_APP_URL}
        )]
    ])
    
    await update.message.reply_text(
        "🐉 **Red Dragon Trading Bot**\n\n"
        "Available commands:\n"
        "/start - Show this message\n"
        "/setapikey <key> - Set your Binance API key\n"
        "/setapisecret <secret> - Set your Binance API secret\n"
        "/showapikey - Show current API key\n"
        "/showapisecret - Show current API secret\n"
        "/checkapi - Test API connection\n"
        "/balance - Check account balance\n"
        "/price <symbol> - Get current price\n"
        "/qqe <symbol> - QQE signal for one pair\n\n"
        "📊 Market Analysis:\n"
        "/market - Analyze whole market for signals\n"
        "/tradeall - Auto-trade all BUY signals (0.6 USDT each)\n\n"
        "⚙️ Trading Mode:\n"
        "/mode <spot|futures> - Switch between Spot/Futures (Default: Futures)\n"
        "/posmode <one_way|hedge> - Set futures position mode\n"
        "/leverage <value> - Set leverage (1-125x)\n\n"
        "⚙️ Trading Control:\n"
        "/enable - Enable auto-trading\n"
        "/disable - Disable auto-trading\n"
        "/status - Trading status\n"
        "/setamount <qty> - Set trade amount\n"
        "/setwallet - Set amount to 1/12 of wallet\n"
        "/setstoploss <percent> - Set stop loss %\n"
        "/settakeprofit <percent> - Set take profit %\n"
        "/setmaxpos <number> - Set max active positions (default: 6)\n\n"
        "📈 Performance:\n"
        "/performance - View stats & results\n"
        "/history - View recent trades\n"
        "/closetrade <id> <price> - Close trade manually\n\n"
        "🔥 New Features:\n"
        "• Futures trading enabled by default\n"
        "• QQE signal reversal auto-close\n"
        "• 1/12 wallet risk per trade\n"
        "• Maximum 6 active positions",
        reply_markup=keyboard
    )

async def balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Get comprehensive account balance across all wallets"""
    client = get_binance_client()
    if client is None:
        await update.message.reply_text("❌ Binance API credentials not set. Use /setapikey and /setapisecret to configure.")
        return
    
    try:
        await update.message.reply_text("🔄 Fetching comprehensive account balance...")
        
        response = "💰 **COMPREHENSIVE ACCOUNT BALANCE**\n\n"
        
        # Use public client for price fetching
        public_client = get_public_client()
        if public_client is None:
            await update.message.reply_text("❌ Could not connect to Binance public API")
            return
        
        # Initialize totals
        spot_total_usdt = 0.0
        futures_total_usdt = 0.0
        funding_total_usdt = 0.0
        margin_total_usdt = 0.0
        isolated_total_usdt = 0.0
        positions_total_value = 0.0
        positions_total_pnl = 0.0
        
        # 1. SPOT WALLET BALANCE
        try:
            account = client.get_account()
            balances = account['balances']
            active_balances = [b for b in balances if float(b['free']) > 0 or float(b['locked']) > 0]
            
            if active_balances:
                response += "🏦 **SPOT WALLET:**\n"
                
                for balance_item in active_balances:
                    symbol = balance_item['asset']
                    free = float(balance_item['free'])
                    locked = float(balance_item['locked'])
                    total = free + locked
                    
                    if total > 0:
                        try:
                            if symbol == "USDT":
                                price = 1.0
                                balance_usdt = total * price
                                spot_total_usdt += balance_usdt
                                response += f"  {symbol}: ${balance_usdt:,.2f}\n"
                            elif symbol == "BUSD":
                                price = 1.0
                                balance_usdt = total * price
                                spot_total_usdt += balance_usdt
                                response += f"  {symbol}: ${balance_usdt:,.2f}\n"
                            else:
                                try:
                                    ticker = public_client.get_symbol_ticker(symbol=f"{symbol}USDT")
                                    price = float(ticker['price'])
                                    balance_usdt = total * price
                                    spot_total_usdt += balance_usdt
                                    response += f"  {symbol}: ${balance_usdt:,.2f}\n"
                                except:
                                    try:
                                        ticker = public_client.get_symbol_ticker(symbol=f"{symbol}BUSD")
                                        price = float(ticker['price'])
                                        balance_usdt = total * price
                                        spot_total_usdt += balance_usdt
                                        response += f"  {symbol}: ${balance_usdt:,.2f}\n"
                                    except:
                                        response += f"  {symbol}: {total:.8f} (price unavailable)\n"
                        except Exception as e:
                            response += f"  {symbol}: {total:.8f} (price error)\n"
                
                response += f"  **Spot Wallet Total: ${spot_total_usdt:,.2f} USDT**\n\n"
            else:
                response += "🏦 **SPOT WALLET:** No assets\n\n"
        except Exception as e:
            response += f"🏦 **SPOT WALLET:** Error - {str(e)}\n\n"
        
        # 2. FUTURES WALLET BALANCE (USDT-M Futures)
        try:
            futures_account = client.futures_account_balance()
            
            if futures_account:
                response += "🚀 **FUTURES WALLET (USDT-M Futures):**\n"
                for asset in futures_account:
                    balance = float(asset['balance'])
                    if balance > 0:
                        asset_name = asset['asset']
                        if asset_name == 'USDT':
                            futures_total_usdt += balance
                            response += f"  {asset_name}: ${balance:,.2f}\n"
                        else:
                            # Try to get price for non-USDT assets
                            try:
                                if asset_name == 'BUSD':
                                    price = 1.0
                                else:
                                    ticker = public_client.get_symbol_ticker(symbol=f"{asset_name}USDT")
                                    price = float(ticker['price'])
                                balance_usdt = balance * price
                                futures_total_usdt += balance_usdt
                                response += f"  {asset_name}: ${balance_usdt:,.2f}\n"
                            except:
                                response += f"  {asset_name}: {balance:.8f} (price unavailable)\n"
                
                response += f"  **USDT-M Futures Total: ${futures_total_usdt:,.2f} USDT**\n\n"
            else:
                response += "🚀 **FUTURES WALLET (USDT-M Futures):** No assets\n\n"
        except Exception as e:
            response += f"🚀 **FUTURES WALLET (USDT-M Futures):** Error - {str(e)}\n\n"
        
        # 3. ONGOING TRADES VALUE (Active Positions)
        try:
            positions = client.futures_position_information()
            active_positions = [p for p in positions if float(p['positionAmt']) != 0]
            
            if active_positions:
                response += "📊 **ONGOING TRADES VALUE (Active Positions):**\n"
                
                for position in active_positions:
                    symbol = position['symbol']
                    position_amt = float(position['positionAmt'])
                    entry_price = float(position['entryPrice'])
                    mark_price = float(position['markPrice'])
                    unrealized_pnl = float(position['unRealizedProfit'])
                    leverage = float(position['leverage'])
                    
                    # Calculate position value
                    notional_value = abs(position_amt) * mark_price / leverage
                    positions_total_pnl += unrealized_pnl
                    positions_total_value += notional_value
                    
                    side = "LONG" if position_amt > 0 else "SHORT"
                    response += f"  🔄 {symbol} | {side} {abs(position_amt):.4f} @ ${entry_price:.4f}\n"
                    response += f"    Current: ${mark_price:.4f} | Leverage: {leverage}x\n"
                    response += f"    Notional: ${notional_value:.2f} | P&L: ${unrealized_pnl:+,.2f}\n"
                
                response += f"  **Total Positions Value: ${positions_total_value:.2f} USDT**\n"
                response += f"  **Total Positions P&L: ${positions_total_pnl:+,.2f} USDT**\n\n"
            else:
                response += "📊 **ONGOING TRADES VALUE (Active Positions):** None\n\n"
        except Exception as e:
            response += f"📊 **ONGOING TRADES VALUE (Active Positions):** Error - {str(e)}\n\n"
        
        # 4. FUNDING WALLET
        try:
            funding_account = client.futures_account()
            funding_balances = funding_account.get('assets', [])
            
            if funding_balances:
                response += "💰 **FUNDING WALLET:**\n"
                for asset in funding_balances:
                    wallet_balance = float(asset.get('walletBalance', 0))
                    if wallet_balance > 0:
                        asset_name = asset['asset']
                        if asset_name == 'USDT':
                            funding_total_usdt += wallet_balance
                            response += f"  {asset_name}: ${wallet_balance:,.2f}\n"
                        else:
                            try:
                                if asset_name == 'BUSD':
                                    price = 1.0
                                else:
                                    ticker = public_client.get_symbol_ticker(symbol=f"{asset_name}USDT")
                                    price = float(ticker['price'])
                                balance_usdt = wallet_balance * price
                                funding_total_usdt += balance_usdt
                                response += f"  {asset_name}: ${balance_usdt:,.2f}\n"
                            except:
                                response += f"  {asset_name}: {wallet_balance:.8f} (price unavailable)\n"
                
                response += f"  **Funding Wallet Total: ${funding_total_usdt:,.2f} USDT**\n\n"
            else:
                response += "💰 **FUNDING WALLET:** No assets\n\n"
        except Exception as e:
            response += f"💰 **FUNDING WALLET:** Error - {str(e)}\n\n"
        
        # 5. CROSS MARGIN ACCOUNT
        try:
            margin_account = client.get_margin_account()
            margin_balances = margin_account.get('userAssets', [])
            
            active_margin = [asset for asset in margin_balances if float(asset.get('free', 0)) > 0 or float(asset.get('locked', 0)) > 0]
            if active_margin:
                response += "🏦 **CROSS MARGIN ACCOUNT:**\n"
                for asset in active_margin:
                    free = float(asset.get('free', 0))
                    locked = float(asset.get('locked', 0))
                    total = free + locked
                    asset_name = asset['asset']
                    
                    try:
                        if asset_name == 'USDT':
                            price = 1.0
                            balance_usdt = total * price
                            margin_total_usdt += balance_usdt
                            response += f"  {asset_name}: ${balance_usdt:,.2f}\n"
                        elif asset_name == 'BUSD':
                            price = 1.0
                            balance_usdt = total * price
                            margin_total_usdt += balance_usdt
                            response += f"  {asset_name}: ${balance_usdt:,.2f}\n"
                        else:
                            ticker = public_client.get_symbol_ticker(symbol=f"{asset_name}USDT")
                            price = float(ticker['price'])
                            balance_usdt = total * price
                            margin_total_usdt += balance_usdt
                            response += f"  {asset_name}: ${balance_usdt:,.2f}\n"
                    except:
                        response += f"  {asset_name}: {total:.8f} (price unavailable)\n"
                
                response += f"  **Cross Margin Total: ${margin_total_usdt:,.2f} USDT**\n\n"
            else:
                response += "🏦 **CROSS MARGIN ACCOUNT:** No assets\n\n"
        except Exception as e:
            response += f"🏦 **CROSS MARGIN ACCOUNT:** Error - {str(e)}\n\n"
        
        # 6. ISOLATED MARGIN ACCOUNTS
        try:
            isolated_accounts = client.get_isolated_margin_account()
            has_isolated = False
            
            for symbol_info in isolated_accounts.get('assets', []):
                base_asset = symbol_info['baseAsset']
                quote_asset = symbol_info['quoteAsset']
                
                base_free = float(symbol_info['baseAsset']['free'])
                base_locked = float(symbol_info['baseAsset']['locked'])
                base_total = base_free + base_locked
                
                quote_free = float(symbol_info['quoteAsset']['free'])
                quote_locked = float(symbol_info['quoteAsset']['locked'])
                quote_total = quote_free + quote_locked
                
                if base_total > 0 or quote_total > 0:
                    if not has_isolated:
                        response += "🔒 **ISOLATED MARGIN ACCOUNTS:**\n"
                        has_isolated = True
                    
                    try:
                        if base_asset == 'USDT':
                            price = 1.0
                            balance_usdt = base_total * price
                            isolated_total_usdt += balance_usdt
                            response += f"  {base_asset}: ${balance_usdt:,.2f}\n"
                        else:
                            ticker = public_client.get_symbol_ticker(symbol=f"{base_asset}USDT")
                            price = float(ticker['price'])
                            balance_usdt = base_total * price
                            isolated_total_usdt += balance_usdt
                            response += f"  {base_asset}: ${balance_usdt:,.2f}\n"
                    except:
                        response += f"  {base_asset}: {base_total:.8f} (price unavailable)\n"
                    
                    try:
                        if quote_asset == 'USDT':
                            price = 1.0
                            balance_usdt = quote_total * price
                            isolated_total_usdt += balance_usdt
                            response += f"  {quote_asset}: ${balance_usdt:,.2f}\n"
                        else:
                            ticker = public_client.get_symbol_ticker(symbol=f"{quote_asset}USDT")
                            price = float(ticker['price'])
                            balance_usdt = quote_total * price
                            isolated_total_usdt += balance_usdt
                            response += f"  {quote_asset}: ${balance_usdt:,.2f}\n"
                    except:
                        response += f"  {quote_asset}: {quote_total:.8f} (price unavailable)\n"
            
            if has_isolated:
                response += f"  **Isolated Margin Total: ${isolated_total_usdt:,.2f} USDT**\n\n"
            else:
                response += "🔒 **ISOLATED MARGIN ACCOUNTS:** None\n\n"
        except Exception as e:
            response += f"🔒 **ISOLATED MARGIN ACCOUNTS:** Error - {str(e)}\n\n"
        
        # 7. EARN WALLET (Not accessible via API)
        response += "💎 **EARN WALLET:**\n"
        response += "  ⚠️ Not accessible via Binance API\n"
        response += "  Check Binance app/website for:\n"
        response += "  • Flexible Savings\n"
        response += "  • Fixed/Staking products\n"
        response += "  • Launchpool rewards\n"
        response += "  • Other Earn products\n\n"
        
        # 8. OTHER WALLETS
        response += "🔄 **OTHER WALLETS:**\n"
        response += "  • Coin-Margined Futures (if any)\n"
        response += "  • Options (if any)\n"
        response += "  • NFT/Collectibles (if any)\n"
        response += "  • Promotional balances\n"
        response += "  ⚠️ Check Binance app/website for complete list\n\n"
        
        # 7. EARN WALLET (Not accessible via API)
        response += "💎 **EARN WALLET:**\n"
        response += "  ⚠️ Not accessible via Binance API\n"
        response += "  Check Binance app/website for:\n"
        response += "  • Flexible Savings\n"
        response += "  • Fixed/Staking products\n"
        response += "  • Launchpool rewards\n"
        response += "  • Other Earn products\n\n"
        
        # 8. OTHER WALLETS
        response += "🔄 **OTHER WALLETS:**\n"
        response += "  • Coin-Margined Futures (if any)\n"
        response += "  • Options (if any)\n"
        response += "  • NFT/Collectibles (if any)\n"
        response += "  • Promotional balances\n"
        response += "  ⚠️ Check Binance app/website for complete list\n\n"
        
        response += f"{'='*50}\n"
        response += "📈 **ACCOUNT SUMMARY**\n"
        response += f"Spot Wallet: ${spot_total_usdt:,.2f} USDT\n"
        response += f"USDT-M Futures Wallet: ${futures_total_usdt:,.2f} USDT\n"
        response += f"Ongoing Trades Value: ${positions_total_value:,.2f} USDT\n"
        response += f"Ongoing Trades P&L: ${positions_total_pnl:+,.2f} USDT\n"
        response += f"Funding Wallet: ${funding_total_usdt:,.2f} USDT\n"
        response += f"Cross Margin Account: ${margin_total_usdt:,.2f} USDT\n"
        response += f"Isolated Margin Accounts: ${isolated_total_usdt:,.2f} USDT\n"
        response += f"Earn Wallet: Not accessible via API\n"
        response += f"Other Wallets: Check Binance app/website\n"
        
        total_account_value = spot_total_usdt + futures_total_usdt + positions_total_value + positions_total_pnl + funding_total_usdt + margin_total_usdt + isolated_total_usdt
        
        response += f"**TOTAL API-ACCESSIBLE VALUE: ${total_account_value:,.2f} USDT**\n\n"
        
        # Add disclaimer about potential missing balances
        response += "⚠️ **IMPORTANT NOTE:**\n"
        response += "This shows balances accessible via Binance API.\n"
        response += "Your actual total balance may be higher if you have:\n"
        response += "• Binance Earn/Flexible Savings\n"
        response += "• Locked Staking rewards\n"
        response += "• Launchpool/Launchpad investments\n"
        response += "• Funds in different accounts\n"
        response += "• Promotional/reward balances\n\n"
        response += f"**API-Accessible Total: ${total_account_value:.2f} USDT**\n"
        response += "Check Binance app/website for complete balance including Earn and other non-API wallets."
        
        await update.message.reply_text(response)
        
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Balance error: {error_msg}")
        await update.message.reply_text(f"❌ Error fetching balance: {error_msg}\n\n🔧 **Troubleshooting:**\n• Check if your API key has 'Read Info' permission\n• Verify API key and secret are correct\n• Make sure IP restrictions allow access\n• Try regenerating API credentials")

async def transfer_to_futures(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Transfer all available funds to USDT-M futures wallet"""
    client = get_binance_client()
    if client is None:
        await update.message.reply_text("❌ Binance API credentials not set. Use /setapikey and /setapisecret to configure.")
        return
    
    try:
        await update.message.reply_text("🔄 Transferring all funds to USDT-M Futures wallet... This may take a moment...")
        
        # Use public client for price fetching
        public_client = get_public_client()
        if public_client is None:
            await update.message.reply_text("❌ Could not connect to Binance public API")
            return
        
        transfer_log = []
        total_transferred = 0.0
        
        # 1. Transfer from SPOT wallet
        try:
            account = client.get_account()
            balances = account['balances']
            active_balances = [b for b in balances if float(b['free']) > 0 or float(b['locked']) > 0]
            
            for balance_item in active_balances:
                symbol = balance_item['asset']
                free = float(balance_item['free'])
                locked = float(balance_item['locked'])
                total = free + locked
                
                if total > 0 and symbol != 'USDT':
                    # For non-USDT assets, we need to sell them to USDT first
                    try:
                        # Check if we can sell to USDT
                        if symbol == 'BUSD':
                            # BUSD can be transferred directly or converted
                            amount_to_transfer = free  # Only transfer free amount
                            if amount_to_transfer > 0.01:  # Minimum transfer amount
                                try:
                                    # Transfer BUSD from spot to futures
                                    transfer_result = client.futures_transfer(asset='BUSD', amount=amount_to_transfer, type=1)  # 1 = from spot to futures
                                    transfer_log.append(f"✅ Transferred {amount_to_transfer:.2f} {symbol} from Spot to Futures")
                                    total_transferred += amount_to_transfer
                                except Exception as e:
                                    transfer_log.append(f"❌ Failed to transfer {symbol} from Spot: {str(e)}")
                        else:
                            # For other assets, try to sell to USDT in spot
                            try:
                                # Get current price
                                ticker = public_client.get_symbol_ticker(symbol=f"{symbol}USDT")
                                price = float(ticker['price'])
                                usdt_value = total * price
                                
                                if usdt_value > 10:  # Only sell if worth more than 10 USDT
                                    # Place market sell order
                                    sell_order = client.order_market_sell(
                                        symbol=f"{symbol}USDT",
                                        quantity=free
                                    )
                                    transfer_log.append(f"✅ Sold {free:.8f} {symbol} (${usdt_value:.2f}) to USDT in Spot")
                                else:
                                    transfer_log.append(f"⚠️ Skipped {symbol}: too small (${usdt_value:.2f})")
                            except Exception as e:
                                transfer_log.append(f"❌ Failed to sell {symbol} to USDT: {str(e)}")
                    except Exception as e:
                        transfer_log.append(f"❌ Error processing {symbol}: {str(e)}")
                
                elif total > 0 and symbol == 'USDT':
                    # Transfer USDT directly
                    amount_to_transfer = free  # Only transfer free amount
                    if amount_to_transfer > 0.01:  # Minimum transfer amount
                        try:
                            transfer_result = client.futures_transfer(asset='USDT', amount=amount_to_transfer, type=1)  # 1 = from spot to futures
                            transfer_log.append(f"✅ Transferred {amount_to_transfer:.2f} USDT from Spot to Futures")
                            total_transferred += amount_to_transfer
                        except Exception as e:
                            transfer_log.append(f"❌ Failed to transfer USDT from Spot: {str(e)}")
        except Exception as e:
            transfer_log.append(f"❌ Error processing Spot wallet: {str(e)}")
        
        # 2. Transfer from CROSS MARGIN account
        try:
            margin_account = client.get_margin_account()
            margin_balances = margin_account.get('userAssets', [])
            
            for asset in margin_balances:
                free = float(asset.get('free', 0))
                symbol = asset['asset']
                
                if free > 0:
                    if symbol == 'USDT':
                        if free > 0.01:
                            try:
                                # Transfer from margin to spot first, then to futures
                                transfer_to_spot = client.transfer(asset=symbol, amount=free, type='MARGIN_MAIN')
                                transfer_to_futures = client.futures_transfer(asset=symbol, amount=free, type=1)
                                transfer_log.append(f"✅ Transferred {free:.2f} {symbol} from Margin to Futures")
                                total_transferred += free
                            except Exception as e:
                                transfer_log.append(f"❌ Failed to transfer {symbol} from Margin: {str(e)}")
                    else:
                        # For other assets, transfer to spot and sell
                        if free > 0.0001:
                            try:
                                transfer_to_spot = client.transfer(asset=symbol, amount=free, type='MARGIN_MAIN')
                                transfer_log.append(f"✅ Transferred {free:.8f} {symbol} from Margin to Spot")
                                # Will be handled in spot processing above
                            except Exception as e:
                                transfer_log.append(f"❌ Failed to transfer {symbol} from Margin to Spot: {str(e)}")
        except Exception as e:
            transfer_log.append(f"❌ Error processing Margin account: {str(e)}")
        
        # 3. Transfer from ISOLATED MARGIN accounts
        try:
            isolated_accounts = client.get_isolated_margin_account()
            
            for symbol_info in isolated_accounts.get('assets', []):
                base_asset = symbol_info['baseAsset']
                quote_asset = symbol_info['quoteAsset']
                
                base_free = float(symbol_info['baseAsset']['free'])
                quote_free = float(symbol_info['quoteAsset']['free'])
                
                # Transfer base asset
                if base_free > 0.0001:
                    try:
                        transfer_to_spot = client.transfer(asset=base_asset, amount=base_free, type='ISOLATEDMARGIN_MAIN')
                        transfer_log.append(f"✅ Transferred {base_free:.8f} {base_asset} from Isolated Margin to Spot")
                    except Exception as e:
                        transfer_log.append(f"❌ Failed to transfer {base_asset} from Isolated Margin: {str(e)}")
                
                # Transfer quote asset (usually USDT)
                if quote_free > 0.01:
                    try:
                        transfer_to_spot = client.transfer(asset=quote_asset, amount=quote_free, type='ISOLATEDMARGIN_MAIN')
                        if quote_asset == 'USDT':
                            transfer_to_futures = client.futures_transfer(asset=quote_asset, amount=quote_free, type=1)
                            transfer_log.append(f"✅ Transferred {quote_free:.2f} {quote_asset} from Isolated Margin to Futures")
                            total_transferred += quote_free
                        else:
                            transfer_log.append(f"✅ Transferred {quote_free:.8f} {quote_asset} from Isolated Margin to Spot")
                    except Exception as e:
                        transfer_log.append(f"❌ Failed to transfer {quote_asset} from Isolated Margin: {str(e)}")
        except Exception as e:
            transfer_log.append(f"❌ Error processing Isolated Margin: {str(e)}")
        
        # 4. Transfer from FUNDING wallet (if any)
        try:
            funding_account = client.futures_account()
            funding_balances = funding_account.get('assets', [])
            
            for asset in funding_balances:
                wallet_balance = float(asset.get('walletBalance', 0))
                symbol = asset['asset']
                
                if wallet_balance > 0 and symbol == 'USDT':
                    # Transfer from futures funding to futures wallet
                    if wallet_balance > 0.01:
                        try:
                            # Funding wallet is already in futures, but let's ensure it's in the main futures wallet
                            transfer_log.append(f"ℹ️ {wallet_balance:.2f} {symbol} already in Futures Funding wallet")
                        except Exception as e:
                            transfer_log.append(f"❌ Error with Funding wallet {symbol}: {str(e)}")
        except Exception as e:
            transfer_log.append(f"❌ Error processing Funding wallet: {str(e)}")
        
        # Prepare response
        response = "💰 **FUND TRANSFER TO FUTURES WALLET COMPLETED**\n\n"
        response += f"**Total Transferred: ${total_transferred:.2f} USDT**\n\n"
        response += "**Transfer Log:**\n"
        
        for log_entry in transfer_log:
            response += f"{log_entry}\n"
        
        response += "\n⚠️ **Note:**\n"
        response += "• Only USDT and BUSD can be transferred directly to Futures\n"
        response += "• Other assets were sold to USDT in Spot before transfer\n"
        response += "• Check /balance to verify transfers\n"
        response += "• Earn wallet and other non-API accounts cannot be transferred via bot"
        
        await update.message.reply_text(response)
        
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Transfer error: {error_msg}")
        await update.message.reply_text(f"❌ Error during transfer: {error_msg}\n\n🔧 **Troubleshooting:**\n• Check if your API key has 'Enable Spot & Margin Trading' permission\n• Verify sufficient funds\n• Some assets may not be transferable\n• Try smaller amounts first")

async def price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Get current price of a symbol"""
    client = get_binance_client()
    if client is None:
        await update.message.reply_text("❌ Binance API credentials not set. Use /setapikey and /setapisecret to configure.")
        return
    
    if not context.args:
        await update.message.reply_text("Usage: /price BTCUSDT")
        return
    
    symbol = context.args[0].upper()
    try:
        ticker = client.get_symbol_info(symbol)
        if not ticker:
            await update.message.reply_text(f"Symbol {symbol} not found")
            return
        
        price_data = client.get_symbol_ticker(symbol=symbol)
        price = float(price_data['price'])
        
        # Get QQE signal for the symbol
        klines = client.get_historical_klines(symbol, Client.KLINE_INTERVAL_1HOUR, "100 hours ago UTC")
        closes = [float(k[4]) for k in klines]
        rsi, smooth_rsi, upper, lower = calculate_qqe(closes)
        
        if rsi is not None:
            if smooth_rsi < lower:
                signal = "🟢 BUY"
            elif smooth_rsi > upper:
                signal = "🔴 SELL"
            else:
                signal = "🟡 NEUTRAL"
            
            await update.message.reply_text(f"💹 {symbol}: ${price:,.2f}\n📊 QQE Signal: {signal}")
        else:
            await update.message.reply_text(f"💹 {symbol}: ${price:,.2f}")
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")

async def trade(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Execute a trade"""
    await update.message.reply_text(
        "📊 Trade Execution\n\n"
        "Usage: /trade <symbol> <side> <quantity> <price>\n"
        "Example: /trade BTCUSDT BUY 0.01 45000\n\n"
        "Warning: This will execute a real trade!"
    )

async def qqe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Get QQE signal for a symbol"""
    client = get_binance_client()
    if client is None:
        await update.message.reply_text("❌ Binance API credentials not set. Use /setapikey and /setapisecret to configure.")
        return
    
    if not context.args:
        await update.message.reply_text("Usage: /qqe BTCUSDT")
        return
    
    symbol = context.args[0].upper()
    try:
        # Get historical data (last 100 candles of 1 hour)
        klines = client.get_historical_klines(symbol, Client.KLINE_INTERVAL_1HOUR, "100 hours ago UTC")
        closes = [float(k[4]) for k in klines]  # Closing prices
        
        rsi, smooth_rsi, upper, lower = calculate_qqe(closes)
        
        if rsi is None:
            await update.message.reply_text(f"❌ Could not calculate QQE for {symbol}")
            return
        
        # Determine signal
        if smooth_rsi < lower:
            signal = "🟢 BUY"
            signal_type = "BUY"
        elif smooth_rsi > upper:
            signal = "🔴 SELL"
            signal_type = "SELL"
        else:
            signal = "🟡 NEUTRAL"
            signal_type = "NEUTRAL"
        
        message = (
            f"📊 QQE Signal: {symbol}\n\n"
            f"RSI: {rsi:.2f}\n"
            f"Smoothed RSI: {smooth_rsi:.2f}\n"
            f"Upper Band: {upper:.2f}\n"
            f"Lower Band: {lower:.2f}\n"
            f"Signal: {signal}\n"
            f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
        
        # Check for open trades in this symbol and close if signal reverses
        closed_trades = []
        current_price = closes[-1]
        
        for order_id, trade in list(ACTIVE_TRADES.items()):
            if trade["symbol"] == symbol:
                # If signal is opposite to trade direction, close it
                if (trade["side"] == "BUY" and signal_type == "SELL") or \
                   (trade["side"] == "SELL" and signal_type == "BUY"):
                    
                    # Calculate profit/loss at current price
                    if trade["side"] == "BUY":
                        profit_loss = (current_price - trade["entry_price"]) * trade["quantity"]
                    else:
                        profit_loss = (trade["entry_price"] - current_price) * trade["quantity"]
                    
                    profit_loss_percent = (profit_loss / (trade["entry_price"] * trade["quantity"])) * 100
                    
                    # Close the trade
                    trade["exit_price"] = current_price
                    trade["exit_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    trade["status"] = "CLOSED"
                    trade["profit_loss"] = profit_loss
                    trade["profit_loss_percent"] = profit_loss_percent
                    
                    # Update statistics
                    if profit_loss > 0:
                        TRADE_STATS["winning_trades"] += 1
                        TRADE_STATS["total_profit"] += profit_loss
                    else:
                        TRADE_STATS["losing_trades"] += 1
                        TRADE_STATS["total_loss"] += abs(profit_loss)
                    
                    del ACTIVE_TRADES[order_id]
                    closed_trades.append((order_id, trade["side"], profit_loss, profit_loss_percent))
                    logger.info(f"Auto-closed trade {order_id} due to signal reversal: {profit_loss:.2f}")
        
        # Add closed trades info to message
        if closed_trades:
            message += "\n\n🚨 TRADES CLOSED (Signal Reversal):\n"
            for order_id, side, pl, pl_pct in closed_trades:
                emoji = "✅" if pl > 0 else "❌"
                message += f"{emoji} Order #{order_id} ({side}): {pl:.2f} ({pl_pct:.2f}%)\n"
        
        # Auto-trade if enabled
        if TRADING_CONFIG["enabled"]:
            if smooth_rsi < lower:
                execute_trade(symbol, "BUY", closes[-1])
            elif smooth_rsi > upper:
                execute_trade(symbol, "SELL", closes[-1])
        
        await update.message.reply_text(message)
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")

# --- New Fibonacci command using QQE as base indicator ---
async def fibonacci(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show Fibonacci retracement levels for a symbol, with QQE signal"""
    client = get_binance_client()
    if client is None:
        await update.message.reply_text("❌ Binance API credentials not set. Use /setapikey and /setapisecret to configure.")
        return
    
    if not context.args:
        await update.message.reply_text("Usage: /fibonacci BTCUSDT")
        return
    symbol = context.args[0].upper()
    try:
        klines = client.get_historical_klines(symbol, Client.KLINE_INTERVAL_1HOUR, "100 hours ago UTC")
        closes = [float(k[4]) for k in klines]
        fib, high, low = None, None, None
        if closes:
            result = calculate_fibonacci_levels(closes)
            if result:
                fib, high, low = result
        rsi, smooth_rsi, upper, lower = calculate_qqe(closes)
        if fib is None or rsi is None:
            await update.message.reply_text(f"❌ Could not calculate Fibonacci or QQE for {symbol}")
            return
        # Determine QQE signal
        if smooth_rsi < lower:
            signal = "🟢 BUY"
        elif smooth_rsi > upper:
            signal = "🔴 SELL"
        else:
            signal = "🟡 NEUTRAL"
        msg = f"📈 Fibonacci Retracement for {symbol}\n"
        msg += f"High: {high:.2f}\nLow: {low:.2f}\n\n"
        for lvl, val in fib.items():
            msg += f"{lvl}: {val:.2f}\n"
        msg += f"\nQQE Signal: {signal}"
        await update.message.reply_text(msg)
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")

async def trade_all(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Trade all pairs with BUY signals (0.6 USDT each)"""
    client = get_binance_client()
    if client is None:
        await update.message.reply_text("❌ Binance API credentials not set. Use /setapikey and /setapisecret to configure.")
        return
    
    if not TRADING_CONFIG["enabled"]:
        await update.message.reply_text("❌ Auto-trading is disabled. Use /enable first.")
        return
    
    await update.message.reply_text("🔄 Scanning and trading all pairs with BUY signals (0.6 USDT each)...")
    
    trades_executed = 0
    
    for symbol in trading_pairs:
        try:
            # Get historical data
            klines = client.get_historical_klines(
                symbol, Client.KLINE_INTERVAL_1HOUR, "100 hours ago UTC"
            )
            closes = [float(k[4]) for k in klines]
            
            rsi, smooth_rsi, upper, lower = calculate_qqe(closes)
            
            if rsi is None:
                continue
            
            current_price = closes[-1]
            
            # Check for BUY signal
            if smooth_rsi < lower:
                # Execute trade
                execute_trade(symbol, "BUY", current_price)
                trades_executed += 1
                logger.info(f"Auto-traded BUY on {symbol} at {current_price}")
                
                # Check if max positions reached
                if len(ACTIVE_TRADES) >= TRADING_CONFIG["max_positions"]:
                    break
        except Exception as e:
            logger.error(f"Error trading {symbol}: {e}")
            continue
    
    await update.message.reply_text(f"✅ Trading complete! Executed {trades_executed} trades.")

async def set_api_key(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Set Binance API key"""
    if not context.args:
        await update.message.reply_text("Usage: /setapikey YOUR_API_KEY")
        return
    
    global BINANCE_API_KEY, binance_client
    BINANCE_API_KEY = context.args[0]
    binance_client = None  # Reset client to force re-initialization
    save_config()  # Save to config file
    await update.message.reply_text("✅ API Key set successfully!")

async def set_api_secret(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Set Binance API secret"""
    if not context.args:
        await update.message.reply_text("Usage: /setapisecret YOUR_API_SECRET")
        return
    
    global BINANCE_API_SECRET, binance_client
    BINANCE_API_SECRET = context.args[0]
    binance_client = None  # Reset client to force re-initialization
    save_config()  # Save to config file
    await update.message.reply_text("✅ API Secret set successfully!")

async def show_api_key(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show current Binance API key"""
    if BINANCE_API_KEY:
        await update.message.reply_text(f"🔑 Current API Key: `{BINANCE_API_KEY}`")
    else:
        await update.message.reply_text("❌ No API key set. Use /setapikey to set it.")

async def show_api_secret(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show current Binance API secret"""
    if BINANCE_API_SECRET:
        await update.message.reply_text(f"🔐 Current API Secret: `{BINANCE_API_SECRET}`")
    else:
        await update.message.reply_text("❌ No API secret set. Use /setapisecret to set it.")

async def check_api(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Check if API credentials are set and working"""
    if not BINANCE_API_KEY or not BINANCE_API_SECRET:
        await update.message.reply_text("❌ API credentials not set.\n\nUse:\n/setapikey YOUR_API_KEY\n/setapisecret YOUR_API_SECRET")
        return
    
    client = get_binance_client()
    if client is None:
        await update.message.reply_text("❌ Failed to create Binance client. Check your API credentials.")
        return
    
    try:
        # Test API connection by getting account info
        account = client.get_account()
        await update.message.reply_text("✅ API credentials are working! Account access confirmed.")
        
        # Test public API for price fetching
        public_client = get_public_client()
        if public_client:
            try:
                ticker = public_client.get_symbol_ticker(symbol="BTCUSDT")
                await update.message.reply_text("✅ Public API working! Price fetching confirmed.")
            except Exception as e:
                await update.message.reply_text(f"⚠️ Public API issue: {str(e)}")
        else:
            await update.message.reply_text("⚠️ Could not create public client for price fetching.")
            
    except Exception as e:
        error_msg = str(e)
        if "API-key" in error_msg or "signature" in error_msg:
            await update.message.reply_text("❌ Invalid API credentials. Please check your API key and secret.")
        elif "permission" in error_msg:
            await update.message.reply_text("❌ API permissions insufficient. Enable 'Read Info' and 'Enable Trading' in Binance API settings.")
        else:
            await update.message.reply_text(f"❌ API connection failed: {error_msg}")

async def alert(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send trade alert"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    await update.message.reply_text(
        f"🚨 Trade Alert!\n"
        f"Symbol: BTCUSDT\n"
        f"Signal: LONG\n"
        f"Leverage: 15x\n"
        f"Timestamp: {timestamp}"
    )

def execute_trade(symbol, side, entry_price):
    """Execute a trade with stop loss and take profit (Spot or Futures)"""
    client = get_binance_client()
    if client is None:
        logger.error("Binance client not available for trading")
        return
    
    try:
        # Calculate quantity based on 0.6 USDT value
        quantity = 0.6 / entry_price  # 0.6 USDT worth
        
        # Check if quantity is valid (minimum order size, etc.)
        try:
            symbol_info = client.get_symbol_info(symbol)
            min_qty = float(symbol_info['filters'][2]['minQty'])  # LOT_SIZE filter
            if quantity < min_qty:
                logger.warning(f"Quantity {quantity} too small for {symbol}, minimum {min_qty}")
                return  # Skip this trade
        except:
            pass  # Continue anyway
        
        # Check maximum positions limit
        if len(ACTIVE_TRADES) >= TRADING_CONFIG["max_positions"]:
            logger.warning(f"Maximum positions ({TRADING_CONFIG['max_positions']}) reached. Cannot open new trade.")
            return
        
        mode = TRADING_CONFIG["mode"]
        
        # Calculate stop loss and take profit (disabled if 0)
        if TRADING_CONFIG["stop_loss_percent"] > 0:
            if side == "BUY":
                stop_loss = entry_price * (1 - TRADING_CONFIG["stop_loss_percent"] / 100)
                take_profit = entry_price * (1 + TRADING_CONFIG["take_profit_percent"] / 100)
            else:
                stop_loss = entry_price * (1 + TRADING_CONFIG["stop_loss_percent"] / 100)
                take_profit = entry_price * (1 - TRADING_CONFIG["take_profit_percent"] / 100)
        else:
            stop_loss = None
            take_profit = None
        
        # Place order based on mode
        if mode == "futures":
            # USDT-M Futures order
            order = client.futures_create_order(
                symbol=symbol,
                side=side,
                positionSide="LONG" if side == "BUY" else "SHORT",
                type="MARKET",
                quantity=quantity
            )
        else:
            # Spot order
            order = client.order_market(
                symbol=symbol,
                side=side,
                quantity=quantity
            )
        
        order_id = order['orderId']
        
        # Store trade info with detailed tracking
        trade_info = {
            "order_id": order_id,
            "symbol": symbol,
            "side": side,
            "quantity": quantity,
            "entry_price": entry_price,
            "stop_loss": stop_loss,
            "take_profit": take_profit,
            "entry_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "status": "OPEN",
            "exit_price": None,
            "exit_time": None,
            "profit_loss": 0.0,
            "profit_loss_percent": 0.0,
            "mode": mode
        }
        
        ACTIVE_TRADES[order_id] = trade_info
        TRADE_HISTORY.append(trade_info)
        
        # Update stats
        TRADE_STATS["total_trades"] += 1
        
        logger.info(f"Trade executed ({mode.upper()}): {symbol} {side} {quantity} at {entry_price} (0.6 USDT worth)")
    except Exception as e:
        error_msg = f"❌ Trade Error: {str(e)}"
        logger.error(error_msg)

async def enable_trading(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Enable auto-trading"""
    TRADING_CONFIG["enabled"] = True
    await update.message.reply_text("✅ Auto-trading ENABLED\n\nQQE signals will now trigger automatic trades!")

async def disable_trading(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Disable auto-trading"""
    TRADING_CONFIG["enabled"] = False
    await update.message.reply_text("⛔ Auto-trading DISABLED")

async def trading_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Get trading status"""
    status = "✅ ENABLED" if TRADING_CONFIG["enabled"] else "⛔ DISABLED"
    mode = TRADING_CONFIG["mode"].upper()
    pos_mode = TRADING_CONFIG["position_mode"].upper() if TRADING_CONFIG["mode"] == "futures" else "N/A"
    
    await update.message.reply_text(
        f"📊 Auto-Trading Status: {status}\n\n"
        f"🔄 Mode: {mode}\n"
        f"📍 Position Mode: {pos_mode}\n"
        f"💰 Trade Amount: 0.6 USDT per trade\n"
        f"⚡ Leverage: {TRADING_CONFIG['leverage']}x\n"
        f"📊 Stop Loss: {TRADING_CONFIG['stop_loss_percent']}%\n"
        f"🎯 Take Profit: Disabled (closes on signal reversal)\n"
        f"📈 Active Trades: {len(ACTIVE_TRADES)} / {TRADING_CONFIG['max_positions']} max"
    )

async def set_trade_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Set trade amount"""
    if not context.args:
        await update.message.reply_text("Usage: /setamount 0.001")
        return
    
    try:
        amount = float(context.args[0])
        TRADING_CONFIG["trade_amount"] = amount
        await update.message.reply_text(f"✅ Trade amount set to {amount}")
    except ValueError:
        await update.message.reply_text("❌ Invalid amount")

async def set_leverage(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Set trading leverage"""
    if not context.args:
        await update.message.reply_text("Usage: /leverage 15\n\nAllowed: 1-125x")
        return
    
    try:
        leverage = int(context.args[0])
        if leverage < 1 or leverage > 125:
            await update.message.reply_text("❌ Leverage must be between 1 and 125")
            return
        
        TRADING_CONFIG["leverage"] = leverage
        await update.message.reply_text(
            f"✅ Leverage set to {leverage}x\n\n"
            f"⚠️ WARNING: High leverage = High risk!\n"
            f"Your position size will be multiplied by {leverage}"
        )
    except ValueError:
        await update.message.reply_text("❌ Invalid leverage. Use numbers only (1-125)")

async def set_wallet_trading(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Set trading amount as 1/12 of wallet"""
    client = get_binance_client()
    if client is None:
        await update.message.reply_text("❌ Binance API credentials not set. Use /setapikey and /setapisecret to configure.")
        return
    
    try:
        account = client.get_account()
        balances = account['balances']
        
        # Filter non-zero balances
        active_balances = [b for b in balances if float(b['free']) > 0 or float(b['locked']) > 0]
        
        total_balance_usdt = 0.0
        
        for balance_item in active_balances:
            symbol = balance_item['asset']
            free = float(balance_item['free'])
            locked = float(balance_item['locked'])
            total = free + locked
            
            if total > 0:
                try:
                    if symbol == "USDT":
                        price = 1.0
                    elif symbol == "BUSD":
                        price = 1.0
                    else:
                        try:
                            ticker = client.get_symbol_ticker(symbol=f"{symbol}USDT")
                            price = float(ticker['price'])
                        except:
                            try:
                                ticker = client.get_symbol_ticker(symbol=f"{symbol}BUSD")
                                price = float(ticker['price'])
                            except:
                                continue
                    
                    balance_usdt = total * price
                    total_balance_usdt += balance_usdt
                except:
                    continue
        
        # Calculate 1/12 of wallet
        trade_amount = total_balance_usdt / 12
        TRADING_CONFIG["trade_amount"] = trade_amount
        
        await update.message.reply_text(
            f"💰 Wallet Total: ${total_balance_usdt:,.2f} USDT\n\n"
            f"✅ Trade Amount Set (1/12): ${trade_amount:,.2f} USDT\n\n"
            f"This means each trade will risk 1/12 of your portfolio!"
        )
        
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}\n\nMake sure your API keys are working.")

async def set_stop_loss(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Set stop loss percentage"""
    if not context.args:
        await update.message.reply_text("Usage: /setstoploss 2")
        return
    
    try:
        sl = float(context.args[0])
        TRADING_CONFIG["stop_loss_percent"] = sl
        await update.message.reply_text(f"✅ Stop loss set to {sl}%")
    except ValueError:
        await update.message.reply_text("❌ Invalid percentage")

async def set_take_profit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Set take profit percentage"""
    if not context.args:
        await update.message.reply_text("Usage: /settakeprofit 5")
        return
    
    try:
        tp = float(context.args[0])
        TRADING_CONFIG["take_profit_percent"] = tp
        await update.message.reply_text(f"✅ Take profit set to {tp}%")
    except ValueError:
        await update.message.reply_text("❌ Invalid percentage")

async def set_max_positions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Set maximum number of active positions"""
    if not context.args:
        await update.message.reply_text("Usage: /setmaxpos 6")
        return
    
    try:
        max_pos = int(context.args[0])
        if max_pos < 1 or max_pos > 20:
            await update.message.reply_text("❌ Max positions must be between 1 and 20")
            return
        
        TRADING_CONFIG["max_positions"] = max_pos
        await update.message.reply_text(f"✅ Maximum positions set to {max_pos}")
    except ValueError:
        await update.message.reply_text("❌ Invalid number")

async def performance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show trading performance and statistics"""
    if TRADE_STATS["total_trades"] == 0:
        await update.message.reply_text("📊 No trades executed yet. Start trading to see statistics!")
        return
    
    # Calculate win rate
    if TRADE_STATS["total_trades"] > 0:
        win_rate = (TRADE_STATS["winning_trades"] / TRADE_STATS["total_trades"]) * 100
    else:
        win_rate = 0
    
    message = (
        f"📈 Bot Performance Statistics\n\n"
        f"Total Trades: {TRADE_STATS['total_trades']}\n"
        f"✅ Winning Trades: {TRADE_STATS['winning_trades']}\n"
        f"❌ Losing Trades: {TRADE_STATS['losing_trades']}\n"
        f"Win Rate: {win_rate:.2f}%\n\n"
        f"💰 Profit/Loss:\n"
        f"Total Profit: ${TRADE_STATS['total_profit']:.2f}\n"
        f"Total Loss: ${TRADE_STATS['total_loss']:.2f}\n"
        f"Net P/L: ${TRADE_STATS['total_profit'] - TRADE_STATS['total_loss']:.2f}"
    )
    
    await update.message.reply_text(message)

async def history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show recent trade history"""
    if not TRADE_HISTORY:
        await update.message.reply_text("📋 No trading history available yet.")
        return
    
    # Get last 5 trades
    recent_trades = TRADE_HISTORY[-5:]
    
    message = "📋 Recent Trade History:\n\n"
    for i, trade in enumerate(recent_trades, 1):
        status_emoji = "📍" if trade["status"] == "OPEN" else "✅" if trade["profit_loss"] > 0 else "❌"
        message += (
            f"{i}. {status_emoji} {trade['symbol']} {trade['side']}\n"
            f"   Entry: ${trade['entry_price']:.2f} @ {trade['entry_time']}\n"
            f"   Status: {trade['status']}\n"
        )
        if trade["status"] == "CLOSED":
            message += f"   P/L: ${trade['profit_loss']:.2f} ({trade['profit_loss_percent']:.2f}%)\n"
        message += "\n"
    
    await update.message.reply_text(message)

async def close_trade(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Manually close a trade"""
    if not context.args:
        await update.message.reply_text("Usage: /closetrade <order_id> <exit_price>")
        return
    
    if len(context.args) < 2:
        await update.message.reply_text("Usage: /closetrade <order_id> <exit_price>")
        return
    
    try:
        order_id = int(context.args[0])
        exit_price = float(context.args[1])
        
        if order_id not in ACTIVE_TRADES:
            await update.message.reply_text(f"❌ Trade {order_id} not found in active trades")
            return
        
        trade = ACTIVE_TRADES[order_id]
        
        # Calculate profit/loss
        if trade["side"] == "BUY":
            profit_loss = (exit_price - trade["entry_price"]) * trade["quantity"]
        else:
            profit_loss = (trade["entry_price"] - exit_price) * trade["quantity"]
        
        profit_loss_percent = (profit_loss / (trade["entry_price"] * trade["quantity"])) * 100
        
        # Update trade info
        trade["exit_price"] = exit_price
        trade["exit_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        trade["status"] = "CLOSED"
        trade["profit_loss"] = profit_loss
        trade["profit_loss_percent"] = profit_loss_percent
        
        # Update statistics
        if profit_loss > 0:
            TRADE_STATS["winning_trades"] += 1
            TRADE_STATS["total_profit"] += profit_loss
        else:
            TRADE_STATS["losing_trades"] += 1
            TRADE_STATS["total_loss"] += abs(profit_loss)
        
        # Remove from active trades
        del ACTIVE_TRADES[order_id]
        
        emoji = "✅" if profit_loss > 0 else "❌"
        message = (
            f"{emoji} Trade Closed!\n\n"
            f"Order ID: {order_id}\n"
            f"Exit Price: ${exit_price:.2f}\n"
            f"Profit/Loss: ${profit_loss:.2f}\n"
            f"P/L %: {profit_loss_percent:.2f}%\n"
            f"Closed @ {trade['exit_time']}"
        )
        
        await update.message.reply_text(message)
        logger.info(f"Trade {order_id} closed with P/L: ${profit_loss:.2f}")
        
    except ValueError:
        await update.message.reply_text("❌ Invalid parameters. Use: /closetrade <order_id> <exit_price>")

async def set_mode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Switch between spot and futures trading"""
    if not context.args:
        current_mode = TRADING_CONFIG["mode"]
        await update.message.reply_text(
            f"Current mode: {current_mode.upper()}\n\n"
            f"Usage: /mode <spot|futures>\n\n"
            f"Example: /mode futures"
        )
        return
    
    mode = context.args[0].lower()
    
    if mode not in ["spot", "futures"]:
        await update.message.reply_text("❌ Invalid mode. Use: /mode <spot|futures>")
        return
    
    TRADING_CONFIG["mode"] = mode
    
    message = (
        f"✅ Trading mode set to: {mode.upper()}\n\n"
        f"📊 Mode Details:\n"
    )
    
    if mode == "futures":
        message += (
            f"🔹 USDT-M Futures\n"
            f"🔹 Leverage: {TRADING_CONFIG['leverage']}x\n"
            f"🔹 Can trade with leverage\n"
            f"🔹 Position mode: {TRADING_CONFIG['position_mode'].upper()}\n\n"
            f"⚠️ Futures trading carries higher risk!"
        )
    else:
        message += (
            f"🔹 Spot Trading\n"
            f"🔹 No leverage\n"
            f"🔹 Buy and hold assets\n"
            f"🔹 Safest trading method"
        )
    
    await update.message.reply_text(message)
    logger.info(f"Trading mode changed to: {mode}")

async def set_position_mode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Set futures position mode (one_way or hedge)"""
    if TRADING_CONFIG["mode"] != "futures":
        await update.message.reply_text("❌ Position mode only applies to Futures trading. Switch to futures first with /mode futures")
        return
    
    if not context.args:
        current_pos_mode = TRADING_CONFIG["position_mode"]
        await update.message.reply_text(
            f"Current position mode: {current_pos_mode.upper()}\n\n"
            f"Usage: /posmode <one_way|hedge>\n\n"
            f"ONE_WAY: Can only have LONG or SHORT, not both\n"
            f"HEDGE: Can have both LONG and SHORT simultaneously"
        )
        return
    
    # Always set to one_way mode
    TRADING_CONFIG["position_mode"] = "one_way"
    message = (
        f"✅ Position mode set to: ONE_WAY (enforced)\n\n"
        f"Mode: ONE_WAY\n"
        "You can only have LONG or SHORT positions, not both"
    )
    await update.message.reply_text(message)
    logger.info(f"Position mode changed to: one_way (enforced)")

def check_signal_reversals():
    """Check for QQE signal reversals on active trades and close if needed"""
    client = get_binance_client()
    if client is None:
        return  # Skip if no client
    
    while True:
        try:
            time.sleep(60)  # Check every minute
            
            if not ACTIVE_TRADES:
                continue
                
            for order_id, trade in list(ACTIVE_TRADES.items()):
                symbol = trade["symbol"]
                side = trade["side"]
                
                try:
                    # Get recent data for this symbol
                    klines = client.get_historical_klines(
                        symbol, Client.KLINE_INTERVAL_1HOUR, "2 hours ago UTC"
                    )
                    closes = [float(k[4]) for k in klines]
                    
                    rsi, smooth_rsi, upper, lower = calculate_qqe(closes)
                    
                    if rsi is None:
                        continue
                    
                    current_price = closes[-1]
                    
                    # Determine current signal
                    if smooth_rsi < lower:
                        current_signal = "BUY"
                    elif smooth_rsi > upper:
                        current_signal = "SELL"
                    else:
                        current_signal = "NEUTRAL"
                    
                    # Check for reversal
                    if (side == "BUY" and current_signal == "SELL") or \
                       (side == "SELL" and current_signal == "BUY"):
                        
                        # Calculate profit/loss at current price
                        if side == "BUY":
                            profit_loss = (current_price - trade["entry_price"]) * trade["quantity"]
                        else:
                            profit_loss = (trade["entry_price"] - current_price) * trade["quantity"]
                        
                        profit_loss_percent = (profit_loss / (trade["entry_price"] * trade["quantity"])) * 100
                        
                        # Close the trade
                        trade["exit_price"] = current_price
                        trade["exit_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        trade["status"] = "CLOSED"
                        trade["profit_loss"] = profit_loss
                        trade["profit_loss_percent"] = profit_loss_percent
                        
                        # Update statistics
                        if profit_loss > 0:
                            TRADE_STATS["winning_trades"] += 1
                            TRADE_STATS["total_profit"] += profit_loss
                        else:
                            TRADE_STATS["losing_trades"] += 1
                            TRADE_STATS["total_loss"] += abs(profit_loss)
                        
                        del ACTIVE_TRADES[order_id]
                        logger.info(f"Auto-closed trade {order_id} ({symbol} {side}) due to signal reversal: P/L ${profit_loss:.2f}")
                        
                except Exception as e:
                    logger.error(f"Error checking reversal for {symbol}: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Signal reversal check error: {e}")
            time.sleep(60)

def sync_data_with_webapp():
    if not WEB_APP_ENABLED:
        return  # Skip if web app is disabled
    
    client = get_binance_client()
    if client is None:
        return  # Skip if no client
    
    webapp_url = os.getenv('WEBAPP_SYNC_URL', 'http://localhost:5000/api/sync')
    
    while True:
        try:
            time.sleep(2)  # Update every 2 seconds
            
            # Get current balance
            balance_data = {}
            try:
                account = client.get_account()
                for balance_item in account['balances']:
                    symbol = balance_item['asset']
                    total = float(balance_item['free']) + float(balance_item['locked'])
                    if total > 0:
                        balance_data[symbol] = total
            except:
                pass
            
            # Prepare data
            webapp_data = {
                "balance": balance_data,
                "active_trades": ACTIVE_TRADES,
                "trading_config": TRADING_CONFIG,
                "trade_stats": TRADE_STATS
            }
            
            # Send to webapp
            try:
                requests.post(
                    webapp_url,
                    json=webapp_data,
                    timeout=2
                )
            except:
                pass  # Web app not running, continue anyway
                
        except Exception as e:
            logger.error(f"Sync error: {str(e)}")

def main():
    """Start the bot"""
    print("🚀 Starting Red Dragon Trading Bot...")
    
    # Load configuration
    load_config()
    print(f"📋 API Key loaded: {'Yes' if BINANCE_API_KEY else 'No'}")
    print(f"🔑 API Secret loaded: {'Yes' if BINANCE_API_SECRET else 'No'}")
    
    # Start a small Flask API to accept commands from the dashboard directly
    def start_command_server():
        app_cmd = Flask('bot_cmd_api')

        @app_cmd.route('/api/command', methods=['POST'])
        def command():
            try:
                data = request.get_json() or {}
                cmd = (data.get('command') or '').lower()
                args = data.get('args') or []

                # Map commands to internal actions
                if cmd in ('setmode', 'set_mode', 'mode') and args:
                    mode = args[0].lower()
                    if mode in ('spot', 'futures'):
                        TRADING_CONFIG['mode'] = mode
                        return jsonify({'ok': True, 'mode': mode})
                    return jsonify({'ok': False, 'error': 'invalid mode'}), 400

                if cmd in ('setleverage', 'set_leverage', 'leverage') and args:
                    try:
                        lev = int(args[0])
                        if lev < 1 or lev > 125:
                            return jsonify({'ok': False, 'error': 'leverage out of range'}), 400
                        TRADING_CONFIG['leverage'] = lev
                        return jsonify({'ok': True, 'leverage': lev})
                    except Exception as e:
                        return jsonify({'ok': False, 'error': 'invalid leverage'}), 400

                if cmd in ('setamount', 'set_amount', 'amount') and args:
                    try:
                        amt = float(args[0])
                        TRADING_CONFIG['trade_amount'] = amt
                        return jsonify({'ok': True, 'trade_amount': amt})
                    except Exception:
                        return jsonify({'ok': False, 'error': 'invalid amount'}), 400

                if cmd in ('toggle_auto_trading', 'toggle', 'enable', 'disable'):
                    # support args like ['enable'] or ['disable']
                    if args:
                        action = str(args[0]).lower()
                        if action in ('enable', 'true', '1'):
                            TRADING_CONFIG['enabled'] = True
                            return jsonify({'ok': True, 'enabled': True})
                        if action in ('disable', 'false', '0'):
                            TRADING_CONFIG['enabled'] = False
                            return jsonify({'ok': True, 'enabled': False})
                    # toggle if no args
                    TRADING_CONFIG['enabled'] = not TRADING_CONFIG['enabled']
                    return jsonify({'ok': True, 'enabled': TRADING_CONFIG['enabled']})

                return jsonify({'ok': False, 'error': 'unknown command'}), 400

            except Exception as e:
                return jsonify({'ok': False, 'error': str(e)}), 500

        # Run on localhost:5001
        try:
            app_cmd.run(host='127.0.0.1', port=5001, debug=False, use_reloader=False)
        except Exception:
            pass

    cmd_thread = threading.Thread(target=start_command_server, daemon=True)
    cmd_thread.start()
    print("🌐 Command server thread started")
    logger.info('Local command HTTP server started on http://127.0.0.1:5001')
    # Use new application API
    app = Application.builder().token(BOT_TOKEN).build()
    print("🤖 Telegram application created")
    
    # Add command handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("balance", balance))
    app.add_handler(CommandHandler("transfer_to_futures", transfer_to_futures))
    app.add_handler(CommandHandler("price", price))
    app.add_handler(CommandHandler("trade", trade))
    app.add_handler(CommandHandler("alert", alert))
    app.add_handler(CommandHandler("qqe", qqe))
    app.add_handler(CommandHandler("market", analyze_market))
    app.add_handler(CommandHandler("tradeall", trade_all))
    app.add_handler(CommandHandler("fibonacci", fibonacci))
    app.add_handler(CommandHandler("setapikey", set_api_key))
    app.add_handler(CommandHandler("setapisecret", set_api_secret))
    app.add_handler(CommandHandler("showapikey", show_api_key))
    app.add_handler(CommandHandler("showapisecret", show_api_secret))
    app.add_handler(CommandHandler("checkapi", check_api))
    app.add_handler(CommandHandler("enable", enable_trading))
    app.add_handler(CommandHandler("disable", disable_trading))
    app.add_handler(CommandHandler("status", trading_status))
    app.add_handler(CommandHandler("setamount", set_trade_amount))
    app.add_handler(CommandHandler("setwallet", set_wallet_trading))
    app.add_handler(CommandHandler("leverage", set_leverage))
    app.add_handler(CommandHandler("setstoploss", set_stop_loss))
    app.add_handler(CommandHandler("settakeprofit", set_take_profit))
    app.add_handler(CommandHandler("setmaxpos", set_max_positions))
    app.add_handler(CommandHandler("performance", performance))
    app.add_handler(CommandHandler("history", history))
    app.add_handler(CommandHandler("closetrade", close_trade))
    app.add_handler(CommandHandler("mode", set_mode))
    app.add_handler(CommandHandler("posmode", set_position_mode))
    
    # Start background thread for signal reversal checking
    reversal_thread = threading.Thread(target=check_signal_reversals, daemon=True)
    reversal_thread.start()
    logger.info("Signal reversal check thread started")
    
    # Start background thread for web app sync (if enabled)
    if WEB_APP_ENABLED:
        sync_thread = threading.Thread(target=sync_data_with_webapp, daemon=True)
        sync_thread.start()
        print("📱 Web app sync enabled")
    else:
        print("📱 Web app sync disabled (set WEB_APP_ENABLED=true to enable)")
    
    # Start polling
    print("✅ Bot running...")
    print("📱 Web app sync enabled (localhost:5000)")
    print("🎯 Ready to receive commands!")
    logger.info("Bot started successfully")
    
    app.run_polling()

if __name__ == "__main__":
    main()
