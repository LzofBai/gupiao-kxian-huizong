Set WshShell = CreateObject("WScript.Shell") 
WshShell.CurrentDirectory = "G:\Ai\项目尝试\3、股票信息K线汇总\gupiao-kxian-huizong\可运行程序\" 
WshShell.Run """G:\Ai\项目尝试\3、股票信息K线汇总\gupiao-kxian-huizong\可运行程序\基金K线监控系统.exe""", 0, False 
Set WshShell = Nothing 
