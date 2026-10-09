@echo off
chcp 65001 >nul
title HỘI ĐỒNG THAM MƯU ĐẦU TƯ TTCK VIỆT NAM (AI BOT)
echo ================================================================
echo 🤖 HỘI ĐỒNG THAM MƯU ĐẦU TƯ TTCK VIỆT NAM (AI BOT 2 CHIỀU)
echo ================================================================
echo.
echo Đang khởi động Telegram Interactive Bot...
echo Nhấn Ctrl + C để dừng bot bất cứ lúc nào.
echo.

cd /d "%~dp0"
python -u main.py -m bot

pause
