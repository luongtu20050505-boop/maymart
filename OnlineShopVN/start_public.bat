@echo off
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
  echo [1/3] Dang tao moi truong Python rieng...
  python -m venv .venv
  if errorlevel 1 goto error
)
echo [2/3] Cai thu vien neu can...
.venv\Scripts\python.exe -m pip install -r requirements.txt
if errorlevel 1 goto error

echo [3/3] Khoi dong Flask + Cloudflare Tunnel...
start "MayMart Flask" .venv\Scripts\python.exe app.py
timeout /t 3 /nobreak >nul
if not exist "cloudflared.exe" (
  echo Dang tai cloudflared...
  powershell -Command "Invoke-WebRequest -Uri 'https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe' -OutFile 'cloudflared.exe'"
)
cloudflared.exe tunnel --url http://localhost:5000
goto end
:error
echo Co loi. Hay doc README.md.
pause
:end
endlocal