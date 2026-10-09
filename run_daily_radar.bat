@echo off
chcp 65001 >nul
echo ===================================================
echo 🚀 HỆ THỐNG QUÉT RADAR CHỨNG KHOÁN CUỐI NGÀY
echo ===================================================

cd /d "%~dp0"
python -c "import sys; sys.path.append('.'); from config import TELEGRAM_CHAT_ID; from alerts.telegram_interactive_bot import handle_scan; handle_scan(chat_id=TELEGRAM_CHAT_ID, top_n=10) if TELEGRAM_CHAT_ID else print('Chưa cấu hình TELEGRAM_CHAT_ID trong .env')"

echo.
echo ✅ Đã gửi báo cáo Top 10 mã cổ phiếu qua Telegram!
pause
