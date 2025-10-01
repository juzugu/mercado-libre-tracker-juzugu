@echo off
setlocal

REM Folder where this .bat lives (your package dir)
set "PKG_DIR=%~dp0"
set "PKG_DIR=%PKG_DIR:~0,-1%"

REM Package name = this folder's name
for %%I in ("%PKG_DIR%") do set "PACKAGE_NAME=%%~nI"

REM Virtualenv inside the package (portable)
set "VENV_DIR=%PKG_DIR%\.venv"

REM Make pip faster: don't phone home
set "PIP_DISABLE_PIP_VERSION_CHECK=1"

REM Create venv if missing (first run)
if not exist "%VENV_DIR%\Scripts\python.exe" (
  echo [setup] Creating virtual environment...
  where py >nul 2>nul && (
    py -m venv "%VENV_DIR%" || ( echo [error] venv failed & goto :end_err )
  ) || (
    python -m venv "%VENV_DIR%" || ( echo [error] venv failed & goto :end_err )
  )
  set "NEED_INSTALL=1"
)

REM Activate venv
call "%VENV_DIR%\Scripts\activate.bat" || ( echo [error] venv activate failed & goto :end_err )

REM Install deps once (or if requirements.txt changes)
if exist "%PKG_DIR%\requirements.txt" (
  if not exist "%VENV_DIR%\.deps_done" set "NEED_INSTALL=1"
)

if "%NEED_INSTALL%"=="1" (
  echo [setup] Installing dependencies...
  if exist "%PKG_DIR%\requirements.txt" (
    python -m pip install -r "%PKG_DIR%\requirements.txt" || goto :end_err
  ) else (
    python -m pip install requests beautifulsoup4 || goto :end_err
  )
  >"%VENV_DIR%\.deps_done" echo ok
)

REM Run the app as a module (needed for relative imports)
pushd "%PKG_DIR%\.."
echo [run] Starting %PACKAGE_NAME%...
python -m "%PACKAGE_NAME%"
set "EC=%ERRORLEVEL%"
popd
exit /b %EC%

:end_err
echo.
echo [fatal] Something went wrong. Leaving the window open so you can read the message.
echo Press any key to close...
pause >nul
exit /b 1
