@echo off
echo.
echo  Checking Python versions installed on this machine...
echo.

echo  System Python (py launcher):
py --list 2>nul || echo  (py launcher not found)

echo.
echo  Python 3.11 at default path:
if exist "C:\Users\FASIH\AppData\Local\Programs\Python\Python311\python.exe" (
    "C:\Users\FASIH\AppData\Local\Programs\Python\Python311\python.exe" --version
) else (
    echo  NOT FOUND
)

echo.
echo  Current venv Python:
if exist venv\Scripts\python.exe (
    venv\Scripts\python.exe --version
) else (
    echo  No venv found - run setup_py311.bat first
)

echo.
pause
