# Telegram Mini App Setup Guide

## ✅ What's Running Now
- **Bot Server**: Python telegram bot (port 5000 internally)
- **Web App**: Flask dashboard (localhost:5000)

## 🎯 How to Use the Mini App

### Option 1: Local Testing
1. Open any browser and go to: `http://localhost:5000`
2. You'll see the trading dashboard with real-time data
3. Send `/start` command in Telegram to see the "📱 Open Dashboard" button

### Option 2: Telegram Mini App (Recommended)
To make this work as a real Telegram Mini App, you need to:

#### Step 1: Get a Server/URL
- Option A: Use ngrok for local tunneling: `ngrok http 5000`
- Option B: Use a VPS (Heroku, AWS, DigitalOcean, etc.)
- Option C: Use cloudflare tunnels

#### Step 2: Update Bot Configuration
In `pythonbot.py`, change:
```python
WEB_APP_URL = "https://yourserver.com/bot"
```

#### Step 3: Configure via BotFather
1. Open BotFather in Telegram
2. Select your bot
3. Send `/setmenubutton`
4. Follow the prompts to add a web app button

#### Step 4: Test
- Send `/start` in your bot
- Click the "📱 Open Dashboard" button
- The mini app will open in Telegram!

## 📊 Dashboard Features

### Real-Time Monitoring
- ✅ Active trading status (ON/OFF)
- ✅ Current trading mode (SPOT/FUTURES)
- ✅ Leverage setting
- ✅ Number of active trades

### Account Information
- 💰 Account balance for all assets
- 📈 Performance statistics (win rate, profit/loss)
- 📊 Active trades with P/L

### Trading Controls
- Enable/Disable trading
- Switch between SPOT and FUTURES
- Set leverage (1-125x)
- Configure trade amount
- Set stop loss and take profit

### Auto-Refresh
- Dashboard updates every 3 seconds
- Real-time sync with bot data
- No manual refresh needed

## 🚀 Quick Start Commands

```bash
# Start both bot and web app
python c:\Users\ICS\Desktop\webapp.py
python c:\Users\ICS\Desktop\pythonbot.py
```

Or use the batch file:
```bash
start_bot.bat
```

## 🔧 Troubleshooting

### Web App Not Loading
- Check if Flask is running: `python webapp.py`
- Check port 5000: `netstat -ano | findstr :5000`
- Restart Flask: `Get-Process python | Stop-Process`

### Bot Can't Connect to Web App
- Make sure Flask is running first
- Check `http://localhost:5000` in browser
- Verify no firewall blocking port 5000

### Mini App Button Not Showing
- Make sure bot is running and web app is accessible
- Update `WEB_APP_URL` with your actual server URL
- Configure via BotFather `/setmenubutton`

## 📱 For Telegram Mini App on Phone

1. Get a public URL for your web app:
   - ngrok: `ngrok http 5000` → Copy the HTTPS URL
   - VPS: Use your server IP/domain

2. Update in `pythonbot.py`:
   ```python
   WEB_APP_URL = "https://your-public-url.com"
   ```

3. Restart bot and test on phone

4. Configure button via BotFather to make it permanent

## 🔐 Security Notes
- This setup exposes your bot to the internet
- Consider adding authentication if needed
- Never share your API keys
- Use HTTPS for production

## Files Created
- `webapp.py` - Flask web server
- `templates/dashboard.html` - Mini app interface
- `start_bot.bat` - Startup script
- `pythonbot.py` - Updated with mini app support
