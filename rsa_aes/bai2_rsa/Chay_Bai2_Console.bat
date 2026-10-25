@echo off
chcp 65001 > nul
title Bai 2: Ma hoa bat doi xung RSA & Chu ky so (Console App)
cd /d "%~dp0"
python app_rsa.py --console
pause
