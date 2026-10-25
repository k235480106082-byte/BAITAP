@echo off
chcp 65001 > nul
title Bai 1: Ma hoa AES (Console App)
cd /d "%~dp0"
python app_aes.py --console
pause
