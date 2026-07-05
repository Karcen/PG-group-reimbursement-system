@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo.
echo   ██████╗ ███████╗██╗███╗   ███╗██████╗
echo   实验室报销管理系统  v1.0
echo.

set BACKEND_PORT=8000
set FRONTEND_PORT=5173
if not exist logs mkdir logs

:: ─── 停止残留进程 ─────────────────────────────────────────
echo [!] 正在清理旧进程...
for /f "tokens=5" %%a in ('netstat -ano 2^>nul ^| findstr ":%BACKEND_PORT% "') do (
    taskkill /f /pid %%a >nul 2>&1
)
for /f "tokens=5" %%a in ('netstat -ano 2^>nul ^| findstr ":%FRONTEND_PORT% "') do (
    taskkill /f /pid %%a >nul 2>&1
)

:: ─── 确认 conda 环境 ──────────────────────────────────────
where conda >nul 2>&1
if %errorlevel% equ 0 (
    conda env list 2>nul | findstr "reimb" >nul
    if %errorlevel% equ 0 (
        set PYTHON_CMD=conda run -n reimb python
        set UVICORN_CMD=conda run -n reimb uvicorn
        echo [√] 使用 conda 环境: reimb
        goto :start_backend
    )
)

:: 回退到 .venv
if exist "backend\.venv\Scripts\uvicorn.exe" (
    set PYTHON_CMD=backend\.venv\Scripts\python
    set UVICORN_CMD=backend\.venv\Scripts\uvicorn
    echo [√] 使用 backend\.venv 虚拟环境
    goto :start_backend
)

echo [!] 未找到专用环境，使用系统 Python
set PYTHON_CMD=python
set UVICORN_CMD=python -m uvicorn

:start_backend
:: ─── 启动后端（最小化窗口） ───────────────────────────────
echo.
echo [>>] 启动后端服务...
cd backend
start "ReimbBackend" /min cmd /c "%UVICORN_CMD% app.main:app --host 0.0.0.0 --port %BACKEND_PORT% > ..\logs\backend.log 2>&1"
cd ..

:: 等待后端就绪（最多20秒）
echo     等待后端就绪...
set /a wait=0
:wait_backend
timeout /t 1 /nobreak >nul
curl -s "http://localhost:%BACKEND_PORT%/health" >nul 2>&1
if %errorlevel% equ 0 goto :backend_ok
set /a wait+=1
if %wait% lss 20 goto :wait_backend
echo [✗] 后端启动超时！请查看 logs\backend.log
exit /b 1

:backend_ok
echo [√] 后端就绪  http://localhost:%BACKEND_PORT%

:: ─── 启动前端（最小化窗口） ───────────────────────────────
echo.
echo [>>] 启动前端服务...
cd frontend
start "ReimbFrontend" /min cmd /c "npm run dev > ..\logs\frontend.log 2>&1"
cd ..

:: 等待前端就绪
echo     等待前端就绪...
timeout /t 6 /nobreak >nul

:: ─── 完成 ──────────────────────────────────────────────────
echo.
echo ═══════════════════════════════════════════
echo   [√] 系统已成功启动！
echo.
echo   前端地址:    http://localhost:%FRONTEND_PORT%
echo   API 文档:    http://localhost:%BACKEND_PORT%/docs
echo.
echo   管理员:    admin / Admin@123456
echo   示例教师:  teacher1 / Teacher@123456
echo   示例学生:  student1 / Student@123456
echo.
echo   日志目录:    logs\
echo   停止系统:    运行 stop.bat
echo ═══════════════════════════════════════════
echo.

:: 自动打开浏览器
start http://localhost:%FRONTEND_PORT%

pause
