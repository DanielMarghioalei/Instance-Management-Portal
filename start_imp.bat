@echo off
title IMP Startup

cd /d "%~dp0"

echo ========================================
echo        Instance Management Portal
echo ========================================
echo.

start "Deployment Worker" cmd /k py app\deployment_engine.py

py -m uvicorn app.main:app --reload

pause