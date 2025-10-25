@echo off
echo ========================================
echo  Zyana - Commit and Push Changes
echo ========================================
echo.

cd /d "%~dp0"

echo [1/3] Adding files...
git add backend/agents/calendar.py backend/agents/intent_router.py backend/routers/calendar.py backend/routers/webhook.py INTELLIGENT_ROUTER_IMPLEMENTATION.md

echo.
echo [2/3] Committing...
git commit -m "feat: Intelligent Intent Router + Google Calendar Fix" -m "GOOGLE CALENDAR FIX:" -m "- Added fallback credential loading (personal bot mode)" -m "- Fixed OAuth callback to support user_id" -m "- Dynamic credential loading per user" -m "" -m "INTELLIGENT INTENT ROUTER:" -m "- ChatGPT-5 powered intent analysis via Fal AI" -m "- Automatic routing to 10+ sub-agents" -m "- Casual conversation for non-actionable messages" -m "- Context-aware responses with user preferences" -m "" -m "FILES:" -m "- backend/agents/intent_router.py (NEW)" -m "- backend/agents/calendar.py (fixed)" -m "- backend/routers/calendar.py (fixed)" -m "- backend/routers/webhook.py (updated)"

echo.
echo [3/3] Pushing to GitHub...
git push origin dev

echo.
echo ========================================
echo  ✅ Done! Render will auto-deploy
echo ========================================
echo.
echo Next steps:
echo 1. Wait 2-3 minutes for Render deployment
echo 2. Test: "Book meeting tomorrow at 10am"
echo 3. Test: "Bro I'm tired today"
echo.
pause

