"""
Ứng dụng Web App Chạy Offline trên Localhost (Microsoft Edge)
Vietnam Stock Analyzer - Command Center
- Khởi chạy web server offline tại http://localhost:5000
- Tự động mở Microsoft Edge khi bắt đầu
- Ô tìm kiếm mã cổ phiếu 1-Click
- Quản lý và xem toàn bộ Báo cáo Chiến lược HTML
- Tích hợp API Bàn tròn Hỏi-Đáp Tương tác Hội đồng 6 AI
"""

import os
import sys
import time
import threading
import subprocess
import webbrowser
from pathlib import Path
from flask import Flask, render_template, request, jsonify, send_from_directory

# Cấu hình UTF-8 cho Windows console
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)
    except Exception:
        pass

from config import REPORTS_DIR
from core.data_loader import get_global_macro_and_commodities
from core.stock_service import analyze_ticker_full
from ai.interactive_advisor import CouncilAdvisor

app = Flask(__name__, template_folder=str(Path(__file__).parent / "templates"))
advisor = CouncilAdvisor()


def get_existing_reports():
    """Lấy danh sách các file báo cáo HTML trong thư mục reports/ kèm Sàn giao dịch chính xác"""
    reports = []
    if not REPORTS_DIR.exists():
        return reports

    from core.db_manager import get_stock_master, save_stock_master
    from core.data_loader import get_governance_data

    files = list(REPORTS_DIR.glob("*.html"))
    files.sort(key=lambda x: x.stat().st_mtime, reverse=True)

    for f in files:
        # Tên file thường có dạng YYYY-MM-DD_SYMBOL.html hoặc YYYY-MM-DD_SYMBOL_VS_SECTOR...
        name_parts = f.stem.split("_")
        date_str = name_parts[0] if len(name_parts) >= 2 else "Gần đây"
        symbol = name_parts[1].upper() if len(name_parts) >= 2 else f.stem.upper()

        size_kb = f.stat().st_size / 1024
        size_str = f"{size_kb:,.0f} KB" if size_kb < 1024 else f"{size_kb / 1024:.1f} MB"

        # Tra cứu sàn giao dịch siêu tốc từ DB Master, Governance Cache hoặc đọc nhanh từ HTML
        exchange = "HOSE"
        if len(symbol) == 3:
            m = get_stock_master(symbol)
            if m and m.get("exchange"):
                exchange = m["exchange"]
            else:
                # Kiểm tra cache file cục bộ (không gọi mạng)
                gov_cache = Path(__file__).parent / "cache" / f"governance_{symbol}.json"
                if gov_cache.exists():
                    try:
                        import json
                        with open(gov_cache, "r", encoding="utf-8") as gf:
                            g_data = json.load(gf)
                            com_code = str(g_data.get("overview", {}).get("com_group_code", "")).upper()
                            if "HNX" in com_code:
                                exchange = "HNX"
                            elif "UPCOM" in com_code:
                                exchange = "UPCOM"
                            else:
                                exchange = "HOSE"
                            save_stock_master(symbol, g_data.get("overview", {}).get("organ_name", symbol), exchange)
                    except Exception:
                        pass
                else:
                    # Đọc nhanh 2000 ký tự đầu của file HTML để lấy badge sàn đã tạo
                    try:
                        with open(f, "r", encoding="utf-8") as hf:
                            head_chunk = hf.read(2500)
                            if ">HNX</span>" in head_chunk:
                                exchange = "HNX"
                            elif ">UPCOM</span>" in head_chunk:
                                exchange = "UPCOM"
                            elif ">HOSE</span>" in head_chunk:
                                exchange = "HOSE"
                    except Exception:
                        pass

        reports.append({
            "filename": f.name,
            "symbol": symbol,
            "exchange": exchange,
            "date": date_str,
            "size": size_str,
            "path": str(f)
        })

    return reports


@app.route("/")
def index():
    """Trang chủ Dashboard & Trạm điều khiển Localhost"""
    macro_raw = get_global_macro_and_commodities()
    macro_data = macro_raw.get("global_commodities", {})
    reports = get_existing_reports()
    return render_template("index.html", macro=macro_data, reports=reports)


@app.route("/reports/<path:filename>")
def serve_report(filename):
    """Phục vụ file báo cáo HTML độc lập"""
    return send_from_directory(REPORTS_DIR, filename)


@app.route("/api/analyze/<symbol>", methods=["GET", "POST"])
def api_analyze(symbol):
    """API Phân tích cổ phiếu trực tiếp theo yêu cầu từ Web"""
    sym = symbol.strip().upper()
    try:
        res = analyze_ticker_full(sym, save_report=True, send_alert=False)
        if "error" in res:
            return jsonify({"status": "error", "error": res["error"]}), 400

        html_path = res.get("html_path")
        report_filename = Path(html_path).name if html_path else f"{sym}.html"

        return jsonify({
            "status": "ok",
            "symbol": sym,
            "report_url": f"/reports/{report_filename}",
            "trade_setup": res.get("trade_setup", {})
        })
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)}), 500


@app.route("/api/council/ask", methods=["POST"])
def api_council_ask():
    """API Hỏi-Đáp Trực Tiếp với Hội Đồng 6 AI"""
    data = request.get_json() or {}
    symbol = data.get("symbol", "").upper().strip()
    question = data.get("question", "").strip()
    expert_id = data.get("expert_id", "all")
    context = data.get("context", {})

    if not question:
        return jsonify({"error": "Thiếu câu hỏi"}), 400

    resp = advisor.answer_question(
        symbol=symbol,
        question=question,
        expert_id=expert_id,
        context=context
    )

    return jsonify(resp)


@app.route("/api/macro")
def api_macro():
    """API Lấy thông tin Vĩ mô Hàng hóa thế giới"""
    return jsonify(get_global_macro_and_commodities())


def open_edge_browser():
    """Tự động mở Microsoft Edge tại localhost:5000"""
    time.sleep(1.2)
    url = "http://localhost:5000"
    print(f"\n[🚀] Đang tự động mở Microsoft Edge tại: {url} ...")
    try:
        # Ưu tiên mở thẳng Microsoft Edge trên Windows
        subprocess.Popen(f'start msedge "{url}"', shell=True)
    except Exception:
        webbrowser.open(url)


if __name__ == "__main__":
    port = 5000
    print("=" * 65)
    print("🏛️ VIETNAM STOCK ANALYZER - LOCALHOST COMMAND CENTER")
    print(f"🌐 Server đang chạy tại: http://localhost:{port}")
    print("💻 Tương thích 100% với trình duyệt Microsoft Edge")
    print("=" * 65)

    # Chạy thread mở trình duyệt Edge ngầm sau khi server khởi động
    threading.Thread(target=open_edge_browser, daemon=True).start()

    # Khởi chạy Flask Server
    app.run(host="0.0.0.0", port=port, debug=False)
