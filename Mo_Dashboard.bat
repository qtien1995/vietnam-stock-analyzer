@echo off
chcp 65001 >nul
echo ===================================================
echo 🏛️ VIETNAM STOCK ANALYZER — KHỞI CHẠY OFFLINE DASHBOARD
echo 🚀 Kiến trúc Zero-Server: Mở trực tiếp trên Microsoft Edge
echo ===================================================

cd /d "%~dp0"
python main.py --mode dashboard

echo.
echo ✅ Đã cập nhật và mở DASHBOARD.html thành công!
timeout /t 3 >nul
