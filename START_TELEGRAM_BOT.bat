@echo off
echo ========================================
echo   Zyana Telegram Bot (Polling Mode)
echo ========================================
echo.
echo This will start the Telegram bot in polling mode
echo No webhook or ngrok needed!
echo.
echo Make sure backend is running first!
echo.
pause
echo.
echo Starting bot...
cd backend
python run_telegram_polling.py
pause

