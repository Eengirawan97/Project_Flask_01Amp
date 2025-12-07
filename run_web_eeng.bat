@echo off
REM ==========================================
REM Simple test launcher: Flask + Ngrok
REM ==========================================

REM Paths
set PYTHON="C:\Users\hp\AppData\Local\Programs\Python\Python313\python.exe"
set APP="D:\Project_integrasi_dan_login\app.py"
set FLASK_PORT=5006
set NGROK="C:\ngrok\ngrok.exe"
set NGROK_CONFIG="C:\Users\hp\AppData\Local\ngrok\ngrok.yml"

REM Run Flask
echo Starting Flask...
start cmd /k %PYTHON% %APP%

REM Wait a few seconds
timeout /t 3 /nobreak

REM Run Ngrok
echo Starting Ngrok...
start cmd /k %NGROK% http %FLASK_PORT% --config %NGROK_CONFIG%
