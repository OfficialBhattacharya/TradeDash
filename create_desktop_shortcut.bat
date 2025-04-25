@echo off
echo Creating desktop shortcut for TradeDash...
powershell -ExecutionPolicy Bypass -File "%~dp0create_shortcut.ps1"
echo Done! You can now launch TradeDash from your desktop.
pause 