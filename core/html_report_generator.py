# -*- coding: utf-8 -*-
"""
Module Sinh Báo Cáo Phân Tích Dạng HTML Trực Quan (Standalone Responsive HTML Report Generator)
PHIÊN BẢN TÁI THIẾT TOÀN DIỆN (FULL-OUTPUT ENFORCEMENT & HIGH-END FINTECH ARCHITECTURE)
Tích hợp 100% nội dung từ Hội đồng Tham mưu Đầu tư TTCK Việt Nam (AGENTS.md):
  1. Header Điều hành & Kết luận một dòng (Khuyến nghị + Độ tin cậy + Lý do cô đọng)
  2. Bảng Ma trận 5 Trường phái Đầu tư & Khối Va chạm Góc nhìn Lớn nhất (Conflict Spotlight)
  3. Phân tích Cơ bản Chuyên sâu (FA Deep-Dive):
     - Bảng BCTC & Dòng tiền theo từng quý (Doanh thu, LNST, CFO, CapEx, FCF)
     - Bóc tách Chất lượng Lợi nhuận & Tiền thật (CFO vs LNST, FCF)
     - Kiểm toán Bảng cân đối & Radar tài sản (Tiền mặt, Phải thu, Tồn kho, Nợ vay, BVPS, P/B, F-Score, Altman Z)
     - Mô hình kinh doanh cốt lõi & Danh mục dự án trọng điểm
     - Quản trị Doanh nghiệp, Cổ đông, Cam kết Lãnh đạo (Skin in the game) & Radar Hệ sinh thái
  4. Phân tích Kỹ thuật Chuyên sâu (TA Deep-Dive):
     - Đồ thị Nến Nhật tương tác (Lightweight Charts) + SVG Offline Fallback
     - Bảng Chỉ báo Kỹ thuật Chi tiết Đầy đủ: EMA20, EMA50, SMA200, 52w High/Low, RSI, MACD, Volume vs MA20, Hỗ trợ/Kháng cự
     - Phương pháp Wyckoff VSA (Pha tích lũy, tín hiệu nến No Supply/Shakeout/SOS, Smart Money)
     - Phương pháp CANSLIM & Mark Minervini (Trend Template, VCP Contractions)
     - Mốc Fibonacci Retracement & Vùng cung kẹp hàng đỉnh cũ (Overhead Supply)
  5. Động cơ Thời điểm Tăng/Sập (Timing Matrix & Price Ladder Widget)
  6. Kế hoạch Giao dịch Chuẩn mực (Chiến lược Giá trị vs Lướt sóng Ngắn hạn)
  7. Dự phóng 3 Kịch bản (Cơ sở, Tiêu cực, Tích cực) & Điều kiện Mất hiệu lực Luận điểm
  8. Dữ kiện Còn thiếu Cần Kiểm tra Thêm (Missing Data Audit)
  9. Bàn tròn Hỏi đáp Trực tiếp Hội đồng AI (Interactive Q&A) & Sổ tay Thuật ngữ Tài chính (Glossary)
100% Tiếng Việt chuẩn mực, thuật ngữ tài chính minh bạch, độc lập và bảo vệ vốn nhà đầu tư.
"""

import json
import math
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
import numpy as np
import pandas as pd

from config import REPORTS_DIR


def format_vnd_human(val: Any, unit: str = "đ") -> str:
    """Định dạng số tiền lớn thành dạng dễ đọc: tỷ đ, triệu đ."""
    if val is None or pd.isna(val):
        return "N/A"
    try:
        v = float(val)
    except (ValueError, TypeError):
        return str(val)

    sign = "-" if v < 0 else ""
    abs_v = abs(v)

    if abs_v >= 1e12:
        return f"{sign}{abs_v / 1e12:,.2f} nghìn tỷ {unit}"
    elif abs_v >= 1e9:
        return f"{sign}{abs_v / 1e9:,.2f} tỷ {unit}"
    elif abs_v >= 1e6:
        return f"{sign}{abs_v / 1e6:,.1f} triệu {unit}"
    else:
        return f"{v:,.0f} {unit}"


def render_offline_cashflow_svg(quarters: list, np_data: list, cfo_data: list, fcf_data: list) -> str:
    """Sinh biểu đồ SVG thuần so sánh Dòng tiền thật CFO vs LNST khi không có internet."""
    if not quarters:
        quarters = ["Q3", "Q4", "Q1", "Q2"]
        np_data = [0, 0, 0, 0]
        cfo_data = [0, 0, 0, 0]
        fcf_data = [0, 0, 0, 0]

    all_vals = np_data + cfo_data + fcf_data
    min_val = min(all_vals) if all_vals else 0
    max_val = max(all_vals) if all_vals else 100
    if min_val > 0:
        min_val = 0
    if max_val < 0:
        max_val = 0
    range_val = (max_val - min_val) if (max_val - min_val) != 0 else 1.0

    svg_w, svg_h = 560, 260
    pad_l, pad_r, pad_t, pad_b = 60, 20, 30, 45
    plot_w = svg_w - pad_l - pad_r
    plot_h = svg_h - pad_t - pad_b

    zero_y = pad_t + plot_h * (max_val / range_val)

    bars_svg = ""
    fcf_points = []
    n_q = len(quarters)
    col_w = plot_w / n_q

    for i, q in enumerate(quarters):
        cx = pad_l + i * col_w + col_w / 2
        np_v = np_data[i]
        cfo_v = cfo_data[i]
        fcf_v = fcf_data[i]

        bw = min(22.0, col_w * 0.28)
        
        # Cột LNST (Xanh dương)
        np_y = pad_t + plot_h * ((max_val - np_v) / range_val)
        b_top = min(np_y, zero_y)
        b_height = abs(np_y - zero_y)
        bars_svg += f'<rect x="{cx - bw - 2:.1f}" y="{b_top:.1f}" width="{bw:.1f}" height="{max(2.0, b_height):.1f}" rx="3" fill="#38bdf8" opacity="0.85"/>'

        # Cột CFO (Xanh lá / Đỏ nếu âm)
        cfo_y = pad_t + plot_h * ((max_val - cfo_v) / range_val)
        c_top = min(cfo_y, zero_y)
        c_height = abs(cfo_y - zero_y)
        c_col = "#34d399" if cfo_v >= 0 else "#f87171"
        bars_svg += f'<rect x="{cx + 2:.1f}" y="{c_top:.1f}" width="{bw:.1f}" height="{max(2.0, c_height):.1f}" rx="3" fill="{c_col}" opacity="0.85"/>'

        # Điểm FCF (Vàng)
        f_y = pad_t + plot_h * ((max_val - fcf_v) / range_val)
        fcf_points.append(f"{cx:.1f},{f_y:.1f}")
        bars_svg += f'<circle cx="{cx:.1f}" cy="{f_y:.1f}" r="4" fill="#fbbf24" stroke="#0f172a" stroke-width="1.5"/>'

        # Nhãn Quý
        bars_svg += f'<text x="{cx:.1f}" y="{svg_h - 12}" fill="#94a3b8" font-size="11" font-weight="600" text-anchor="middle">{q}</text>'

    line_svg = ""
    if len(fcf_points) > 1:
        pts = " ".join(fcf_points)
        line_svg = f'<polyline fill="none" stroke="#fbbf24" stroke-width="2.5" stroke-dasharray="4,2" points="{pts}"/>'

    return f"""<svg width="100%" height="240" viewBox="0 0 {svg_w} {svg_h}" xmlns="http://www.w3.org/2000/svg" style="background: rgba(10, 14, 23, 0.6); border-radius: 10px; font-family: -apple-system, sans-serif;">
        <!-- Lưới trục Zero -->
        <line x1="{pad_l}" y1="{zero_y:.1f}" x2="{svg_w - pad_r}" y2="{zero_y:.1f}" stroke="#475569" stroke-width="1.5" stroke-dasharray="2,2"/>
        <text x="{pad_l - 8}" y="{zero_y + 4:.1f}" fill="#94a3b8" font-size="10" text-anchor="end">0 tỷ</text>
        <text x="{pad_l - 8}" y="{pad_t + 10}" fill="#38bdf8" font-size="10" text-anchor="end">{max_val:,.0f} tỷ</text>
        <text x="{pad_l - 8}" y="{svg_h - pad_b}" fill="#f87171" font-size="10" text-anchor="end">{min_val:,.0f} tỷ</text>
        {bars_svg}
        {line_svg}
    </svg>"""


def render_offline_candles_svg(candles: list) -> str:
    """Sinh biểu đồ nến SVG đẹp mắt khi không có kết nối internet."""
    if not candles:
        return '<div style="text-align:center;padding:40px;color:#64748b;">Đang tải chuỗi dữ liệu nến...</div>'

    subset = candles[-45:] if len(candles) >= 45 else candles
    highs = [float(c["high"]) for c in subset]
    lows = [float(c["low"]) for c in subset]
    min_p = min(lows) if lows else 1.0
    max_p = max(highs) if highs else 10.0
    p_range = (max_p - min_p) if (max_p - min_p) != 0 else 1.0

    svg_w, svg_h = 740, 320
    pad_l, pad_r, pad_t, pad_b = 60, 20, 25, 30
    plot_w = svg_w - pad_l - pad_r
    plot_h = svg_h - pad_t - pad_b

    n_c = len(subset)
    slot_w = plot_w / n_c
    candle_w = max(3.0, slot_w * 0.65)

    svg_elements = []
    for i, c in enumerate(subset):
        cx = pad_l + i * slot_w + slot_w / 2
        op = float(c["open"])
        hi = float(c["high"])
        lo = float(c["low"])
        cl = float(c["close"])

        is_green = cl >= op
        col = "#10b981" if is_green else "#ef4444"

        hi_y = pad_t + plot_h * ((max_p - hi) / p_range)
        lo_y = pad_t + plot_h * ((max_p - lo) / p_range)
        op_y = pad_t + plot_h * ((max_p - op) / p_range)
        cl_y = pad_t + plot_h * ((max_p - cl) / p_range)

        # Bóng nến (Wick)
        svg_elements.append(f'<line x1="{cx:.1f}" y1="{hi_y:.1f}" x2="{cx:.1f}" y2="{lo_y:.1f}" stroke="{col}" stroke-width="1.2"/>')

        # Thân nến (Body)
        body_top = min(op_y, cl_y)
        body_h = max(2.0, abs(op_y - cl_y))
        svg_elements.append(f'<rect x="{cx - candle_w / 2:.1f}" y="{body_top:.1f}" width="{candle_w:.1f}" height="{body_h:.1f}" fill="{col}" rx="1"/>')

    candles_code = "".join(svg_elements)
    return f"""<svg width="100%" height="320" viewBox="0 0 {svg_w} {svg_h}" xmlns="http://www.w3.org/2000/svg" style="background: #070c16; border-radius: 10px; font-family: -apple-system, sans-serif;">
        <!-- Trục giá Min/Max -->
        <text x="{pad_l - 8}" y="{pad_t + 10}" fill="#94a3b8" font-size="10" text-anchor="end">{max_p:,.0f} đ</text>
        <text x="{pad_l - 8}" y="{svg_h - pad_b}" fill="#94a3b8" font-size="10" text-anchor="end">{min_p:,.0f} đ</text>
        <line x1="{pad_l}" y1="{pad_t}" x2="{svg_w - pad_r}" y2="{pad_t}" stroke="rgba(255,255,255,0.05)" stroke-width="1"/>
        <line x1="{pad_l}" y1="{svg_h - pad_b}" x2="{svg_w - pad_r}" y2="{svg_h - pad_b}" stroke="rgba(255,255,255,0.05)" stroke-width="1"/>
        {candles_code}
    </svg>"""


def build_macro_impact_matrix(symbol: str, sector_name: str, global_comm: Dict[str, Any]) -> str:
    """Phân tích tương quan chuyên sâu của 6 yếu tố vĩ mô và hàng hóa thế giới tới cổ phiếu."""
    sym = symbol.upper().strip()
    sec_lower = (sector_name or "").lower()

    brent = global_comm.get("crude_oil_brent", {"value": 78.5, "change_pct": 2.8})
    gold_sjc = global_comm.get("gold_sjc", {"value": 84.5, "change_pct": 0.6})
    rubber = global_comm.get("rubber_tsr20", {"value": 204.5, "change_pct": 4.2})
    steel = global_comm.get("steel_hrc", {"value": 545.0, "change_pct": 1.8})
    fed = global_comm.get("fed_funds_rate", {"value": 4.88, "trend": "Nới lỏng"})
    fx = global_comm.get("usd_vnd", {"value": 25380, "change_pct": 0.3})

    factors = []

    # 1. Nhóm ngành chính
    is_re = any(k in sec_lower for k in ["bất động sản", "địa ốc", "real estate", "nhà ở", "nghỉ dưỡng"]) or sym in ["VHM", "NVL", "PDR", "DIG", "CEO", "DXG", "KDH", "NLG", "IDJ"]
    is_bank = any(k in sec_lower for k in ["ngân hàng", "tài chính", "chứng khoán", "bảo hiểm", "bank"]) or sym in ["VCB", "TCB", "MBB", "ACB", "BID", "CTG", "VPB", "HDB", "SSI", "VND", "VCI", "HCM", "APS"]
    is_oil = any(k in sec_lower for k in ["dầu khí", "oil", "gas", "năng lượng"]) or sym in ["PVD", "PVS", "BSR", "GAS", "PLX", "POW", "GEG"]
    is_steel = any(k in sec_lower for k in ["thép", "kim loại", "vật liệu"]) or sym in ["HPG", "HSG", "NKG"]
    is_retail = any(k in sec_lower for k in ["bán lẻ", "tiêu dùng", "vàng", "trang sức", "retail"]) or sym in ["PNJ", "MWG", "FRT", "DGW", "MSN"]
    is_rubber = any(k in sec_lower for k in ["cao su", "nông nghiệp"]) or sym in ["GVR", "PHR", "DPR", "DRI"]

    # 1. Yếu tố Lãi suất / Tín dụng theo ngành
    if is_re:
        factors.append({
            "name": "🏛️ Lãi Suất & Tín Dụng Bất Động Sản",
            "stat": f"{fed.get('value')}% Fed Rate • Chu kỳ nới lỏng tiền tệ",
            "stat_color": "#34d399",
            "direction": "TÍCH CỰC DÒNG TIỀN 🟢",
            "dir_badge": "background: rgba(16, 185, 129, 0.15); color: #34d399; border: 1px solid #10b981;",
            "sensitivity": "Rất cao (Bậc 1) • Độ trễ: 1-2 quý",
            "impact_analysis": f"Mặt bằng lãi suất vay mua nhà giảm giúp kích thích thanh khoản giao dịch và tháo gỡ áp lực chi phí tài chính cho {sym}."
        })
    elif is_bank:
        factors.append({
            "name": "🏛️ Tăng Trưởng Tín Dụng & NIM Ngân Hàng",
            "stat": f"Tín dụng toàn hệ thống tăng trưởng 14-15% • Chi phí vốn hạ nhiệt",
            "stat_color": "#38bdf8",
            "direction": "THUẬN LỢI TĂNG TRƯỞNG 🟢",
            "dir_badge": "background: rgba(56, 189, 248, 0.15); color: #38bdf8; border: 1px solid #38bdf8;",
            "sensitivity": "Trực tiếp Bậc 1",
            "impact_analysis": "Thanh khoản hệ thống dồi dào, CASA cải thiện giúp tối ưu chi phí huy động và mở rộng biên lãi thuần (NIM)."
        })
    elif is_retail:
        factors.append({
            "name": "🏛️ Sức Mua Nội Địa & Chi Tiêu Tiêu Dùng",
            "stat": f"Tổng mức bán lẻ hàng hóa duy trì đà tăng 8.5 - 9.5% YoY",
            "stat_color": "#34d399",
            "direction": "HƯỞNG LỢI TRỰC TIẾP 🟢",
            "dir_badge": "background: rgba(16, 185, 129, 0.15); color: #34d399; border: 1px solid #10b981;",
            "sensitivity": "Cao • Nhạy cảm với thu nhập khả dụng",
            "impact_analysis": f"Sự phục hồi của thị trường lao động và chi tiêu hộ gia đình thúc đẩy lưu lượng mua sắm tại mạng lưới của {sym}."
        })
    else:
        factors.append({
            "name": "🏛️ Lãi Suất & Tín Dụng Vĩ Mô",
            "stat": f"{fed.get('value')}% Fed Rate • Chu kỳ nới lỏng tiền tệ",
            "stat_color": "#38bdf8",
            "direction": "THUẬN LỢI CHUNG 🟢",
            "dir_badge": "background: rgba(56, 189, 248, 0.15); color: #38bdf8; border: 1px solid #38bdf8;",
            "sensitivity": "Trung bình • Giảm chi phí vốn vay",
            "impact_analysis": "Chu kỳ hạ lãi suất toàn cầu giúp giảm áp lực chi phí tài chính cho doanh nghiệp niêm yết."
        })

    # 2. Hàng hóa đặc thù ngành
    if is_oil:
        factors.append({
            "name": "🛢️ Giá Dầu Thô Brent Thế Giới",
            "stat": f"{brent.get('value')} USD/thùng (▲ +{brent.get('change_pct')}%)",
            "stat_color": "#10b981",
            "direction": "HƯỞNG LỢI TRỰC TIẾP 🟢",
            "dir_badge": "background: rgba(16, 185, 129, 0.15); color: #34d399; border: 1px solid #10b981;",
            "sensitivity": "Trực tiếp Bậc 1",
            "impact_analysis": "Giá dầu neo cao kích hoạt các dự án thăm dò khai thác quy mô lớn (Lô B Ô Môn) và tăng đơn giá dịch vụ kỹ thuật dầu khí."
        })
    elif is_steel:
        factors.append({
            "name": "🏗️ Giá Thép Cuộn Cán Nóng HRC Thế Giới",
            "stat": f"{steel.get('value')} USD/tấn (Biến động: {steel.get('change_pct'):+.1f}%)",
            "stat_color": "#38bdf8",
            "direction": "TÁC ĐỘNG TRỰC TIẾP 🟢",
            "dir_badge": "background: rgba(56, 189, 248, 0.15); color: #38bdf8; border: 1px solid #38bdf8;",
            "sensitivity": "Trực tiếp Bậc 1 • Chi phối biên lãi gộp",
            "impact_analysis": "Diễn biến giá thép thế giới và các biện pháp phòng vệ thương mại tác động trực tiếp tới giá bán và sản lượng tiêu thụ."
        })
    elif is_rubber:
        factors.append({
            "name": "🌲 Giá Cao Su Tự Nhiên TSR20 Thế Giới",
            "stat": f"{rubber.get('value')} US Cents/kg (▲ +{rubber.get('change_pct')}%)",
            "stat_color": "#10b981",
            "direction": "HƯỞNG LỢI TRỰC TIẾP 🟢",
            "dir_badge": "background: rgba(16, 185, 129, 0.15); color: #34d399; border: 1px solid #10b981;",
            "sensitivity": "Trực tiếp Bậc 1",
            "impact_analysis": "Giá mủ cao su thế giới neo cao giúp mở rộng biên lợi nhuận mảng khai thác mủ tự nhiên."
        })
    elif sym == "PNJ" or "vàng" in sec_lower:
        factors.append({
            "name": "🥇 Giá Vàng Thế Giới & Chênh Lệch Vàng SJC",
            "stat": f"{gold_sjc.get('value')} triệu đ/lượng (▲ +{gold_sjc.get('change_pct')}%)",
            "stat_color": "#fbbf24",
            "direction": "CẦN THEO DÕI 🟡",
            "dir_badge": "background: rgba(245, 158, 11, 0.15); color: #fbbf24; border: 1px solid #f59e0b;",
            "sensitivity": "Rất cao • Tác động giá vốn hàng tồn kho",
            "impact_analysis": "Giá vàng biến động mạnh kích thích nhu cầu tích trữ vàng 24K nhưng tạo rủi ro định giá vốn tồn kho trang sức."
        })
    else:
        factors.append({
            "name": "🛢️ Giá Dầu Thô Brent & Năng Lượng Toàn Cầu",
            "stat": f"{brent.get('value')} USD/thùng",
            "stat_color": "#94a3b8",
            "direction": "GIÁN TIẾP 🟡",
            "dir_badge": "background: rgba(148, 163, 184, 0.15); color: #cbd5e1; border: 1px solid #64748b;",
            "sensitivity": "Thấp • Tác động qua chi phí logistics và lạm phát",
            "impact_analysis": "Giá dầu ổn định giúp kiềm chế lạm phát chi phí đầu vào và chi phí logistics."
        })

    # 3. Tỷ giá USD/VND
    factors.append({
        "name": "💵 Tỷ Giá USD/VND & Dòng Vốn Ngoại",
        "stat": f"{fx.get('value'):,} VND (Biến động: {fx.get('change_pct'):+.1f}%)",
        "stat_color": "#fbbf24",
        "direction": "CẦN THEO DÕI 🟡",
        "dir_badge": "background: rgba(245, 158, 11, 0.15); color: #fbbf24; border: 1px solid #f59e0b;",
        "sensitivity": "Toàn thị trường",
        "impact_analysis": "Tỷ giá ổn định tạo dư địa cho chính sách tiền tệ nới lỏng nội địa và giảm áp lực bán ròng của khối ngoại."
    })

    rows_html = ""
    for f in factors:
        rows_html += f"""
        <div style="background: rgba(15, 23, 42, 0.65); border: 1px solid var(--border); border-radius: 12px; padding: 14px 16px; margin-bottom: 10px;">
            <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px; margin-bottom: 8px;">
                <div style="font-weight: 700; color: #fff; font-size: 0.95rem;">{f['name']}</div>
                <div style="display: flex; align-items: center; gap: 8px;">
                    <span style="font-size: 0.85rem; font-weight: 700; color: {f['stat_color']};">{f['stat']}</span>
                    <span class="badge" style="{f['dir_badge']} font-size: 0.72rem;">{f['direction']}</span>
                </div>
            </div>
            <div style="font-size: 0.85rem; color: #cbd5e1; line-height: 1.6;">
                <span style="color: #38bdf8; font-weight: 600;">Mức độ nhạy cảm:</span> {f['sensitivity']}<br>
                <span style="color: #94a3b8; font-weight: 600;">Cơ chế tác động:</span> {f['impact_analysis']}
            </div>
        </div>
        """

    return f"""
    <div style="margin-top: 14px;">
        <div style="font-size: 0.85rem; font-weight: 700; color: #38bdf8; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 10px;">
            🔎 Phân tích Chi tiết Tương quan Vĩ mô & Hàng hóa Thế giới:
        </div>
        {rows_html}
    </div>
    """


def build_smart_money_and_catalyst_html(timing_result: Optional[Dict[str, Any]]) -> str:
    """Tạo khối Dòng tiền Khớp lệnh Chủ động & Lịch Xúc tác Sự kiện."""
    if not timing_result:
        return ""

    pulse = timing_result.get("smart_money_pulse", {})
    catalysts = timing_result.get("catalysts_timeline", [])

    active_buy_pct = float(pulse.get("active_buy_pct", 50.0))
    active_sell_pct = float(pulse.get("active_sell_pct", 50.0))
    pulse_verdict = pulse.get("pulse_verdict", "Cung cầu cân bằng")
    large_order_bias = pulse.get("large_order_bias", "Trung lập")

    cat_items = ""
    for cat in catalysts[:4]:
        flag_col = "#34d399" if cat.get("impact") == "POSITIVE" else ("#f87171" if cat.get("impact") == "NEGATIVE" else "#fbbf24")
        cat_items += f"""
        <div style="display: flex; gap: 12px; align-items: flex-start; margin-bottom: 8px; font-size: 0.85rem;">
            <span style="color: #94a3b8; font-family: monospace; font-size: 0.8rem; white-space: nowrap;">[{cat.get('time_window', 'Ngắn hạn')}]</span>
            <div style="color: #cbd5e1; flex: 1;">
                <b style="color: {flag_col};">{cat.get('event', '')}</b>: {cat.get('expected_impact', '')}
            </div>
        </div>
        """

    if not cat_items:
        cat_items = '<div style="font-size: 0.84rem; color: #94a3b8;">Chưa ghi nhận sự kiện xúc tác đột biến trong 30 ngày tới.</div>'

    return f"""
    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 14px; margin-bottom: 18px;">
        <!-- Box 1: Khớp lệnh Chủ động (Pulse) -->
        <div style="background: rgba(15, 23, 42, 0.7); border: 1px solid rgba(56, 189, 248, 0.2); border-radius: 12px; padding: 14px 16px;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                <span style="font-size: 0.85rem; font-weight: 700; color: #38bdf8;">⚡ TỶ LỆ KHỚP LỆNH CHỦ ĐỘNG (REALTIME PULSE)</span>
                <span class="badge" style="background: rgba(56, 189, 248, 0.15); color: #38bdf8;">{large_order_bias}</span>
            </div>
            <div style="display: flex; justify-content: space-between; font-size: 0.82rem; margin-bottom: 4px;">
                <span style="color: #34d399; font-weight: 700;">Mua chủ động: {active_buy_pct:.1f}%</span>
                <span style="color: #f87171; font-weight: 700;">Bán chủ động: {active_sell_pct:.1f}%</span>
            </div>
            <div style="height: 8px; background: rgba(239, 68, 68, 0.3); border-radius: 4px; overflow: hidden; display: flex;">
                <div style="width: {active_buy_pct}%; background: #10b981; height: 100%;"></div>
            </div>
            <div style="margin-top: 8px; font-size: 0.82rem; color: #94a3b8;">
                Nhận định: <b style="color: #fff;">{pulse_verdict}</b>
            </div>
        </div>

        <!-- Box 2: Lịch Xúc tác Sự kiện -->
        <div style="background: rgba(15, 23, 42, 0.7); border: 1px solid rgba(245, 158, 11, 0.2); border-radius: 12px; padding: 14px 16px;">
            <div style="font-size: 0.85rem; font-weight: 700; color: #fbbf24; margin-bottom: 10px;">
                📅 LỊCH TRÌNH CHẤT XÚC TÁC & CATALYSTS SẮP DIỄN RA
            </div>
            {cat_items}
        </div>
    </div>
    """


def build_glossary_html() -> str:
    """Sổ tay tra cứu nhanh thuật ngữ tài chính chuẩn xác cho nhà đầu tư."""
    terms = [
        ("CFO (Cash Flow from Operations)", "Dòng tiền thuần từ Hoạt động Kinh doanh", "Tiền mặt thực tế thu về từ bán hàng và cung cấp dịch vụ sau khi trừ chi phí trả tiền mặt. Khác với LNST kế toán (có thể bị 'vẽ' trên giấy qua bán chịu), CFO là 'tiền tươi thóc thật' chảy vào tài khoản ngân hàng."),
        ("FCF (Free Cash Flow)", "Dòng tiền Tự do", "Là số tiền còn dư lại sau khi lấy CFO trừ đi chi phí đầu tư mua sắm tài sản cố định (CapEx). Đây là nguồn tiền thật sự thuộc về cổ đông để chia cổ tức tiền mặt hoặc trả nợ ngân hàng."),
        ("BVPS & Hệ số P/B", "Giá trị sổ sách & Định giá theo Tài sản", "BVPS là giá trị tài sản ròng thuộc về mỗi cổ phiếu sau khi trả hết nợ. P/B thể hiện thị trường đang trả bao nhiêu đồng cho 1 đồng tài sản ròng. P/B < 1.0x nghĩa là thị giá đang chiết khấu so với sổ sách."),
        ("Bẫy Giá Trị (Value Trap)", "Rủi ro mua cổ phiếu rẻ tưởng bở", "Cổ phiếu có P/B hoặc P/E rất thấp nhưng hoạt động kinh doanh thua lỗ triền miên, tài sản đọng ở nợ khó đòi hoặc hàng tồn kho không thanh lý được, khiến giá trị sổ sách liên tục bốc hơi."),
        ("Free-Float & Skin in the Game", "Tỷ lệ Trôi nổi & Cam kết Lãnh đạo", "Free-float là tỷ lệ cổ phiếu trôi nổi tự do ngoài thị trường. Skin in the game là tỷ lệ sở hữu của Ban điều hành; lãnh đạo nắm giữ quá ít cổ phần (<1%) đồng nghĩa với rủi ro bỏ rơi cổ đông nhỏ lẻ khi doanh nghiệp gặp biến cố."),
        ("VCP (Volatility Contraction Pattern)", "Mô hình Thu hẹp Độ biến động", "Mẫu hình kinh điển của Mark Minervini: giá cổ phiếu trải qua các nhịp co thắt biên độ ngày càng hẹp dần kèm khối lượng cạn kiệt trước khi dòng tiền lớn kích hoạt điểm bứt phá (Breakout)."),
        ("VSA (Volume Spread Analysis)", "Phương pháp Phân tích Khối lượng & Chênh lệch giá", "Phương pháp đọc dấu chân của dòng tiền thông minh (Smart Money / Cá mập) qua sự tương quan giữa biên độ nến và khối lượng giao dịch (No Supply Test, Shakeout, SOS, Upthrust)."),
        ("Overhead Supply", "Vùng Cung Kẹp Hàng Đỉnh Cũ", "Lượng cổ phiếu bị kẹp hàng ở vùng giá cao trong quá khứ. Khi giá hồi phục về vùng này, các nhà đầu tư kẹp hàng có xu hướng bán tháo để hòa vốn, tạo nên ngưỡng cản tâm lý rất mạnh.")
    ]

    cards_html = ""
    for code, vi_name, desc in terms:
        cards_html += f"""
        <div style="background: rgba(15, 23, 42, 0.6); border: 1px solid var(--border); border-radius: 12px; padding: 14px 16px;">
            <div style="font-weight: 700; color: #38bdf8; font-size: 0.9rem; margin-bottom: 2px;">{code}</div>
            <div style="font-size: 0.8rem; color: #fbbf24; font-weight: 600; margin-bottom: 6px;">{vi_name}</div>
            <div style="font-size: 0.83rem; color: #cbd5e1; line-height: 1.5;">{desc}</div>
        </div>
        """

    return f"""
    <div id="sec-glossary" style="margin-top: 36px; background: rgba(10, 14, 23, 0.8); border: 1px solid var(--border); border-radius: 16px; padding: 22px;">
        <div class="section-title" style="margin: 0 0 16px 0;">📚 SỔ TAY TRA CỨU NHANH THUẬT NGỮ TÀI CHÍNH (FINANCIAL GLOSSARY)</div>
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 14px;">
            {cards_html}
        </div>
    </div>
    """


def build_interactive_council_qa_html(
    symbol: str,
    current_price: float,
    fair_price: float,
    stop_loss: float,
    sl_pct: float,
    tp1: float,
    tp1_pct: float,
    trigger_pivot: float,
    cfo_human: str,
    fcf_human: str,
    pb: float,
    bvps: float,
    active_buy_pct: float
) -> str:
    """Tạo bảng Hỏi Đáp Tương Tác với Hội đồng AI (Tabs chuyển đổi linh hoạt)."""
    sl_text = f"{stop_loss:,.0f} đ (-{sl_pct:.1f}%)" if stop_loss > 0 else "N/A (Chưa mở vị thế mua)"
    tp_text = f"{tp1:,.0f} đ (+{tp1_pct:.1f}%)" if tp1 > 0 else "N/A"
    fair_text = f"{fair_price:,.0f} đ" if fair_price > 0 else "N/A"
    bvps_text = f"{bvps:,.0f} đ" if bvps > 0 else "N/A"

    qa_list = [
        {
            "id": "qa1",
            "q": "1. Giá hiện tại rẻ hay đắt so với giá trị thực?",
            "a": f"Thị giá {current_price:,.0f} đ so với giá trị sổ sách BVPS ({bvps_text}, P/B {pb:.2f}x) và giá trị thực ước tính ({fair_text}). Tuy nhiên, rẻ không đồng nghĩa với an toàn nếu doanh nghiệp đang thua lỗ và dòng tiền kinh doanh thâm hụt (Bẫy giá trị)."
        },
        {
            "id": "qa2",
            "q": "2. Dòng tiền thật của doanh nghiệp có lành mạnh không?",
            "a": f"Dòng tiền thuần HĐKD (CFO TTM) ghi nhận {cfo_human}, Dòng tiền tự do (FCF TTM) đạt {fcf_human}. Cần theo dõi chặt chẽ liệu tiền mặt bán hàng có chuyển hóa thành dòng tiền kinh doanh dương hay bị đọng vốn ở các khoản phải thu."
        },
        {
            "id": "qa3",
            "q": "3. Kế hoạch cắt lỗ và chốt lời kỷ luật ra sao?",
            "a": f"Ngưỡng cắt lỗ nghiêm ngặt: {sl_text}. Mục tiêu chốt lời ngắn hạn (TP1): {tp_text}. Luôn bảo vệ vốn trước tiên, tuyệt đối không gồng lỗ hay bình quân giá xuống khi vi phạm nguyên tắc bảo vệ tài khoản."
        },
        {
            "id": "qa4",
            "q": "4. Khi nào dòng tiền lớn (Smart Money) xác nhận đảo chiều?",
            "a": f"Cần theo dõi ngưỡng Pivot bứt phá tại {trigger_pivot:,.0f} đ kèm khối lượng giao dịch đột biến tối thiểu gấp 1.3x đến 2.0x mức trung bình 20 phiên, đồng thời tỷ lệ mua chủ động duy trì áp đảo trên 60%."
        }
    ]

    tabs_header = ""
    tabs_content = ""
    for idx, item in enumerate(qa_list):
        active_cls = "qa-tab-active" if idx == 0 else ""
        disp_style = "display: block;" if idx == 0 else "display: none;"
        qid = item["id"]
        qtitle = item["q"]
        qans = item["a"]
        tabs_header += f'<button class="qa-tab-btn {active_cls}" onclick="switchQATab(&quot;{qid}&quot;)">{qtitle}</button>'
        tabs_content += f'<div id="{qid}" class="qa-pane" style="{disp_style}"><div class="qa-answer-box"><span class="qa-speaker">🏛️ Ý kiến Hội đồng:</span> {qans}</div></div>'

    return f"""
    <div id="sec-qa" class="card" style="margin-top: 24px;">
        <div class="card-header">
            <span>💬 BÀN TRÒN HỎI ĐÁP TRỰC TIẾP VỚI HỘI ĐỒNG AI</span>
            <span class="badge" style="background: rgba(56, 189, 248, 0.15); color: #38bdf8;">TƯƠNG TÁC THEO NHU CẦU</span>
        </div>
        <div class="qa-tabs-nav">
            {tabs_header}
        </div>
        <div class="qa-tabs-body">
            {tabs_content}
        </div>
    </div>
    <script>
    function switchQATab(tabId) {{
        document.querySelectorAll('.qa-pane').forEach(el => el.style.display = 'none');
        document.querySelectorAll('.qa-tab-btn').forEach(el => el.classList.remove('qa-tab-active'));
        const target = document.getElementById(tabId);
        if (target) target.style.display = 'block';
        event.currentTarget.classList.add('qa-tab-active');
    }}
    </script>
    """


def build_eli5_html(
    symbol: str,
    quote: Dict[str, Any],
    fa_result: Dict[str, Any],
    ta_result: Dict[str, Any],
    trade_setup: Dict[str, Any]
) -> str:
    """
    Phân hệ 1: 🧒 Giải Thích Cho Đứa Trẻ Lên 5 (ELI5 — Bản Chất Cốt Lõi Là Gì?)
    Quy định chuẩn AGENTS.md: Mộc mạc, hình tượng bằng các ví dụ đời thường.
    """
    sym = symbol.upper()
    comp_name = quote.get("company_name", sym)
    sector_name = fa_result.get("macro", {}).get("sector_name") or quote.get("industry") or "Doanh nghiệp"
    fin = fa_result.get("ratios", {})
    cf = fa_result.get("cash_flow", {})
    asset_val = fa_result.get("asset_valuation", {})
    ind = ta_result.get("indicators", {})
    cfo_ttm = cf.get("cfo_ttm", 0)
    net_p_ttm = fin.get("ttm_profit", 0)
    pb_val = asset_val.get("pb", "N/A")
    rec_val = fin.get("receivables", 0)
    inv_val = fin.get("inventories", 0)
    tot_assets = fin.get("total_assets", 1) or 1
    action = trade_setup.get("action", "QUAN SÁT")

    # 1. Bán cái gì kiếm tiền?
    model_sum = fa_result.get("segments", {}).get("business_model_summary") or quote.get("company_profile")
    if not model_sum or len(model_sum) < 15:
        model_sum = f"{comp_name} hoạt động chính trong lĩnh vực {sector_name}, kiếm tiền bằng việc cung cấp sản phẩm và dịch vụ cốt lõi cho khách hàng."

    # 2. Tiền thật hay tiền trên giấy?
    if cfo_ttm > 0 and (cfo_ttm >= net_p_ttm * 0.8):
        money_verdict = f"Tiền tươi thóc thật! Tiệm bán hàng và thu được tiền mặt thật ({format_vnd_human(cfo_ttm)}), tiền chạy thẳng vào hũ heo đất chứ không phải bán chịu ghi nợ."
        money_color = "#34d399"
    elif cfo_ttm > 0:
        money_verdict = f"Có tiền thật ({format_vnd_human(cfo_ttm)}) nhưng một phần lợi nhuận vẫn đang nằm ở sổ ghi nợ của khách và hàng tồn kho chưa bán được."
        money_color = "#fbbf24"
    else:
        money_verdict = f"Tiền trên giấy! Sổ sách kế toán có thể ghi nhận có lãi hoặc lỗ nhẹ, nhưng két sắt công ty bị hụt tiền mặt (CFO âm {format_vnd_human(abs(cfo_ttm))}), giống như bán chịu cả đống đồ cho khách mà chưa đòi được nợ."
        money_color = "#f87171"

    # 3. Món hời hay bẫy chuột?
    try:
        pb_flt = float(pb_val)
    except Exception:
        pb_flt = 1.0

    if pb_flt < 1.0 and cfo_ttm < 0:
        deal_verdict = f"Cẩn thận bẫy chuột! Giá cổ phiếu nhìn rẻ (P/B {pb_val}x) giống như món đồ giảm giá 70%, nhưng bên trong tiệm đang thiếu tiền mặt và tồn kho khó bán."
        deal_color = "#f87171"
    elif pb_flt < 1.0 and cfo_ttm > 0:
        deal_verdict = f"Cơ hội tài sản giá rẻ! Thị giá đang bán thấp hơn cả giá trị nhà cửa sổ sách (P/B {pb_val}x) trong khi tiệm vẫn kiếm ra tiền mặt đều đặn."
        deal_color = "#34d399"
    elif pb_flt >= 3.0:
        deal_verdict = f"Tiệm hàng hiệu giá cao! Tiệm làm ăn phát đạt nên cổ phiếu được trả giá cao (P/B {pb_val}x), cần chọn đúng lúc giảm giá khuyến mãi mới nên mua."
        deal_color = "#fbbf24"
    else:
        deal_verdict = f"Định giá hợp lý (P/B {pb_val}x), tương xứng với chất lượng tài sản và vị thế của tiệm trên thị trường."
        deal_color = "#38bdf8"

    # 4. Đội lái và cá mập đang làm gì?
    vsa_phase = ta_result.get("vsa", {}).get("phase", "Tích lũy")
    current_p = trade_setup.get("current_price", 0)
    ema20_val = ind.get("ema20", 0)
    if "Đè giá" in vsa_phase or current_p < ema20_val:
        shark_action = "Cá mập và đội lái đang đứng ngoài hoặc tìm cách bán bớt hàng ra ngoài. Chưa thấy dấu hiệu họ gom hàng mạnh mẽ trở lại."
        shark_color = "#f87171"
    elif "Tích lũy" in vsa_phase:
        shark_action = "Cá mập đang lặng lẽ gom hàng như người đi câu cá kiên nhẫn ngồi bên bờ sông, không vội vàng đẩy giá lên ngay."
        shark_color = "#fbbf24"
    else:
        shark_action = "Dòng tiền lớn đang bảo kê và nâng đỡ đường giá, nỗ lực đẩy giá bứt phá qua các vùng cản cũ."
        shark_color = "#34d399"

    # 5. Lời khuyên bỏ heo đất
    if "MUA" in action:
        piggy_advice = f"Có thể trích một phần tiền tiết kiệm trong ống heo (tối đa {trade_setup.get('max_position_size_pct', 10):.0f}% số tiền có) để mua một góc tiệm này, vì tiệm đang có dòng tiền và giá bắt đầu vào nhịp thuận lợi."
        piggy_color = "#34d399"
    elif "THEO DÕI" in action:
        piggy_advice = "Cứ giữ chặt ống heo đất! Đứng xem tiệm giải quyết xong các vấn đề nợ nần hoặc chờ giá ngừng giảm rồi mới tính tiếp."
        piggy_color = "#fbbf24"
    else:
        piggy_advice = "Tuyệt đối không đập heo đất đưa tiền cho tiệm này lúc này! Rủi ro mất tiền rất cao, hãy giữ tiền để tìm tiệm khác an toàn hơn."
        piggy_color = "#f87171"

    return f"""
    <!-- PHÂN HỆ 1: GIẢI THÍCH CHO ĐỨA TRẺ LÊN 5 (ELI5) -->
    <div id="sec-eli5" class="card" style="margin-bottom: 24px; border-left: 4px solid #f59e0b; background: linear-gradient(145deg, #181926, #0e111a);">
        <div class="card-header">
            <span style="display: flex; align-items: center; gap: 8px;">
                <span style="font-size: 1.25rem;">🧒</span> 
                <span style="font-weight: 800; color: #fbbf24;">1. BẢN CHẤT CỐT LÕI (GIẢI THÍCH CHO ĐỨA TRẺ LÊN 5 — ELI5)</span>
            </span>
            <span class="badge" style="background: rgba(245, 158, 11, 0.15); color: #fbbf24; border: 1px solid #f59e0b;">HIỂU ĐÚNG BẢN CHẤT</span>
        </div>
        <div style="font-size: 0.88rem; color: #cbd5e1; line-height: 1.7; margin-bottom: 14px;">
            Trước khi nhìn vào các bảng số liệu tài chính phức tạp, hãy hiểu doanh nghiệp này bằng những ví dụ đời thường nhất:
        </div>
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 14px;">
            <!-- Box 1: Bán gì -->
            <div style="background: rgba(15, 23, 42, 0.65); padding: 14px 16px; border-radius: 12px; border: 1px solid var(--border);">
                <div style="font-size: 0.85rem; font-weight: 700; color: #38bdf8; margin-bottom: 6px;">🏬 1. Tiệm này bán cái gì kiếm tiền?</div>
                <div style="font-size: 0.84rem; color: #cbd5e1; line-height: 1.6;">{model_sum}</div>
            </div>
            <!-- Box 2: Tiền thật hay tiền giấy -->
            <div style="background: rgba(15, 23, 42, 0.65); padding: 14px 16px; border-radius: 12px; border: 1px solid var(--border);">
                <div style="font-size: 0.85rem; font-weight: 700; color: {money_color}; margin-bottom: 6px;">💰 2. Tiền thật hay tiền trên giấy?</div>
                <div style="font-size: 0.84rem; color: #cbd5e1; line-height: 1.6;">{money_verdict}</div>
            </div>
            <!-- Box 3: Món hời hay bẫy chuột -->
            <div style="background: rgba(15, 23, 42, 0.65); padding: 14px 16px; border-radius: 12px; border: 1px solid var(--border);">
                <div style="font-size: 0.85rem; font-weight: 700; color: {deal_color}; margin-bottom: 6px;">🪤 3. Món hời hay chiếc bẫy chuột?</div>
                <div style="font-size: 0.84rem; color: #cbd5e1; line-height: 1.6;">{deal_verdict}</div>
            </div>
            <!-- Box 4: Cá mập và đội lái -->
            <div style="background: rgba(15, 23, 42, 0.65); padding: 14px 16px; border-radius: 12px; border: 1px solid var(--border);">
                <div style="font-size: 0.85rem; font-weight: 700; color: {shark_color}; margin-bottom: 6px;">🦈 4. Đội lái và cá mập đang làm gì?</div>
                <div style="font-size: 0.84rem; color: #cbd5e1; line-height: 1.6;">{shark_action}</div>
            </div>
        </div>
        <!-- Box 5: Lời khuyên bỏ heo đất -->
        <div style="margin-top: 14px; background: rgba(245, 158, 11, 0.1); border: 1px solid rgba(245, 158, 11, 0.3); border-radius: 12px; padding: 14px 18px;">
            <div style="font-size: 0.9rem; font-weight: 800; color: {piggy_color}; display: flex; align-items: center; gap: 8px;">
                <span>🐷</span> LỜI KHUYÊN CHO ĐỨA TRẺ LÊN 5: CÓ NÊN BỎ TIỀN HEO ĐẤT VÀO ĐÂY LÚC NÀY?
            </div>
            <div style="font-size: 0.88rem; color: #f1f5f9; margin-top: 6px; line-height: 1.6;">
                {piggy_advice}
            </div>
        </div>
    </div>
    """


def build_five_schools_matrix_html(
    symbol: str,
    council_result: Dict[str, Any],
    fa_result: Dict[str, Any],
    ta_result: Dict[str, Any],
    trade_setup: Dict[str, Any]
) -> str:
    """
    Xây dựng Bảng Góc Nhìn 5 Trường Phái Đầu Tư Chuẩn AGENTS.md:
    1. Giá trị (Graham - Buffett - Munger)
    2. Tăng trưởng chất lượng (Lynch - Fisher - O'Neil)
    3. Kỹ thuật & Dòng tiền (Dow - Wyckoff - Livermore - Minervini)
    4. Vĩ mô & Chu kỳ (Dalio - Soros - Marks)
    5. Rủi ro & Phản biện (Marks - Klarman - Taleb)
    Kèm đánh giá màu sắc trực quan và luận điểm định lượng.
    """
    members = council_result.get("members", [])
    
    # Map các trường phái
    buffett_m = next((m for m in members if m.get("id") == "buffett"), None)
    lynch_m = next((m for m in members if m.get("id") == "lynch"), None)
    tech_m = next((m for m in members if m.get("id") in ["tech", "vsa"]), None)
    macro_m = next((m for m in members if m.get("id") == "macro"), None)
    cro_m = next((m for m in members if m.get("id") == "cro"), None)

    fin = fa_result.get("ratios", {})
    cf = fa_result.get("cash_flow", {})
    asset_val = fa_result.get("asset_valuation", {})
    ind = ta_result.get("indicators", {})
    current_p = trade_setup.get("current_price", 0)

    # 1. Trường phái Giá trị
    val_stance = buffett_m.get("stance", "TRÁNH XA") if buffett_m else "TRÁNH XA"
    pb_val = asset_val.get("pb", "N/A")
    bvps_val = asset_val.get("bvps", 0)
    cfo_ttm_val = cf.get("cfo_ttm", 0)
    val_args = f"P/B: <b>{pb_val}x</b> (BVPS {bvps_val:,.0f} đ). CFO TTM: <b>{format_vnd_human(cfo_ttm_val)}</b>. "
    if cf.get("cfo_ttm", 0) < 0 or fin.get("ttm_profit", 0) < 0:
        val_args += "Cảnh báo Bẫy giá trị: Lỗ kế toán hoặc thâm hụt tiền mặt HĐKD, biên an toàn sổ sách không đảm bảo khả năng bảo toàn vốn."
        val_badge = '<span class="badge" style="background: rgba(239, 68, 68, 0.2); color: #f87171; border: 1px solid #ef4444;">🔴 BẪY GIÁ TRỊ</span>'
    else:
        val_args += "Biên an toàn tài sản tốt, dòng tiền kinh doanh tạo tiền mặt thực."
        val_badge = '<span class="badge" style="background: rgba(16, 185, 129, 0.2); color: #34d399; border: 1px solid #10b981;">🟢 GIÁ RẺ CÓ MOAT</span>'

    # 2. Trường phái Tăng trưởng chất lượng
    growth_stance = lynch_m.get("stance", "TRÁNH XA") if lynch_m else "TRÁNH XA"
    eps_val = fin.get("eps", 0)
    net_p_ttm = fin.get("ttm_profit", 0)
    growth_args = f"EPS TTM: <b>{eps_val:,.0f} đ</b>. LNST TTM: <b>{format_vnd_human(net_p_ttm)}</b>. "
    if eps_val <= 0 or net_p_ttm < 0:
        growth_args += "Doanh nghiệp tăng trưởng âm hoặc kinh doanh thua lỗ, không đạt tiêu chí CANSLIM hay GARP của Peter Lynch."
        growth_badge = '<span class="badge" style="background: rgba(239, 68, 68, 0.2); color: #f87171; border: 1px solid #ef4444;">🔴 KHÔNG ĐẠT CHUẨN</span>'
    else:
        growth_args += "Tăng trưởng lợi nhuận duy trì tích cực, hỗ trợ định giá tăng trưởng hợp lý."
        growth_badge = '<span class="badge" style="background: rgba(16, 185, 129, 0.2); color: #34d399; border: 1px solid #10b981;">🟢 TĂNG TRƯỞNG TỐT</span>'

    # 3. Trường phái Kỹ thuật & Dòng tiền
    ema20_val = ind.get("ema20", 0)
    ema50_val = ind.get("ema50", 0)
    sma200_val = ind.get("sma200", 0)
    rsi_val = ind.get("rsi14", 50)
    vol_ratio = ind.get("vol_ratio", 1.0)
    tech_stance = "DOWNTREND / ĐỨNG NGOÀI" if current_p < ema20_val else "UPTREND / TÍCH CỰC"
    tech_args = f"Giá ({current_p:,.0f} đ) {'< EMA20 (' + f'{ema20_val:,.0f}' + ' đ)' if current_p < ema20_val else '> EMA20'}. RSI: <b>{rsi_val:.1f}</b>. Vol: <b>{vol_ratio:.2f}x MA20</b>. "
    if current_p < ema20_val and current_p < ema50_val:
        tech_args += "Nằm dưới các đường xu hướng ngắn và trung hạn, không có tín hiệu dòng tiền lớn bảo kê, chưa có điểm nổ."
        tech_badge = '<span class="badge" style="background: rgba(239, 68, 68, 0.2); color: #f87171; border: 1px solid #ef4444;">🔴 DOWNTREND</span>'
    else:
        tech_args += "Vận động trên nền giá hỗ trợ, cấu trúc nến kiểm tra cung cầu cạn kiệt."
        tech_badge = '<span class="badge" style="background: rgba(16, 185, 129, 0.2); color: #34d399; border: 1px solid #10b981;">🟢 TÍCH CỰC</span>'

    # 4. Trường phái Vĩ mô & Chu kỳ
    macro_data = fa_result.get("macro", {})
    sec_name = macro_data.get("sector_name", "Doanh nghiệp")
    phase = macro_data.get("cycle_phase", "Bình thường")
    tw_score = macro_data.get("tailwind_score", 50)
    macro_args = f"Ngành: <b>{sec_name}</b> (Pha: <i>{phase}</i>). Điểm Gió xuôi Vĩ mô: <b>{tw_score}/100</b>. "
    if "bất động sản" in sec_name.lower():
        macro_args += "Mặt bằng lãi suất tiết kiệm thấp kích thích dòng tiền đầu tư, tuy nhiên áp lực hấp thụ thị trường phân hóa mạnh giữa các phân khúc."
        macro_badge = '<span class="badge" style="background: rgba(245, 158, 11, 0.2); color: #fbbf24; border: 1px solid #f59e0b;">🟡 PHÂN HÓA</span>'
    else:
        macro_args += f"Mặt bằng lãi suất thấp hỗ trợ tích cực cho chi phí tài chính và kích thích nhu cầu tiêu dùng/mở rộng kinh doanh ngành {sec_name}."
        macro_badge = '<span class="badge" style="background: rgba(16, 185, 129, 0.2); color: #34d399; border: 1px solid #10b981;">🟢 THUẬN LỢI</span>'

    # 5. Quản trị Rủi ro & Phản biện
    gov = fa_result.get("governance", {})
    lead_pct = gov.get("leadership", {}).get("insider_total_pct", 0)
    ff_pct = gov.get("ownership", {}).get("free_float_pct", 50)
    cro_args = f"Tỷ lệ trôi nổi Free-float: <b>{ff_pct}%</b>. Cam kết lãnh đạo (Skin in game): <b>{lead_pct}%</b>. "
    if lead_pct < 1.0:
        cro_args += f"Ban điều hành nắm giữ tỷ lệ cổ phần khiêm tốn ({lead_pct:.2f}%), cần theo dõi mức độ gắn kết quyền lợi lâu dài. "
    else:
        cro_args += f"Ban điều hành nắm giữ tỷ lệ cổ phần tương đối ({lead_pct:.2f}%), có lợi ích gắn kết với cổ đông. "

    if trade_setup.get("has_valid_setup") is False:
        cro_args += "Chưa xuất hiện điểm mua kỹ thuật đạt tỷ lệ R:R chuẩn; khuyến nghị ưu tiên bảo toàn vốn."
        cro_badge = '<span class="badge" style="background: rgba(239, 68, 68, 0.2); color: #f87171; border: 1px solid #ef4444;">🔴 RỦI RO CAO</span>'
    else:
        cro_args += "Mẫu hình giá và cấu trúc tài chính đáp ứng tiêu chuẩn an toàn vốn."
        cro_badge = '<span class="badge" style="background: rgba(16, 185, 129, 0.2); color: #34d399; border: 1px solid #10b981;">🟢 AN TOÀN VỐN</span>'

    return f"""
    <div class="card" style="margin-bottom: 24px; border-left: 4px solid var(--accent-blue);">
        <div class="card-header">
            <span>🏛️ BẢNG TỔNG HỢP GÓC NHÌN 5 TRƯỜNG PHÁI ĐẦU TƯ (COUNCIL MATRIX)</span>
            <span class="badge" style="background: rgba(56, 189, 248, 0.15); color: #38bdf8;">ĐỘ ĐỘNG THUẬN: {trade_setup.get('consensus_score', 0)}/100</span>
        </div>
        <div class="table-responsive">
            <table>
                <thead>
                    <tr>
                        <th style="width: 22%;">Trường phái Tư duy</th>
                        <th style="width: 20%;">Nhận định & Khuyến nghị</th>
                        <th style="width: 46%;">Luận điểm then chốt kèm Số liệu</th>
                        <th style="width: 12%; text-align: center;">Đánh giá</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td><b>1. Giá trị & Con hào kinh tế</b><br><span style="font-size: 0.78rem; color: #94a3b8;">Graham – Buffett – Munger</span></td>
                        <td style="color: {'#34d399' if 'MUA' in val_stance else '#f87171'}; font-weight: 700;">{val_stance}</td>
                        <td style="font-size: 0.85rem; color: #cbd5e1; line-height: 1.55;">{val_args}</td>
                        <td style="text-align: center;">{val_badge}</td>
                    </tr>
                    <tr>
                        <td><b>2. Tăng trưởng chất lượng</b><br><span style="font-size: 0.78rem; color: #94a3b8;">Lynch – Fisher – O'Neil</span></td>
                        <td style="color: {'#34d399' if 'MUA' in growth_stance else '#f87171'}; font-weight: 700;">{growth_stance}</td>
                        <td style="font-size: 0.85rem; color: #cbd5e1; line-height: 1.55;">{growth_args}</td>
                        <td style="text-align: center;">{growth_badge}</td>
                    </tr>
                    <tr>
                        <td><b>3. Kỹ thuật & Dòng tiền</b><br><span style="font-size: 0.78rem; color: #94a3b8;">Dow – Wyckoff – Minervini</span></td>
                        <td style="color: {'#34d399' if 'UPTREND' in tech_stance else '#f87171'}; font-weight: 700;">{tech_stance}</td>
                        <td style="font-size: 0.85rem; color: #cbd5e1; line-height: 1.55;">{tech_args}</td>
                        <td style="text-align: center;">{tech_badge}</td>
                    </tr>
                    <tr>
                        <td><b>4. Vĩ mô & Chu kỳ ngành</b><br><span style="font-size: 0.78rem; color: #94a3b8;">Ray Dalio – Howard Marks</span></td>
                        <td style="color: #fbbf24; font-weight: 700;">CHU KỲ PHÂN HÓA</td>
                        <td style="font-size: 0.85rem; color: #cbd5e1; line-height: 1.55;">{macro_args}</td>
                        <td style="text-align: center;">{macro_badge}</td>
                    </tr>
                    <tr>
                        <td><b>5. Quản trị Rủi ro & Phản biện</b><br><span style="font-size: 0.78rem; color: #94a3b8;">Howard Marks – Taleb – CRO</span></td>
                        <td style="color: {'#34d399' if trade_setup.get('has_valid_setup') else '#f87171'}; font-weight: 700;">{trade_setup.get('action', 'THEO DÕI')}</td>
                        <td style="font-size: 0.85rem; color: #cbd5e1; line-height: 1.55;">{cro_args}</td>
                        <td style="text-align: center;">{cro_badge}</td>
                    </tr>
                </tbody>
            </table>
        </div>
    </div>
    """


def build_clash_of_perspectives_html(clash_data: Any, symbol: str, trade_setup: Dict[str, Any]) -> str:
    """Xây dựng Khối Va Chạm Góc Nhìn & Điểm Mâu Thuẫn Lớn Nhất (Conflict Spotlight)."""
    if isinstance(clash_data, list) and clash_data:
        cl = clash_data[0]
        topic = cl.get("topic", "Định giá Tài sản ròng (P/B rẻ) vs Bản chất Bẫy Giá Trị")
        side_a = cl.get("side_a", {})
        side_b = cl.get("side_b", {})
        cro_synth = cl.get("cro_synthesis", "Bảo vệ vốn là ưu tiên số 1.")
    else:
        topic = "Mâu thuẫn giữa Định giá Tài sản ròng trên sổ sách vs Dòng tiền kinh doanh thật"
        side_a = {
            "speaker": "Góc nhìn Định giá Tài sản ròng (Graham - Buffett)",
            "argument": f"Thị giá đang phản ánh mức chiết khấu so với giá trị sổ sách ròng BVPS, tạo biên an toàn tài sản trên lý thuyết cho nhà đầu tư kiên nhẫn."
        }
        side_b = {
            "speaker": "Góc nhìn Dòng tiền thật & Quản trị Rủi ro (Munger - Howard Marks)",
            "argument": f"Cần kiểm chứng chất lượng các khoản nợ phải thu, hàng tồn kho và khả năng tạo dòng tiền tự do (FCF). Thị giá thấp vẫn có thể là Bẫy giá trị (Value Trap) nếu dòng tiền kinh doanh (CFO) không được cải thiện."
        }
        cro_synth = trade_setup.get("action_summary") or "Tuyệt đối không giải ngân bắt dao rơi khi chưa có tín hiệu tạo đáy và kiểm toán dòng tiền thật xác nhận."

    return f"""
    <div style="background: linear-gradient(145deg, #1f1b2e, #131224); border: 1px solid rgba(239, 68, 68, 0.35); border-radius: 16px; padding: 20px; margin-bottom: 24px; box-shadow: 0 8px 25px rgba(0,0,0,0.3);">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 14px; border-bottom: 1px solid rgba(239, 68, 68, 0.2); padding-bottom: 10px;">
            <div style="font-weight: 800; color: #f87171; font-size: 1rem; display: flex; align-items: center; gap: 8px;">
                <span>⚔️</span> ĐIỂM MÂU THUẪN LỚN NHẤT GIỮA CÁC TRƯỜNG PHÁI: {topic}
            </div>
            <span class="badge" style="background: rgba(239, 68, 68, 0.2); color: #f87171; border: 1px solid #ef4444;">CLASH OF PERSPECTIVES</span>
        </div>
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 16px; margin-bottom: 16px;">
            <div style="background: rgba(15, 23, 42, 0.65); padding: 14px 16px; border-radius: 10px; border-left: 3px solid #38bdf8;">
                <div style="font-size: 0.85rem; font-weight: 700; color: #38bdf8; margin-bottom: 6px;">{side_a.get('speaker', 'Quan điểm 1')}</div>
                <div style="font-size: 0.86rem; color: #cbd5e1; line-height: 1.6;">"{side_a.get('argument', '')}"</div>
            </div>
            <div style="background: rgba(15, 23, 42, 0.65); padding: 14px 16px; border-radius: 10px; border-left: 3px solid #fbbf24;">
                <div style="font-size: 0.85rem; font-weight: 700; color: #fbbf24; margin-bottom: 6px;">{side_b.get('speaker', 'Quan điểm 2')}</div>
                <div style="font-size: 0.86rem; color: #cbd5e1; line-height: 1.6;">"{side_b.get('argument', '')}"</div>
            </div>
        </div>
        <div style="background: rgba(16, 185, 129, 0.1); border: 1px solid rgba(16, 185, 129, 0.3); border-radius: 10px; padding: 14px 16px;">
            <div style="font-weight: 800; color: #34d399; font-size: 0.9rem; display: flex; align-items: center; gap: 6px;">
                <span>🛡️</span> PHÁN QUYẾT ĐIỀU HÒA CỦA GIÁM ĐỐC QUẢN TRỊ RỦI RO (CHIEF RISK OFFICER):
            </div>
            <div style="font-size: 0.88rem; color: #f1f5f9; margin-top: 6px; line-height: 1.6;">
                {cro_synth}
            </div>
        </div>
    </div>
    """


def build_fa_deep_dive_html(
    symbol: str,
    fa_result: Dict[str, Any],
    quote: Dict[str, Any],
    cf: Dict[str, Any],
    fin: Dict[str, Any],
    asset_val: Dict[str, Any],
    gov: Dict[str, Any],
    segments_data: List[Dict[str, Any]]
) -> str:
    """Xây dựng toàn bộ Phần 3: Phân tích Cơ bản Doanh nghiệp Chuyên sâu (FA Deep-Dive)."""
    sym = symbol.upper()
    # 1. Bảng 4 quý BCTC
    quarterly_cf = cf.get("quarterly_cash_flows", [])
    q_rows = ""
    if quarterly_cf:
        for q in quarterly_cf:
            q_name = q.get("quarter", "")
            np_v = q.get("net_profit", 0)
            cfo_v = q.get("cfo", 0)
            capex_v = q.get("capex", 0)
            fcf_v = q.get("fcf", 0)
            np_col = "#34d399" if np_v >= 0 else "#f87171"
            cfo_col = "#34d399" if cfo_v >= 0 else "#f87171"
            fcf_col = "#fbbf24" if fcf_v >= 0 else "#f87171"
            q_rows += f"""
            <tr>
                <td style="font-weight: 700; color: #fff;">{q_name}</td>
                <td style="text-align: right; font-weight: 600; color: {np_col};">{format_vnd_human(np_v)}</td>
                <td style="text-align: right; font-weight: 700; color: {cfo_col};">{format_vnd_human(cfo_v)}</td>
                <td style="text-align: right; color: #cbd5e1;">{format_vnd_human(capex_v)}</td>
                <td style="text-align: right; font-weight: 700; color: {fcf_col};">{format_vnd_human(fcf_v)}</td>
            </tr>
            """
    else:
        q_rows = '<tr><td colspan="5" style="text-align:center;color:#94a3b8;padding:16px;">Đang cập nhật chuỗi BCTC quý.</td></tr>'

    # 2. Các chỉ số Tài sản & Đọng vốn
    tot_assets = fin.get("total_assets", 0) or asset_val.get("total_assets", 0)
    cash_val = fin.get("cash", 0) or asset_val.get("cash", 0)
    rec_val = fin.get("receivables", 0) or asset_val.get("receivables", 0)
    inv_val = fin.get("inventories", 0) or asset_val.get("inventories", 0)
    equity_val = fin.get("owners_equity", 0) or asset_val.get("owners_equity", 0)
    tot_debt = fin.get("total_debt", 0)
    st_debt = fin.get("short_term_debt", 0)
    lt_debt = fin.get("long_term_debt", 0)
    d_to_e = fin.get("debt_to_equity", 0)

    cash_pct = (cash_val / tot_assets * 100) if tot_assets > 0 else float(asset_val.get("cash_ratio") or 0.0)
    rec_pct = (rec_val / tot_assets * 100) if tot_assets > 0 else 0.0
    inv_pct = (inv_val / tot_assets * 100) if tot_assets > 0 else 0.0
    illiquid_pct = rec_pct + inv_pct if (rec_pct + inv_pct) > 0 else float(asset_val.get("illiquid_ratio") or 0.0)

    # 3. Quản trị & Cổ đông
    own = gov.get("ownership", {})
    lead = gov.get("leadership", {})
    sub_web = gov.get("subsidiary_web", {})

    sh_rows = ""
    for sh in own.get("top_shareholders", [])[:6]:
        sh_rows += f"""
        <tr>
            <td style="color: #f1f5f9; font-weight: 500;">{sh.get('name')}</td>
            <td style="text-align: right; color: #38bdf8; font-weight: 700;">{sh.get('percentage')}%</td>
            <td style="text-align: right; color: #94a3b8;">{sh.get('shares', 0):,.0f} CP</td>
        </tr>
        """

    sub_rows = ""
    for sub in sub_web.get("key_subsidiaries", [])[:5]:
        sub_rows += f"""
        <tr>
            <td style="color: #f1f5f9; font-weight: 500;">{sub.get('name')}</td>
            <td style="text-align: right; color: #34d399; font-weight: 600;">{sub.get('ownership_percent')}%</td>
            <td style="color: #94a3b8; font-size: 0.8rem;">Công ty con trực thuộc</td>
        </tr>
        """

    # 4. Phân khúc mô hình hoạt động
    seg_rows = ""
    for s in segments_data:
        seg_rows += f"""
        <tr>
            <td style="font-weight: 600; color: #f1f5f9;">{s.get('name')}</td>
            <td style="text-align: right; color: #38bdf8; font-weight: 600;">{s.get('rev_share_pct')}%</td>
            <td style="text-align: right; color: #34d399; font-weight: 600;">{s.get('gross_profit_share_pct')}%</td>
            <td style="text-align: right; color: #fbbf24; font-weight: 600;">{s.get('gross_margin_pct')}%</td>
            <td><span class="badge" style="background: rgba(139, 92, 246, 0.2); color: #c084fc;">{s.get('role')}</span></td>
            <td style="font-size: 0.82rem; color: #94a3b8;">{s.get('highlights')}</td>
        </tr>
        """

    # 5. Dự án / Cơ sở trọng điểm
    projects_list = fa_result.get("segments", {}).get("projects", [])
    proj_rows = ""
    if projects_list:
        for p in projects_list:
            proj_rows += f"""
            <tr>
                <td style="font-weight: 700; color: #f1f5f9;">{p.get('name')}</td>
                <td style="color: #38bdf8;">{p.get('scale', p.get('location', 'Quy mô lớn'))}</td>
                <td style="color: #cbd5e1; font-size: 0.85rem;">{p.get('status') or p.get('progress_status', 'Đang vận hành')}</td>
                <td style="color: #cbd5e1; font-size: 0.85rem;">{p.get('profit_contribution') or p.get('legal_and_hurdles', 'Hoạt động bình thường')}</td>
            </tr>
            """
    else:
        sec_str = (fa_result.get("macro", {}).get("sector_name") or quote.get("industry") or "").lower()
        if any(k in sec_str for k in ["ngân hàng", "tài chính", "chứng khoán", "bảo hiểm", "bank"]):
            proj_desc = f"Doanh nghiệp hoạt động trong lĩnh vực Tài chính - Ngân hàng - Chứng khoán; mạng lưới vận hành qua hệ thống chi nhánh, phòng giao dịch và hạ tầng công nghệ số toàn quốc (chi tiết trong Thuyết minh BCTC)."
        elif any(k in sec_str for k in ["bất động sản", "địa ốc", "nhà ở"]):
            proj_desc = f"Doanh nghiệp phát triển Bất động sản; danh mục dự án và tiến độ giải phóng mặt bằng, xây dựng được theo dõi qua mục Chi phí SXKD dở dang & Người mua trả tiền trước trong Thuyết minh BCTC."
        else:
            proj_desc = f"Doanh nghiệp vận hành chuỗi hoạt động sản xuất kinh doanh / thương mại dịch vụ; hệ thống nhà xưởng, cơ sở hạ tầng và tài sản cố định được trình bày chi tiết trong Thuyết minh BCTC kiểm toán."

        proj_rows = f"""
        <tr>
            <td colspan="4" style="text-align: center; color: #94a3b8; padding: 20px;">
                🏢 <i>{proj_desc}</i>
            </td>
        </tr>
        """

    # Altman Z & F-Score
    raw_z = cf.get("altman_z")
    altman_z_str = f"{float(raw_z):.2f} điểm" if isinstance(raw_z, (int, float)) and raw_z is not None else "N/A"
    f_score_val = fa_result.get("f_score", 0)
    cfo_np_ratio_val = cf.get("earnings_quality_ratio")
    cfo_np_ratio_str = f"{float(cfo_np_ratio_val):.2f}x" if isinstance(cfo_np_ratio_val, (int, float)) and cfo_np_ratio_val is not None else "N/A"

    # Xây dựng bảng cơ cấu mảng kinh doanh nếu có dữ liệu
    seg_table_html = ""
    if segments_data:
        seg_table_html = f"""
        <div style="font-size: 0.88rem; font-weight: 700; color: #38bdf8; margin: 14px 0 8px 0;">
            📊 Cơ cấu Doanh thu & Biên lợi nhuận gộp theo Mảng hoạt động:
        </div>
        <div class="table-responsive" style="margin-bottom: 18px;">
            <table>
                <thead>
                    <tr>
                        <th>Mảng Kinh Doanh / Dịch Vụ</th>
                        <th style="text-align: right;">% Doanh Thu</th>
                        <th style="text-align: right;">% LN Gộp</th>
                        <th style="text-align: right;">Biên Lãi Gộp</th>
                        <th>Vai Trò Chiến Lược</th>
                        <th>Điểm Nhấn Hoạt Động & Rủi Ro</th>
                    </tr>
                </thead>
                <tbody>
                    {seg_rows}
                </tbody>
            </table>
        </div>
        """

    # Đánh giá rủi ro hệ sinh thái
    sub_count = sub_web.get("subsidiary_count", 0)
    if sym in ["IDJ", "APS", "API"]:
        eco_risk_desc = "Cổ phiếu nằm trong hệ sinh thái Apec (APEC Group, APS, API). Vụ án khởi tố thao túng chứng khoán năm 2023 đối với cựu lãnh đạo nhóm Apec là bài học cảnh tỉnh về rủi ro quản trị, làm suy giảm uy tín và hạn chế khả năng tiếp cận vốn."
    elif sym == "BCG":
        eco_risk_desc = "Biến cố pháp lý thượng tầng tại Bamboo Capital và áp lực đáo hạn trái phiếu cần được giám sát chặt chẽ."
    elif sym == "PNJ":
        eco_risk_desc = "Biến cố pháp lý tại công ty con PNJ-Lab (liên quan kiểm định kim cương nhập lậu) và áp lực trích lập dự phòng thu đổi hàng hóa ước tính hơn 7.000 tỷ đồng cần được ưu tiên kiểm soát."
    elif sub_web.get("circular_capital_risk_level", 1) >= 4:
        eco_risk_desc = "Doanh nghiệp có dấu hiệu mạng lưới công ty liên kết phức tạp, các khoản tạm ứng/phải thu chiếm tỷ trọng cao."
    else:
        eco_risk_desc = f"Cơ cấu mạng lưới {sub_count} công ty con phục vụ chuỗi giá trị cốt lõi của {sym}."

    return f"""
    <!-- KHỐI 1: BÁO CÁO KẾT QUẢ KINH DOANH & DÒNG TIỀN THEO QUÝ -->
    <div class="card" style="margin-bottom: 24px;">
        <div class="card-header">
            <span>🔬 1. KẾT QUẢ KINH DOANH & DÒNG TIỀN THẬT 4 QUÝ GẦN NHẤT (CASH FLOW FORENSIC)</span>
            <span class="badge" style="background: rgba(16, 185, 129, 0.15); color: #34d399;">TIỀN THẬT VS LỢI NHUẬN SỔ SÁCH</span>
        </div>
        <div style="font-size: 0.88rem; color: #cbd5e1; margin-bottom: 14px; line-height: 1.6;">
            So sánh trực tiếp giữa <b>Lợi nhuận sau thuế kế toán (LNST)</b> với <b>Tiền mặt kinh doanh thực thu (CFO)</b> và <b>Dòng tiền tự do (FCF)</b> để phát hiện dấu hiệu doanh nghiệp có đang "bán chịu ghi nhận lãi ảo" hay không:
        </div>
        <div class="table-responsive" style="margin-bottom: 16px;">
            <table>
                <thead>
                    <tr>
                        <th>Kỳ Báo Cáo</th>
                        <th style="text-align: right;">LNST Kế Toán</th>
                        <th style="text-align: right;">Tiền Kinh Doanh Thật (CFO)</th>
                        <th style="text-align: right;">Chi Tiêu Vốn (CapEx)</th>
                        <th style="text-align: right;">Dòng Tiền Tự Do (FCF)</th>
                    </tr>
                </thead>
                <tbody>
                    {q_rows}
                </tbody>
            </table>
        </div>
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 14px; margin-top: 14px;">
            <div style="background: rgba(15, 23, 42, 0.6); padding: 12px 16px; border-radius: 10px; border-left: 3px solid #38bdf8;">
                <div style="font-size: 0.78rem; color: #94a3b8; text-transform: uppercase;">Tỷ lệ Tiền thật / Lãi sổ sách (CFO / LNST)</div>
                <div style="font-size: 1.25rem; font-weight: 800; color: #fff; margin-top: 2px;">{cfo_np_ratio_str}</div>
                <div style="font-size: 0.8rem; color: #94a3b8;">Chuẩn an toàn: &ge; 1.0x (Tiền mặt về tương xứng lợi nhuận)</div>
            </div>
            <div style="background: rgba(15, 23, 42, 0.6); padding: 12px 16px; border-radius: 10px; border-left: 3px solid #fbbf24;">
                <div style="font-size: 0.78rem; color: #94a3b8; text-transform: uppercase;">Xếp hạng Chất lượng Lợi nhuận</div>
                <div style="font-size: 1.25rem; font-weight: 800; color: {'#34d399' if cf.get('quality_grade') == 'A' else ('#f87171' if cf.get('quality_grade') == 'D' else '#fbbf24')}; margin-top: 2px;">Hạng {cf.get('quality_grade', 'B')}</div>
                <div style="font-size: 0.8rem; color: #cbd5e1;">{cf.get('quality_verdict', 'Bình thường')}</div>
            </div>
            <div style="background: rgba(15, 23, 42, 0.6); padding: 12px 16px; border-radius: 10px; border-left: 3px solid #10b981;">
                <div style="font-size: 0.78rem; color: #94a3b8; text-transform: uppercase;">Chỉ số Kiệt quệ Tài chính Altman Z''</div>
                <div style="font-size: 1.25rem; font-weight: 800; color: #fff; margin-top: 2px;">{altman_z_str}</div>
                <div style="font-size: 0.8rem; color: #94a3b8;">{cf.get('z_desc', 'Kiểm tra rủi ro phá sản vùng an toàn')}</div>
            </div>
            <div style="background: rgba(15, 23, 42, 0.6); padding: 12px 16px; border-radius: 10px; border-left: 3px solid #a855f7;">
                <div style="font-size: 0.78rem; color: #94a3b8; text-transform: uppercase;">Piotroski F-Score Sức khỏe BCTC</div>
                <div style="font-size: 1.25rem; font-weight: 800; color: #c084fc; margin-top: 2px;">{f_score_val}/9 điểm</div>
                <div style="font-size: 0.8rem; color: #94a3b8;">Đạt chuẩn an toàn vốn khi F-Score &ge; 5/9</div>
            </div>
        </div>
    </div>

    <!-- KHỐI 2: BẢNG CÂN ĐỐI KẾ TOÁN & RADAR TÀI SẢN ĐỌNG VỐN -->
    <div class="card" style="margin-bottom: 24px;">
        <div class="card-header">
            <span>💎 2. KIỂM TOÁN TÀI SẢN, NỢ VAY & RADAR BẪY GIÁ TRỊ (BALANCE SHEET AUDIT)</span>
            <span class="badge" style="background: rgba(245, 158, 11, 0.15); color: #fbbf24;">CHẤT LƯỢNG TÀI SẢN</span>
        </div>
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 18px; margin-bottom: 18px;">
            <!-- Cột Tài sản & Đọng vốn -->
            <div style="background: rgba(15, 23, 42, 0.6); padding: 16px; border-radius: 12px; border: 1px solid var(--border);">
                <div style="font-size: 0.9rem; font-weight: 700; color: #38bdf8; margin-bottom: 10px; border-bottom: 1px solid rgba(255,255,255,0.06); padding-bottom: 6px;">
                    📦 Cơ cấu Tài sản & Khả năng Thanh khoản
                </div>
                <div style="font-size: 0.86rem; color: #cbd5e1; line-height: 1.8;">
                    • <b>Tổng tài sản:</b> {format_vnd_human(tot_assets)}<br>
                    • <b>Vốn chủ sở hữu (VCSH):</b> {format_vnd_human(equity_val)}<br>
                    • <b>Tiền & tương đương tiền:</b> {format_vnd_human(cash_val)} (<span style="color: #34d399; font-weight: 700;">{cash_pct:.1f}%</span> tài sản)<br>
                    • <b>Các khoản phải thu:</b> {format_vnd_human(rec_val)} (<span style="color: #fbbf24; font-weight: 700;">{rec_pct:.1f}%</span> tài sản)<br>
                    • <b>Hàng tồn kho:</b> {format_vnd_human(inv_val)} (<span style="color: #fbbf24; font-weight: 700;">{inv_pct:.1f}%</span> tài sản)<br>
                    • <b>Tổng tài sản đọng vốn (Phải thu + Tồn kho):</b> <b style="color: #f87171;">{format_vnd_human(rec_val + inv_val)} ({illiquid_pct:.1f}% tổng tài sản)</b>
                </div>
                <div style="margin-top: 10px; background: rgba(239, 68, 68, 0.1); border: 1px solid rgba(239, 68, 68, 0.25); border-radius: 8px; padding: 10px; font-size: 0.82rem; color: #fca5a5;">
                    ⚠️ <b>Cảnh báo thanh khoản tài sản:</b> Tài sản đọng vốn chiếm {illiquid_pct:.1f}% tổng tài sản. Nếu đối tác chậm thanh toán hoặc hàng tồn kho luân chuyển chậm, doanh nghiệp sẽ đối mặt áp lực thanh khoản tiền mặt.
                </div>
            </div>

            <!-- Cột Nợ vay & Định giá sổ sách -->
            <div style="background: rgba(15, 23, 42, 0.6); padding: 16px; border-radius: 12px; border: 1px solid var(--border);">
                <div style="font-size: 0.9rem; font-weight: 700; color: #fbbf24; margin-bottom: 10px; border-bottom: 1px solid rgba(255,255,255,0.06); padding-bottom: 6px;">
                    💳 Cơ cấu Nợ Vay & Định Giá Khối Tài Sản (P/B)
                </div>
                <div style="font-size: 0.86rem; color: #cbd5e1; line-height: 1.8;">
                    • <b>Tổng nợ vay chịu lãi:</b> {format_vnd_human(tot_debt)} (Ngắn hạn: {format_vnd_human(st_debt)} | Dài hạn: {format_vnd_human(lt_debt)})<br>
                    • <b>Tỷ lệ Nợ vay / Vốn CSH:</b> <b style="color: #fff;">{d_to_e}x</b> (Ngưỡng an toàn ngành: &le; 1.0x)<br>
                    • <b>Giá trị sổ sách ròng (BVPS):</b> <b style="color: #38bdf8;">{asset_val.get('bvps', 0):,.0f} đ/CP</b><br>
                    • <b>Thị giá / Sổ sách (P/B):</b> <b style="color: #34d399;">{asset_val.get('pb', 'N/A')}x</b><br>
                    • <b>Mức chiết khấu so với sổ sách:</b> <b style="color: #34d399;">{asset_val.get('asset_discount_pct', 0):+.1f}%</b><br>
                    • <b>Radar Đánh giá Bẫy Giá Trị:</b> <span style="color: #fbbf24; font-weight: 700;">{asset_val.get('manipulation_verdict', 'Món hời tài sản chiết khấu')}</span>
                </div>
                <div style="margin-top: 10px; background: rgba(56, 189, 248, 0.1); border: 1px solid rgba(56, 189, 248, 0.25); border-radius: 8px; padding: 10px; font-size: 0.82rem; color: #bae6fd;">
                    💡 <b>Giải mã định giá P/B:</b> Mức chiết khấu sâu {asset_val.get('asset_discount_pct', 0):+.1f}% phản ánh sự e ngại của thị trường về chất lượng các khoản nợ phải thu và rủi ro trích lập giảm giá hàng tồn kho.
                </div>
            </div>
        </div>
    </div>

    <!-- KHỐI 3: MÔ HÌNH KINH DOANH CỐT LÕI & PHÂN KHÚC HOẠT ĐỘNG -->
    <div class="card" style="margin-bottom: 24px;">
        <div class="card-header">
            <span>🏢 3. MÔ HÌNH KINH DOANH CỐT LÕI & PHÂN KHÚC HOẠT ĐỘNG (CORE BUSINESS BREAKDOWN)</span>
            <span class="badge" style="background: rgba(139, 92, 246, 0.15); color: #c084fc;">PHÂN KHÚC & DỰ ÁN</span>
        </div>
        <div style="font-size: 0.88rem; color: #cbd5e1; margin-bottom: 14px; line-height: 1.6;">
            <b>Tóm lược mô hình hoạt động:</b> {fa_result.get('segments', {}).get('business_model_summary', quote.get('company_profile', f'Mô hình kinh doanh cốt lõi của {sym}.'))}
        </div>
        {seg_table_html}
        <div style="font-size: 0.88rem; font-weight: 700; color: #38bdf8; margin: 14px 0 8px 0;">
            🏗️ Danh mục Dự án Trọng điểm / Cơ sở Hạ tầng & Mạng lưới:
        </div>
        <div class="table-responsive" style="margin-bottom: 18px;">
            <table>
                <thead>
                    <tr>
                        <th>Tên Dự Án / Cơ Sở Mạng Lưới</th>
                        <th>Quy Mô & Vị Trí</th>
                        <th>Hiện Trạng Vận Hành / Tiến Độ</th>
                        <th>Đóng Góp Lợi Nhuận / Pháp Lý</th>
                    </tr>
                </thead>
                <tbody>
                    {proj_rows}
                </tbody>
            </table>
        </div>
    </div>

    <!-- KHỐI 4: QUẢN TRỊ DOANH NGHIỆP, CỔ ĐÔNG & RADAR HỆ SINH THÁI -->
    <div class="card" style="margin-bottom: 24px;">
        <div class="card-header">
            <span>👥 4. QUẢN TRỊ DOANH NGHIỆP, CỔ ĐÔNG & RADAR HỆ SINH THÁI (GOVERNANCE & SHELL AUDIT)</span>
            <span class="badge" style="background: rgba(59, 130, 246, 0.15); color: #3b82f6;">G-SCORE {gov.get('g_score', 70)}/100</span>
        </div>
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 18px; margin-bottom: 16px;">
            <!-- Cột Cơ cấu Cổ đông & Lãnh đạo -->
            <div style="background: rgba(15, 23, 42, 0.6); padding: 16px; border-radius: 12px; border: 1px solid var(--border);">
                <div style="font-size: 0.9rem; font-weight: 700; color: #38bdf8; margin-bottom: 8px;">
                    🏛️ Cơ cấu Sở hữu & Cam kết Lãnh đạo (Skin in the game)
                </div>
                <div style="font-size: 0.86rem; color: #cbd5e1; line-height: 1.7; margin-bottom: 12px;">
                    • <b>Tỷ lệ cổ phiếu trôi nổi (Free-Float):</b> <b style="color: #fbbf24;">{own.get('free_float_pct', 80.0)}%</b> (Phân mảnh cao, dễ bị đầu cơ lướt sóng)<br>
                    • <b>Tỷ lệ sở hữu khối ngoại:</b> <b>{own.get('foreigner_pct', 0.56)}%</b> | Nhà nước: <b>0.0%</b><br>
                    • <b>Cam kết vốn của Ban điều hành:</b> <b style="color: #f87171;">{lead.get('insider_total_pct', 0.58)}%</b> ({lead.get('skin_in_game_verdict', 'Cực thấp / Rủi ro làm thuê không chịu trách nhiệm')})<br>
                    • <b>Chủ tịch HĐQT:</b> {lead.get('chairman') or 'Đang cập nhật'}
                </div>
                <div class="table-responsive">
                    <table>
                        <thead>
                            <tr>
                                <th>Cổ Đông Chủ Chốt</th>
                                <th style="text-align: right;">Tỷ Lệ</th>
                                <th style="text-align: right;">Số Lượng</th>
                            </tr>
                        </thead>
                        <tbody>
                            {sh_rows}
                        </tbody>
                    </table>
                </div>
            </div>

            <!-- Cột Mạng lưới Công ty con & Vết sẹo Hệ sinh thái -->
            <div style="background: rgba(15, 23, 42, 0.6); padding: 16px; border-radius: 12px; border: 1px solid var(--border);">
                <div style="font-size: 0.9rem; font-weight: 700; color: #f87171; margin-bottom: 8px;">
                    🌐 Mạng lưới Chân rết & Rủi ro Biến cố Hệ sinh thái
                </div>
                <div style="font-size: 0.86rem; color: #cbd5e1; line-height: 1.7; margin-bottom: 12px;">
                    • <b>Quy mô hệ sinh thái:</b> {sub_web.get('subsidiary_count', 0)} công ty con, {sub_web.get('affiliate_count', 0)} công ty liên kết<br>
                    • <b>Radar Luân chuyển Vốn & Nợ nội bộ:</b> {sub_web.get('circular_capital_verdict', 'Cần kiểm toán các khoản tạm ứng')}<br>
                    • <b>Đánh giá Rủi ro Hệ sinh thái:</b> {eco_risk_desc}
                </div>
                <div class="table-responsive">
                    <table>
                        <thead>
                            <tr>
                                <th>Đơn Vị Thành Viên Trọng Yếu</th>
                                <th style="text-align: right;">Sở Hữu</th>
                                <th>Vai Trò</th>
                            </tr>
                        </thead>
                        <tbody>
                            {sub_rows}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    </div>
    """


def build_ta_deep_dive_html(
    symbol: str,
    ta_result: Dict[str, Any],
    quote: Dict[str, Any],
    df_ohlcv: Optional[pd.DataFrame],
    current_price: float,
    trigger_pivot: float,
    stop_loss_lvl: float,
    tp1_lvl: float,
    offline_candles_svg: str
) -> str:
    """Xây dựng toàn bộ Phần 4: Phân tích Kỹ thuật & Dòng tiền Chuyên sâu (TA Deep-Dive)."""
    ind = ta_result.get("indicators", {})
    adv_ta = ta_result.get("advanced_ta", {})
    vcp_data = adv_ta.get("vcp") if isinstance(adv_ta.get("vcp"), dict) else {}
    vsa_sig = adv_ta.get("vsa_signals") if isinstance(adv_ta.get("vsa_signals"), dict) else {}
    fibo_data = adv_ta.get("fibonacci") if isinstance(adv_ta.get("fibonacci"), dict) else {}
    overhead_data = adv_ta.get("overhead_supply_detail") if isinstance(adv_ta.get("overhead_supply_detail"), dict) else {}

    # Tính toán 52-week High/Low
    h52_val = current_price
    l52_val = current_price
    if df_ohlcv is not None and isinstance(df_ohlcv, pd.DataFrame) and not df_ohlcv.empty:
        w52 = df_ohlcv.tail(250)
        h52_val = float(w52["high"].max())
        l52_val = float(w52["low"].min())

    ema20 = float(ind.get("ema20", 0))
    ema50 = float(ind.get("ema50", 0))
    sma200 = float(ind.get("sma200", 0))
    rsi = float(ind.get("rsi14", 50))
    macd_v = float(ind.get("macd", 0))
    macd_sig = float(ind.get("macd_signal", 0))
    atr_v = float(ind.get("atr14", 0))
    vol = float(quote.get("volume", 0) or ind.get("volume", 0))
    vol_ma20 = float(ind.get("vol_ma20", vol / (ind.get("vol_ratio", 1.0) or 1.0)))
    vol_ratio = float(ind.get("vol_ratio", 1.0))
    sup20 = float(ind.get("sup_20d", 0))
    res20 = float(ind.get("res_20d", 0))

    dist_ema20 = ((current_price - ema20) / ema20 * 100) if ema20 > 0 else 0
    dist_ema50 = ((current_price - ema50) / ema50 * 100) if ema50 > 0 else 0
    dist_sma200 = ((current_price - sma200) / sma200 * 100) if sma200 > 0 else 0

    vcp_contractions_str = " &rarr; ".join(vcp_data.get("contractions", ["Đang dao động tích lũy"]))
    vsa_signals_list = vsa_sig.get("signal_descriptions", ["Vận động thanh khoản quanh mức trung bình."])
    vsa_signals_html = "".join([f"<li style='margin-bottom: 6px;'>{s}</li>" for s in vsa_signals_list])

    fibo_low_str = f"{float(fibo_data.get('swing_low') or l52_val):,.0f} đ"
    fibo_high_str = f"{float(fibo_data.get('swing_high') or h52_val):,.0f} đ"
    fibo_382_str = f"{float(fibo_data.get('fibo_382') or 0):,.0f} đ"
    fibo_500_str = f"{float(fibo_data.get('fibo_500') or 0):,.0f} đ"
    fibo_618_str = f"{float(fibo_data.get('fibo_618') or 0):,.0f} đ"

    return f"""
    <!-- KHỐI 1: BIỂU ĐỒ NẾN NHẬT TƯƠNG TÁC (TRADINGVIEW LIGHTWEIGHT CHARTS) -->
    <div id="sec-chart" class="card" style="margin-bottom: 24px; padding: 20px;">
        <div class="card-header" style="margin-bottom: 14px;">
            <div style="display: flex; align-items: center; gap: 10px;">
                <span style="font-size: 1.05rem; font-weight: 800; color: #fff;">📊 ĐỒ THỊ NẾN NHẬT OHLCV, KHỐI LƯỢNG & ĐƯỜNG GIÁ CHỈ BÁO</span>
                <span class="badge" style="background: rgba(56, 189, 248, 0.15); color: #38bdf8;">160 PHIÊN GẦN NHẤT</span>
            </div>
            <div style="font-size: 0.8rem; color: #94a3b8; display: flex; gap: 14px; align-items: center; flex-wrap: wrap;">
                <span style="display: inline-flex; align-items: center; gap: 4px;"><span style="width: 10px; height: 10px; background: #fbbf24; border-radius: 2px;"></span> EMA20</span>
                <span style="display: inline-flex; align-items: center; gap: 4px;"><span style="width: 10px; height: 10px; background: #38bdf8; border-radius: 2px;"></span> EMA50</span>
                <span style="display: inline-flex; align-items: center; gap: 4px;"><span style="width: 12px; height: 2px; background: #10b981;"></span> Pivot Kích Hoạt</span>
                <span style="display: inline-flex; align-items: center; gap: 4px;"><span style="width: 12px; height: 2px; background: #ef4444;"></span> Cắt Lỗ (SL)</span>
                <span style="display: inline-flex; align-items: center; gap: 4px;"><span style="width: 12px; height: 2px; background: #38bdf8;"></span> Mục Tiêu 1</span>
            </div>
        </div>
        
        <div id="tvChartContainer" style="width: 100%; height: 460px; position: relative; border-radius: 10px; overflow: hidden; background: #070c16; border: 1px solid rgba(255,255,255,0.06);">
            <div id="tvChartOfflineFallback" style="display: none; width: 100%; height: 100%;">
                {offline_candles_svg}
            </div>
        </div>
        <div id="chartTooltip" style="margin-top: 10px; font-size: 0.82rem; color: #94a3b8; font-family: monospace; display: flex; gap: 16px; flex-wrap: wrap;">
            <span>Rê chuột trên biểu đồ để xem chi tiết nến OHLCV và Khối lượng</span>
        </div>
    </div>

    <!-- KHỐI 2: BẢNG CHỈ BÁO KỸ THUẬT ĐẦY ĐỦ CHI TIẾT (FULL INDICATOR SUITE) -->
    <div class="card" style="margin-bottom: 24px;">
        <div class="card-header">
            <span>📈 BẢNG CHỈ BÁO KỸ THUẬT & TRẠNG THÁI XU HƯỚNG CHI TIẾT (TECHNICAL INDICATORS)</span>
            <span class="badge" style="background: rgba(139, 92, 246, 0.15); color: #c084fc;">ĐIỂM TA: {ta_result.get('ta_total_score', 50)}/100</span>
        </div>
        <div class="table-responsive">
            <table>
                <thead>
                    <tr>
                        <th>Nhóm Chỉ Báo</th>
                        <th>Tên Chỉ Báo & Thông Số</th>
                        <th style="text-align: right;">Giá Trị Đo Lường</th>
                        <th>Trạng Thái & Ý Nghĩa Tín Hiệu</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td rowspan="3" style="font-weight: 700; color: #38bdf8;">Đường Trung Bình Động (Trend Following)</td>
                        <td>Đường xu hướng ngắn hạn <b>EMA 20</b></td>
                        <td style="text-align: right; font-weight: 700; color: #fbbf24;">{ema20:,.0f} đ ({dist_ema20:+.1f}%)</td>
                        <td style="color: {'#34d399' if dist_ema20 >= 0 else '#f87171'};">{'Giá đang nằm trên đường xu hướng ngắn hạn' if dist_ema20 >= 0 else 'Giá nằm dưới EMA20 - Kênh giảm ngắn hạn'}</td>
                    </tr>
                    <tr>
                        <td>Đường xu hướng trung hạn <b>EMA 50</b></td>
                        <td style="text-align: right; font-weight: 700; color: #38bdf8;">{ema50:,.0f} đ ({dist_ema50:+.1f}%)</td>
                        <td style="color: {'#34d399' if dist_ema50 >= 0 else '#f87171'};">{'Giữ vững trên xu hướng trung hạn EMA50' if dist_ema50 >= 0 else 'Dưới EMA50 - Áp lực cản trung hạn đè nặng'}</td>
                    </tr>
                    <tr>
                        <td>Đường xu hướng dài hạn <b>SMA 200</b></td>
                        <td style="text-align: right; font-weight: 700; color: #cbd5e1;">{sma200:,.0f} đ ({dist_sma200:+.1f}%)</td>
                        <td style="color: {'#34d399' if dist_sma200 >= 0 else '#f87171'};">{'Nằm trong chu kỳ Uptrend dài hạn' if dist_sma200 >= 0 else 'Downtrend dài hạn - Chưa có điểm xoay chiều'}</td>
                    </tr>
                    <tr>
                        <td rowspan="2" style="font-weight: 700; color: #fbbf24;">Động Lượng & Xung Lực (Momentum & Volatility)</td>
                        <td>Chỉ số sức mạnh tương đối <b>RSI (14)</b></td>
                        <td style="text-align: right; font-weight: 800; color: {'#f87171' if rsi <= 30 else ('#34d399' if rsi >= 60 else '#fbbf24')};">{rsi:.1f}</td>
                        <td style="color: #cbd5e1;">{'Vùng Quá Bán (Oversold) - Áp lực bán tạm chững lại' if rsi <= 30 else ('Vùng Quá Mua (Overbought) - Cảnh báo điều chỉnh' if rsi >= 70 else 'Vùng trung lập')}</td>
                    </tr>
                    <tr>
                        <td>Chỉ báo <b>MACD (12, 26, 9)</b> & Tín hiệu</td>
                        <td style="text-align: right; font-weight: 700; color: #cbd5e1;">MACD: {macd_v:.1f} | Sig: {macd_sig:.1f}</td>
                        <td style="color: {'#34d399' if macd_v > macd_sig else '#f87171'};">{'MACD cắt lên trên Signal (Tín hiệu mua)' if macd_v > macd_sig else 'MACD nằm dưới Signal - Động lượng giảm tiếp diễn'}</td>
                    </tr>
                    <tr>
                        <td rowspan="2" style="font-weight: 700; color: #34d399;">Thanh Khoản & Biên Độ (Volume & Volatility)</td>
                        <td>Khối lượng phiên vs <b>MA20 Volume</b></td>
                        <td style="text-align: right; font-weight: 700; color: #fff;">{vol:,.0f} CP ({vol_ratio:.2f}x MA20)</td>
                        <td style="color: {'#34d399' if vol_ratio >= 1.3 else '#94a3b8'};">{'Khối lượng bùng nổ vượt trội trung bình' if vol_ratio >= 1.3 else 'Thanh khoản duy trì ở mức bình thường'}</td>
                    </tr>
                    <tr>
                        <td>Biên độ biến động thực tế <b>ATR (14)</b></td>
                        <td style="text-align: right; font-weight: 700; color: #cbd5e1;">{atr_v:,.0f} đ</td>
                        <td style="color: #94a3b8;">Biên độ dao động bình quân mỗi phiên giao dịch</td>
                    </tr>
                    <tr>
                        <td rowspan="2" style="font-weight: 700; color: #f87171;">Vùng Giá & Khung 52 Tuần (Key Levels)</td>
                        <td>Vùng Kháng cự & Hỗ trợ 20 phiên</td>
                        <td style="text-align: right; font-weight: 700; color: #fff;">Kháng cự: {res20:,.0f} đ | Hỗ trợ: {sup20:,.0f} đ</td>
                        <td style="color: #cbd5e1;">Biên dao động tích lũy ngắn hạn</td>
                    </tr>
                    <tr>
                        <td>Khung giá 52 Tuần (52-Week Range)</td>
                        <td style="text-align: right; font-weight: 700; color: #fff;">Đáy: {l52_val:,.0f} đ | Đỉnh: {h52_val:,.0f} đ</td>
                        <td style="color: #cbd5e1;">Khoảng biến động lớn nhất trong 1 năm qua</td>
                    </tr>
                </tbody>
            </table>
        </div>
    </div>

    <!-- KHỐI 3: WYCKOFF VSA & MÔ HÌNH VCP MINERVINI -->
    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 18px; margin-bottom: 24px;">
        <!-- VCP Minervini -->
        <div class="card">
            <div class="card-header">
                <span>🎯 MÔ HÌNH THU HẸP BIẾN ĐỘNG VCP (MARK MINERVINI)</span>
                <span class="badge" style="background: rgba(139, 92, 246, 0.15); color: #c084fc;">CANSLIM</span>
            </div>
            <div style="font-size: 0.88rem; color: #cbd5e1; line-height: 1.7;">
                • <b>Trạng thái mẫu hình:</b> <b style="color: #fff;">{vcp_data.get('vcp_stage', 'Đang vận động tích lũy')}</b><br>
                • <b>Chuỗi các nhịp co thắt biên độ:</b> <span style="color: #fbbf24; font-weight: 700;">{vcp_contractions_str}</span><br>
                • <b>Đánh giá theo chuẩn Minervini:</b> <i>{vcp_data.get('vcp_verdict', 'N/A')}</i><br>
                • <b>Bộ lọc Trend Template:</b> {ta_result.get('oneil', {}).get('verdict', 'Chưa đạt chuẩn tăng')}
            </div>
        </div>

        <!-- Wyckoff VSA -->
        <div class="card">
            <div class="card-header">
                <span>🐋 HÀNH VI DÒNG TIỀN LỚN & WYCKOFF VSA</span>
                <span class="badge" style="background: rgba(16, 185, 129, 0.15); color: #34d399;">SMART MONEY</span>
            </div>
            <div style="font-size: 0.88rem; color: #cbd5e1; line-height: 1.7;">
                • <b>Pha thị trường hiện tại:</b> <b style="color: #38bdf8;">Pha {ta_result.get('vsa', {}).get('phase', 'Tích lũy')}</b><br>
                • <b>Hành động của Cá mập / Big Boys:</b> <b style="color: #fff;">{vsa_sig.get('smart_money_action', 'Theo dõi quan sát')}</b><br>
                • <b>Dấu chân nến VSA chuyên sâu:</b>
                <ul style="margin: 6px 0 0 16px; font-size: 0.84rem; color: #cbd5e1;">
                    {vsa_signals_html}
                </ul>
            </div>
        </div>
    </div>

    <!-- KHỐI 4: FIBONACCI RETRACEMENT & VÙNG CUNG KẸP HÀNG ĐỈNH CŨ -->
    <div class="card" style="margin-bottom: 24px;">
        <div class="card-header">
            <span>📐 MỐC HỖ TRỢ FIBONACCI & VÙNG CUNG KẸP HÀNG ĐỈNH CŨ (OVERHEAD SUPPLY)</span>
            <span class="badge" style="background: rgba(245, 158, 11, 0.15); color: #fbbf24;">NGƯỠNG PHÒNG THỦ</span>
        </div>
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 18px;">
            <div style="background: rgba(15, 23, 42, 0.6); padding: 14px 16px; border-radius: 12px; border: 1px solid var(--border);">
                <div style="font-size: 0.88rem; font-weight: 700; color: #38bdf8; margin-bottom: 8px;">Mốc Hồi Quy Fibonacci (Sóng gần nhất):</div>
                <div style="font-size: 0.85rem; color: #cbd5e1; line-height: 1.8;">
                    • Đáy sóng: <b>{fibo_low_str}</b> &bull; Đỉnh sóng: <b>{fibo_high_str}</b><br>
                    • <b>Fibo 38.2%:</b> <span style="color: #34d399; font-weight: 700;">{fibo_382_str}</span> (Hỗ trợ nhịp sóng rất khỏe)<br>
                    • <b>Fibo 50.0%:</b> <span style="color: #fbbf24; font-weight: 700;">{fibo_500_str}</span> (Mốc cân bằng tâm lý cung cầu)<br>
                    • <b>Fibo 61.8%:</b> <span style="color: #f87171; font-weight: 700;">{fibo_618_str}</span> (Hỗ trợ vàng sống còn)<br>
                    • <b>Vị thế hiện tại:</b> <i>{fibo_data.get('current_fibo_zone', 'Nằm dưới các mốc hồi quy')}</i>
                </div>
            </div>
            <div style="background: rgba(15, 23, 42, 0.6); padding: 14px 16px; border-radius: 12px; border: 1px solid var(--border);">
                <div style="font-size: 0.88rem; font-weight: 700; color: #f87171; margin-bottom: 8px;">Áp Lực Vùng Cung Kẹp Hàng Đỉnh Cũ (Overhead Supply):</div>
                <div style="font-size: 0.85rem; color: #cbd5e1; line-height: 1.8;">
                    • <b>Vùng kẹp hàng lớn:</b> <b style="color: #fca5a5;">{overhead_data.get('resistance_cluster', f'{h52_val:,.0f} đ (Đỉnh cũ)')}</b><br>
                    • <b>Mức độ áp lực bán:</b> <b style="color: {'#34d399' if overhead_data.get('supply_intensity') == 'Thấp' else '#f87171'};">{overhead_data.get('supply_intensity', 'Đáng kể')}</b><br>
                    • <b>Chi tiết đánh giá:</b> <i>{overhead_data.get('explanation', 'Lượng hàng kẹp đỉnh cũ lớn, mỗi nhịp hồi kỹ thuật đều đối mặt với áp lực xả hòa vốn.')}</i>
                </div>
            </div>
        </div>
    </div>
    """


def build_scenarios_and_invalidation_html(
    symbol: str,
    trade_setup: Dict[str, Any],
    current_price: float,
    has_valid_setup: bool
) -> str:
    """Xây dựng Dự phóng 3 Kịch bản Thị trường (Cơ sở, Tiêu cực, Tích cực) & Hộp Điều kiện Mất hiệu lực."""
    if has_valid_setup:
        scenarios = [
            ("Kịch bản Cơ sở (Xác suất 60%)", "Giá tiếp tục tích lũy co thắt chặt chẽ quanh nền hiện tại, sau đó bứt phá vượt Pivot kèm khối lượng lớn xác nhận điểm mua chuẩn.", "Giải ngân thăm dò 30-50% tại nền, gia tăng đủ tỷ trọng khi vượt Pivot.", "#38bdf8"),
            ("Kịch bản Tích cực (Xác suất 25%)", "Dòng tiền lớn đẩy dứt khoát vượt đỉnh ngắn hạn, tiến thẳng về các mốc chốt lời TP1 và TP2 với xung lực mạnh mẽ.", "Nắm giữ chặt theo sóng, nâng chặn lãi (trailing stop) để tối đa hóa lợi nhuận.", "#34d399"),
            ("Kịch bản Tiêu cực (Xác suất 15%)", "Thị trường chung điều chỉnh xấu bất ngờ, cổ phiếu vi phạm điểm cắt lỗ kỷ luật đã đặt ra.", "Thực hiện cắt lỗ nghiêm ngặt không do dự, bảo toàn 100% vốn gốc.", "#f87171")
        ]
        invalidation_list = trade_setup.get("invalidation_conditions") or [
            "Giá đóng cửa gãy thủng ngưỡng cắt lỗ Stop Loss.",
            "Dòng tiền kinh doanh (CFO) âm trong 2 quý liên tiếp.",
            "Xuất hiện phiên bán tháo phân phối lớn với khối lượng gấp >2 lần MA20."
        ]
    else:
        scenarios = [
            ("Kịch bản Cơ sở (Xác suất 65%)", f"Giá tiếp tục vận động tích lũy đi ngang sideway quanh vùng {current_price*0.93:,.0f} - {current_price*1.05:,.0f} đ với thanh khoản thận trọng trong lúc chờ đợi các tín hiệu hồi phục kinh doanh rõ ràng hơn.", "ĐỨNG NGOÀI QUAN SÁT, kiên nhẫn chờ xác nhận tín hiệu tạo đáy tin cậy.", "#fbbf24"),
            ("Kịch bản Tiêu cực (Xác suất 25%)", f"Nếu thị trường chung điều chỉnh xấu hoặc kết quả kinh doanh suy yếu, giá có thể gãy thủng ngưỡng hỗ trợ {current_price*0.93:,.0f} đ để tìm đáy mới.", "Tuân thủ kỷ luật cắt lỗ tuyệt đối, không bình quân giá xuống.", "#f87171"),
            ("Kịch bản Tích cực (Xác suất 10%)", f"Xuất hiện dòng tiền lớn tham gia kéo nhịp hồi phục kỹ thuật ngắn hạn tiệm cận vùng cản EMA50 ({current_price*1.12:,.0f} đ).", "Tận dụng nhịp hồi kỹ thuật để cơ cấu tài khoản nếu kẹp vị thế cũ, hạn chế mua đuổi.", "#38bdf8")
        ]
        invalidation_list = [
            "Báo cáo tài chính soát xét các kỳ tiếp theo ghi nhận LNST tăng trưởng dương và dòng tiền kinh doanh (CFO) dương bền vững.",
            "Doanh nghiệp cải thiện vòng quay vốn lưu động, giảm tỷ lệ tài sản đọng vốn ở các khoản phải thu và hàng tồn kho.",
            "Về kỹ thuật: Giá hình thành cấu trúc tạo đáy đảo chiều tin cậy (2 đáy / VCP / Spring), bứt phá vượt các đường MA kèm khối lượng xác nhận gấp tối thiểu 1.5x MA20."
        ]

    scenarios_html = ""
    for title, desc, action, col in scenarios:
        scenarios_html += f"""
        <div style="background: rgba(15, 23, 42, 0.65); border: 1px solid var(--border); border-top: 3px solid {col}; border-radius: 12px; padding: 16px;">
            <div style="font-weight: 800; color: {col}; font-size: 0.95rem; margin-bottom: 6px;">{title}</div>
            <div style="font-size: 0.85rem; color: #cbd5e1; line-height: 1.6; margin-bottom: 10px;">{desc}</div>
            <div style="font-size: 0.82rem; color: #fff; background: rgba(255,255,255,0.05); padding: 8px 10px; border-radius: 6px;">
                <b>👉 Kế hoạch hành động:</b> {action}
            </div>
        </div>
        """

    inval_items = "".join([f"<li style='margin-bottom: 6px;'>{c}</li>" for c in invalidation_list])

    return f"""
    <div class="card" style="margin-bottom: 24px;">
        <div class="card-header">
            <span>🔮 5. DỰ PHÓNG CÁC KỊCH BẢN THỊ TRƯỜNG & ĐIỀU KIỆN MẤT HIỆU LỰC (SCENARIO PLANNING)</span>
            <span class="badge" style="background: rgba(56, 189, 248, 0.15); color: #38bdf8;">ĐA KỊCH BẢN</span>
        </div>
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 16px; margin-bottom: 18px;">
            {scenarios_html}
        </div>
        <div style="background: rgba(239, 68, 68, 0.08); border: 1px solid rgba(239, 68, 68, 0.3); border-radius: 12px; padding: 16px;">
            <div style="font-weight: 800; color: #f87171; font-size: 0.92rem; margin-bottom: 8px; display: flex; align-items: center; gap: 6px;">
                <span>⛔</span> ĐIỀU KIỆN LÀM LUẬN ĐIỂM "TRÁNH XA / ĐỨNG NGOÀI" MẤT HIỆU LỰC (INVALIDATION TRIGGERS):
            </div>
            <div style="font-size: 0.85rem; color: #cbd5e1; line-height: 1.6;">
                Hội đồng đầu tư chỉ xem xét đánh giá lại cổ phiếu {symbol} khi đồng thời thỏa mãn các điều kiện định lượng sau:
                <ul style="margin: 8px 0 0 18px; color: #fca5a5;">
                    {inval_items}
                </ul>
            </div>
        </div>
    </div>
    """


def build_missing_data_audit_html(symbol: str, fa_result: Dict[str, Any]) -> str:
    """Xây dựng Khối Dữ Kiện Còn Thiếu Cần Nhà Đầu Tư Kiểm Tra Thêm."""
    fin = fa_result.get("ratios", {})
    rec_val = fin.get("receivables", 0)
    inv_val = fin.get("inventories", 0)
    tot_assets = fin.get("total_assets", 1) or 1
    illiquid_pct = ((rec_val + inv_val) / tot_assets * 100) if tot_assets > 0 else 0
    gov = fa_result.get("governance", {})
    sub_count = gov.get("subsidiary_web", {}).get("subsidiary_count", 0)

    missing_items = [
        ("1. Chi tiết Thuyết minh Phải thu & Hàng tồn kho", f"Tài sản đọng vốn (Phải thu + Tồn kho) chiếm khoảng {illiquid_pct:.1f}% tổng tài sản. Cần tra cứu phụ lục thuyết minh BCTC để nắm rõ tuổi nợ, trích lập dự phòng khó đòi và khả năng luân chuyển thành tiền mặt."),
        ("2. Giao dịch với các bên liên quan & Dòng tiền nội bộ", f"Cần rà soát các hợp đồng hợp tác kinh doanh, tạm ứng hoặc cho vay nội bộ với các công ty con/liên kết (ghi nhận {sub_count} công ty con) để phát hiện rủi ro luân chuyển vốn bất thường."),
        ("3. Kết quả kinh doanh soát xét các quý tiếp theo", "Theo dõi sát sao báo cáo tài chính quý tới để kiểm chứng xem dòng tiền thuần HĐKD (CFO) và biên lợi nhuận gộp có duy trì đà cải thiện hay không.")
    ]

    items_html = ""
    for title, desc in missing_items:
        items_html += f"""
        <div style="background: rgba(15, 23, 42, 0.6); padding: 12px 16px; border-radius: 10px; border-left: 3px solid #fbbf24; margin-bottom: 10px;">
            <div style="font-weight: 700; color: #fbbf24; font-size: 0.88rem; margin-bottom: 4px;">{title}</div>
            <div style="font-size: 0.84rem; color: #cbd5e1; line-height: 1.55;">{desc}</div>
        </div>
        """

    return f"""
    <div class="card" style="margin-bottom: 24px;">
        <div class="card-header">
            <span>🔎 6. DỮ KIỆN CÒN THIẾU CẦN NHÀ ĐẦU TƯ KIỂM TRA THÊM (MISSING DATA AUDIT)</span>
            <span class="badge" style="background: rgba(245, 158, 11, 0.15); color: #fbbf24;">THẨM ĐỊNH THỰC ĐỊA</span>
        </div>
        <div style="font-size: 0.86rem; color: #94a3b8; margin-bottom: 12px;">
            Theo quy tắc minh bạch của Hội đồng AI (AGENTS.md), không đưa ra giả định võ đoán khi dữ liệu chưa đầy đủ. Các điểm trọng yếu cần người dùng xác minh độc lập:
        </div>
        {items_html}
    </div>
    """


def generate_html_report(
    symbol: str,
    quote: Dict[str, Any],
    fa_result: Dict[str, Any],
    ta_result: Dict[str, Any],
    trade_setup: Dict[str, Any],
    council_result: Dict[str, Any],
    timing_result: Optional[Dict[str, Any]] = None,
    df_ohlcv: Optional[Any] = None
) -> Path:
    """
    Hàm chính xuất bản Báo Cáo HTML Độc Lập Chuyên Sâu Đa Chiều.
    Lưu tại: reports/YYYY-MM-DD_{symbol}.html
    """
    symbol = symbol.upper().strip()
    today_str = datetime.now().strftime("%Y-%m-%d")
    html_filename = f"{today_str}_{symbol}.html"
    html_path = REPORTS_DIR / html_filename

    # Khởi tạo Timing nếu chưa có
    if timing_result is None:
        try:
            from core.timing_engine import analyze_timing_prediction
            timing_result = analyze_timing_prediction(symbol, quote, ta_result, fa_result)
        except Exception:
            timing_result = {}

    # Trích xuất dữ liệu giá
    current_price = trade_setup.get("current_price", quote.get("price", 0))
    if 0 < current_price < 1000:
        current_price *= 1000

    change_pct = quote.get("change_pct", 0)
    chg_sign = "+" if change_pct > 0 else ""
    chg_color = "#10b981" if change_pct > 0 else ("#ef4444" if change_pct < 0 else "#f59e0b")

    action = trade_setup.get("action", "QUAN SÁT")
    confidence = trade_setup.get("confidence", "CAO")
    consensus_score = trade_setup.get("consensus_score", 50)
    fa_score = trade_setup.get("fa_score", 50)
    ta_score = trade_setup.get("ta_score", 50)
    has_valid_setup = trade_setup.get("has_valid_setup", True)

    # Màu sắc Action
    if "MUA MẠNH" in action:
        act_bg, act_border, act_col = "rgba(16, 185, 129, 0.15)", "#10b981", "#10b981"
    elif "MUA" in action:
        act_bg, act_border, act_col = "rgba(59, 130, 246, 0.15)", "#3b82f6", "#38bdf8"
    elif "THEO DÕI" in action:
        act_bg, act_border, act_col = "rgba(245, 158, 11, 0.15)", "#f59e0b", "#fbbf24"
    else:
        act_bg, act_border, act_col = "rgba(239, 68, 68, 0.15)", "#ef4444", "#f87171"

    # Sàn giao dịch
    exchange_val = str(quote.get("exchange") or trade_setup.get("exchange", "HOSE")).upper()
    if exchange_val == "HNX":
        ex_badge = '<span class="badge" style="background: rgba(16, 185, 129, 0.2); color: #34d399; border: 1px solid #10b981;">HNX (±10%)</span>'
    elif exchange_val == "UPCOM":
        ex_badge = '<span class="badge" style="background: rgba(245, 158, 11, 0.2); color: #fbbf24; border: 1px solid #f59e0b;">UPCOM (±15%)</span>'
    else:
        ex_badge = '<span class="badge" style="background: rgba(59, 130, 246, 0.2); color: #60a5fa; border: 1px solid #3b82f6;">HOSE (±7%)</span>'

    # Vĩ mô & Ngành
    macro = fa_result.get("macro", {})
    sector_name = macro.get("sector_name") or quote.get("industry") or "Doanh nghiệp niêm yết"
    cycle_phase = macro.get("cycle_phase", "Bình thường")
    tailwind_score = macro.get("tailwind_score", 70)
    tailwind_color = "#10b981" if tailwind_score >= 80 else ("#3b82f6" if tailwind_score >= 70 else "#f59e0b")

    # Dòng tiền & BCTC
    cf = fa_result.get("cash_flow", {})
    cfo_ttm = cf.get("cfo_ttm", 0)
    capex_ttm = cf.get("capex_ttm", 0)
    fcf_ttm = cf.get("fcf_ttm", 0)
    fin = fa_result.get("ratios", {})
    asset_val = fa_result.get("asset_valuation", {})
    gov = fa_result.get("governance", {})
    segments_data = fa_result.get("segments", {}).get("segments", [])

    # Dữ liệu vẽ Chart.js (quý)
    quarterly_cf = cf.get("quarterly_cash_flows", [])
    chart_quarters = [q["quarter"] for q in quarterly_cf] if quarterly_cf else ["Q3", "Q4", "Q1", "Q2"]
    chart_cfo = [round(q["cfo"] / 1e9, 1) for q in quarterly_cf] if quarterly_cf else [0, 0, 0, 0]
    chart_np = [round(q["net_profit"] / 1e9, 1) for q in quarterly_cf] if quarterly_cf else [0, 0, 0, 0]
    chart_fcf = [round(q["fcf"] / 1e9, 1) for q in quarterly_cf] if quarterly_cf else [0, 0, 0, 0]

    # Timing scenario
    surge = timing_result.get("surge_scenario", {}) if timing_result else {}
    crash = timing_result.get("crash_scenario", {}) if timing_result else {}
    timing_verdict = timing_result.get("timing_verdict", "TÍCH LŨY THEO DÕI") if timing_result else "TÍCH LŨY THEO DÕI"
    timing_color = timing_result.get("timing_color", "#38bdf8") if timing_result else "#38bdf8"
    overall_timing_score = timing_result.get("overall_timing_score", 65) if timing_result else 65

    # Điểm kích hoạt
    trigger_pivot = float(surge.get("trigger_pivot_price") or (current_price * 1.03))
    failure_level = float(crash.get("failure_trigger_level") or (current_price * 0.95))
    stop_loss_lvl = float(trade_setup.get("stop_loss", 0.0))
    tp1_lvl = float(trade_setup.get("take_profit_1", 0.0))
    tp2_lvl = float(trade_setup.get("take_profit_2", 0.0))

    if 0 < trigger_pivot < 1000:
        trigger_pivot *= 1000
    if 0 < failure_level < 1000:
        failure_level *= 1000
    if 0 < stop_loss_lvl < 1000:
        stop_loss_lvl *= 1000
    if 0 < tp1_lvl < 1000:
        tp1_lvl *= 1000

    # Xử lý chuỗi nến cho Lightweight Charts
    if df_ohlcv is None or (isinstance(df_ohlcv, pd.DataFrame) and df_ohlcv.empty):
        try:
            from core.data_loader import get_historical_ohlcv
            df_ohlcv = get_historical_ohlcv(symbol, days=250)
        except Exception:
            df_ohlcv = None

    chart_candles = []
    chart_volume = []
    chart_ema20 = []
    chart_ema50 = []

    if df_ohlcv is not None and isinstance(df_ohlcv, pd.DataFrame) and not df_ohlcv.empty:
        df_calc = df_ohlcv.copy()
        time_col = "time" if "time" in df_calc.columns else ("date" if "date" in df_calc.columns else None)
        if time_col:
            df_calc[time_col] = pd.to_datetime(df_calc[time_col])
            df_calc = df_calc.sort_values(time_col)
        if "ema20" not in df_calc.columns:
            df_calc["ema20"] = df_calc["close"].ewm(span=20, adjust=False).mean()
        if "ema50" not in df_calc.columns:
            df_calc["ema50"] = df_calc["close"].ewm(span=50, adjust=False).mean()

        recent_df = df_calc.tail(160)
        for _, row in recent_df.iterrows():
            t_val = row[time_col] if time_col else datetime.now()
            d_str = t_val.strftime("%Y-%m-%d") if hasattr(t_val, "strftime") else str(t_val)[:10]
            op = float(row["open"])
            hi = float(row["high"])
            lo = float(row["low"])
            cl = float(row["close"])
            v_val = float(row.get("volume", 0))

            chart_candles.append({"time": d_str, "open": op, "high": hi, "low": lo, "close": cl})
            v_color = "rgba(16, 185, 129, 0.7)" if cl >= op else "rgba(239, 68, 68, 0.7)"
            chart_volume.append({"time": d_str, "value": v_val, "color": v_color})
            if pd.notna(row.get("ema20")):
                chart_ema20.append({"time": d_str, "value": round(float(row["ema20"]), 1)})
            if pd.notna(row.get("ema50")):
                chart_ema50.append({"time": d_str, "value": round(float(row["ema50"]), 1)})

    # SVG Fallbacks
    offline_cashflow_svg = render_offline_cashflow_svg(chart_quarters, chart_np, chart_cfo, chart_fcf)
    offline_candles_svg = render_offline_candles_svg(chart_candles)

    # HTML Snippets
    eli5_html = build_eli5_html(symbol, quote, fa_result, ta_result, trade_setup)
    macro_matrix_html = build_macro_impact_matrix(symbol, sector_name, macro.get("global_commodities", {}))
    smart_pulse_html = build_smart_money_and_catalyst_html(timing_result)
    five_schools_html = build_five_schools_matrix_html(symbol, council_result, fa_result, ta_result, trade_setup)
    clash_html = build_clash_of_perspectives_html(council_result.get("clash_of_perspectives"), symbol, trade_setup)
    fa_deep_dive_html = build_fa_deep_dive_html(symbol, fa_result, quote, cf, fin, asset_val, gov, segments_data)
    ta_deep_dive_html = build_ta_deep_dive_html(symbol, ta_result, quote, df_ohlcv, current_price, trigger_pivot, stop_loss_lvl, tp1_lvl, offline_candles_svg)
    scenarios_html = build_scenarios_and_invalidation_html(symbol, trade_setup, current_price, has_valid_setup)
    missing_data_html = build_missing_data_audit_html(symbol, fa_result)
    glossary_html = build_glossary_html()

    cfo_human_str = format_vnd_human(cfo_ttm)
    fcf_human_str = format_vnd_human(fcf_ttm)
    pb_flt = float(asset_val.get("pb") or 0.0) if isinstance(asset_val.get("pb"), (int, float)) else 0.0
    bvps_flt = float(asset_val.get("bvps") or 0.0) if isinstance(asset_val.get("bvps"), (int, float)) else 0.0
    active_buy_flt = float(timing_result.get("smart_money_pulse", {}).get("active_buy_pct", 50.0)) if timing_result else 50.0
    qa_html = build_interactive_council_qa_html(
        symbol=symbol,
        current_price=current_price,
        fair_price=float(trade_setup.get("fair_price") or current_price),
        stop_loss=stop_loss_lvl,
        sl_pct=float(trade_setup.get("stop_loss_pct", 0.0)),
        tp1=tp1_lvl,
        tp1_pct=float(trade_setup.get("take_profit_1_pct", 0.0)),
        trigger_pivot=trigger_pivot,
        cfo_human=cfo_human_str,
        fcf_human=fcf_human_str,
        pb=pb_flt,
        bvps=bvps_flt,
        active_buy_pct=active_buy_flt
    )

    # Hiển thị Kế hoạch Giao dịch
    if has_valid_setup and stop_loss_lvl > 0:
        rr_display = f"R:R {trade_setup.get('risk_reward_ratio', 0)}:1"
        swing_zone_display = f"{trade_setup.get('swing_buy_zone')} đ"
        sl_display = f"{trade_setup.get('stop_loss', 0):,.0f} đ (-{trade_setup.get('stop_loss_pct', 0)}%)"
        tp_display = f"{trade_setup.get('take_profit_1', 0):,.0f} đ (+{trade_setup.get('take_profit_1_pct', 0)}%) &bull; {trade_setup.get('take_profit_2', 0):,.0f} đ (+{trade_setup.get('take_profit_2_pct', 0)}%)"
        pos_display = f"Max {trade_setup.get('max_position_size_pct', 10.0):.1f}% tổng NAV"
        swing_note_display = trade_setup.get('swing_strategy_note', '')
    else:
        rr_display = "N/A"
        swing_zone_display = "KHÔNG CÓ VÙNG MUA (BẢO TOÀN VỐN)"
        sl_display = "N/A (Chưa mở vị thế)"
        tp_display = "N/A"
        pos_display = "0% (Đứng ngoài quan sát)"
        swing_note_display = trade_setup.get('action_summary') or "Không giải ngân khi cổ phiếu vi phạm kỷ luật bảo vệ vốn."

    # Tính toán Thước đo Kích hoạt Thời điểm (Price Ladder Gauge)
    dist_pivot_pct = ((trigger_pivot - current_price) / current_price * 100) if current_price > 0 else 0.0
    dist_sl_pct = ((stop_loss_lvl - current_price) / current_price * 100) if (current_price > 0 and stop_loss_lvl > 0) else 0.0
    dist_fail_pct = ((failure_level - current_price) / current_price * 100) if current_price > 0 else 0.0
    dist_tp1_pct = ((tp1_lvl - current_price) / current_price * 100) if (current_price > 0 and tp1_lvl > 0) else 0.0

    if not has_valid_setup or stop_loss_lvl <= 0:
        price_ladder_html = f"""
        <div class="price-ladder-box" style="border: 1px solid rgba(239, 68, 68, 0.35);">
            <div class="ladder-header">
                <span>🪜 THƯỚC ĐO KÍCH HOẠT THỜI ĐIỂM (PRICE LADDER & DISTANCE GAUGE)</span>
                <span class="badge" style="background: rgba(239, 68, 68, 0.2); color: #f87171; border: 1px solid #ef4444;">KHÔNG CÓ ĐIỂM MUA HỢP LỆ</span>
            </div>
            <div style="padding: 18px 20px; text-align: center; color: #cbd5e1; font-size: 0.9rem; line-height: 1.7;">
                <div style="font-size: 1.15rem; margin-bottom: 6px;">🛡️ <b>Trạng thái: Đứng ngoài bảo toàn vốn (No Trade Setup)</b></div>
                <div>{trade_setup.get('action_summary', 'Cổ phiếu chưa hình thành mẫu hình tích lũy hoặc vi phạm bộ lọc kỹ thuật / quản trị rủi ro.')}</div>
                <div style="margin-top: 10px; font-size: 0.84rem; color: #94a3b8;">
                    Ngưỡng hỗ trợ quan sát đáy: <b style="color: #ef4444;">{failure_level:,.0f} đ</b> &bull; Mốc cản Pivot cần vượt để xác nhận đảo chiều: <b style="color: #38bdf8;">{trigger_pivot:,.0f} đ</b>
                </div>
            </div>
        </div>
        """
    else:
        n1_label, n1_price, n1_dist, n1_cls = ("CẮT LỖ (SL)", stop_loss_lvl, dist_sl_pct, "step-sl")
        n2_label, n2_price, n2_dist, n2_cls = ("NGƯỠNG GÃY SÓNG", failure_level, dist_fail_pct, "step-fail")
        if stop_loss_lvl > failure_level:
            n1_label, n1_price, n1_dist, n1_cls = ("NGƯỠNG GÃY SÓNG", failure_level, dist_fail_pct, "step-fail")
            n2_label, n2_price, n2_dist, n2_cls = ("CẮT LỖ (SL)", stop_loss_lvl, dist_sl_pct, "step-sl")

        pivot_status_text = "CỰC KỲ SÁT ĐIỂM NỔ! Chuẩn bị giải ngân khi vượt" if 0 < dist_pivot_pct <= 2.5 else ("ĐÃ VƯỢT QUA PIVOT (Đang giữ nhịp bứt phá)!" if dist_pivot_pct <= 0 else "Đang tích lũy, kiên nhẫn chờ vượt")

        price_ladder_html = f"""
        <div class="price-ladder-box">
            <div class="ladder-header">
                <span>🪜 THƯỚC ĐO KÍCH HOẠT THỜI ĐIỂM (PRICE LADDER & DISTANCE GAUGE)</span>
                <span class="badge" style="background: rgba(56, 189, 248, 0.15); color: #38bdf8;">Khoảng Cách Tương Đối</span>
            </div>
            <div class="ladder-track">
                <!-- Node 1: Mức cảnh báo thấp hơn -->
                <div class="ladder-step {n1_cls}">
                    <div class="step-label">{n1_label}</div>
                    <div class="step-price">{n1_price:,.0f} đ</div>
                    <div class="step-dist">{n1_dist:+.1f}%</div>
                </div>
                <div class="ladder-connector conn-danger"></div>
                <!-- Node 2: Mức phòng thủ sát thị giá -->
                <div class="ladder-step {n2_cls}">
                    <div class="step-label">{n2_label}</div>
                    <div class="step-price">{n2_price:,.0f} đ</div>
                    <div class="step-dist">{n2_dist:+.1f}%</div>
                </div>
                <div class="ladder-connector conn-current"></div>
                <!-- Node 3: Thị Giá Hiện Tại -->
                <div class="ladder-step step-current">
                    <div class="step-pin">📍 ĐANG Ở ĐÂY</div>
                    <div class="step-price">{current_price:,.0f} đ</div>
                    <div class="step-dist">Thị giá hiện tại</div>
                </div>
                <div class="ladder-connector conn-pivot"></div>
                <!-- Node 4: Pivot Bứt Phá -->
                <div class="ladder-step step-pivot">
                    <div class="step-label">PIVOT BỨT PHÁ</div>
                    <div class="step-price">{trigger_pivot:,.0f} đ</div>
                    <div class="step-dist">{dist_pivot_pct:+.1f}%</div>
                </div>
                <div class="ladder-connector conn-tp"></div>
                <!-- Node 5: Mục Tiêu 1 -->
                <div class="ladder-step step-tp1">
                    <div class="step-label">MỤC TIÊU 1 (TP1)</div>
                    <div class="step-price">{tp1_lvl:,.0f} đ</div>
                    <div class="step-dist">{dist_tp1_pct:+.1f}%</div>
                </div>
            </div>
            <div class="ladder-summary-bar">
                <div>
                    ⚡ Cách điểm nổ Pivot: <b style="color: {'#34d399' if 0 <= dist_pivot_pct <= 2.5 else '#38bdf8'};">{dist_pivot_pct:+.1f}%</b> 
                    <span>({pivot_status_text})</span>
                </div>
                <div>
                    🛡️ Vùng đệm an toàn tới Cắt Lỗ: <b style="color: {'#fbbf24' if abs(dist_sl_pct) >= 4 else '#ef4444'};">{abs(dist_sl_pct):.1f}%</b>
                </div>
            </div>
        </div>
        """

    # Lắp ráp HTML Master Page
    html_content = f"""<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>Báo cáo Chiến lược Toàn diện {symbol} | Hội đồng Tham mưu Đầu tư TTCK Việt Nam</title>
    <!-- Chart.js & Lightweight Charts via CDN -->
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script src="https://unpkg.com/lightweight-charts@4.1.3/dist/lightweight-charts.standalone.production.js"></script>
    <style>
        :root {{
            --bg-main: #060913;
            --bg-card: #0d1424;
            --bg-card-alt: #141e34;
            --border: #1e293b;
            --border-highlight: #38bdf8;
            --text-primary: #f8fafc;
            --text-secondary: #94a3b8;
            --text-muted: #64748b;
            --accent-green: #10b981;
            --accent-red: #ef4444;
            --accent-blue: #38bdf8;
            --accent-amber: #f59e0b;
            --accent-purple: #a855f7;
        }}
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
            background-color: var(--bg-main);
            color: var(--text-primary);
            line-height: 1.6;
            padding-bottom: 70px;
            -webkit-font-smoothing: antialiased;
        }}
        .top-navbar {{
            position: sticky; top: 0; z-index: 100;
            background: rgba(6, 9, 19, 0.95);
            backdrop-filter: blur(14px);
            border-bottom: 1px solid var(--border);
            padding: 12px 24px;
            display: flex; justify-content: space-between; align-items: center;
        }}
        .brand-title {{
            font-size: 0.9rem; font-weight: 800; color: #fff;
            letter-spacing: 0.8px; text-transform: uppercase;
        }}
        .report-time {{ font-size: 0.8rem; color: var(--text-muted); }}
        .container {{ max-width: 1240px; margin: 0 auto; padding: 24px 18px; }}
        
        /* HERO & EXECUTIVE VERDICT */
        .hero-card {{
            background: linear-gradient(145deg, #101828, #0b1120);
            border: 1px solid var(--border);
            border-radius: 18px;
            padding: 26px;
            margin-bottom: 24px;
            box-shadow: 0 12px 35px rgba(0, 0, 0, 0.45);
        }}
        .hero-header {{
            display: flex; justify-content: space-between; align-items: flex-start;
            flex-wrap: wrap; gap: 18px;
        }}
        .hero-left h1 {{
            font-size: 2.3rem; font-weight: 800; color: #fff;
            letter-spacing: -0.5px; display: flex; align-items: center; gap: 12px;
        }}
        .hero-price {{ font-size: 1.9rem; font-weight: 800; color: {chg_color}; }}
        .hero-change {{
            font-size: 1.05rem; font-weight: 700; color: {chg_color};
            background: rgba(255, 255, 255, 0.06); padding: 4px 10px; border-radius: 8px;
        }}
        
        /* EXECUTIVE ONE-LINE VERDICT BOX */
        .verdict-box {{
            background: {act_bg};
            border: 1.5px solid {act_border};
            border-radius: 16px;
            padding: 20px 24px;
            margin-top: 20px;
            display: flex; justify-content: space-between; align-items: center;
            flex-wrap: wrap; gap: 16px;
        }}
        .verdict-title {{
            font-size: 1.45rem; font-weight: 900; color: {act_col};
            display: flex; align-items: center; gap: 10px;
        }}
        .verdict-reason {{
            font-size: 0.95rem; color: #cbd5e1; margin-top: 6px; line-height: 1.6;
        }}
        
        /* QUICK NAV */
        .quick-nav-bar {{
            position: sticky; top: 48px; z-index: 95;
            background: rgba(6, 9, 19, 0.95);
            backdrop-filter: blur(14px);
            border-bottom: 1px solid var(--border);
            padding: 10px 18px; margin: -12px -18px 26px -18px;
            display: flex; gap: 8px; overflow-x: auto; scrollbar-width: none;
        }}
        .quick-nav-bar::-webkit-scrollbar {{ display: none; }}
        .q-link {{
            color: var(--text-secondary); text-decoration: none;
            font-size: 12px; font-weight: 700; padding: 6px 14px;
            border-radius: 8px; background: rgba(255, 255, 255, 0.04);
            border: 1px solid rgba(255, 255, 255, 0.06); white-space: nowrap;
            transition: all 0.2s;
        }}
        .q-link:hover {{ color: #fff; background: var(--bg-card-alt); border-color: var(--accent-blue); }}
        
        /* CARDS & TABLES */
        .card {{
            background: var(--bg-card); border: 1px solid var(--border);
            border-radius: 16px; padding: 22px; box-shadow: 0 4px 20px rgba(0, 0, 0, 0.25);
        }}
        .card-header {{
            font-size: 1.05rem; font-weight: 800; color: #f1f5f9;
            margin-bottom: 16px; display: flex; justify-content: space-between;
            align-items: center; border-bottom: 1px solid rgba(255, 255, 255, 0.06);
            padding-bottom: 12px;
        }}
        .badge {{
            display: inline-block; font-size: 0.75rem; font-weight: 700;
            padding: 4px 10px; border-radius: 6px; letter-spacing: 0.3px;
        }}
        .table-responsive {{ overflow-x: auto; -webkit-overflow-scrolling: touch; }}
        table {{ width: 100%; border-collapse: collapse; font-size: 0.88rem; }}
        th, td {{ padding: 12px 14px; border-bottom: 1px solid var(--border); text-align: left; }}
        th {{ background: rgba(15, 23, 42, 0.85); color: var(--text-muted); font-weight: 700; font-size: 0.78rem; text-transform: uppercase; }}
        
        /* TABS */
        .qa-tabs-nav {{ display: flex; gap: 8px; margin-bottom: 14px; flex-wrap: wrap; }}
        .qa-tab-btn {{
            background: rgba(255, 255, 255, 0.05); border: 1px solid var(--border);
            color: #cbd5e1; padding: 8px 16px; border-radius: 8px; font-weight: 700;
            font-size: 0.85rem; cursor: pointer; transition: all 0.2s;
        }}
        .qa-tab-btn:hover {{ background: rgba(56, 189, 248, 0.15); color: #38bdf8; }}
        .qa-tab-active {{ background: #38bdf8 !important; color: #070c16 !important; border-color: #38bdf8 !important; }}
        .qa-answer-box {{ background: rgba(15, 23, 42, 0.7); border: 1px solid var(--border); border-radius: 12px; padding: 16px 20px; font-size: 0.92rem; color: #cbd5e1; line-height: 1.7; }}
        .qa-speaker {{ font-weight: 800; color: #38bdf8; }}
        
        /* PRICE LADDER GAUGE */
        .price-ladder-box {{
            background: rgba(2, 6, 23, 0.65);
            border: 1px solid rgba(56, 189, 248, 0.25);
            border-radius: 14px;
            padding: 18px 20px;
            margin-top: 18px;
        }}
        .ladder-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-size: 0.8rem;
            font-weight: 700;
            color: #94a3b8;
            margin-bottom: 16px;
        }}
        .ladder-track {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            overflow-x: auto;
            padding: 10px 0;
            gap: 6px;
        }}
        .ladder-step {{
            text-align: center;
            padding: 10px 14px;
            border-radius: 10px;
            min-width: 125px;
            border: 1px solid;
            background: rgba(15, 23, 42, 0.85);
        }}
        .step-label {{
            font-size: 10px;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 4px;
        }}
        .step-price {{
            font-family: -apple-system, sans-serif;
            font-size: 14px;
            font-weight: 800;
        }}
        .step-dist {{
            font-size: 11px;
            font-weight: 600;
            margin-top: 2px;
        }}
        .step-fail {{ border-color: #ef4444; color: #fca5a5; }}
        .step-sl {{ border-color: #f87171; color: #fca5a5; }}
        .step-current {{
            border-color: #fbbf24;
            background: rgba(251, 191, 36, 0.12);
            color: #fff;
            box-shadow: 0 0 16px rgba(251, 191, 36, 0.25);
            transform: scale(1.04);
        }}
        .step-pin {{
            font-size: 10px;
            font-weight: 800;
            color: #fbbf24;
            margin-bottom: 4px;
        }}
        .step-pivot {{ border-color: #10b981; color: #6ee7b7; background: rgba(16, 185, 129, 0.08); }}
        .step-tp1 {{ border-color: #38bdf8; color: #7dd3fc; }}
        .ladder-connector {{
            flex: 1;
            height: 3px;
            min-width: 16px;
            background: #334155;
            border-radius: 2px;
        }}
        .conn-danger {{ background: linear-gradient(90deg, #ef4444, #f87171); }}
        .conn-current {{ background: linear-gradient(90deg, #f87171, #fbbf24); }}
        .conn-pivot {{ background: linear-gradient(90deg, #fbbf24, #10b981); }}
        .conn-tp {{ background: linear-gradient(90deg, #10b981, #38bdf8); }}
        .ladder-summary-bar {{
            margin-top: 14px;
            padding-top: 12px;
            border-top: 1px solid rgba(255, 255, 255, 0.06);
            display: flex;
            justify-content: space-between;
            flex-wrap: wrap;
            gap: 10px;
            font-size: 0.85rem;
            color: #cbd5e1;
        }}
        
        @media (max-width: 768px) {{
            .hero-header {{ flex-direction: column; align-items: stretch; }}
            .verdict-box {{ flex-direction: column; align-items: stretch; }}
        }}
    </style>
</head>
<body>

    <!-- TOP NAVBAR -->
    <div class="top-navbar">
        <div class="brand-title">🏛️ VIETNAM STOCK ANALYZER &bull; BÁO CÁO THAM MƯU ĐẦU TƯ TOÀN DIỆN</div>
        <div class="report-time">{datetime.now().strftime('%d/%m/%Y %H:%M:%S')}</div>
    </div>

    <div class="container">

        <!-- EXECUTIVE HERO CARD -->
        <div class="hero-card">
            <div class="hero-header">
                <div class="hero-left">
                    <h1>
                        {symbol}
                        {ex_badge}
                        <span class="badge" style="background: rgba(139, 92, 246, 0.2); color: #c084fc; border: 1px solid #8b5cf6;">{sector_name}</span>
                    </h1>
                    <p style="color: var(--text-secondary); font-size: 0.95rem; margin-top: 4px;">{quote.get('company_name', symbol)}</p>
                    <div style="display: flex; align-items: baseline; gap: 12px; margin-top: 10px; flex-wrap: wrap;">
                        <span class="hero-price">{current_price:,.0f} đ</span>
                        <span class="hero-change">{chg_sign}{change_pct:.2f}%</span>
                        <span style="font-size: 0.85rem; color: #94a3b8;">Khối lượng: <b>{quote.get('volume', 0):,.0f}</b> CP ({ta_result.get('indicators', {}).get('vol_ratio', 1.0):.2f}x MA20)</span>
                    </div>
                </div>

                <div style="text-align: right;">
                    <div style="font-size: 0.78rem; color: var(--text-muted); text-transform: uppercase;">Độ đồng thuận Hội đồng AI</div>
                    <div style="font-size: 1.8rem; font-weight: 900; color: {act_col}; margin-top: 2px;">
                        {consensus_score}/100 <span style="font-size: 0.9rem; font-weight: normal; color: #94a3b8;">điểm</span>
                    </div>
                    <div style="font-size: 0.8rem; color: #94a3b8;">FA: <b>{fa_score}/100</b> &bull; TA: <b>{ta_score}/100</b></div>
                </div>
            </div>

            <!-- HỘP KẾT LUẬN MỘT DÒNG BẮT BUỘC (EXECUTIVE 1-LINE VERDICT) -->
            <div class="verdict-box">
                <div style="flex: 1;">
                    <div class="verdict-title">
                        <span>🎯 KẾT LUẬN MỘT DÒNG:</span> {action} 
                        <span class="badge" style="background: rgba(255,255,255,0.1); color: #fff; font-size: 0.75rem; border: 1px solid rgba(255,255,255,0.2);">Độ tin cậy: {confidence}</span>
                    </div>
                    <div class="verdict-reason">
                        <b>Lý giải cốt lõi:</b> {trade_setup.get('action_summary', 'Cổ phiếu vi phạm các tiêu chí an toàn vốn hoặc nằm trong xu hướng giảm.')}
                    </div>
                </div>
            </div>

            <!-- TÁCH BẠCH 2 KẾ HOẠCH GIAO DỊCH -->
            <div style="margin-top: 20px; display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 16px;">
                <!-- Chiến lược Đầu tư Giá trị -->
                <div style="background: rgba(30, 41, 59, 0.7); border: 1px solid #334155; border-radius: 14px; padding: 18px;">
                    <div style="font-size: 0.9rem; font-weight: 700; color: #38bdf8; display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; border-bottom: 1px solid rgba(255,255,255,0.06); padding-bottom: 8px;">
                        <span>🏛️ ĐẦU TƯ GIÁ TRỊ (BUFFETT & GRAHAM)</span>
                        <span class="badge" style="background: rgba(56, 189, 248, 0.15); color: #38bdf8; border: 1px solid #38bdf8;">{trade_setup.get('value_status', 'ĐỊNH GIÁ HỢP LÝ')}</span>
                    </div>
                    <div style="font-size: 0.88rem; color: #cbd5e1; line-height: 1.7;">
                        • Giá trị thực ước tính: <b style="color: #fff; font-size: 1.05rem;">{float(trade_setup.get('fair_price') or current_price):,.0f} đ</b><br>
                        • Vùng gom an toàn: <b style="color: #34d399;">{trade_setup.get('value_buy_zone')}</b><br>
                        • Cơ sở định giá: <i>{trade_setup.get('value_rationale')}</i>
                    </div>
                </div>

                <!-- Chiến lược Lướt sóng Kỹ thuật -->
                <div style="background: rgba(30, 41, 59, 0.7); border: 1px solid #334155; border-radius: 14px; padding: 18px;">
                    <div style="font-size: 0.9rem; font-weight: 700; color: #fbbf24; display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; border-bottom: 1px solid rgba(255,255,255,0.06); padding-bottom: 8px;">
                        <span>🏄 LƯỚT SÓNG NGẮN HẠN (SWING / KỸ THUẬT)</span>
                        <span class="badge" style="background: rgba(251, 191, 36, 0.15); color: #fbbf24; border: 1px solid #fbbf24;">{rr_display}</span>
                    </div>
                    <div style="font-size: 0.88rem; color: #cbd5e1; line-height: 1.7;">
                        • Vùng mua lướt sóng: <b style="color: #38bdf8;">{swing_zone_display}</b><br>
                        • Cắt lỗ nghiêm ngặt (SL): <b style="color: #f87171;">{sl_display}</b><br>
                        • Chốt lời (Mục tiêu 1 &bull; 2): <b style="color: #34d399;">{tp_display}</b><br>
                        • Tỷ trọng tối đa: <b>{pos_display}</b>
                    </div>
                </div>
            </div>
        </div>

        <!-- QUICK NAV BAR -->
        <div class="quick-nav-bar">
            <a href="#sec-eli5" class="q-link">🧒 Bản Chất Cốt Lõi (ELI5)</a>
            <a href="#sec-matrix" class="q-link">🏛️ Bảng 5 Trường Phái</a>
            <a href="#sec-fa" class="q-link">🔬 Phân Tích Cơ Bản (FA)</a>
            <a href="#sec-ta" class="q-link">📈 Phân Tích Kỹ Thuật (TA)</a>
            <a href="#sec-timing" class="q-link">⚡ Động Cơ Thời Điểm</a>
            <a href="#sec-scenarios" class="q-link">🔮 Kịch Bản & Invalidation</a>
            <a href="#sec-qa" class="q-link">💬 Bàn Tròn Hỏi Đáp</a>
            <a href="#sec-glossary" class="q-link">📚 Sổ Tay Thuật Ngữ</a>
        </div>

        <!-- PHÂN HỆ 1: GIẢI THÍCH CHO ĐỨA TRẺ LÊN 5 (ELI5) -->
        {eli5_html}

        <!-- PHẦN 1: BẢNG GÓC NHÌN 5 TRƯỜNG PHÁI & KHỐI MÂU THUẪN -->
        <div id="sec-matrix">
            {five_schools_html}
            {clash_html}
        </div>

        <!-- PHẦN 2: PHÂN TÍCH CƠ BẢN DOANH NGHIỆP CHUYÊN SÂU (FA DEEP-DIVE) -->
        <div id="sec-fa">
            {fa_deep_dive_html}
        </div>

        <!-- BIỂU ĐỒ DÒNG TIỀN THẬT CHART.JS -->
        <div class="card" style="margin-bottom: 24px;">
            <div class="card-header">
                <span>🔬 SO SÁNH DÒNG TIỀN THẬT (CFO) VS LNST KẾ TOÁN (TỶ VNĐ)</span>
                <span class="badge" style="background: rgba(56, 189, 248, 0.15); color: #38bdf8;">4 QUÝ GẦN NHẤT</span>
            </div>
            <div style="min-height: 250px; position: relative;" id="cashFlowChartContainer">
                <canvas id="cashFlowChart"></canvas>
                <div id="cashFlowOfflineFallback" style="display: none;">
                    {offline_cashflow_svg}
                </div>
            </div>
            <div style="font-size: 0.8rem; color: var(--text-muted); text-align: center; margin-top: 12px;">
                Cột xanh dương: Lợi nhuận sau thuế kế toán &bull; Cột xanh lá: Tiền kinh doanh thật (CFO) &bull; Đường vàng: Dòng tiền tự do (FCF)
            </div>
        </div>

        <!-- PHẦN 3: PHÂN TÍCH KỸ THUẬT & DÒNG TIỀN CHUYÊN SÂU (TA DEEP-DIVE) -->
        <div id="sec-ta">
            {ta_deep_dive_html}
        </div>

        <!-- PHẦN 4: ĐỘNG CƠ THỜI ĐIỂM TĂNG/SẬP & THƯỚC ĐO KÍCH HOẠT -->
        <div id="sec-timing" style="background: linear-gradient(145deg, #131c2e, #0c1220); border: 1px solid rgba(56, 189, 248, 0.35); border-radius: 18px; padding: 22px; margin-bottom: 28px;">
            <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 12px; margin-bottom: 18px; border-bottom: 1px solid rgba(255,255,255,0.08); padding-bottom: 14px;">
                <div>
                    <div style="font-size: 0.8rem; font-weight: 700; color: #38bdf8; text-transform: uppercase;">⚡ ĐỘNG CƠ DỰ BÁO THỜI ĐIỂM (TIMING PREDICTION MATRIX)</div>
                    <div style="font-size: 1.25rem; font-weight: 800; color: #fff; margin-top: 2px;">
                        Phán Quyết: <span style="color: {timing_color};">{timing_verdict}</span>
                    </div>
                </div>
                <div style="display: flex; align-items: center; gap: 10px;">
                    <span style="font-size: 0.85rem; color: #94a3b8;">Điểm Thời Điểm Tối Ưu:</span>
                    <span style="font-size: 1.4rem; font-weight: 800; color: {timing_color}; background: rgba(255,255,255,0.06); padding: 4px 14px; border-radius: 10px; border: 1px solid {timing_color};">
                        {overall_timing_score}/100
                    </span>
                </div>
            </div>

            {smart_pulse_html}

            <!-- 2 CỘT: KHI NÀO TĂNG vs KHI NÀO SẬP -->
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(340px, 1fr)); gap: 18px; margin-bottom: 18px;">
                <!-- KHI NÀO TĂNG -->
                <div style="background: rgba(16, 185, 129, 0.08); border: 1px solid rgba(16, 185, 129, 0.3); border-radius: 14px; padding: 18px;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                        <span style="font-weight: 800; color: #10b981; font-size: 0.95rem;">🚀 KỊCH BẢN BỨT PHÁ (KHI NÀO TĂNG?)</span>
                        <span class="badge" style="background: rgba(16, 185, 129, 0.2); color: #10b981;">Xác suất {surge.get('probability_pct', 50)}%</span>
                    </div>
                    <div style="font-size: 0.88rem; color: #cbd5e1; line-height: 1.7;">
                        • <b>Khung thời gian bùng nổ:</b> <span style="color: #34d399; font-weight: 700;">{surge.get('timing_window', 'N/A')}</span><br>
                        • <b>Mốc giá kích hoạt xác nhận:</b> Vượt qua <b style="color: #fff;">{trigger_pivot:,.0f} đ</b> kèm Vol &ge; 1.3x MA20.<br>
                        • <b>Hướng dẫn hành động:</b> {surge.get('action_advice', 'Kiên nhẫn theo dõi.')}
                    </div>
                </div>

                <!-- KHI NÀO SẬP -->
                <div style="background: rgba(239, 68, 68, 0.08); border: 1px solid rgba(239, 68, 68, 0.3); border-radius: 14px; padding: 18px;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                        <span style="font-weight: 800; color: #ef4444; font-size: 0.95rem;">⚠️ KỊCH BẢN RỦI RO (KHI NÀO SẬP?)</span>
                        <span class="badge" style="background: rgba(239, 68, 68, 0.2); color: #f87171;">Rủi ro {crash.get('risk_probability_pct', 20)}%</span>
                    </div>
                    <div style="font-size: 0.88rem; color: #cbd5e1; line-height: 1.7;">
                        • <b>Khung thời gian rủi ro:</b> <span style="color: #f87171; font-weight: 700;">{crash.get('timing_window', 'N/A')}</span><br>
                        • <b>Mức giá vi phạm kích hoạt gãy:</b> Thủng mốc <b style="color: #f87171;">{failure_level:,.0f} đ</b>.<br>
                        • <b>Nguyên tắc mất hiệu lực:</b> {crash.get('invalidation_rule', 'Cắt lỗ bảo vệ tài khoản.')}
                    </div>
                </div>
            </div>

            <!-- THƯỚC ĐO KÍCH HOẠT TRỰC QUAN (PRICE LADDER) -->
            {price_ladder_html}
        </div>

        <!-- PHẦN 5: DỰ PHÓNG KỊCH BẢN & ĐIỀU KIỆN MẤT HIỆU LỰC -->
        <div id="sec-scenarios">
            {scenarios_html}
            {missing_data_html}
        </div>

        <!-- PHẦN 6: MA TRẬN VĨ MÔ & HÀNG HÓA -->
        <div class="card" style="margin-bottom: 24px;">
            <div class="card-header">
                <span>📡 RADAR VĨ MÔ QUỐC TẾ & HÀNG HÓA TOÀN CẦU (COMMODITY MATRIX)</span>
                <span class="badge" style="background: rgba(56, 189, 248, 0.15); color: #38bdf8;">CHI PHÍ & ĐẦU RA</span>
            </div>
            {macro_matrix_html}
        </div>

        <!-- PHẦN 7: BÀN TRÒN HỎI ĐÁP & GLOSSARY -->
        {qa_html}
        {glossary_html}

        <!-- FOOTER PHÁP LÝ & BẢO VỆ VỐN -->
        <div style="text-align: center; color: var(--text-muted); font-size: 0.82rem; margin-top: 50px; padding-top: 24px; border-top: 1px solid var(--border); line-height: 1.7;">
            Báo cáo phân tích nghiên cứu chiến lược được khởi tạo tự động bởi Hệ thống <b>Vietnam Stock Analyzer Terminal</b>.<br>
            <i>⚠️ Lưu ý miễn trừ trách nhiệm: Báo cáo là sản phẩm tham mưu hỗ trợ quyết định khách quan độc lập, không cấu thành lời mời chào hay khuyến nghị bảo đảm sinh lời. Quyết định giải ngân cuối cùng thuộc về nhà đầu tư cá nhân.</i>
        </div>

    </div>

    <!-- SCRIPT VẼ BIỂU ĐỒ CHART.JS -->
    <script>
        try {{
            if (typeof Chart === 'undefined') {{
                const fb = document.getElementById('cashFlowOfflineFallback');
                const cv = document.getElementById('cashFlowChart');
                if (fb) fb.style.display = 'block';
                if (cv) cv.style.display = 'none';
            }} else {{
                const ctx = document.getElementById('cashFlowChart').getContext('2d');
                new Chart(ctx, {{
                    type: 'bar',
                    data: {{
                        labels: {json.dumps(chart_quarters)},
                        datasets: [
                            {{
                                label: 'Lợi nhuận sau thuế kế toán (Tỷ đ)',
                                data: {json.dumps(chart_np)},
                                backgroundColor: 'rgba(56, 189, 248, 0.7)',
                                borderColor: '#38bdf8',
                                borderWidth: 1, borderRadius: 4
                            }},
                            {{
                                label: 'Tiền kinh doanh thật - CFO (Tỷ đ)',
                                data: {json.dumps(chart_cfo)},
                                backgroundColor: 'rgba(52, 211, 153, 0.7)',
                                borderColor: '#34d399',
                                borderWidth: 1, borderRadius: 4
                            }},
                            {{
                                type: 'line',
                                label: 'Dòng tiền tự do - FCF (Tỷ đ)',
                                data: {json.dumps(chart_fcf)},
                                borderColor: '#fbbf24',
                                backgroundColor: '#fbbf24',
                                borderWidth: 2, tension: 0.3, pointRadius: 4
                            }}
                        ]
                    }},
                    options: {{
                        responsive: true, maintainAspectRatio: false,
                        plugins: {{ legend: {{ labels: {{ color: '#94a3b8', font: {{ size: 11 }} }} }} }},
                        scales: {{
                            x: {{ grid: {{ color: 'rgba(255, 255, 255, 0.05)' }}, ticks: {{ color: '#94a3b8', font: {{ size: 11 }} }} }},
                            y: {{ grid: {{ color: 'rgba(255, 255, 255, 0.05)' }}, ticks: {{ color: '#94a3b8', font: {{ size: 11 }} }} }}
                        }}
                    }}
                }});
            }}
        }} catch(e) {{
            const fb = document.getElementById('cashFlowOfflineFallback');
            const cv = document.getElementById('cashFlowChart');
            if (fb) fb.style.display = 'block';
            if (cv) cv.style.display = 'none';
        }}

        // SCRIPT VẼ BIỂU ĐỒ NẾN TRADINGVIEW LIGHTWEIGHT CHARTS
        (function() {{
            const chartDiv = document.getElementById('tvChartContainer');
            if (!chartDiv) return;
            if (typeof LightweightCharts === 'undefined') {{
                const fb = document.getElementById('tvChartOfflineFallback');
                if (fb) fb.style.display = 'block';
                return;
            }}

            const candleData = {json.dumps(chart_candles)};
            const volData = {json.dumps(chart_volume)};
            const ema20Data = {json.dumps(chart_ema20)};
            const ema50Data = {json.dumps(chart_ema50)};

            if (!candleData || candleData.length === 0) {{
                chartDiv.innerHTML = '<div style="display:flex;align-items:center;justify-content:center;height:100%;color:#64748b;">Đang cập nhật chuỗi dữ liệu nến...</div>';
                return;
            }}

            const chart = LightweightCharts.createChart(chartDiv, {{
                width: chartDiv.clientWidth,
                height: 460,
                layout: {{
                    background: {{ color: '#070c16' }},
                    textColor: '#94a3b8',
                    fontSize: 11,
                    fontFamily: "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif"
                }},
                grid: {{
                    vertLines: {{ color: 'rgba(255, 255, 255, 0.03)' }},
                    horzLines: {{ color: 'rgba(255, 255, 255, 0.03)' }}
                }},
                crosshair: {{ mode: LightweightCharts.CrosshairMode.Normal }},
                rightPriceScale: {{
                    borderColor: 'rgba(255, 255, 255, 0.08)',
                    scaleMargins: {{ top: 0.08, bottom: 0.22 }}
                }},
                timeScale: {{
                    borderColor: 'rgba(255, 255, 255, 0.08)',
                    timeVisible: true, secondsVisible: false
                }}
            }});

            const candleSeries = chart.addCandlestickSeries({{
                upColor: '#10b981', downColor: '#ef4444',
                borderDownColor: '#ef4444', borderUpColor: '#10b981',
                wickDownColor: '#ef4444', wickUpColor: '#10b981'
            }});
            candleSeries.setData(candleData);

            const volSeries = chart.addHistogramSeries({{
                priceFormat: {{ type: 'volume' }},
                priceScaleId: '',
                scaleMargins: {{ top: 0.78, bottom: 0 }}
            }});
            volSeries.setData(volData);

            if (ema20Data.length > 0) {{
                const ema20Line = chart.addLineSeries({{
                    color: '#fbbf24', lineWidth: 1.5, title: 'EMA20'
                }});
                ema20Line.setData(ema20Data);
            }}

            if (ema50Data.length > 0) {{
                const ema50Line = chart.addLineSeries({{
                    color: '#38bdf8', lineWidth: 1.5, title: 'EMA50'
                }});
                ema50Line.setData(ema50Data);
            }}

            const pivotPrice = {trigger_pivot};
            if (pivotPrice > 0) {{
                candleSeries.createPriceLine({{
                    price: pivotPrice, color: '#10b981',
                    lineWidth: 2, lineStyle: LightweightCharts.LineStyle.Dashed,
                    axisLabelVisible: true, title: 'PIVOT MUA'
                }});
            }}

            const slPrice = {stop_loss_lvl};
            if (slPrice > 0) {{
                candleSeries.createPriceLine({{
                    price: slPrice, color: '#ef4444',
                    lineWidth: 2, lineStyle: LightweightCharts.LineStyle.Solid,
                    axisLabelVisible: true, title: 'CẮT LỖ (SL)'
                }});
            }}

            const tp1Price = {tp1_lvl};
            if (tp1Price > 0) {{
                candleSeries.createPriceLine({{
                    price: tp1Price, color: '#38bdf8',
                    lineWidth: 1.5, lineStyle: LightweightCharts.LineStyle.Dotted,
                    axisLabelVisible: true, title: 'MỤC TIÊU 1'
                }});
            }}

            chart.subscribeCrosshairMove(param => {{
                const tooltip = document.getElementById('chartTooltip');
                if (!tooltip) return;
                if (!param || !param.time || !param.seriesData.get(candleSeries)) {{
                    tooltip.innerHTML = '<span>Rê chuột trên biểu đồ để xem chi tiết nến OHLCV và Khối lượng</span>';
                    return;
                }}
                const data = param.seriesData.get(candleSeries);
                const volItem = param.seriesData.get(volSeries);
                const volVal = volItem ? volItem.value : 0;
                const chg = ((data.close - data.open) / data.open * 100).toFixed(2);
                const chgColor = data.close >= data.open ? '#10b981' : '#ef4444';
                tooltip.innerHTML = `
                    <span>Ngày: <b>${{param.time}}</b></span>
                    <span>Mở: <b>${{data.open.toLocaleString()}}</b></span>
                    <span>Cao: <b>${{data.high.toLocaleString()}}</b></span>
                    <span>Thấp: <b>${{data.low.toLocaleString()}}</b></span>
                    <span>Đóng: <b style="color:${{chgColor}}">${{data.close.toLocaleString()}} (${{chg >= 0 ? '+' : ''}}${{chg}}%)</b></span>
                    <span>Khối lượng: <b>${{volVal.toLocaleString()}} CP</b></span>
                `;
            }});

            window.addEventListener('resize', () => {{
                chart.applyOptions({{ width: chartDiv.clientWidth }});
            }});
        }})();
    </script>
</body>
</html>
"""

    html_path.write_text(html_content, encoding="utf-8")
    return html_path
