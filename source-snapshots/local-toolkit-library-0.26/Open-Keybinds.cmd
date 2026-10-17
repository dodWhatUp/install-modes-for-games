@echo off
setlocal
rem Reuse an explicitly selected existing host runtime. Never install Python or bypass policy.
if not defined GAME_TOOLS_PYTHON (
 echo This source module is not installed into Unified Game Tools yet.
 echo Set GAME_TOOLS_PYTHON to the existing Python executable used by the Hub.
 echo Or run: python scripts\Game-Keybinds.py gui
 echo Read 00_START_HERE.html for the integration handoff and tested boundaries.
 pause
 exit /b 2
)
if not exist "%GAME_TOOLS_PYTHON%" (
 echo The selected existing Python executable was not found. No fallback or installation was attempted.
 pause
 exit /b 2
)
"%GAME_TOOLS_PYTHON%" -c "import sys; assert sys.version_info >= (3, 10); import tkinter" 
if errorlevel 1 (
 echo The selected runtime needs Python 3.10 or later and Tk. No packages were installed.
 pause
 exit /b 2
)
if defined GAME_TOOL_HUB_DATA_DIR (
 "%GAME_TOOLS_PYTHON%" "%~dp0scripts\Game-Keybinds.py" --data-dir "%GAME_TOOL_HUB_DATA_DIR%" gui
) else (
 "%GAME_TOOLS_PYTHON%" "%~dp0scripts\Game-Keybinds.py" gui
)
if errorlevel 1 pause
endlocal
