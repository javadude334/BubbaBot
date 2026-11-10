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
"%PYTHON_EXE%" -m bubbabot.local_test_server
exit /b %ERRORLEVEL%
