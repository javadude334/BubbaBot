@echo off
setlocal
cd /d "%~dp0"
set "PYTHONHOME="
set "PYTHONPATH="
set "PYTHONSTARTUP="
set "PYTHONNOUSERSITE=1"
set "PYTHONUTF8=1"
set "PYTHON_EXE=%LOCALAPPDATA%\Programs\Python\Python314\python.exe"
if not exist "%PYTHON_EXE%" (
    echo ERROR: Python 3.14 not found.
    exit /b 1
)
if not exist "bubba.local.json" (
    echo Copy bubba.local.example.json to bubba.local.json and edit as needed.
    exit /b 1
)
"%PYTHON_EXE%" -m bubbabot.local_runner --config bubba.local.json
exit /b %ERRORLEVEL%
