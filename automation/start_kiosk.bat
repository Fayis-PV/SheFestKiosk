@echo off
REM Kiosk Auto-Launcher

cd /d C:\Kiosk

REM Cleanup old processes
taskkill /F /IM python.exe >nul 2>&1
taskkill /F /IM chrome.exe >nul 2>&1
timeout /t 2 /nobreak >nul

REM Start watchdog (which starts backend)
start /min "" .venv\Scripts\python.exe automation\watchdog.py

REM Wait for backend to be ready
timeout /t 5 /nobreak >nul

:WAIT
curl -s http://localhost:5000/api/health >nul 2>&1
if errorlevel 1 (
    timeout /t 2 /nobreak >nul
    goto WAIT
)

REM Launch browser in kiosk mode
start "" "C:\Program Files\Google\Chrome\Application\chrome.exe" --kiosk http://localhost:5000 --start-fullscreen --autoplay-policy=no-user-gesture-required --disable-infobars --no-first-run

exit
