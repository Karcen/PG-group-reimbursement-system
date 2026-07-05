@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo 正在停止服务...
set BACKEND_PORT=8000
set FRONTEND_PORT=5173
for /f "tokens=5" %%a in ('netstat -ano 2^>nul ^| findstr ":%BACKEND_PORT% "') do (
    taskkill /f /pid %%a >nul 2>&1
)
for /f "tokens=5" %%a in ('netstat -ano 2^>nul ^| findstr ":%FRONTEND_PORT% "') do (
    taskkill /f /pid %%a >nul 2>&1
)
echo [√] 服务已停止。
pause
