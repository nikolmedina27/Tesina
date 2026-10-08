@echo off
rem SteelPlan en la RED LOCAL de la planta: otras PCs y tablets abren http://IP-DE-ESTA-PC:8600
rem Windows pedira permiso en el firewall la primera vez. Usar solo en la red interna de la empresa.
setlocal
cd /d "%~dp0.."
set "PY=%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
if not exist "%PY%" set "PY=py"
echo Direcciones de esta PC (usar la IPv4 de la red de la planta):
ipconfig | findstr /i "IPv4"
echo.
echo Enlace para el equipo: http://IP-DE-ARRIBA:8600
"%PY%" -m uvicorn plataforma.server:app --host 0.0.0.0 --port 8600
endlocal
