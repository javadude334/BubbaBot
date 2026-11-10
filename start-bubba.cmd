@echo off
setlocal
cd /d "%~dp0"
rem Isolate BubbaBot from Python 2.7 settings used by Mystic MRC.
set "PYTHONHOME="
set "PYTHONPATH="
set "PYTHONSTARTUP="
set "PYTHONNOUSERSITE=1"
set "PYTHONUTF8=1"
set "PYTHON_EXE=%LOCALAPPDATA%\Programs\Python\Python314\python.exe"
if not exist "%PYTHON_EXE%" (
    echo ERROR: Python 3.14 not found at "%PYTHON_EXE%".
    echo Update PYTHON_EXE in this script for the target machine.
    exit /b 1
)
echo BubbaBot offline validation
"%PYTHON_EXE%" -I -m unittest discover -s tests -v
set "EXIT_CODE=%ERRORLEVEL%"
if not "%EXIT_CODE%"=="0" echo ERROR: BubbaBot tests failed with exit code %EXIT_CODE%.
exit /b %EXIT_CODE%
