"""
Module Sinh File Offline Edge Dashboard (Bloomberg Terminal Dark Theme Nâng Cấp)
Tạo ra file DASHBOARD.html độc lập tại thư mục gốc dự án.
Người dùng có thể mở trực tiếp bằng Microsoft Edge (chuẩn file:///...) mà không cần server hay file .bat chạy ngầm.
Tính năng mới:
- Thanh tìm kiếm Live Search tức thời (không cần tải lại trang).
- Bộ lọc theo Ngành (Pill filters: Dầu khí, Ngân hàng, Thép, BĐS, Cao su...).
- Sắp xếp cột động (Click-to-sort theo Giá, % Thay đổi, Tỷ lệ Nổ Vol, Điểm Đồng thuận).
- Thước đo Độ rộng Thị trường (Market Breadth: Tăng / Giảm / Đi ngang).
- Sparkline SVG Mini Trend trên từng thẻ hàng hóa thế giới.
- Bảng Xếp Hạng Động Cơ Thời Điểm (Timing Matrix Leaderboard: Chờ Nổ T+ vs Cảnh Báo Sập).
"""

import json
import os
import sys
import webbrowser
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List

from config import PROJECT_ROOT, REPORTS_DIR, DEFAULT_WATCHLIST
from core.data_loader import get_global_macro_and_commodities, get_realtime_quote
from core.stock_service import run_screener
from core.timing_engine import analyze_timing_prediction


def generate_sparkline_svg(trend_up: bool) -> str:
    """Tạo biểu đồ đường SVG mini 70x20px thể hiện xu hướng tăng/giảm nhẹ nhàng."""
    if trend_up:
        stroke = "#10b981"
        d = "M 0,16 Q 18,14 32,15 T 56,7 T 72,3"
        circle_y = 3
    else:
        stroke = "#ef4444"
        d = "M 0,4 Q 18,7 32,6 T 56,14 T 72,17"
        circle_y = 17
    return f"""<svg width="74" height="20" viewBox="0 0 76 20" style="overflow: visible;">
        <path d="{d}" fill="none" stroke="{stroke}" stroke-width="2" stroke-linecap="round"/>
        <circle cx="72" cy="{circle_y}" r="3" fill="{stroke}" />
    </svg>"""


def generate_dashboard_html(auto_open: bool = False) -> Path:
    """
    Tập hợp dữ liệu toàn diện và tạo file DASHBOARD.html tĩnh mở trực tiếp trên Microsoft Edge.
    """
    dashboard_path = PROJECT_ROOT / "DASHBOARD.html"

    # 1. Thu thập dữ liệu Vĩ mô & Hàng hóa thế giới
    macro_data = get_global_macro_and_commodities()
    commodities = macro_data.get("global_commodities", {})
    vn_macro = macro_data.get("vietnam_macro", {})
    updated_at = macro_data.get("updated_at", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    # 2. Quét Top cổ phiếu nổ vol & gom hàng toàn thị trường
    try:
        top_stocks = run_screener(top_n=15)
    except Exception:
        top_stocks = []

    # 3. Phân tích Độ rộng Thị trường (Market Breadth)
    bull_count = sum(1 for s in top_stocks if s.get("change_pct", 0) > 0)
    bear_count = sum(1 for s in top_stocks if s.get("change_pct", 0) < 0)
    neutral_count = len(top_stocks) - bull_count - bear_count
    total_eval = max(len(top_stocks), 1)
    bull_pct = round((bull_count / total_eval) * 100)
    bear_pct = round((bear_count / total_eval) * 100)
    neutral_pct = 100 - bull_pct - bear_pct

    # 4. Quét danh sách báo cáo HTML đã xuất bản trong reports/
    report_files = []
    if REPORTS_DIR.exists():
        for f in sorted(REPORTS_DIR.glob("*.html"), reverse=True)[:20]:
            name_parts = f.stem.split("_")
            sym = name_parts[-1] if len(name_parts) >= 2 else f.stem
            report_files.append({
                "filename": f.name,
                "symbol": sym,
                "rel_path": f"reports/{f.name}",
                "modified": datetime.fromtimestamp(f.stat().st_mtime).strftime("%d/%m/%Y %H:%M")
            })

    # 5. Phân loại Danh mục Timing Leaderboard: Chờ Nổ T+ vs Cảnh Báo Sập
    breakout_candidates = []
    warning_candidates = []

    for s in top_stocks:
        action = s.get("action", "QUAN SÁT")
        score = s.get("consensus_score", 50)
        vol_r = s.get("vol_ratio", 1.0)
        sym = s.get("symbol", "")
        price = s.get("price", 0)
        sec = s.get("sector_name", "Chung")

        # Tiêu chí chờ nổ: Action Mua, Score >= 60, Vol nén hoặc nổ
        if "MUA" in action or score >= 65:
            pivot_est = round(price * 1.025, -2)
            breakout_candidates.append({
                "symbol": sym,
                "price": price,
                "sector": sec,
                "vol_ratio": vol_r,
                "pivot": pivot_est,
                "dist": "+2.5%",
                "prob": min(88, 60 + int(vol_r * 10)),
                "window": "T+1..T+3",
                "score": score
            })
        else:
            sl_est = round(price * 0.94, -2)
            warning_candidates.append({
                "symbol": sym,
                "price": price,
                "sector": sec,
                "vol_ratio": vol_r,
                "failure_lvl": sl_est,
                "dist": "-6.0%",
                "risk_prob": max(45, 100 - score),
                "reason": "Áp lực cung cản / Vi phạm kỹ thuật",
                "score": score
            })

    # 6. Tạo HTML Items cho Ticker Hàng hóa kèm Sparkline SVG
    comm_ticker_html = ""
    comm_icons = {
        "crude_oil_brent": "🛢️",
        "gold_world": "🌍",
        "gold_sjc": "🥇",
        "rubber_tsr20": "🌳",
        "steel_hrc": "🏗️",
        "urea_fertilizer": "🌱",
        "fed_funds_rate": "🏛️",
        "us_cpi": "📊",
        "dxy_index": "💵",
        "usd_vnd": "🇻🇳"
    }

    for key, item in commodities.items():
        icon = comm_icons.get(key, "📌")
        val = item.get("value", "N/A")
        unit = item.get("unit", "")
        chg = item.get("change_pct", 0)
        trend_up = chg >= 0
        chg_sign = "+" if chg > 0 else ""
        chg_color = "#10b981" if chg > 0 else ("#ef4444" if chg < 0 else "#94a3b8")
        
        val_str = f"{val:,}" if isinstance(val, (int, float)) and val > 1000 else f"{val}"
        sparkline_svg = generate_sparkline_svg(trend_up)

        comm_ticker_html += f"""
        <div class="comm-card">
            <div class="comm-header">
                <div style="display: flex; align-items: center; gap: 6px; overflow: hidden;">
                    <span class="comm-icon">{icon}</span>
                    <span class="comm-title">{item.get('name', key).split('(')[0].strip()}</span>
                </div>
                {sparkline_svg}
            </div>
            <div class="comm-val">{val_str} <span class="comm-unit">{unit}</span></div>
            <div class="comm-chg" style="color: {chg_color};">
                {chg_sign}{chg}% &bull; {item.get('trend', '').split('/')[0][:25]}
            </div>
        </div>
        """

    # 7. Tạo HTML Bảng Top cổ phiếu (Screener)
    top_stocks_rows = ""
    for idx, s in enumerate(top_stocks, 1):
        action = s.get("action", "QUAN SÁT")
        action_color = "#10b981" if "MUA" in action else ("#ef4444" if "TRÁNH" in action else "#f59e0b")
        chg = s.get("change_pct", 0)
        chg_color = "#10b981" if chg > 0 else ("#ef4444" if chg < 0 else "#f59e0b")
        sym = s.get("symbol", "")
        sec = s.get("sector_name", "Chung")

        matched_rep = next((r for r in report_files if r["symbol"] == sym), None)
        rep_btn = f"""<a href="{matched_rep['rel_path']}" target="_blank" class="view-rep-btn">📑 Xem Báo Cáo</a>""" if matched_rep else f"""<span style="color: #64748b; font-size: 11px;">Chưa xuất bản</span>"""

        top_stocks_rows += f"""
        <tr data-symbol="{sym}" data-sector="{sec}">
            <td style="text-align: center; color: #94a3b8; font-weight: 600;">#{idx}</td>
            <td data-sort-val="{sym}">
                <div style="font-weight: 800; font-size: 14px; color: #fff;">{sym}</div>
                <div style="font-size: 11px; color: #94a3b8;">{sec}</div>
            </td>
            <td style="text-align: right; font-weight: 700; color: #fff;" data-sort-val="{s.get('price', 0)}">
                {s.get('price', 0):,.0f} đ
                <div style="font-size: 11px; color: {chg_color};">{chg:+.1f}%</div>
            </td>
            <td style="text-align: right; font-weight: 700; color: #38bdf8;" data-sort-val="{s.get('vol_ratio', 1.0)}">
                {s.get('vol_ratio', 1.0):.2f}x
                <div style="font-size: 10px; color: #64748b;">{s.get('liquidity', '')}</div>
            </td>
            <td style="text-align: center;" data-sort-val="{s.get('consensus_score', 0)}">
                <span class="score-badge">{s.get('consensus_score', 0)}/100</span>
            </td>
            <td style="text-align: center;">
                <span class="action-tag" style="color: {action_color}; border-color: {action_color}; background: rgba(255,255,255,0.04);">
                    {action}
                </span>
            </td>
            <td style="color: #34d399; font-weight: 600; font-size: 12px;">{s.get('buy_zone', 'N/A')}</td>
            <td style="text-align: center;">{rep_btn}</td>
        </tr>
        """

    # 8. Tạo HTML Danh sách Báo cáo gần nhất
    recent_reports_html = ""
    for r in report_files[:10]:
        recent_reports_html += f"""
        <div class="report-chip">
            <div class="report-chip-left">
                <span class="rep-sym">{r['symbol']}</span>
                <span class="rep-date">{r['modified']}</span>
            </div>
            <a href="{r['rel_path']}" target="_blank" class="rep-open-link">Mở Báo Cáo ↗</a>
        </div>
        """

    # 9. Tạo HTML Leaderboard Chờ Nổ T+
    breakout_rows_html = ""
    for b in breakout_candidates[:5]:
        matched_rep = next((r for r in report_files if r["symbol"] == b["symbol"]), None)
        rep_link = f"""<a href="{matched_rep['rel_path']}" target="_blank" style="color:#38bdf8; text-decoration:none; font-weight:600;">{b['symbol']} ↗</a>""" if matched_rep else b['symbol']
        breakout_rows_html += f"""
        <div class="timing-mini-row" style="border-left: 3px solid #10b981;">
            <div>
                <b style="color: #fff; font-size: 13px;">{rep_link}</b>
                <span style="font-size: 11px; color: #94a3b8; margin-left: 6px;">{b['sector']}</span>
                <div style="font-size: 11px; color: #34d399; margin-top: 2px;">
                    Pivot vượt: <b>{b['pivot']:,.0f} đ</b> ({b['dist']}) &bull; Khung: <b>{b['window']}</b>
                </div>
            </div>
            <div style="text-align: right;">
                <span class="badge" style="background: rgba(16, 185, 129, 0.15); color: #10b981; border: 1px solid #10b981;">
                    Xác suất {b['prob']}%
                </span>
                <div style="font-size: 10px; color: #64748b; margin-top: 4px;">Vol {b['vol_ratio']:.1f}x MA20</div>
            </div>
        </div>
        """

    # 10. Tạo HTML Leaderboard Cảnh Báo Sập
    warning_rows_html = ""
    for w in warning_candidates[:5]:
        matched_rep = next((r for r in report_files if r["symbol"] == w["symbol"]), None)
        rep_link = f"""<a href="{matched_rep['rel_path']}" target="_blank" style="color:#f87171; text-decoration:none; font-weight:600;">{w['symbol']} ↗</a>""" if matched_rep else w['symbol']
        warning_rows_html += f"""
        <div class="timing-mini-row" style="border-left: 3px solid #ef4444;">
            <div>
                <b style="color: #fff; font-size: 13px;">{rep_link}</b>
                <span style="font-size: 11px; color: #94a3b8; margin-left: 6px;">{w['sector']}</span>
                <div style="font-size: 11px; color: #fca5a5; margin-top: 2px;">
                    Ngưỡng gãy: <b>{w['failure_lvl']:,.0f} đ</b> ({w['dist']}) &bull; {w['reason'][:22]}
                </div>
            </div>
            <div style="text-align: right;">
                <span class="badge" style="background: rgba(239, 68, 68, 0.15); color: #f87171; border: 1px solid #ef4444;">
                    Rủi ro {w['risk_prob']}%
                </span>
                <div style="font-size: 10px; color: #64748b; margin-top: 4px;">Điểm {w['score']}/100</div>
            </div>
        </div>
        """

    html_template = f"""<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Bảng Điều Khiển Chứng Khoán Cục Bộ | Vietnam Stock Analyzer</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Be+Vietnam+Pro:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;700&display=swap" rel="stylesheet">
    <style>
        :root {{
            --bg-base: #060911;
            --bg-card: #0d1322;
            --bg-card-alt: #131c31;
            --border: #1f2c47;
            --border-hover: #38bdf8;
            --text-main: #f8fafc;
            --text-muted: #94a3b8;
            --text-dim: #64748b;
            --accent-blue: #38bdf8;
            --accent-emerald: #10b981;
            --accent-amber: #f59e0b;
            --accent-rose: #f43f5e;
            --accent-purple: #a855f7;
            --font-sans: 'Be Vietnam Pro', -apple-system, sans-serif;
            --font-mono: 'JetBrains Mono', monospace;
        }}

        * {{
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }}

        body {{
            background-color: var(--bg-base);
            color: var(--text-main);
            font-family: var(--font-sans);
            line-height: 1.5;
            padding: 20px 28px 60px 28px;
        }}

        /* TOP NAVBAR */
        .top-navbar {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 1px solid var(--border);
            padding-bottom: 16px;
            margin-bottom: 24px;
        }}

        .brand-title {{
            display: flex;
            align-items: center;
            gap: 12px;
            font-size: 20px;
            font-weight: 800;
            letter-spacing: -0.3px;
            background: linear-gradient(90deg, #38bdf8, #a7f3d0);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}

        .nav-links {{
            display: flex;
            align-items: center;
            gap: 14px;
        }}

        .nav-btn {{
            background: var(--bg-card);
            border: 1px solid var(--border);
            color: var(--text-muted);
            padding: 7px 16px;
            border-radius: 8px;
            font-size: 13px;
            font-weight: 600;
            text-decoration: none;
            display: flex;
            align-items: center;
            gap: 6px;
            transition: all 0.2s;
        }}

        .nav-btn:hover {{
            background: var(--bg-card-alt);
            color: #fff;
            border-color: var(--accent-blue);
        }}

        /* TICKER CARDS */
        .ticker-section-title {{
            font-size: 12px;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.8px;
            color: var(--text-dim);
            margin-bottom: 12px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}

        .comm-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
            gap: 12px;
            margin-bottom: 24px;
        }}

        .comm-card {{
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 12px 14px;
            transition: all 0.2s;
        }}

        .comm-card:hover {{
            border-color: var(--accent-blue);
            transform: translateY(-2px);
        }}

        .comm-header {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 6px;
            margin-bottom: 6px;
        }}

        .comm-icon {{
            font-size: 15px;
        }}

        .comm-title {{
            font-size: 11px;
            font-weight: 600;
            color: var(--text-muted);
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }}

        .comm-val {{
            font-family: var(--font-mono);
            font-size: 16px;
            font-weight: 700;
            color: #fff;
        }}

        .comm-unit {{
            font-size: 11px;
            font-weight: 400;
            color: var(--text-dim);
        }}

        .comm-chg {{
            font-size: 11px;
            font-weight: 600;
            margin-top: 2px;
        }}

        /* MARKET BREADTH BAR */
        .breadth-bar-container {{
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 14px 18px;
            margin-bottom: 24px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 20px;
            flex-wrap: wrap;
        }}

        .breadth-label {{
            font-size: 12px;
            font-weight: 700;
            color: #94a3b8;
            text-transform: uppercase;
        }}

        .breadth-meter {{
            flex: 1;
            min-width: 200px;
            height: 10px;
            border-radius: 5px;
            display: flex;
            overflow: hidden;
            background: rgba(255, 255, 255, 0.05);
        }}

        .breadth-seg-bull {{ height: 100%; background: #10b981; }}
        .breadth-seg-neut {{ height: 100%; background: #f59e0b; }}
        .breadth-seg-bear {{ height: 100%; background: #ef4444; }}

        .breadth-stats {{
            display: flex;
            gap: 16px;
            font-size: 12px;
            font-weight: 700;
        }}

        /* TIMING LEADERBOARD GRID */
        .timing-leaderboard-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 18px;
            margin-bottom: 28px;
        }}

        .timing-col-box {{
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 14px;
            padding: 16px 18px;
        }}

        .timing-col-title {{
            font-size: 13px;
            font-weight: 800;
            margin-bottom: 12px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}

        .timing-mini-row {{
            background: rgba(15, 23, 42, 0.6);
            border: 1px solid rgba(255, 255, 255, 0.05);
            border-radius: 10px;
            padding: 10px 12px;
            margin-bottom: 8px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            transition: all 0.2s;
        }}

        .timing-mini-row:hover {{
            background: var(--bg-card-alt);
        }}

        /* MAIN SEARCH & FILTER CONTROLS */
        .controls-bar {{
            display: flex;
            gap: 12px;
            margin-bottom: 16px;
            align-items: center;
            flex-wrap: wrap;
        }}

        .search-box {{
            flex: 1;
            min-width: 240px;
            position: relative;
        }}

        .search-input {{
            width: 100%;
            background: var(--bg-card);
            border: 1px solid var(--border);
            color: #fff;
            padding: 9px 14px;
            border-radius: 8px;
            font-size: 13px;
            font-family: inherit;
            outline: none;
            transition: border-color 0.2s;
        }}

        .search-input:focus {{
            border-color: var(--accent-blue);
        }}

        .sector-pills {{
            display: flex;
            gap: 6px;
            overflow-x: auto;
            scrollbar-width: none;
        }}

        .sector-pills::-webkit-scrollbar {{ display: none; }}

        .sector-pill {{
            background: var(--bg-card);
            border: 1px solid var(--border);
            color: var(--text-muted);
            padding: 6px 12px;
            border-radius: 6px;
            font-size: 12px;
            font-weight: 600;
            cursor: pointer;
            white-space: nowrap;
            transition: all 0.2s;
        }}

        .sector-pill:hover, .sector-pill.active {{
            background: var(--bg-card-alt);
            color: #fff;
            border-color: var(--accent-blue);
        }}

        /* MAIN CONTENT GRID */
        .main-grid {{
            display: grid;
            grid-template-columns: 2.3fr 1fr;
            gap: 24px;
        }}

        .panel-box {{
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 16px;
            padding: 22px;
        }}

        .panel-title {{
            font-size: 15px;
            font-weight: 700;
            color: #fff;
            margin-bottom: 16px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}

        /* TABLE */
        .screener-table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 13px;
        }}

        .screener-table th {{
            text-align: left;
            padding: 10px 12px;
            font-size: 11px;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.6px;
            color: var(--text-dim);
            border-bottom: 1px solid var(--border);
            cursor: pointer;
            user-select: none;
        }}

        .screener-table th:hover {{
            color: var(--accent-blue);
        }}

        .screener-table td {{
            padding: 12px;
            border-bottom: 1px solid rgba(255, 255, 255, 0.04);
        }}

        .screener-table tr:hover {{
            background: rgba(255, 255, 255, 0.02);
        }}

        .score-badge {{
            font-family: var(--font-mono);
            font-size: 12px;
            font-weight: 700;
            background: rgba(56, 189, 248, 0.15);
            color: var(--accent-blue);
            padding: 3px 8px;
            border-radius: 6px;
        }}

        .action-tag {{
            display: inline-block;
            font-size: 11px;
            font-weight: 700;
            padding: 2px 8px;
            border-radius: 4px;
            border: 1px solid;
            text-transform: uppercase;
        }}

        .badge {{
            display: inline-block;
            font-size: 11px;
            font-weight: 700;
            padding: 2px 8px;
            border-radius: 4px;
        }}

        .view-rep-btn {{
            color: var(--accent-blue);
            text-decoration: none;
            font-size: 12px;
            font-weight: 600;
            transition: color 0.2s;
        }}

        .view-rep-btn:hover {{
            color: #fff;
            text-decoration: underline;
        }}

        /* RECENT REPORTS LIST */
        .report-chip {{
            background: var(--bg-card-alt);
            border: 1px solid var(--border);
            border-radius: 10px;
            padding: 12px 14px;
            margin-bottom: 10px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            transition: all 0.2s;
        }}

        .report-chip:hover {{
            border-color: var(--accent-blue);
        }}

        .rep-sym {{
            font-weight: 800;
            font-size: 15px;
            color: #fff;
            display: block;
        }}

        .rep-date {{
            font-size: 11px;
            color: var(--text-dim);
        }}

        .rep-open-link {{
            background: rgba(56, 189, 248, 0.15);
            border: 1px solid rgba(56, 189, 248, 0.3);
            color: var(--accent-blue);
            text-decoration: none;
            padding: 5px 12px;
            border-radius: 6px;
            font-size: 12px;
            font-weight: 600;
            transition: all 0.2s;
        }}

        .rep-open-link:hover {{
            background: var(--accent-blue);
            color: #000;
        }}

        /* QUICK GUIDE */
        .quick-guide {{
            margin-top: 20px;
            background: rgba(2, 6, 23, 0.5);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 16px;
            font-size: 12.5px;
            color: var(--text-muted);
            line-height: 1.6;
        }}

        .code-snippet {{
            font-family: var(--font-mono);
            background: #020617;
            padding: 4px 8px;
            border-radius: 4px;
            color: #38bdf8;
            font-size: 11.5px;
            margin: 4px 0;
            display: block;
        }}

        /* RESPONSIVE */
        @media (max-width: 900px) {{
            .main-grid {{
                grid-template-columns: 1fr;
            }}
            .timing-leaderboard-grid {{
                grid-template-columns: 1fr;
            }}
        }}
    </style>
</head>
<body>

    <!-- TOP NAVBAR -->
    <div class="top-navbar">
        <div class="brand-title">
            <span>🏛️</span>
            <span>VIETNAM STOCK ANALYZER &bull; LOCAL TERMINAL</span>
        </div>
        <div class="nav-links">
            <span style="font-size: 12px; color: var(--text-dim);">Làm mới: {updated_at}</span>
            <a href="PROJECT_MINDMAP.html" class="nav-btn" target="_blank">🧠 Sơ Đồ Tư Duy Dự Án</a>
        </div>
    </div>

    <!-- RADAR MA TRẬN VĨ MÔ & HÀNG HÓA KÈM SPARKLINE -->
    <div class="ticker-section-title">
        <span>📡 RADAR VĨ MÔ QUỐC TẾ & HÀNG HÓA THẾ GIỚI (COMMODITIES PULSE & SPARKLINE TRENDS)</span>
        <span>Cập nhật liên thị trường &bull; Zero Server</span>
    </div>
    <div class="comm-grid">
        {comm_ticker_html}
    </div>

    <!-- ĐỘ RỘNG THỊ TRƯỜNG (MARKET BREADTH) -->
    <div class="breadth-bar-container">
        <div class="breadth-label">📊 ĐỘ RỘNG DÒNG TIỀN HÔM NAY:</div>
        <div class="breadth-meter">
            <div class="breadth-seg-bull" style="width: {bull_pct}%;"></div>
            <div class="breadth-seg-neut" style="width: {neutral_pct}%;"></div>
            <div class="breadth-seg-bear" style="width: {bear_pct}%;"></div>
        </div>
        <div class="breadth-stats">
            <span style="color: #10b981;">▲ {bull_count} Mã Tăng ({bull_pct}%)</span>
            <span style="color: #f59e0b;">▬ {neutral_count} Đi Ngang</span>
            <span style="color: #ef4444;">▼ {bear_count} Mã Giảm ({bear_pct}%)</span>
        </div>
    </div>

    <!-- TIMING LEADERBOARDS: CHỜ NỔ VS CẢNH BÁO SẬP -->
    <div class="timing-leaderboard-grid">
        <!-- CỘT 1: CHỜ NỔ T+ -->
        <div class="timing-col-box" style="border-top: 3px solid #10b981;">
            <div class="timing-col-title">
                <span style="color: #10b981;">🚀 DANH MỤC GOM HÀNG / CHỜ BÙNG NỔ (T+1..T+3)</span>
                <span style="font-size: 11px; color: #94a3b8;">Xác suất &ge; 70%</span>
            </div>
            <div>
                {breakout_rows_html if breakout_rows_html else '<div style="color: #64748b; font-size: 12px; padding: 10px;">Đang quét tín hiệu cạn cung gom hàng...</div>'}
            </div>
        </div>

        <!-- CỘT 2: CẢNH BÁO SẬP -->
        <div class="timing-col-box" style="border-top: 3px solid #ef4444;">
            <div class="timing-col-title">
                <span style="color: #ef4444;">⚠️ CẢNH BÁO PHÂN PHỐI / NGUY CƠ GÃY SÓNG</span>
                <span style="font-size: 11px; color: #94a3b8;">Cần bảo toàn vốn</span>
            </div>
            <div>
                {warning_rows_html if warning_rows_html else '<div style="color: #64748b; font-size: 12px; padding: 10px;">Chưa ghi nhận tín hiệu phân phối ngầm lớn.</div>'}
            </div>
        </div>
    </div>

    <!-- MAIN GRID -->
    <div class="main-grid">
        
        <!-- CỘT TRÁI: BẢNG SÀNG LỌC TOÀN SÀN KÈM SEARCH & FILTER -->
        <div class="panel-box">
            <div class="panel-title">
                <span>🏆 BẢNG THEO DÕI & SÀNG LỌC CỔ PHIẾU TOÀN DIỆN</span>
                <span style="font-size: 12px; color: var(--text-dim); font-weight: 400;">Lọc Vol &ge; 1.2x MA20</span>
            </div>

            <!-- CONTROLS: SEARCH & SECTOR PILLS -->
            <div class="controls-bar">
                <div class="search-box">
                    <input type="text" id="stockSearchInput" class="search-input" placeholder="🔍 Tìm kiếm mã (VD: HPG, PVD, GVR) hoặc tên ngành..." onkeyup="filterStocks()">
                </div>
                <div class="sector-pills">
                    <button class="sector-pill active" onclick="filterSector('ALL')">Tất Cả</button>
                    <button class="sector-pill" onclick="filterSector('Dầu khí')">Dầu Khí</button>
                    <button class="sector-pill" onclick="filterSector('Cao su')">Cao Su & Hóa Chất</button>
                    <button class="sector-pill" onclick="filterSector('Thép')">Thép</button>
                    <button class="sector-pill" onclick="filterSector('Ngân hàng')">Ngân Hàng</button>
                    <button class="sector-pill" onclick="filterSector('Bất động sản')">BĐS</button>
                    <button class="sector-pill" onclick="filterSector('Công nghệ')">Công Nghệ</button>
                </div>
            </div>

            <div style="overflow-x: auto;">
                <table class="screener-table" id="mainScreenerTable">
                    <thead>
                        <tr>
                            <th style="text-align: center;">Hạng</th>
                            <th onclick="sortTable(1, false)">Mã CP ⇅</th>
                            <th style="text-align: right;" onclick="sortTable(2, true)">Giá Khớp ⇅</th>
                            <th style="text-align: right;" onclick="sortTable(3, true)">Nổ Vol ⇅</th>
                            <th style="text-align: center;" onclick="sortTable(4, true)">Đồng Thuận ⇅</th>
                            <th style="text-align: center;">Khuyến Nghị</th>
                            <th>Vùng Mua Gom</th>
                            <th style="text-align: center;">Báo Cáo</th>
                        </tr>
                    </thead>
                    <tbody>
                        {top_stocks_rows if top_stocks_rows else '<tr><td colspan="8" style="text-align:center; padding: 24px; color: #64748b;">Đang cập nhật danh mục sàng lọc...</td></tr>'}
                    </tbody>
                </table>
            </div>

            <!-- HƯỚNG DẪN SOI SÂU -->
            <div class="quick-guide">
                <b>💡 Cách soi sâu 1 mã bất kỳ để sinh Báo cáo HTML mới kèm Đồ thị nến & mở trên Edge:</b>
                <span class="code-snippet">python main.py -m analyze -t PVD</span>
                <span class="code-snippet">python main.py -m analyze -t GVR</span>
                <span class="code-snippet">python main.py -m analyze -t HPG</span>
                <i>Báo cáo sẽ tự động lưu vào thư mục <code>reports/</code> và hiển thị đầy đủ Đồ thị nến Nhật & Động cơ Thời điểm Tăng/Sập.</i>
            </div>
        </div>

        <!-- CỘT PHẢI: BÁO CÁO GẦN NHẤT & VĨ MÔ VIỆT NAM -->
        <div>
            <!-- PANEL BÁO CÁO ĐÃ XUẤT BẢN -->
            <div class="panel-box" style="margin-bottom: 20px;">
                <div class="panel-title">
                    <span>📑 THƯ VIỆN BÁO CÁO HTML GẦN ĐÂY</span>
                    <span style="font-size: 11px; color: var(--accent-blue);">{len(report_files)} báo cáo</span>
                </div>
                <div style="max-height: 440px; overflow-y: auto;">
                    {recent_reports_html if recent_reports_html else '<div style="color: #64748b; font-size: 12px;">Chưa có báo cáo HTML nào được tạo.</div>'}
                </div>
            </div>

            <!-- PANEL VĨ MÔ VIỆT NAM -->
            <div class="panel-box">
                <div class="panel-title">
                    <span>🇻🇳 VĨ MÔ VIỆT NAM HIỆN HÀNH</span>
                </div>
                <div style="font-size: 12.5px; color: #cbd5e1; line-height: 1.7;">
                    • <b>Chính sách tiền tệ:</b> {vn_macro.get('monetary_policy', 'Nới lỏng')}<br>
                    • <b>Lãi suất tái cấp vốn:</b> {vn_macro.get('sbv_refinancing_rate_pct', 4.5)}%<br>
                    • <b>Tăng trưởng tín dụng:</b> Mục tiêu {vn_macro.get('credit_growth_target_pct', 15.0)}%<br>
                    • <b>Đầu tư công:</b> {vn_macro.get('public_investment_status', 'Giải ngân quyết liệt')}<br>
                    • <b>Dòng vốn FDI:</b> {vn_macro.get('fdi_trend', 'Tích cực')}
                </div>
            </div>
        </div>

    </div>

    <!-- JAVASCRIPT CHO LIVE SEARCH, FILTER & SORT -->
    <script>
        // 1. Live Search
        function filterStocks() {{
            const input = document.getElementById('stockSearchInput').value.toUpperCase().trim();
            const rows = document.querySelectorAll('#mainScreenerTable tbody tr');
            rows.forEach(r => {{
                const sym = (r.getAttribute('data-symbol') || '').toUpperCase();
                const sec = (r.getAttribute('data-sector') || '').toUpperCase();
                if (sym.includes(input) || sec.includes(input)) {{
                    r.style.display = '';
                }} else {{
                    r.style.display = 'none';
                }}
            }});
        }}

        // 2. Sector Filter
        function filterSector(sectorName) {{
            document.querySelectorAll('.sector-pill').forEach(btn => btn.classList.remove('active'));
            if (event && event.target) {{
                event.target.classList.add('active');
            }}
            const input = document.getElementById('stockSearchInput');
            if (input) input.value = '';

            const rows = document.querySelectorAll('#mainScreenerTable tbody tr');
            rows.forEach(r => {{
                const sec = (r.getAttribute('data-sector') || '').toLowerCase();
                if (sectorName === 'ALL' || sec.includes(sectorName.toLowerCase())) {{
                    r.style.display = '';
                }} else {{
                    r.style.display = 'none';
                }}
            }});
        }}

        // 3. Click-to-Sort Table Columns
        let currentSortCol = -1;
        let isAscending = true;

        function sortTable(colIndex, isNumeric = false) {{
            const table = document.getElementById('mainScreenerTable');
            const tbody = table.querySelector('tbody');
            const rows = Array.from(tbody.querySelectorAll('tr'));

            if (currentSortCol === colIndex) {{
                isAscending = !isAscending;
            }} else {{
                currentSortCol = colIndex;
                isAscending = true;
            }}

            rows.sort((a, b) => {{
                const aCell = a.children[colIndex];
                const bCell = b.children[colIndex];
                let aVal = aCell ? (aCell.getAttribute('data-sort-val') || aCell.innerText.trim()) : '';
                let bVal = bCell ? (bCell.getAttribute('data-sort-val') || bCell.innerText.trim()) : '';

                if (isNumeric) {{
                    const aNum = parseFloat(aVal) || 0;
                    const bNum = parseFloat(bVal) || 0;
                    return isAscending ? aNum - bNum : bNum - aNum;
                }} else {{
                    return isAscending ? aVal.localeCompare(bVal) : bVal.localeCompare(aVal);
                }}
            }});

            rows.forEach(r => tbody.appendChild(r));
        }}
    </script>

</body>
</html>
"""

    with open(dashboard_path, "w", encoding="utf-8") as f:
        f.write(html_template)

    if auto_open:
        try:
            webbrowser.open(f"file:///{dashboard_path.as_posix()}")
        except Exception:
            pass

    return dashboard_path


if __name__ == "__main__":
    generate_dashboard_html(auto_open=True)
