# Set Telegram Webhook for Zyana Backend

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "  SETTING TELEGRAM WEBHOOK " -ForegroundColor Green
Write-Host "========================================`n" -ForegroundColor Cyan

$BACKEND_URL = "https://zyana-backend.onrender.com"
$BOT_TOKEN = "7984613392:AAF4_EajP5H8M4HGX2vmPUa_fhENLjaqktU"
$WEBHOOK_URL = "$BACKEND_URL/webhook/telegram"

Write-Host "Backend URL: $BACKEND_URL" -ForegroundColor Yellow
Write-Host "Webhook Endpoint: $WEBHOOK_URL`n" -ForegroundColor Yellow

# Method 1: Using Invoke-WebRequest (PowerShell native)
try {
    Write-Host "Setting webhook..." -ForegroundColor White
    
    $body = @{
        url = $WEBHOOK_URL
    }
    
    $response = Invoke-WebRequest `
        -Uri "https://api.telegram.org/bot$BOT_TOKEN/setWebhook" `
        -Method Post `
        -Body ($body | ConvertTo-Json) `
        -ContentType "application/json"
    
    Write-Host "✅ Webhook Set Successfully!" -ForegroundColor Green
    Write-Host "`nResponse:" -ForegroundColor Cyan
    $response.Content | ConvertFrom-Json | ConvertTo-Json -Depth 3
    
} catch {
    Write-Host "❌ Error: $_" -ForegroundColor Red
    Write-Host "`nTrying alternative method..." -ForegroundColor Yellow
    
    # Method 2: Using simple GET request
    try {
        $url = "https://api.telegram.org/bot$BOT_TOKEN/setWebhook?url=$WEBHOOK_URL"
        $result = Invoke-WebRequest -Uri $url -Method Get
        Write-Host "✅ Webhook Set (Alternative Method)!" -ForegroundColor Green
        Write-Host "`nResponse:" -ForegroundColor Cyan
        $result.Content
    } catch {
        Write-Host "❌ Still failed: $_" -ForegroundColor Red
        Write-Host "`n💡 Try using curl from Git Bash or WSL" -ForegroundColor Yellow
    }
}

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "  VERIFY WEBHOOK " -ForegroundColor Yellow
Write-Host "========================================`n" -ForegroundColor Cyan

try {
    Write-Host "Checking webhook info..." -ForegroundColor White
    $info = Invoke-WebRequest -Uri "https://api.telegram.org/bot$BOT_TOKEN/getWebhookInfo" -Method Get
    Write-Host "`nWebhook Info:" -ForegroundColor Cyan
    $info.Content | ConvertFrom-Json | ConvertTo-Json -Depth 3
} catch {
    Write-Host "❌ Could not get webhook info: $_" -ForegroundColor Red
}

Write-Host "`n========================================`n" -ForegroundColor Cyan

