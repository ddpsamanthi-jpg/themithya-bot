@echo off
REM Start Red Dragon - Binance Trading Bot with Web App

echo Starting Red Dragon - Binance Trading Bot with Web App Dashboard...
echo.

REM Kill any existing Python processes
taskkill /F /IM python.exe >nul 2>&1

REM Wait a moment
timeout /t 2 /nobreak

REM Start web app in a new window
echo Starting Web App on localhost:5000...
start "Red Dragon - Trading Bot Web App" python "%~dp0webapp.py"

REM Wait for web app to start
timeout /t 3 /nobreak

REM Start main bot
echo Starting Telegram Bot...
python "%~dp0pythonbot.py"

pause
