@echo off
setlocal
cd /d "%~dp0"
where py >nul 2>nul
if errorlevel 1 (
  set PY=python
) else (
  set PY=py
)
if not exist ".venv\Scripts\python.exe" (
  echo [1/3] Dang tao moi truong Python rieng...
  %PY% -m venv .venv
  if errorlevel 1 goto error
)
echo [2/3] Kiem tra va cai thu vien can thiet...
.venv\Scripts\python.exe -m pip install -r requirements.txt
if errorlevel 1 goto error
echo [3/3] Dang khoi dong May Mart...
echo Mo trinh duyet tai http://127.0.0.1:5000
.venv\Scripts\python.exe app.py
goto end
:error
echo.
echo Co loi khi cai dat/chay. Hay doc README.md va kiem tra Python, Internet.
pause
:end
endlocal
