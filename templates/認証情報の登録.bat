@echo off
setlocal
rem ============================================================
rem comken credential registration GUI launcher
rem Set COMKEN_ROOT to the shared comken repository root.
rem Copy this file to each project root before use.
rem ============================================================
set "COMKEN_ROOT=\\server\share\tools\comken"

if not exist "%COMKEN_ROOT%\comken\__init__.py" (
  echo.
  echo [!] comken was not found: %COMKEN_ROOT%
  echo     Set COMKEN_ROOT to the correct shared folder.
  pause
  exit /b 1
)

rem Add comken only for this launcher process; do not change PC settings.
set "PYTHONPATH=%COMKEN_ROOT%;%PYTHONPATH%"
python -m comken.credentials --gui
if errorlevel 1 (
  echo.
  echo [!] Failed to start the GUI.
  echo     - Check that Python is installed.
  echo     - Check that COMKEN_ROOT points to the shared comken folder.
  pause
)

endlocal