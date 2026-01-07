@echo off
REM Run as Administrator

echo ========================================
echo   Auto-Login Configuration
echo ========================================
echo.

REM Get username and password
set /p USERNAME="Enter your Windows username (e.g., kiosk): "
set /p PASSWORD="Enter your Windows password: "

REM Enable auto-login
reg add "HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Winlogon" /v AutoAdminLogon /t REG_SZ /d "1" /f
reg add "HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Winlogon" /v DefaultUserName /t REG_SZ /d "%USERNAME%" /f
reg add "HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Winlogon" /v DefaultPassword /t REG_SZ /d "%PASSWORD%" /f

echo.
echo ========================================
echo   Auto-Login Enabled!
echo ========================================
echo Username: %USERNAME%
echo.
echo Restart your computer to test.
echo.
pause
