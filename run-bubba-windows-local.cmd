@echo off
setlocal
cd /d "%~dp0"
set "PYTHONHOME="
set "PYTHONPATH="
set "PYTHONSTARTUP="
set "PYTHONNOUSERSITE=1"
set "PYTHONUTF8=1"
where py >nul 2>&1
if errorlevel 1 (
  echo ERROR: Python launcher py not found.
  exit /b 1
)
py -3.14 -c "import sys; assert sys.version_info[:2] == (3, 14)" >nul 2>&1
if errorlevel 1 (
  echo ERROR: Python 3.14 is required for this local test launcher.
  exit /b 1
)
if not exist "bubba.local.json" (
  echo ERROR: Copy bubba.local.example.json to bubba.local.json first.
  exit /b 1
)
echo BubbaBot offline simulation - loopback only, no public MRC or AI API.
py -3.14 -m bubbabot.local_runner --config bubba.local.json --max-sessions 3
exit /b %ERRORLEVEL%
