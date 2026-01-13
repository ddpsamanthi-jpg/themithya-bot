# 🤖 Themithya - Binance Trading Bot with Telegram Mini App

Welcome to **Themithya** - Your complete Binance auto-trading bot solution with Telegram integration!

## 📦 What's Included

This folder contains everything you need to run your trading bot:

### 🔧 Core Files
- **pythonbot.py** - Main Telegram bot with trading logic
- **webapp.py** - Flask web server for dashboard
- **launcher.py** - Easy one-command launcher
- **start_bot.bat** - Windows batch starter

### 🎨 Web Interface
- **templates/dashboard.html** - Mini app dashboard UI
- Dark theme optimized for Telegram
- Real-time trading controls

### 📚 Documentation
- **SETUP_COMPLETE.md** - Full setup instructions
- **README_MINI_APP.md** - Quick start guide
- **MINI_APP_SETUP.md** - Detailed configuration
- **CHANGES.txt** - What was added

## 🚀 Quick Start

### Option 1: Easy Launcher (Recommended)
```bash
python launcher.py
```

### Option 2: Manual Start
```bash
# Terminal 1: Start web app
python webapp.py

# Terminal 2: Start bot
python pythonbot.py
```

### Option 3: Windows Batch
```bash
start_bot.bat
```

### Option 4: Deploy to Free Cloud Server ⭐
```bash
# Setup deployment
python deploy.py

# Then follow DEPLOYMENT.md instructions
```

## ☁️ Cloud Deployment

Deploy your bot to a free cloud server for 24/7 operation:

### Supported Platforms
- **Railway** (Recommended) - 512MB RAM, 1GB storage
- **Render** - 750 hours/month free
- **Heroku** - 550 hours/month free
- **Fly.io** - 3 free VMs with 256MB RAM each

### Quick Deploy
1. Run `python deploy.py` to set up environment variables
2. Follow the detailed guide in `DEPLOYMENT.md`
3. Your bot will run 24/7 on the cloud!

## 📱 Access Dashboard

### In Telegram (Best Way)
1. Open your Telegram bot
2. Send: `/start`
3. Click "📱 Open Dashboard" button
4. Mini app opens in Telegram!

### In Browser
- Open: `http://localhost:5000`
- See dashboard with real-time data

## ✨ Features

### 📊 Real-Time Monitoring
- ✅ Account balance (all assets in USDT)
- ✅ Active trades with entry price & P/L
- ✅ Performance statistics (win rate, profit/loss)
- ✅ Trading status (ON/OFF)

### ⚙️ Trading Controls
- ✅ Enable/Disable auto-trading
- ✅ Switch between SPOT and FUTURES
- ✅ Set leverage (1-125x)
- ✅ Adjust trade amount
- ✅ Configure stop loss & take profit

### 📈 Market Analysis
- ✅ Scan 65+ trading pairs
- ✅ QQE signal detection
- ✅ Signal strength ranking
- ✅ Market trends analysis

### 🎯 Advanced Features
- ✅ USDT-M Futures support
- ✅ Leverage configuration
- ✅ Wallet-based position sizing
- ✅ Automatic trade closure on signal reversal
- ✅ Performance tracking & statistics

## 🔧 Configuration

### API Keys
Edit `pythonbot.py` and update:
```python
BOT_TOKEN = "your_telegram_bot_token"
BINANCE_API_KEY = "your_binance_api_key"
BINANCE_API_SECRET = "your_binance_api_secret"
```

### Web App URL
For phone/public access, update:
```python
WEB_APP_URL = "https://your-public-url.com"
```

### Trading Settings
All settings can be configured via Telegram commands:
- `/leverage 15` - Set 15x leverage
- `/setamount 0.5` - Set trade amount
- `/setwallet` - Use 1/12 of wallet
- `/setstoploss 2` - Set 2% stop loss
- `/settakeprofit 5` - Set 5% take profit

## 📋 Telegram Commands

### Market Data
- `/start` - Show commands & dashboard button
- `/balance` - Check account balance
- `/price BTCUSDT` - Get current price
- `/qqe BTCUSDT` - QQE signal for one pair
- `/market` - Analyze all markets

### Trading Control
- `/enable` - Enable auto-trading
- `/disable` - Disable auto-trading
- `/status` - Show current settings
- `/trade BTCUSDT BUY` - Place manual trade
- `/closetrade ID PRICE` - Close trade

### Configuration
- `/mode spot` - Switch to spot trading
- `/mode futures` - Switch to futures trading
- `/leverage 15` - Set leverage
- `/setamount 0.5` - Set trade amount
- `/setwallet` - Set 1/12 of wallet
- `/setstoploss 2` - Set stop loss %
- `/settakeprofit 5` - Set take profit %

### Performance
- `/performance` - View stats & win rate
- `/history` - View recent trades

## 🌐 For Phone Users

To access the mini app on your phone:

### Step 1: Get a Public URL
Choose one:
- **ngrok** (free): `ngrok http 5000`
- **VPS** (Heroku, AWS, DigitalOcean)
- **Cloudflare Tunnel** (free)

### Step 2: Update Bot
Edit `pythonbot.py`:
```python
WEB_APP_URL = "https://your-public-url.com"
```

### Step 3: Restart Bot
```bash
python launcher.py
```

### Step 4: Configure Button
Message BotFather in Telegram:
- `/setmenubutton`
- Select your bot
- Add web app with your URL

### Step 5: Test
- Open Telegram on phone
- Send `/start` to bot
- Click dashboard button
- Mini app opens!

## 📊 Dashboard Overview

The web app shows:

```
┌─────────────────────────────────┐
│    Trading Bot Dashboard        │
├─────────────────────────────────┤
│ Trading: ✓ ON      Mode: SPOT   │
│ Leverage: 15x      Active: 0    │
├─────────────────────────────────┤
│ [Enable] [Disable] [Refresh]   │
├─────────────────────────────────┤
│ Balance:     (USDT values)      │
│ Performance: (stats)            │
│ Trades:      (active)           │
│ Settings:    (controls)         │
└─────────────────────────────────┘
```

## 🔐 Security Notes

### Current Setup (Local Use)
- ✅ Localhost only
- ✅ No authentication needed
- ✅ Safe for local network
- ✅ API keys in code (fine for dev)

### For Production
- ⚠️ Use HTTPS only
- ⚠️ Add authentication
- ⚠️ Use environment variables for keys
- ⚠️ Deploy to secure server
- ⚠️ Add rate limiting

## 🆘 Troubleshooting

### Web App Not Loading
```bash
# Start web app directly
python webapp.py

# Check if it's running
curl http://localhost:5000
```

### Bot Not Starting
```bash
# Check Python version
python --version

# Reinstall dependencies
pip install -r requirements.txt

# Start manually
python pythonbot.py
```

### No Data in Dashboard
1. Make sure both services are running
2. Check Binance API keys are correct
3. Wait 3 seconds for first update
4. Open browser console (F12) for errors

### Button Not Showing
1. Restart bot: `python launcher.py`
2. Send `/start` again
3. Configure via BotFather if needed

## 📁 File Structure

```
themithya/
├── pythonbot.py              # Main bot
├── webapp.py                 # Web server
├── launcher.py              # Easy launcher
├── start_bot.bat            # Windows batch
├── templates/
│   └── dashboard.html       # Mini app UI
├── SETUP_COMPLETE.md        # Setup guide
├── README_MINI_APP.md       # Quick start
├── MINI_APP_SETUP.md        # Detailed setup
└── CHANGES.txt              # What was added
```

## 🎯 Common Tasks

### Enable Futures Trading
```
1. Send /mode futures
2. Send /leverage 15
3. Send /enable
```

### Set Trade Amount
```
1. Send /setamount 0.5
   (0.5 in trade pair currency)

Or use 1/12 of wallet:
1. Send /setwallet
```

### Monitor Performance
```
1. Send /performance (stats)
2. Send /history (trades)
3. Send /status (current config)
```

### Close a Trade
```
/closetrade ORDER_ID PRICE
```

## 💡 Tips

1. **Use /start often** - Always refer to the command list
2. **Monitor /status** - Check settings before trading
3. **Test with small amounts** - Start with 0.001 BTC
4. **Review /history** - Check past trades
5. **Use /market** - See what's trending
6. **Check /performance** - Track your win rate

## 🚀 Next Steps

1. ✅ Extract all files to themithya folder ✓
2. ⬜ Update API keys in pythonbot.py
3. ⬜ Test locally: `python launcher.py`
4. ⬜ Send /start in Telegram
5. ⬜ Monitor dashboard
6. ⬜ Configure trading settings
7. ⬜ Enable auto-trading

## 📞 Support

### If Something Fails
1. Check console for error messages
2. Verify API credentials
3. Ensure port 5000 is free
4. Reinstall dependencies: `pip install -r requirements.txt`
5. Restart both services

### Common Issues
- **"Cannot connect to Binance"** → Check API keys
- **"Port 5000 in use"** → Kill other processes
- **"No dashboard button"** → Restart bot
- **"No data showing"** → Wait 3 seconds & refresh

## 📈 Trading Strategy Tips

### QQE Signals
- **BUY Signal**: RSI above upper band
- **SELL Signal**: RSI below lower band
- **Strength**: Based on deviation from midline

### Risk Management
- Set leverage cautiously (15x shown)
- Use stop loss (2% shown)
- Set take profit (5% shown)
- Position size = 1/12 wallet

### Monitoring
- Check dashboard every hour
- Review trades daily
- Track win rate weekly
- Adjust settings as needed

## 🎉 You're Ready!

Everything is set up. Start with:
```bash
python launcher.py
```

Then access your mini app dashboard!

**Happy Trading! 📈🚀**

---

**Version**: 1.0 with Telegram Mini App  
**Last Updated**: January 9, 2026  
**Status**: Production Ready ✅
