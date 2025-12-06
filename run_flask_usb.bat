@echo off
echo ==============================
echo Starting Flask USB Mobile Access
echo ==============================
echo.

REM --- Set platform-tools path ---
set PLATFORM_TOOLS=C:\platform-tools
cd /d %PLATFORM_TOOLS%

REM --- Restart ADB server ---
adb kill-server
adb start-server

REM --- Check connected devices ---
echo Checking devices...
adb devices
echo.

REM --- Forward Flask port 5000 to mobile ---
echo Forwarding port 5000...
adb forward tcp:5000 tcp:5000
adb forward --list
echo.

REM --- Move to Flask project folder ---
set PROJECT_DIR=C:\Users\HP\OneDrive\Desktop\jm4
cd /d %PROJECT_DIR%

REM --- Run Flask server ---
echo Running Flask project...
python app.py
pause

