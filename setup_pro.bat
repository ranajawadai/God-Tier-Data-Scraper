@echo off
color 0A
title ULTIMATE DATA SCRAPER PRO - SETUP

echo ---------------------------------------------------
echo      ULTIMATE DATA SCRAPER PRO - ZERO COST EDITION
echo ---------------------------------------------------
echo.
echo [*] Installing Dependencies (FastAPI, Selenium, etc)...
pip install -r requirements_pro.txt

echo.
echo [!] SETUP COMPLETE!
echo.
echo [*] Starting Server...
echo [*] Access the Dashboard at: http://localhost:8000
echo.

python backend_pro.py
pause
