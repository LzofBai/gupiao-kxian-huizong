@echo off
chcp 65001 >nul
cd /d "%~dp0"

rem 检查并创建必要目录
if not exist "data" mkdir data
if not exist "logs" mkdir logs
if not exist "config" mkdir config

rem 启动浏览器
start http://localhost:5000

rem 延迟1秒后启动服务器（后台运行）
timeout /t 1 /nobreak >nul

rem 使用WMIC启动隐藏进程（最稳定的方式）
wmic process call create "\"%~dp0基金K线监控系统.exe\"" >nul 2>&1