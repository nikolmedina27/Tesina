@echo off
rem SteelPlan: inicia el servidor (si no esta corriendo) y abre el enlace en el navegador.
rem Solo en esta PC (127.0.0.1). Para la red local usar iniciar_red_local.bat.
setlocal
cd /d "%~dp0.."
set "PY=%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
if not exist "%PY%" set "PY=py"
set "URL=http://localhost:8600"

powershell -NoProfile -Command "try { Invoke-WebRequest -UseBasicParsing '%URL%/api/docs' -TimeoutSec 2 | Out-Null; exit 0 } catch { exit 1 }"
if %errorlevel%==0 goto abrir

echo Iniciando SteelPlan...
start "SteelPlan - servidor (no cerrar)" /min "%PY%" -m uvicorn plataforma.server:app --host 127.0.0.1 --port 8600
powershell -NoProfile -Command "for ($i=0; $i -lt 80; $i++) { try { Invoke-WebRequest -UseBasicParsing '%URL%/api/docs' -TimeoutSec 2 | Out-Null; exit 0 } catch { Start-Sleep -Milliseconds 750 } }; exit 1"
if not %errorlevel%==0 (
  echo No se pudo iniciar el servidor. Revise la ventana "SteelPlan - servidor".
  pause
  exit /b 1
)

:abrir
start "" "%URL%"
endlocal
