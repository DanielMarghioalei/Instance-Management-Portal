@echo off
title IMP - FastAPI Server

cd /d "%~dp0"

echo ========================================
echo        Instance Management Portal
echo ========================================
echo.

py -m uvicorn app.main:app --reload

pause