@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo ========================================
echo   基金估值与K线监控系统
echo ========================================
echo.
echo 正在启动Web服务器...
echo 启动后将自动打开浏览器 http://localhost:5000
echo.

rem 启动浏览器
start http://localhost:5000

rem 延迟1秒后启动服务器
timeout /t 1 /nobreak >nul
python web_server.py
pause
