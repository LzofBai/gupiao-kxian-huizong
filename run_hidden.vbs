Set WshShell = CreateObject("WScript.Shell") 
WshShell.Run "python web_server.py", 0, False 
Set WshShell = Nothing 
