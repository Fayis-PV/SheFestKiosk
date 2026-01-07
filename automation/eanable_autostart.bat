@echo off
REM Run this as Administrator

REM Create scheduled task
schtasks /create /tn "Kiosk" /tr "C:\Kiosk\automation\start_kiosk.bat" /sc onlogon /rl highest /f

REM Disable sleep/screensaver
powercfg /change monitor-timeout-ac 0
powercfg /change standby-timeout-ac 0
powercfg /change hibernate-timeout-ac 0
reg add "HKCU\Control Panel\Desktop" /v ScreenSaveActive /t REG_SZ /d 0 /f

REM Set high performance power plan
powercfg /setactive 8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c

echo Auto-start enabled!
echo Power settings configured!
echo Restart computer to test.
pause
