@echo off
chcp 65001 >nul
echo ===================================================
echo 🚀 HỆ THỐNG QUÉT RADAR CHỨNG KHOÁN CUỐI NGÀY (1 CHIỀU)
echo ===================================================

cd /d "%~dp0"
python -c "import sys; sys.path.append('.'); from alerts.telegram_bot import send_telegram_radar; send_telegram_radar(top_n=10)"

echo.
echo ✅ Đã quét và bắn báo cáo Top 10 qua Telegram 1 chiều thành công!
pause
