@echo off
setlocal

set "PORT=%~1"
if "%PORT%"=="" set "PORT=8000"

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\serve-local.ps1" -Port %PORT% -Root "%~dp0"
