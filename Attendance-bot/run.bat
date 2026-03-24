@echo off
cd /d "%~dp0"

if not exist venv\Scripts\activate.bat (
    echo [ERROR] venv not found. Run setup.bat first.
    pause
    exit /b 1
)

call venv\Scripts\activate.bat

echo.
echo  ================================================
echo   ATTENDANCE BOT - Starting...
echo   Dashboard: http://localhost:5000
echo  ================================================
echo.

if "%1"=="--test" (
    echo  [TEST MODE] Joining first test class immediately...
    python bot.py --test
) else (
    python bot.py
)

pause
