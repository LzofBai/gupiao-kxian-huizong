@echo off
chcp 65001 >nul
cd /d "%~dp0"

rem 删除旧的VBS文件（如果存在）
if exist "run_hidden.vbs" del /f "run_hidden.vbs"

rem 创建隐藏运行的VBS脚本
echo Set WshShell = CreateObject("WScript.Shell") > run_hidden.vbs
echo WshShell.Run "python web_server.py", 0, False >> run_hidden.vbs
echo Set WshShell = Nothing >> run_hidden.vbs

rem 启动浏览器
start http://localhost:5000

rem 延迟1秒后启动服务器（隐藏窗口）
timeout /t 1 /nobreak >nul
wscript "run_hidden.vbs"
