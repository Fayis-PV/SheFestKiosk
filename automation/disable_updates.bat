@echo off
REM Run as Administrator before event

REM Pause updates for 7 days
reg add "HKLM\SOFTWARE\Policies\Microsoft\Windows\WindowsUpdate\AU" /v NoAutoUpdate /t REG_DWORD /d 1 /f

echo Windows Updates paused for 7 days
pause
