@echo off
REM Double-click this file on Windows to install syncsub.
REM It runs the PowerShell installer with the execution policy bypassed.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0platform\windows\install.ps1"
echo.
pause
