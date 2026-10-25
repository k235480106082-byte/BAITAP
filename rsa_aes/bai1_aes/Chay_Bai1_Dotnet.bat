@echo off
chcp 65001 > nul
set "PATH=%LOCALAPPDATA%\dotnet;%PATH%"
cd /d "%~dp0"
dotnet run
pause
