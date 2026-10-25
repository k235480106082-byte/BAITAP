@echo off
chcp 65001 > nul
set "PATH=%LOCALAPPDATA%\dotnet;%PATH%"
cd /d "%~dp0bai2_rsa"
dotnet run
pause
