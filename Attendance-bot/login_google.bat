@echo off
cd /d "%~dp0"

if not exist venv\Scripts\activate.bat (
    echo [ERROR] venv not found. Run setup.bat first.
    pause
    exit /b 1
)

call venv\Scripts\activate.bat

python -c "import playwright" >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Playwright not installed. Run setup.bat first.
    pause
    exit /b 1
)

echo.
echo  Opening Chrome for Google login...
echo  Log in, then close Chrome when done.
echo.

python login_google.py

pause
