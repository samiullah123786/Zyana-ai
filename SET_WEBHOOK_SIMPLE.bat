@echo off
echo.
echo ========================================
echo   SETTING TELEGRAM WEBHOOK
echo ========================================
echo.

set BACKEND_URL=https://zyana-backend.onrender.com
set BOT_TOKEN=7984613392:AAF4_EajP5H8M4HGX2vmPUa_fhENLjaqktU
set WEBHOOK_URL=%BACKEND_URL%/webhook/telegram

echo Backend: %BACKEND_URL%
echo Webhook: %WEBHOOK_URL%
echo.

REM Using curl (if available)
curl -X POST "https://api.telegram.org/bot%BOT_TOKEN%/setWebhook?url=%WEBHOOK_URL%"

echo.
echo ========================================
echo   VERIFYING WEBHOOK
echo ========================================
echo.

curl "https://api.telegram.org/bot%BOT_TOKEN%/getWebhookInfo"

echo.
pause

