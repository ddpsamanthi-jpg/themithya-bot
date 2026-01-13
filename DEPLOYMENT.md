# 🚀 Red Dragon Trading Bot - Free Server Deployment

This guide will help you deploy the Red Dragon Binance trading bot to a free cloud server.

## 📋 Prerequisites

1. **GitHub Account** - Required for most free hosting platforms
2. **Telegram Bot Token** - Get from [@BotFather](https://t.me/botfather)
3. **Binance API Keys** - Get from your Binance account
4. **Git** - Installed on your system

## 🌐 Free Hosting Options

### Option 1: Railway (Recommended) ⭐

Railway offers a generous free tier with 512MB RAM and 1GB storage.

#### Steps:

1. **Create Railway Account**
   - Go to [railway.app](https://railway.app)
   - Sign up with GitHub

2. **Create New Project**
   - Click "New Project"
   - Choose "Deploy from GitHub repo"
   - Connect your GitHub account
   - Select this repository

3. **Set Environment Variables**
   - Go to your project dashboard
   - Click "Variables" tab
   - Add these variables:
     ```
     BOT_TOKEN=your_telegram_bot_token
     BINANCE_API_KEY=your_binance_api_key
     BINANCE_API_SECRET=your_binance_api_secret
     WEB_APP_ENABLED=false
     ```

4. **Deploy**
   - Railway will automatically detect the Procfile and deploy
   - Your bot will be running at a Railway URL

### Option 2: Render

Render offers free web services with 750 hours/month.

#### Steps:

1. **Create Render Account**
   - Go to [render.com](https://render.com)
   - Sign up with GitHub

2. **Create New Web Service**
   - Click "New" → "Web Service"
   - Connect your GitHub repo
   - Configure:
     - **Runtime**: Python 3
     - **Build Command**: `pip install -r requirements.txt`
     - **Start Command**: `python pythonbot.py`

3. **Set Environment Variables**
   ```
   BOT_TOKEN=your_telegram_bot_token
   BINANCE_API_KEY=your_binance_api_key
   BINANCE_API_SECRET=your_binance_api_secret
   WEB_APP_ENABLED=false
   ```

4. **Deploy**
   - Click "Create Web Service"
   - Wait for deployment to complete

### Option 3: Heroku

Heroku offers 550 free hours/month.

#### Steps:

1. **Install Heroku CLI**
   ```bash
   # Download from https://devcenter.heroku.com/articles/heroku-cli
   ```

2. **Login and Create App**
   ```bash
   heroku login
   heroku create your-bot-name
   ```

3. **Set Environment Variables**
   ```bash
   heroku config:set BOT_TOKEN=your_telegram_bot_token
   heroku config:set BINANCE_API_KEY=your_binance_api_key
   heroku config:set BINANCE_API_SECRET=your_binance_api_secret
   heroku config:set WEB_APP_ENABLED=false
   ```

4. **Deploy**
   ```bash
   git push heroku main
   ```

### Option 4: Fly.io

Fly.io offers 3 free VMs with 256MB RAM each.

#### Steps:

1. **Install Fly CLI**
   ```bash
   # Download from https://fly.io/docs/getting-started/installing-flyctl/
   ```

2. **Create App**
   ```bash
   fly launch
   # Follow the prompts
   ```

3. **Set Secrets**
   ```bash
   fly secrets set BOT_TOKEN=your_telegram_bot_token
   fly secrets set BINANCE_API_KEY=your_binance_api_key
   fly secrets set BINANCE_API_SECRET=your_binance_api_secret
   fly secrets set WEB_APP_ENABLED=false
   ```

4. **Deploy**
   ```bash
   fly deploy
   ```

## 🔧 Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `BOT_TOKEN` | ✅ | Your Telegram bot token from BotFather |
| `BINANCE_API_KEY` | ✅ | Your Binance API key |
| `BINANCE_API_SECRET` | ✅ | Your Binance API secret |
| `WEB_APP_ENABLED` | ❌ | Set to `true` to enable web dashboard (default: false) |
| `WEB_APP_URL` | ❌ | URL for web app (only needed if web app enabled) |

## 📱 Testing Your Deployment

1. **Check Bot Status**
   - Send `/start` to your bot on Telegram
   - It should respond with the welcome message

2. **Test Commands**
   - `/balance` - Check if API keys are working
   - `/status` - Check bot status

3. **Monitor Logs**
   - Railway: Click "Deployments" → "View Logs"
   - Render: Go to service dashboard → "Logs" tab
   - Heroku: `heroku logs --tail -a your-app-name`
   - Fly.io: `fly logs`

## ⚠️ Important Notes

- **Free tiers have limitations**: Most free plans sleep/stop after inactivity
- **API Rate Limits**: Binance has rate limits, so don't spam commands
- **Security**: Never share your API keys or bot token
- **Backup**: Keep your `config.json` backed up locally
- **Updates**: To update your bot, push changes to your Git repository

## 🆘 Troubleshooting

### Bot Not Responding
1. Check if the server is running (green status)
2. Check logs for errors
3. Verify environment variables are set correctly
4. Test API keys locally first

### API Errors
1. Make sure your Binance API keys have correct permissions
2. Check IP restrictions on your API keys
3. Verify API keys are not expired

### Deployment Errors
1. Check build logs for missing dependencies
2. Ensure Python version is compatible
3. Verify Procfile syntax

## 💡 Pro Tips

- **Monitor Usage**: Keep an eye on your free tier limits
- **Auto-Restart**: Most platforms auto-restart crashed apps
- **Logs**: Always check logs when something goes wrong
- **Backup**: Regularly backup your configuration

## 📞 Support

If you encounter issues:
1. Check the logs first
2. Verify all environment variables
3. Test locally before deploying
4. Check platform-specific documentation

Happy trading! 🚀📈