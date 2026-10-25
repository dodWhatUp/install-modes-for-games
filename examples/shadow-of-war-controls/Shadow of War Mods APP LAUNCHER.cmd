@echo off
setlocal
if not exist "%~dp0launcher-pythonw.txt" goto missing
if not exist "%~dp0launcher-workspace.txt" goto missing
set /p "APP_PYTHONW="<"%~dp0launcher-pythonw.txt"
set /p "APP_WORKSPACE="<"%~dp0launcher-workspace.txt"
if not exist "%APP_PYTHONW%" goto missing
if not exist "%APP_WORKSPACE%\graphics-profiles.json" goto missing
if not exist "%~dp0mod_panel.py" goto missing
start "" "%APP_PYTHONW%" "%~dp0mod_panel.py" --workspace "%APP_WORKSPACE%"
exit /b
:missing
echo The APP LAUNCHER setup is missing. Read README.md in this app folder.
pause
exit /b 1
