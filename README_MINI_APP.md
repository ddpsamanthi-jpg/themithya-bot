# 🐉 Red Dragon - Binance Trading Bot Mini App

Your **Red Dragon** trading bot now has a **Telegram Mini App** - a beautiful dashboard you can open directly in Telegram!

## 🎨 **New Features Added**

### 🌅 **Custom Background Image**
- Full-screen background using your provided image
- Dark overlay for better readability
- Professional trading atmosphere

### 📱 **Left Sidebar Menu**
- **Menu Button** (top) - Main navigation
- **Profile Icon** (middle) - User profile access
- **Dashboard Icon** (bottom) - Quick dashboard access
- Hover effects and smooth animations

## 🚀 Quick Start

### 1. Start the Bot
Run this command (from `c:\Users\ICS\Desktop`):
```bash
python webapp.py
python pythonbot.py
```

### 2. Open the Dashboard
- **Local (Browser)**: Go to `http://localhost:5000`
- **Telegram (Mini App)**: Send `/start` to your bot, click "📱 Open Dashboard"

## 📊 What You Can Do

✅ **Monitor in Real-Time**
- Trading status (ON/OFF)
- Mode (SPOT/FUTURES)
- Active trades count
- Balance in all assets

✅ **View Performance**
- Total trades
- Win rate
- Total profit/loss
- Active trades list with P/L

✅ **Control Settings**
- Enable/Disable trading
- Change mode (SPOT ↔ FUTURES)
- Set leverage
- Adjust trade amount

✅ **Auto-Refresh**
- Updates every 3 seconds
- Real-time sync with bot
- No manual refresh needed

## 📱 For Phone (Telegram Mini App)

To use this on your phone:

1. **Get a Public URL** (choose one):
   - [ngrok](https://ngrok.com/) - Free tunneling
   - VPS - Heroku, AWS, DigitalOcean
   - Cloudflare Tunnel

2. **Update URL** in `pythonbot.py`:
   ```python
   WEB_APP_URL = "https://your-public-url.com"
   ```

3. **Restart Bot**:
   - Stop current processes
   - Run `python webapp.py` and `python pythonbot.py` again

4. **Configure in Telegram** (BotFather):
   - Message BotFather: `/setmenubutton`
   - Select your bot
   - Add web app button with your URL

5. **Test on Phone**:
   - Send `/start` to bot
   - Click "📱 Open Dashboard"
   - Mini app opens in Telegram!

## 📁 Files

| File | Purpose |
|------|---------|
| `webapp.py` | Flask web server (dashboard backend) |
| `pythonbot.py` | Telegram bot (updated with mini app) |
| `templates/dashboard.html` | Mini app interface |
| `start_bot.bat` | Quick startup script |
| `MINI_APP_SETUP.md` | Detailed setup guide |

## 🔧 Commands

**Start Both Services (Recommended):**
```bash
# Windows batch file
start_bot.bat

# Cross-platform Python launcher
python launcher.py
```

**Start Separately:**
```bash
# Terminal 1: Web App
python webapp.py

# Terminal 2: Bot
python pythonbot.py
```

## ✨ Features

- 🎨 **Custom Background Image** - Professional trading interface
- 📱 **Left Sidebar Menu** - Easy navigation with icons
- 🌙 **Dark Theme** - Optimized for Telegram and trading
- ⚡ **Lightning-fast Updates** - 3-second refresh cycle
- 📱 **Mobile-Friendly** - Responsive design for all devices
- 🔄 **Real-time Sync** - Live data from your trading bot
- 🎯 **One-click Controls** - Instant trading management

## ⚠️ Important

1. **Keep both running**: Bot + Web App must run simultaneously
2. **Port 5000**: Make sure nothing else uses this port
3. **Internet**: For mini app on phone, needs public URL
4. **APIs**: Make sure your Binance API keys are valid

## 🎯 Next Steps

1. ✅ Bot is running
2. ✅ Web app is running
3. Open browser: `http://localhost:5000`
4. Try the dashboard!
5. Send `/start` in Telegram to see mini app button

**Happy Trading! 🚀**
