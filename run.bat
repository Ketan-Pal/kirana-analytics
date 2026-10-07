@echo off
title Kirana 7-Eleven Retail Intelligence System
cd /d "%~dp0"
echo ========================================================
echo   Kirana 7-Eleven Retail Intelligence System
echo   Tanpin Kanri Analytics & Recommendation Engine
echo ========================================================
echo.
echo Initializing database and starting web server...
echo Access URL: http://localhost:8000
echo Access from mobile on local Wi-Fi: http://<your-pc-ip>:8000
echo.
python main.py
pause
