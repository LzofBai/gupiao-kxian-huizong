@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo ============================================================
echo  基金估值与K线监控系统
echo ============================================================
echo.

rem 检查并创建必要目录
if not exist "data" mkdir data
if not exist "logs" mkdir logs
if not exist "config" mkdir config

rem 启动浏览器
start http://localhost:5000

rem 延迟1秒后启动服务器
timeout /t 1 /nobreak >nul

echo 正在启动服务器...
echo 访问地址: http://localhost:5000
echo 关闭此窗口可停止服务
echo.

"基金K线监控系统.exe"
pause
