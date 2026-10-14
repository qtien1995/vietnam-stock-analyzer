"""
Vietnam Stock Analyzer - Zero-Server Dashboard Entry Point
Tương thích ngược: Cho phép chạy `python app.py` để cập nhật và mở
Bảng điều khiển Offline (DASHBOARD.html) trên Microsoft Edge mà không cần web server.
"""

import sys
from pathlib import Path

# Fix Windows console UTF-8 display
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)
    except Exception:
        pass

from core.dashboard_generator import generate_dashboard_html


def run_offline_dashboard():
    print("=" * 65)
    print("🏛️ VIETNAM STOCK ANALYZER — OFFLINE COMMAND CENTER")
    print("🚀 Kiến trúc Zero-Server: Cập nhật & Mở trực tiếp trên Microsoft Edge")
    print("=" * 65)
    path = generate_dashboard_html(auto_open=True)
    print(f"✅ Đã tạo và mở Dashboard thành công tại: {path}")


if __name__ == "__main__":
    run_offline_dashboard()
