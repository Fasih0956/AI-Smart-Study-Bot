@echo off
cd /d "%~dp0"
echo.
echo  ================================================
echo   ATTENDANCE BOT - Setup using Python 3.11
echo  ================================================
echo.
echo  Verifying Python 3.11...
py -3.11 --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python 3.11 not found.
    echo  Run:  winget install Python.Python.3.11
    pause
    exit /b 1
)
py -3.11 --version
echo  Python 3.11 confirmed.
echo.
echo [1/7] Removing old venv...
if exist venv rmdir /s /q venv
echo  Done.
echo.
echo [2/7] Creating fresh venv with Python 3.11...
py -3.11 -m venv venv
call venv\Scripts\activate.bat
echo  Venv created.
echo.
echo [3/7] Upgrading pip + setuptools...
python -m pip install --upgrade pip setuptools wheel
echo.
echo [4/7] Installing core packages...
pip install playwright==1.44.0
pip install schedule==1.2.1 python-dateutil==2.9.0 pytz==2024.1
pip install requests==2.32.2 websockets==12.0 aiohttp==3.9.5
pip install flask==3.0.3 flask-socketio==5.3.6 simple-websocket
pip install openpyxl==3.1.2
pip install colorlog==6.8.2 rich==13.7.1 psutil==5.9.8
pip install Pillow==10.3.0
pip install python-dotenv==1.0.1
echo.
echo [5/7] Installing audio + speech packages...
pip install numpy==1.26.4
pip install SpeechRecognition==3.10.4
pip install sounddevice==0.4.6 soundfile==0.12.1
pip install pyaudio
if errorlevel 1 (
    echo     pyaudio failed - trying pipwin...
    pip install pipwin
    pipwin install pyaudio
)
echo.
echo [6/7] Installing Playwright browser...
python -m playwright install chromium
echo.
echo [7/7] Installing PyTorch CUDA 12.1...
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
if errorlevel 1 (
    echo     Trying CUDA 11.8...
    pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
    if errorlevel 1 (
        echo     Installing CPU-only PyTorch...
        pip install torch torchvision torchaudio
    )
)
echo.
echo [+] Installing Whisper...
pip install openai-whisper
if errorlevel 1 (
    pip install git+https://github.com/openai/whisper.git
)
echo.
echo [+] Creating folders...
if not exist logs mkdir logs
if not exist screenshots mkdir screenshots
if not exist profiles\chrome_profile mkdir profiles\chrome_profile
echo.
echo  ================================================
echo   ALL DONE! Python 3.11 venv ready.
echo.
echo   Now run these in order:
echo     1. verify_install.bat
echo     2. login_google.bat
echo     3. telegram_setup.bat
echo     4. run.bat --test
echo  ================================================
echo.
pause
