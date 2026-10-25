@echo off
chcp 65001 > nul
set "PATH=%LOCALAPPDATA%\dotnet;%PATH%"
title Bai 2: Ma hoa RSA (C# Windows Forms)
cd /d "%~dp0"
dotnet run
pause
