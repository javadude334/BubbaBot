@echo off
setlocal
cd /d "%~dp0"
rem Keep Python 2.7 environment settings out of BubbaBot.
set "PYTHONHOME="
set "PYTHONPATH="
set "PYTHONSTARTUP="
set "PYTHONNOUSERSITE=1"
set "PYTHONUTF8=1"
set "PYTHON_EXE=%LOCALAPPDATA%\Programs\Python\Python314\python.exe"
if not exist "%PYTHON_EXE%" (
    echo ERROR: Python 3.14 not found at "%PYTHON_EXE%".
    exit /b 1
)
rem Default room can be overridden by passing --room RoomName.
if "%~1"=="" (
    "%PYTHON_EXE%" -m bubbabot.demo --room BubbaRoom
) else (
    "%PYTHON_EXE%" -m bubbabot.demo %*
)
exit /b %ERRORLEVEL%
