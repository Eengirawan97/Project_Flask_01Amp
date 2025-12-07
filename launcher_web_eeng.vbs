Set WshShell = CreateObject("WScript.Shell")

projectFolder = "D:\Project_integrasi_dan_login"
appName = "app.py"
flaskPort = "5006"

WshShell.CurrentDirectory = projectFolder

' Jalankan Flask di CMD
WshShell.Run "cmd /k python " & appName, 1, False

' Tunggu 10 detik biar Flask siap
WScript.Sleep 10000

' Jalankan Ngrok di CMD
WshShell.Run "cmd /k ngrok http " & flaskPort, 1, False
