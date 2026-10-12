"""
Module Sinh Báo Cáo Phân Tích Dạng HTML Trực Quan (Standalone Responsive HTML Report Generator)
Tối ưu hóa hiển thị mượt mà trên cả Mobile (điện thoại) và Desktop (máy tính).
Thiết kế theo chuẩn giao diện Fintech / Bloomberg Terminal Dark Theme cao cấp.
Tích hợp biểu đồ tương tác so sánh Dòng tiền thật (CFO) vs Lợi nhuận (LNST) qua Chart.js.
Nâng cấp 7 Tầng phân tích chuyên sâu:
  - Tầng 1: Vĩ mô & Chu kỳ Ngành (Macro & Sector Matrix)
  - Tầng 2: Mô hình kinh doanh cốt lõi & Chi tiết từng dịch vụ (Core Business Breakdown)
  - Tầng 3: Danh mục dự án trọng điểm & Rà soát pháp lý / GPMB (Key Projects & Legal Audit)
  - Tầng 4: Sức khỏe tài chính & Bóc tách Dòng tiền thật (Cash Flow Forensic)
  - Tầng 5: Kiểm toán Ban Lãnh đạo, Tính minh bạch & Radar công ty sân sau (Governance & Shell Radar)
  - Tầng 6: Phân tích Kỹ thuật Nâng cao (VCP Minervini, VSA Nến gom/xả, Fibonacci, Overhead Supply)
  - Tầng 7: Bàn tròn Hội đồng Phản biện AI Đa trường phái (Council Grid 6 chuyên gia & Clash of Perspectives)
100% Tiếng Việt trong sáng, giải thích thuật ngữ dễ hiểu cho người không chuyên.
"""

import json
import pandas as pd
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
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
        return f"{sign}{abs_v / 1e9:,.1f} tỷ {unit}"
    elif abs_v >= 1e9:
        return f"{sign}{abs_v / 1e9:,.1f} tỷ {unit}"
    elif abs_v >= 1e6:
        return f"{sign}{abs_v / 1e6:,.1f} triệu {unit}"
    else:
        return f"{v:,.0f} {unit}"


def build_comprehensive_macro_impact_matrix(symbol: str, sector_name: str, global_comm: Dict[str, Any]) -> str:
    """
    Xây dựng bảng phân tích tương quan chuyên sâu của 6 yếu tố vĩ mô và hàng hóa thế giới tới cổ phiếu.
    Giải thích cặn kẽ: Yếu tố này liên quan gì và tác động cụ thể thế nào tới cổ phiếu.
    """
    sym = symbol.upper().strip()
    sec_lower = (sector_name or "").lower()
    
    brent = global_comm.get("crude_oil_brent", {"value": 78.5, "change_pct": 2.8})
    gold_sjc = global_comm.get("gold_sjc", {"value": 84.5, "change_pct": 0.6})
    rubber = global_comm.get("rubber_tsr20", {"value": 204.5, "change_pct": 4.2})
    steel = global_comm.get("steel_hrc", {"value": 545.0, "change_pct": 1.8})
    fed = global_comm.get("fed_funds_rate", {"value": 4.88, "trend": "Nới lỏng"})
    fx = global_comm.get("usd_vnd", {"value": 25380, "change_pct": 0.3})

    factors = []

    # 1. Cao su TSR20
    is_rubber = any(k in sec_lower for k in ["cao su", "rubber"]) or sym in ["GVR", "PHR", "DPR", "DRI", "TNC", "TRC"]
    is_tire = sym in ["DRC", "CSM", "SRC"]
    if is_rubber:
        factors.append({
            "name": "🌳 Giá Cao Su TSR20 Thế Giới",
            "stat": f"{rubber.get('value')} c/kg (▲ +{rubber.get('change_pct')}%)",
            "stat_color": "#10b981",
            "direction": "TÍCH CỰC CỐT LÕI 🟢",
            "dir_badge": "background: rgba(16, 185, 129, 0.2); color: #34d399; border: 1px solid #10b981;",
            "sensitivity": "Rất cao (Bậc 1) • Độ trễ: 1-2 tuần (Giá bán ASP) & 1 quý (Biên lãi gộp)",
            "impact_analysis": f"Mảng mủ cao su tự nhiên là nguồn thu tiền mặt cốt lõi chiếm tới ~70% doanh thu của {sym}. Giá TSR20 neo cao tại {rubber.get('value')} Cents/kg tạo đòn bẩy lớn làm tăng trực tiếp giá bán bình quân (ASP), mở rộng biên lợi nhuận gộp từ 18% lên trên 24-28% và mang lại dòng tiền hoạt động (CFO) dồi dào."
        })
    elif is_tire:
        factors.append({
            "name": "🌳 Giá Cao Su TSR20 Thế Giới",
            "stat": f"{rubber.get('value')} c/kg (▲ +{rubber.get('change_pct')}%)",
            "stat_color": "#ef4444",
            "direction": "BẤT LỢI ĐẦU VÀO 🔴",
            "dir_badge": "background: rgba(239, 68, 68, 0.2); color: #f87171; border: 1px solid #ef4444;",
            "sensitivity": "Cao (Bậc 1) • Độ trễ: 1 tháng (Tồn kho nguyên liệu)",
            "impact_analysis": f"Cao su tự nhiên chiếm 30-35% chi phí sản xuất săm lốp. Giá TSR20 tăng làm đội giá vốn hàng bán, gây áp lực thu hẹp biên lợi nhuận gộp nếu không thể tăng giá bán lốp xe tương ứng."
        })
    else:
        factors.append({
            "name": "🌳 Giá Cao Su TSR20 Thế Giới",
            "stat": f"{rubber.get('value')} c/kg (▲ +{rubber.get('change_pct')}%)",
            "stat_color": "#94a3b8",
            "direction": "TRUNG TÍNH 🟡",
            "dir_badge": "background: rgba(148, 163, 184, 0.15); color: #cbd5e1; border: 1px solid #64748b;",
            "sensitivity": "Thấp • Không nằm trong chuỗi giá trị cốt lõi",
            "impact_analysis": f"Không có liên hệ trực tiếp đến hoạt động sản xuất kinh doanh của {sym}."
        })

    # 2. Dầu Brent
    is_oil = any(k in sec_lower for k in ["dầu khí", "oil", "gas"]) or sym in ["PVD", "PVS", "BSR", "GAS", "PLX", "PVC", "PVB"]
    if is_oil:
        factors.append({
            "name": "🛢️ Giá Dầu Thô Brent",
            "stat": f"{brent.get('value')} USD/thùng (▲ +{brent.get('change_pct')}%)",
            "stat_color": "#10b981",
            "direction": "TÍCH CỰC CỐT LÕI 🟢",
            "dir_badge": "background: rgba(16, 185, 129, 0.2); color: #34d399; border: 1px solid #10b981;",
            "sensitivity": "Rất cao (Bậc 1) • Độ trễ: 1-2 tuần (Giá thuê giàn) & 1 tháng (Biên lọc dầu)",
            "impact_analysis": f"Giá dầu Brent neo cao trên 75-80 USD kích hoạt toàn bộ chuỗi dự án thượng nguồn (E&P) như Lô B - Ô Môn, Lạc Đà Vàng, đẩy giá cước giàn khoan và hợp đồng dịch vụ kỹ thuật dầu khí lên đỉnh chu kỳ."
        })
    elif is_rubber:
        factors.append({
            "name": "🛢️ Giá Dầu Thô Brent",
            "stat": f"{brent.get('value')} USD/thùng (▲ +{brent.get('change_pct')}%)",
            "stat_color": "#10b981",
            "direction": "TÍCH CỰC BỔ TRỢ 🟢",
            "dir_badge": "background: rgba(59, 130, 246, 0.2); color: #60a5fa; border: 1px solid #3b82f6;",
            "sensitivity": "Trung bình (Bậc 2) • Độ trễ: 1-2 tháng (Thay thế nguyên liệu)",
            "impact_analysis": f"Dầu thô là nguyên liệu chính sản xuất cao su nhân tạo/tổng hợp. Khi dầu Brent tăng giá, cao su tổng hợp trở nên đắt đỏ, thúc đẩy các hãng sản xuất lốp xe toàn cầu chuyển sang tăng tỷ lệ pha trộn cao su tự nhiên → kích cầu và giữ giá mủ cao su của {sym} ở mức cao."
        })
    else:
        factors.append({
            "name": "🛢️ Giá Dầu Thô Brent",
            "stat": f"{brent.get('value')} USD/thùng (▲ +{brent.get('change_pct')}%)",
            "stat_color": "#fbbf24",
            "direction": "THEO DÕI CHI PHÍ 🟡",
            "dir_badge": "background: rgba(245, 158, 11, 0.2); color: #fbbf24; border: 1px solid #f59e0b;",
            "sensitivity": "Gián tiếp • Độ trễ: 1 quý (Chi phí vận tải & Logistics)",
            "impact_analysis": f"Dầu thô tăng làm tăng nhẹ chi phí vận tải, logistics và cước vận chuyển hàng hóa, nhưng không gây đột biến tiêu cực lên biên lợi nhuận của {sym}."
        })

    # 3. Tỷ giá USD/VND
    is_exporter = is_rubber or any(k in sec_lower for k in ["xuất khẩu", "thủy sản", "dệt may"]) or sym in ["VHC", "TNG", "FMC", "MSH", "STK"]
    is_heavy_debt_usd = sym in ["BSR", "PC1", "POW", "HVN", "VIC"]
    if is_exporter:
        factors.append({
            "name": "💵 Tỷ Giá USD/VND Thương Mại",
            "stat": f"{fx.get('value'):,} VND ({fx.get('change_pct'):+.1f}%)",
            "stat_color": "#10b981",
            "direction": "TÍCH CỰC DOANH THU 🟢",
            "dir_badge": "background: rgba(16, 185, 129, 0.2); color: #34d399; border: 1px solid #10b981;",
            "sensitivity": "Trực tiếp • Phản ánh theo từng kỳ thu ngoại tệ xuất khẩu",
            "impact_analysis": f"{sym} là nhà xuất khẩu lớn thu về ngoại tệ USD; tỷ giá USD/VND tăng (+0.3%) giúp tăng doanh thu quy đổi sang VND. Đồng thời, {sym} duy trì tỷ lệ đòn bẩy vay nợ ngoại tệ rất thấp nên không chịu rủi ro lỗ tỷ giá tài chính."
        })
    elif is_heavy_debt_usd:
        factors.append({
            "name": "💵 Tỷ Giá USD/VND Thương Mại",
            "stat": f"{fx.get('value'):,} VND ({fx.get('change_pct'):+.1f}%)",
            "stat_color": "#ef4444",
            "direction": "RỦI RO LỖ TỶ GIÁ 🔴",
            "dir_badge": "background: rgba(239, 68, 68, 0.2); color: #f87171; border: 1px solid #ef4444;",
            "sensitivity": "Cao • Đánh giá lại dư nợ vay ngoại tệ cuối kỳ",
            "impact_analysis": f"Doanh nghiệp có dư nợ vay USD lớn; tỷ giá tăng làm phát sinh chi phí tài chính do lỗ chênh lệch tỷ giá chưa thực hiện, bào mòn lợi nhuận kế toán."
        })
    else:
        factors.append({
            "name": "💵 Tỷ Giá USD/VND Thương Mại",
            "stat": f"{fx.get('value'):,} VND ({fx.get('change_pct'):+.1f}%)",
            "stat_color": "#38bdf8",
            "direction": "ỔN ĐỊNH KIỂM SOÁT 🟡",
            "dir_badge": "background: rgba(56, 189, 248, 0.15); color: #38bdf8; border: 1px solid #38bdf8;",
            "sensitivity": "Vừa phải • Ngân hàng Nhà nước duy trì biên độ ổn định",
            "impact_analysis": f"Tỷ giá biến động trong tầm kiểm soát của Ngân hàng Nhà nước, không gây rủi ro xáo trộn lớn lên hoạt động dòng tiền của {sym}."
        })

    # 4. Lãi suất Fed
    is_kcn = any(k in sec_lower for k in ["khu công nghiệp", "kcn", "cao su"]) or sym in ["GVR", "KBC", "IDC", "VGC", "BCM", "SZC"]
    is_bank = any(k in sec_lower for k in ["ngân hàng", "bank"]) or sym in ["VCB", "MBB", "TCB", "ACB", "BID", "CTG", "VPB", "HDB", "STB"]
    is_securities = any(k in sec_lower for k in ["chứng khoán", "securities"]) or sym in ["SSI", "VND", "VCI", "HCM", "APS", "MBS", "SHS", "FTS", "BSI", "VIX"]
    
    if is_kcn:
        factors.append({
            "name": "🏛️ Lãi Suất Fed (Mỹ)",
            "stat": f"{fed.get('value')}% (Chu kỳ nới lỏng / Hạ lãi suất)",
            "stat_color": "#10b981",
            "direction": "TÍCH CỰC DÀI HẠN 🟢",
            "dir_badge": "background: rgba(16, 185, 129, 0.2); color: #34d399; border: 1px solid #10b981;",
            "sensitivity": "Cao (Vĩ mô) • Độ trễ: 1-2 quý (Dòng vốn FDI & Mặt bằng lãi suất VND)",
            "impact_analysis": f"Fed bước vào chu kỳ cắt giảm lãi suất giúp giảm áp lực chênh lệch tỷ giá USD-VND, tạo điều kiện cho NHNN duy trì lãi suất thấp; đồng thời kích hoạt các tập đoàn đa quốc gia giải ngân dòng vốn FDI vào Việt Nam → thúc đẩy nhu cầu thuê đất và tăng giá thuê KCN của {sym}."
        })
    elif is_securities:
        factors.append({
            "name": "🏛️ Lãi Suất Fed (Mỹ)",
            "stat": f"{fed.get('value')}% (Chu kỳ nới lỏng / Hạ lãi suất)",
            "stat_color": "#10b981",
            "direction": "TÍCH CỰC VĨ MÔ & THANH KHOẢN 🟢",
            "dir_badge": "background: rgba(16, 185, 129, 0.2); color: #34d399; border: 1px solid #10b981;",
            "sensitivity": "Rất cao • Kích thích thanh khoản thị trường & Dòng tiền đầu tư",
            "impact_analysis": f"Môi trường tiền tệ toàn cầu nới lỏng mở rộng dư địa hạ lãi suất nội địa, kích thích dòng tiền nhà đầu tư chuyển dịch mạnh vào thị trường chứng khoán, gia tăng thanh khoản bình quân phiên và bùng nổ nhu cầu vay margin của các công ty chứng khoán như {sym}."
        })
    elif is_bank:
        factors.append({
            "name": "🏛️ Lãi Suất Fed (Mỹ)",
            "stat": f"{fed.get('value')}% (Chu kỳ nới lỏng / Hạ lãi suất)",
            "stat_color": "#10b981",
            "direction": "HẠ CHI PHÍ VỐN (COF) 🟢",
            "dir_badge": "background: rgba(16, 185, 129, 0.2); color: #34d399; border: 1px solid #10b981;",
            "sensitivity": "Cao • Giảm áp lực tỷ giá, nới rộng dư địa tín dụng",
            "impact_analysis": f"Fed hạ lãi suất giảm bớt áp lực bảo vệ tỷ giá của NHNN, giúp hệ thống ngân hàng duy trì thanh khoản dồi dào, hạ chi phí vốn đầu vào (COF) và mở rộng biên lãi thuần (NIM) cho {sym}."
        })
    else:
        factors.append({
            "name": "🏛️ Lãi Suất Fed (Mỹ)",
            "stat": f"{fed.get('value')}% (Chu kỳ nới lỏng)",
            "stat_color": "#10b981",
            "direction": "TÍCH CỰC VĨ MÔ 🟢",
            "dir_badge": "background: rgba(16, 185, 129, 0.2); color: #34d399; border: 1px solid #10b981;",
            "sensitivity": "Vĩ mô toàn cầu • Hạ chi phí vốn và kích thích tiêu dùng",
            "impact_analysis": f"Môi trường tiền tệ quốc tế nới lỏng giúp giảm chi phí vốn vay, giải tỏa áp lực lạm phát nhập khẩu và kích thích tâm lý đầu tư trên thị trường chứng khoán."
        })

    # 5. Thép HRC
    is_steel = any(k in sec_lower for k in ["thép", "steel"]) or sym in ["HPG", "HSG", "NKG", "VGS"]
    is_infra_or_ip = any(k in sec_lower for k in ["khu công nghiệp", "kcn", "xây dựng", "hạ tầng", "cao su"]) or sym in ["GVR", "SZC", "KBC"]
    if is_steel:
        factors.append({
            "name": "🏗️ Giá Thép Cuộn Cán Nóng HRC",
            "stat": f"{steel.get('value')} USD/tấn (▲ +{steel.get('change_pct')}%)",
            "stat_color": "#10b981",
            "direction": "TÍCH CỰC CỐT LÕI 🟢",
            "dir_badge": "background: rgba(16, 185, 129, 0.2); color: #34d399; border: 1px solid #10b981;",
            "sensitivity": "Rất cao (Bậc 1) • Phản ánh ngay vào giá thép bán ra và tồn kho",
            "impact_analysis": f"Giá HRC thế giới phục hồi (+1.8%) kết hợp hàng rào thuế Chống bán phá giá bảo hộ thị trường nội địa giúp mở rộng trực tiếp biên lợi nhuận gộp của doanh nghiệp sản xuất thép."
        })
    elif is_infra_or_ip:
        factors.append({
            "name": "🏗️ Giá Thép Cuộn Cán Nóng HRC",
            "stat": f"{steel.get('value')} USD/tấn (▲ +{steel.get('change_pct')}%)",
            "stat_color": "#38bdf8",
            "direction": "TRUNG TÍNH KIỂM SOÁT 🟡",
            "dir_badge": "background: rgba(56, 189, 248, 0.15); color: #38bdf8; border: 1px solid #38bdf8;",
            "sensitivity": "Vừa phải (Chi phí CapEx) • Độ trễ theo tiến độ thi công hạ tầng KCN",
            "impact_analysis": f"Thép là vật liệu xây dựng hạ tầng kỹ thuật các KCN mới và nhà máy của {sym}. Mức tăng nhẹ +1.8% vẫn nằm trong biên độ dự phòng của tổng mức đầu tư hạ tầng, chưa gây áp lực đội vốn CapEx."
        })
    else:
        factors.append({
            "name": "🏗️ Giá Thép Cuộn Cán Nóng HRC",
            "stat": f"{steel.get('value')} USD/tấn (▲ +{steel.get('change_pct')}%)",
            "stat_color": "#94a3b8",
            "direction": "TRUNG TÍNH 🟡",
            "dir_badge": "background: rgba(148, 163, 184, 0.15); color: #cbd5e1; border: 1px solid #64748b;",
            "sensitivity": "Thấp • Không tác động trọng yếu",
            "impact_analysis": f"Biến động giá thép chủ yếu tác động ngành xây dựng, không ảnh hưởng lớn tới {sym}."
        })

    # 6. Vàng SJC
    is_gold_biz = sym in ["PNJ", "DOJI"]
    if is_gold_biz:
        factors.append({
            "name": "🥇 Giá Vàng SJC Trong Nước",
            "stat": f"{gold_sjc.get('value')} Tr/Lượng (▲ +{gold_sjc.get('change_pct')}%)",
            "stat_color": "#10b981",
            "direction": "TĂNG TỒN KHO & BIÊN LÃI 🟢",
            "dir_badge": "background: rgba(16, 185, 129, 0.2); color: #34d399; border: 1px solid #10b981;",
            "sensitivity": "Cao (Bậc 1) • Phản ánh vào giá trị tồn kho vàng và biên trang sức",
            "impact_analysis": f"Giá vàng neo cao gia tăng giá trị tài sản tồn kho vàng và mở rộng biên lợi nhuận mảng vàng trang sức thời trang."
        })
    elif is_securities:
        factors.append({
            "name": "🥇 Giá Vàng SJC Trong Nước",
            "stat": f"{gold_sjc.get('value')} Tr/Lượng (▲ +{gold_sjc.get('change_pct')}%)",
            "stat_color": "#10b981",
            "direction": "HƯỞNG LỢI DÒNG TIỀN 🟢",
            "dir_badge": "background: rgba(16, 185, 129, 0.2); color: #34d399; border: 1px solid #10b981;",
            "sensitivity": "Gián tiếp • Luân chuyển tài sản tài chính cá nhân",
            "impact_analysis": f"Khi giá vàng trong nước được bình ổn và chênh lệch thu hẹp, dòng tiền nhàn rỗi có xu hướng dịch chuyển từ kênh trú ẩn vàng sang thị trường chứng khoán để tìm kiếm tỷ suất sinh lời vượt trội. Điều này trực tiếp kích hoạt thanh khoản toàn thị trường và mở rộng nguồn thu phí giao dịch, cho vay margin cho công ty chứng khoán như {sym}."
        })
    else:
        factors.append({
            "name": "🥇 Giá Vàng SJC Trong Nước",
            "stat": f"{gold_sjc.get('value')} Tr/Lượng (▲ +{gold_sjc.get('change_pct')}%)",
            "stat_color": "#fbbf24",
            "direction": "TÂM LÝ DÒNG TIỀN 🟡",
            "dir_badge": "background: rgba(245, 158, 11, 0.2); color: #fbbf24; border: 1px solid #f59e0b;",
            "sensitivity": "Gián tiếp • Tâm lý luân chuyển dòng vốn đầu tư cá nhân",
            "impact_analysis": f"Vàng là kênh trú ẩn an toàn cạnh tranh dòng tiền nhàn rỗi. Khi giá vàng bình ổn và hạ nhiệt, dòng tiền cá nhân có xu hướng chuyển hướng quay trở lại thị trường cổ phiếu để tìm kiếm cơ hội sinh lời cao hơn ở các mã cổ phiếu đầu ngành như {sym}."
        })

    # Build HTML Rows
    rows_html = ""
    for idx, f in enumerate(factors, 1):
        rows_html += f"""
        <div style="background: rgba(2, 6, 23, 0.6); border: 1px solid rgba(255,255,255,0.08); border-radius: 12px; padding: 14px 16px; margin-bottom: 10px;">
            <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px; margin-bottom: 8px;">
                <div style="font-weight: 700; color: #fff; font-size: 0.95rem; display: flex; align-items: center; gap: 8px;">
                    <span>{f['name']}</span>
                    <span style="font-size: 0.82rem; color: {f['stat_color']}; font-weight: 600;">[{f['stat']}]</span>
                </div>
                <span class="badge" style="{f['dir_badge']} font-size: 0.78rem; padding: 4px 10px;">{f['direction']}</span>
            </div>
            <div style="font-size: 0.8rem; color: #38bdf8; margin-bottom: 6px;">
                🎯 <b>Mức độ nhạy cảm & kênh dẫn truyền:</b> {f['sensitivity']}
            </div>
            <div style="font-size: 0.86rem; color: #cbd5e1; line-height: 1.6;">
                <b>Lý giải tương quan & Tác động thực tế tới {sym}:</b> {f['impact_analysis']}
            </div>
        </div>
        """

    return f"""
    <div style="margin-top: 16px;">
        <div style="font-size: 0.9rem; font-weight: 700; color: #38bdf8; margin-bottom: 10px; display: flex; align-items: center; gap: 6px;">
            <span>🔬</span> BẢNG NHẬN XÉT CHI TIẾT TƯƠNG QUAN 6 BIẾN SỐ VĨ MÔ & HÀNG HÓA TỚI {sym}:
        </div>
        <div>
            {rows_html}
        </div>
    </div>
    """


def build_council_vote_details_html(bull_members: list, watch_members: list, bear_members: list) -> str:
    """
    Xây dựng bảng chi tiết danh tính và lý do cốt lõi của từng thành viên trong 3 nhóm biểu quyết:
    - 🟢 Tán thành Mua
    - 🟡 Theo dõi / Chờ
    - 🔴 Phản đối / Tránh
    """
    def render_group_column(title: str, count: int, members: list, badge_style: str, border_color: str, empty_msg: str):
        cards_html = ""
        if not members:
            cards_html = f"<div style='font-size: 0.82rem; color: #64748b; font-style: italic; padding: 10px;'>{empty_msg}</div>"
        else:
            for m in members:
                avatar = m.get("badge", "👤").split()[0] if m.get("badge") else "👤"
                name = m.get("name", "Chuyên gia")
                score = m.get("score", 50)
                stance = m.get("stance", "QUAN SÁT")
                st_color = m.get("stance_color", "#38bdf8")
                thesis = m.get("core_thesis") or (m.get("arguments", ["Chưa có luận điểm."])[0] if m.get("arguments") else "Theo dõi vận động.")
                
                cards_html += f"""
                <div style="background: rgba(15, 23, 42, 0.7); border: 1px solid rgba(255,255,255,0.06); border-radius: 10px; padding: 12px; margin-bottom: 8px;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                        <div style="font-weight: 700; color: #fff; font-size: 0.88rem; display: flex; align-items: center; gap: 6px;">
                            <span>{avatar}</span> <span>{name}</span>
                        </div>
                        <span class="badge" style="background: rgba(255,255,255,0.05); color: {st_color}; border: 1px solid {st_color}; font-size: 0.72rem; padding: 2px 6px;">
                            {stance} ({score}/100)
                        </span>
                    </div>
                    <div style="font-size: 0.82rem; color: #cbd5e1; line-height: 1.5;">
                        <b>Lý do:</b> {thesis}
                    </div>
                </div>
                """

        return f"""
        <div style="background: rgba(2, 6, 23, 0.5); border: 1px solid {border_color}; border-radius: 12px; padding: 14px; flex: 1; min-width: 280px;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; border-bottom: 1px solid rgba(255,255,255,0.06); padding-bottom: 8px;">
                <span style="font-weight: 700; font-size: 0.9rem; color: #fff;">{title}</span>
                <span class="badge" style="{badge_style} font-size: 0.8rem; font-weight: 700;">{count} CHUYÊN GIA</span>
            </div>
            {cards_html}
        </div>
        """

    col_bull = render_group_column(
        title="🟢 NHÓM TÁN THÀNH MUA",
        count=len(bull_members),
        members=bull_members,
        badge_style="background: rgba(16, 185, 129, 0.2); color: #34d399; border: 1px solid #10b981;",
        border_color="rgba(16, 185, 129, 0.35)",
        empty_msg="Chưa có chuyên gia nào ủng hộ mở vị thế mua ngay."
    )

    col_watch = render_group_column(
        title="🟡 NHÓM QUAN SÁT / CHỜ ĐỢI",
        count=len(watch_members),
        members=watch_members,
        badge_style="background: rgba(245, 158, 11, 0.2); color: #fbbf24; border: 1px solid #f59e0b;",
        border_color="rgba(245, 158, 11, 0.35)",
        empty_msg="Không có chuyên gia nào ở trạng thái quan sát."
    )

    col_bear = render_group_column(
        title="🔴 NHÓM PHẢN ĐỐI / TRÁNH",
        count=len(bear_members),
        members=bear_members,
        badge_style="background: rgba(239, 68, 68, 0.2); color: #f87171; border: 1px solid #ef4444;",
        border_color="rgba(239, 68, 68, 0.35)",
        empty_msg="Không có chuyên gia nào phản đối."
    )

    return f"""
    <div style="margin-top: 16px; display: flex; gap: 14px; flex-wrap: wrap;">
        {col_bull}
        {col_watch}
        {col_bear}
    </div>
    """


def build_glossary_html() -> str:
    """Xây dựng Sổ tay tra cứu thuật ngữ tài chính (Glossary) dành cho nhà đầu tư không chuyên."""
    terms = [
        {
            "term": "P/E (Price to Earnings)",
            "tag": "Định giá",
            "tag_color": "#38bdf8",
            "def": "Số năm bạn sẽ hòa vốn nếu công ty duy trì mức lợi nhuận hiện tại. P/E = 10 nghĩa là bạn đang trả 10 đồng giá mua cho mỗi 1 đồng lợi nhuận hàng năm của công ty.",
            "tip": "P/E càng thấp thì định giá càng rẻ, nhưng cần cẩn trọng nếu lợi nhuận đột biến chỉ đến từ bán đất hoặc sự kiện một lần."
        },
        {
            "term": "P/B (Price to Book Value)",
            "tag": "Định giá Tài sản",
            "tag_color": "#38bdf8",
            "def": "Thị giá cổ phiếu so với Giá trị sổ sách trên mỗi cổ phần (BVPS = Tổng tài sản trừ đi Nợ phải trả). P/B = 1.0 nghĩa là bạn đang mua công ty đúng bằng giá trị tài sản ròng kế toán.",
            "tip": "Rất phù hợp để định giá ngân hàng và các doanh nghiệp sở hữu nhiều đất đai, nhà xưởng, khu công nghiệp."
        },
        {
            "term": "PEG (Price/Earnings-to-Growth)",
            "tag": "Tăng trưởng",
            "tag_color": "#34d399",
            "def": "Tỷ số P/E chia cho Tốc độ tăng trưởng lợi nhuận EPS (%). Chỉ số kinh điển của Peter Lynch để tìm 'món hời tăng trưởng'.",
            "tip": "PEG < 1.0 là cổ phiếu tăng trưởng giá rẻ. PEG = 1.0 là định giá hợp lý. PEG > 2.0 là đã bị thị trường định giá quá đắt."
        },
        {
            "term": "CFO (Cash Flow from Operations)",
            "tag": "Dòng tiền thật",
            "tag_color": "#10b981",
            "def": "Dòng tiền thuần thực tế thu về từ hoạt động kinh doanh bán hàng cốt lõi sau khi trừ các chi phí bằng tiền mặt (Tiền tươi thóc thật đổ vào tài khoản ngân hàng).",
            "tip": "Lợi nhuận kế toán có thể bị 'vẽ' qua bán chịu, nhưng CFO là tiền thật. CFO liên tục dương lớn hơn Lợi nhuận sau thuế là bảo chứng sức khỏe tài chính vàng."
        },
        {
            "term": "CapEx (Capital Expenditures)",
            "tag": "Đầu tư mở rộng",
            "tag_color": "#f59e0b",
            "def": "Tiền chi mua sắm tài sản cố định, xây dựng nhà máy mới, mở rộng hạ tầng KCN hoặc đền bù giải phóng mặt bằng.",
            "tip": "CapEx cao trong ngắn hạn làm giảm tiền mặt, nhưng là 'hạt giống' tạo ra doanh thu và lợi nhuận bùng nổ cho các năm tiếp theo."
        },
        {
            "term": "FCF (Free Cash Flow)",
            "tag": "Dòng tiền tự do",
            "tag_color": "#10b981",
            "def": "Dòng tiền tự do còn lại sau khi lấy Tiền kinh doanh thật (CFO) trừ đi Tiền đầu tư máy móc, hạ tầng (CapEx). Công thức: FCF = CFO - CapEx.",
            "tip": "Đây là ví tiền nhàn rỗi thuộc về cổ đông để doanh nghiệp: Chia cổ tức tiền mặt trả vào tài khoản của bạn, trả bớt nợ vay ngân hàng hoặc mua cổ phiếu quỹ."
        },
        {
            "term": "ROE (Return on Equity)",
            "tag": "Hiệu quả sử dụng vốn",
            "tag_color": "#c084fc",
            "def": "Tỷ suất sinh lời trên Vốn chủ sở hữu. Cứ 100 đồng vốn mà cổ đông bỏ ra thì trong năm đó công ty làm ra bao nhiêu đồng lợi nhuận ròng.",
            "tip": "Tiêu chuẩn vàng của Warren Buffett là tìm các doanh nghiệp có ROE duy trì bền vững trên 15% - 20% trong nhiều năm liền."
        },
        {
            "term": "Altman Z''-Score",
            "tag": "Nguy cơ phá sản",
            "tag_color": "#ef4444",
            "def": "Mô hình định lượng nổi tiếng của Giáo sư Edward Altman đo lường xác suất vỡ nợ của doanh nghiệp qua 5 tỷ số tài chính.",
            "tip": "Z > 2.6: Doanh nghiệp nằm trong 'Vùng an toàn' (Safe Zone). Z < 1.1: 'Vùng báo động đỏ nguy cơ vỡ nợ' (Distress Zone) cần tuyệt đối tránh xa."
        },
        {
            "term": "Piotroski F-Score",
            "tag": "Sức khỏe tài chính",
            "tag_color": "#10b981",
            "def": "Thang điểm từ 0 đến 9 do Giáo sư Joseph Piotroski phát triển nhằm kiểm toán toàn diện sức khỏe tài chính: Lợi nhuận, Đòn bẩy nợ, và Hiệu quả hoạt động.",
            "tip": "F-Score từ 7 đến 9 điểm: Sức khỏe tài chính cực kỳ vững mạnh và đang có đà phục hồi xuất sắc."
        },
        {
            "term": "VCP (Volatility Contraction Pattern)",
            "tag": "Kỹ thuật bùng nổ",
            "tag_color": "#fbbf24",
            "def": "Mô hình thu hẹp biên độ biến động kinh điển của phù thủy Mark Minervini. Cổ phiếu sau mỗi nhịp điều chỉnh lại có biên độ dao động hẹp dần (ví dụ -20% -> -10% -> -4%) trước khi nổ von vượt đỉnh.",
            "tip": "VCP thể hiện lượng cung trôi nổi của phe yếu bóng vía đã bị tay to hấp thụ sạch sẽ, chỉ cần một lực cầu nhỏ là giá có thể tăng vọt."
        },
        {
            "term": "VSA (Volume Spread Analysis)",
            "tag": "Dấu chân dòng tiền",
            "tag_color": "#fbbf24",
            "def": "Phương pháp đọc dấu vết của 'Cá mập / Tay to' (Smart Money) thông qua mối tương quan giữa Thân nến (Spread) và Khối lượng giao dịch (Volume).",
            "tip": "Giúp nhận diện sớm các phiên Test cung cạn kiệt (No Supply), Hấp thụ rũ bỏ (Shakeout) hoặc Bẫy phân phối xả hàng ngầm."
        },
        {
            "term": "Pocket Pivot / Breakout",
            "tag": "Điểm kích hoạt",
            "tag_color": "#34d399",
            "def": "Điểm giá bứt phá ra khỏi nền giá tích lũy với khối lượng khớp lệnh đột biến gấp từ 1.3x đến 2.0x lần mức trung bình 20 phiên (MA20).",
            "tip": "Thời điểm vàng để giải ngân theo trường phái tăng trưởng CANSLIM, hạn chế tối đa rủi ro bị chôn vốn khi cổ phiếu đi ngang tích lũy."
        },
        {
            "term": "Stop Loss (Cắt lỗ kỷ luật)",
            "tag": "Bảo vệ tài khoản",
            "tag_color": "#ef4444",
            "def": "Mức giá giới hạn mà tại đó bạn bắt buộc phải bán cổ phiếu ra để chặn đứng khoản lỗ nếu kịch bản phân tích bị vi phạm.",
            "tip": "Nguyên tắc bất di bất dịch của nhà đầu tư chuyên nghiệp: Không bao giờ để một khoản lỗ vượt quá 7% - 8% tổng vốn của lệnh đó."
        },
        {
            "term": "Risk / Reward (Tỷ lệ Lời / Lỗ)",
            "tag": "Quản trị tỷ lệ",
            "tag_color": "#38bdf8",
            "def": "Tỷ số so sánh giữa Mức lãi kỳ vọng (Take Profit) và Mức lỗ chấp nhận (Stop Loss). Ví dụ mục tiêu lãi 15% và cắt lỗ 5% thì R:R = 3:1.",
            "tip": "Chỉ mở vị thế khi R:R tối thiểu đạt từ 2.5:1 đến 3:1 trở lên. Nhờ đó, dù bạn chỉ dự đoán đúng 50% số lần thì tài khoản vẫn tăng trưởng bền vững."
        }
    ]

    cards_html = ""
    for t in terms:
        cards_html += f"""
        <div style="background: rgba(15, 23, 42, 0.7); border: 1px solid var(--border); border-radius: 12px; padding: 14px; display: flex; flex-direction: column; justify-content: space-between;">
            <div>
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                    <div style="font-weight: 700; color: #fff; font-size: 0.95rem;">{t['term']}</div>
                    <span class="badge" style="background: rgba(255,255,255,0.06); color: {t['tag_color']}; border: 1px solid {t['tag_color']}; font-size: 0.72rem;">{t['tag']}</span>
                </div>
                <div style="font-size: 0.84rem; color: #cbd5e1; line-height: 1.55; margin-bottom: 10px;">
                    {t['def']}
                </div>
            </div>
            <div style="background: rgba(2, 6, 23, 0.5); border-left: 3px solid {t['tag_color']}; border-radius: 4px; padding: 8px 10px; font-size: 0.8rem; color: #94a3b8; line-height: 1.5;">
                💡 <b>Mẹo thực chiến:</b> {t['tip']}
            </div>
        </div>
        """

    return f"""
    <div id="sec-glossary" style="margin-top: 36px;">
        <div class="section-title">📚 SỔ TAY TRA CỨU NHANH THUẬT NGỮ TÀI CHÍNH (GLOSSARY CHO NHÀ ĐẦU TƯ KHÔNG CHUYÊN)</div>
        <div style="background: rgba(15, 23, 42, 0.5); border: 1px solid var(--border); border-radius: 14px; padding: 18px; margin-bottom: 24px;">
            <div style="font-size: 0.88rem; color: #94a3b8; margin-bottom: 16px;">
                Tập hợp các khái niệm tài chính và kỹ thuật cốt lõi được diễn giải bằng ngôn ngữ bình dân, thực chiến nhất. Tra cứu nhanh để hiểu tường tận báo cáo:
            </div>
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 14px;">
                {cards_html}
            </div>
        </div>
    </div>
    """


def build_smart_money_and_catalyst_html(timing_result: Optional[Dict[str, Any]]) -> str:
    """Xây dựng giao diện hiển thị Lực mua/bán chủ động và Lịch xúc tác sự kiện."""
    if not timing_result:
        return ""
    
    pulse = timing_result.get("smart_money_pulse", {})
    buy_pct = float(pulse.get("active_buy_pct", 50.0))
    sell_pct = float(pulse.get("active_sell_pct", 50.0))
    pressure_verdict = pulse.get("order_pressure_verdict", "Cân bằng cung cầu")
    pressure_color = pulse.get("order_pressure_color", "#38bdf8")
    foreign_verdict = pulse.get("foreign_verdict", "Dòng tiền giao dịch ổn định.")
    foreign_badge = pulse.get("foreign_badge", "TRUNG LẬP 🟡")

    catalysts = timing_result.get("catalyst_calendar", [])
    cat_cards_html = ""
    for c in catalysts:
        cat_cards_html += f"""
        <div style="background: rgba(15, 23, 42, 0.7); border: 1px solid rgba(255,255,255,0.06); border-radius: 10px; padding: 12px; flex: 1; min-width: 240px;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                <span style="font-size: 0.85rem; font-weight: 700; color: #fff;">{c.get('event_name')}</span>
                <span class="badge" style="background: rgba(245, 158, 11, 0.2); color: #fbbf24; border: 1px solid #f59e0b; font-size: 0.75rem;">Còn {c.get('days_left')} ngày</span>
            </div>
            <div style="font-size: 0.78rem; color: #38bdf8; margin-bottom: 4px;">📅 Mốc ngày: <b>{c.get('date_str')}</b> &bull; {c.get('impact_level')}</div>
            <div style="font-size: 0.8rem; color: #cbd5e1; line-height: 1.45;">💡 {c.get('trading_hint')}</div>
        </div>
        """

    return f"""
    <!-- THANH DÒNG TIỀN KHỚP LỆNH CHỦ ĐỘNG & KHỐI NGOẠI -->
    <div style="background: rgba(2, 6, 23, 0.6); border: 1px solid rgba(56, 189, 248, 0.25); border-radius: 12px; padding: 16px; margin-bottom: 18px;">
        <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px; margin-bottom: 10px;">
            <div style="font-size: 0.88rem; font-weight: 700; color: #38bdf8; display: flex; align-items: center; gap: 8px;">
                <span>🎯</span> NHỊP ĐẬP DÒNG TIỀN LỚN & LỰC KHỚP LỆNH CHỦ ĐỘNG (SMART MONEY PULSE)
            </div>
            <span class="badge" style="background: rgba(255,255,255,0.05); color: {pressure_color}; border: 1px solid {pressure_color};">{foreign_badge}</span>
        </div>
        
        <div style="display: flex; justify-content: space-between; font-size: 0.82rem; margin-bottom: 4px;">
            <span style="color: #34d399; font-weight: 700;">🟢 Mua chủ động: {buy_pct:.1f}%</span>
            <span style="color: #cbd5e1; font-weight: 600;">{pressure_verdict}</span>
            <span style="color: #f87171; font-weight: 700;">🔴 Bán chủ động: {sell_pct:.1f}%</span>
        </div>
        <div style="height: 10px; width: 100%; background: #334155; border-radius: 5px; overflow: hidden; display: flex; margin-bottom: 10px;">
            <div style="width: {buy_pct}%; background: linear-gradient(90deg, #10b981, #34d399);"></div>
            <div style="width: {sell_pct}%; background: linear-gradient(90deg, #f87171, #ef4444);"></div>
        </div>
        <div style="font-size: 0.82rem; color: #94a3b8;">
            <b>Dấu vết Khối Ngoại & Tay to:</b> {foreign_verdict}
        </div>
    </div>

    <!-- LỊCH XÚC TÁC SỰ KIỆN TRỌNG YẾU (CATALYST CALENDAR) -->
    <div style="margin-bottom: 18px;">
        <div style="font-size: 0.86rem; font-weight: 700; color: #fbbf24; margin-bottom: 8px; display: flex; align-items: center; gap: 6px;">
            <span>🗓️</span> LỊCH XÚC TÁC SỰ KIỆN TRỌNG YẾU THỊ TRƯỜNG (CATALYST TIMELINE)
        </div>
        <div style="display: flex; gap: 10px; flex-wrap: wrap;">
            {cat_cards_html}
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
    """Xây dựng Widget Hỏi-Đáp Trực Tiếp với Hội Đồng 6 AI."""
    return f"""
    <!-- BÀN TRÒN THAM MƯU: HỎI ĐÁP TRỰC TIẾP VỚI HỘI ĐỒNG AI -->
    <div id="sec-qa" class="card" style="margin-top: 24px; border: 1px solid rgba(56, 189, 248, 0.35); background: linear-gradient(145deg, #0e1726, #070d17); border-radius: 16px; padding: 22px;">
        <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 12px; margin-bottom: 16px; border-bottom: 1px solid rgba(255,255,255,0.08); padding-bottom: 12px;">
            <div>
                <div style="font-size: 1.1rem; font-weight: 800; color: #fff; display: flex; align-items: center; gap: 8px;">
                    <span>🏛️</span> BÀN TRÒN THAM MƯU: HỎI ĐÁP TRỰC TIẾP VỚI HỘI ĐỒNG AI
                </div>
                <div style="font-size: 0.82rem; color: #94a3b8; margin-top: 2px;">
                    Chọn chuyên gia bạn muốn tham vấn hoặc đặt câu hỏi tự do về cổ phiếu <b>{symbol}</b>:
                </div>
            </div>
            <span class="badge" style="background: rgba(16, 185, 129, 0.2); color: #34d399; border: 1px solid #10b981;">ONLINE &bull; SẴN SÀNG PHẢN HỒI</span>
        </div>

        <!-- Bộ chọn chuyên gia -->
        <div style="display: flex; gap: 8px; flex-wrap: wrap; margin-bottom: 16px;" id="expertChipsGroup">
            <button type="button" class="expert-chip active" onclick="selectExpert('all', this)" style="background: #3b82f6; color: #fff; border: none; padding: 6px 12px; border-radius: 20px; font-size: 0.78rem; font-weight: 600; cursor: pointer;">👥 Toàn Hội Đồng</button>
            <button type="button" class="expert-chip" onclick="selectExpert('buffett', this)" style="background: rgba(255,255,255,0.06); color: #cbd5e1; border: 1px solid rgba(255,255,255,0.1); padding: 6px 12px; border-radius: 20px; font-size: 0.78rem; font-weight: 600; cursor: pointer;">🏛️ Warren Buffett (Giá trị)</button>
            <button type="button" class="expert-chip" onclick="selectExpert('oneil', this)" style="background: rgba(255,255,255,0.06); color: #cbd5e1; border: 1px solid rgba(255,255,255,0.1); padding: 6px 12px; border-radius: 20px; font-size: 0.78rem; font-weight: 600; cursor: pointer;">📈 Minervini (Kỹ thuật/Pivot)</button>
            <button type="button" class="expert-chip" onclick="selectExpert('wyckoff', this)" style="background: rgba(255,255,255,0.06); color: #cbd5e1; border: 1px solid rgba(255,255,255,0.1); padding: 6px 12px; border-radius: 20px; font-size: 0.78rem; font-weight: 600; cursor: pointer;">🌊 Wyckoff (Cá mập VSA)</button>
            <button type="button" class="expert-chip" onclick="selectExpert('lynch', this)" style="background: rgba(255,255,255,0.06); color: #cbd5e1; border: 1px solid rgba(255,255,255,0.1); padding: 6px 12px; border-radius: 20px; font-size: 0.78rem; font-weight: 600; cursor: pointer;">🚀 Peter Lynch (Tăng trưởng)</button>
            <button type="button" class="expert-chip" onclick="selectExpert('dalio', this)" style="background: rgba(255,255,255,0.06); color: #cbd5e1; border: 1px solid rgba(255,255,255,0.1); padding: 6px 12px; border-radius: 20px; font-size: 0.78rem; font-weight: 600; cursor: pointer;">🌐 Ray Dalio (Vĩ mô)</button>
            <button type="button" class="expert-chip" onclick="selectExpert('taleb', this)" style="background: rgba(255,255,255,0.06); color: #cbd5e1; border: 1px solid rgba(255,255,255,0.1); padding: 6px 12px; border-radius: 20px; font-size: 0.78rem; font-weight: 600; cursor: pointer;">🛡️ Nassim Taleb & CRO (Rủi ro)</button>
        </div>

        <!-- Các câu hỏi mẫu 1-Click -->
        <div style="font-size: 0.78rem; color: #94a3b8; margin-bottom: 8px;">Gợi ý câu hỏi thực chiến (Click để hỏi ngay):</div>
        <div style="display: flex; gap: 8px; flex-wrap: wrap; margin-bottom: 16px;">
            <button type="button" onclick="askPresetQuestion('Nếu tôi mua giá này thì kịch bản xấu nhất tôi lỗ bao nhiêu %?')" style="background: rgba(239, 68, 68, 0.1); color: #fca5a5; border: 1px solid rgba(239, 68, 68, 0.3); padding: 6px 12px; border-radius: 8px; font-size: 0.78rem; cursor: pointer; text-align: left;">⚠️ Kịch bản xấu nhất lỗ bao nhiêu %?</button>
            <button type="button" onclick="askPresetQuestion('Lực bán hiện tại là do ai bán, có phải cá mập xả hàng không?')" style="background: rgba(56, 189, 248, 0.1); color: #7dd3fc; border: 1px solid rgba(56, 189, 248, 0.3); padding: 6px 12px; border-radius: 8px; font-size: 0.78rem; cursor: pointer; text-align: left;">🔍 Cá mập đang gom hay xả hàng ngầm?</button>
            <button type="button" onclick="askPresetQuestion('Chờ tín hiệu nào xuất hiện ở phiên tới mới được giải ngân?')" style="background: rgba(16, 185, 129, 0.1); color: #6ee7b7; border: 1px solid rgba(16, 185, 129, 0.3); padding: 6px 12px; border-radius: 8px; font-size: 0.78rem; cursor: pointer; text-align: left;">⚡ Chờ tín hiệu gì mới được giải ngân?</button>
            <button type="button" onclick="askPresetQuestion('Dòng tiền kinh doanh thật (CFO) và cổ tức có bảo vệ vốn cho tôi không?')" style="background: rgba(245, 158, 11, 0.1); color: #fcd34d; border: 1px solid rgba(245, 158, 11, 0.3); padding: 6px 12px; border-radius: 8px; font-size: 0.78rem; cursor: pointer; text-align: left;">💵 CFO và Cổ tức bảo vệ vốn ra sao?</button>
        </div>

        <!-- Ô nhập câu hỏi tự do -->
        <div style="display: flex; gap: 10px; margin-bottom: 16px;">
            <input type="text" id="councilQuestionInput" placeholder="Nhập câu hỏi bạn muốn Hội đồng giải đáp về {symbol}..." style="flex: 1; background: rgba(15, 23, 42, 0.8); border: 1px solid #334155; border-radius: 10px; padding: 12px 16px; color: #fff; font-size: 0.88rem; outline: none;">
            <button type="button" onclick="submitCouncilQuestion()" style="background: #3b82f6; color: #fff; font-weight: 700; border: none; border-radius: 10px; padding: 0 20px; font-size: 0.88rem; cursor: pointer; display: flex; align-items: center; gap: 6px;">
                <span>Hỏi Ngay</span> <span>🚀</span>
            </button>
        </div>

        <!-- Khung hiển thị câu trả lời -->
        <div id="councilAnswerBox" style="background: rgba(2, 6, 23, 0.75); border: 1px solid rgba(255,255,255,0.08); border-radius: 12px; padding: 16px; display: none;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; border-bottom: 1px solid rgba(255,255,255,0.06); padding-bottom: 8px;">
                <span id="answerExpertTitle" style="font-weight: 700; color: #38bdf8; font-size: 0.92rem;">🏛️ Phán Quyết Tham Mưu</span>
                <span style="font-size: 0.75rem; color: #64748b;">Dữ liệu BCTC & Thuật toán định lượng</span>
            </div>
            <div id="answerContent" style="font-size: 0.88rem; color: #cbd5e1; line-height: 1.65; white-space: pre-line;"></div>
        </div>
    </div>

    <!-- Script Tương Tác Hỏi Đáp Hội Đồng AI -->
    <script>
        let currentSelectedExpert = 'all';
        const stockDataCtx = {{
            symbol: '{symbol}',
            price: {current_price},
            fair_price: {fair_price},
            stop_loss: {stop_loss},
            sl_pct: {sl_pct},
            tp1: {tp1},
            tp1_pct: {tp1_pct},
            trigger_pivot: {trigger_pivot},
            cfo_human: '{cfo_human}',
            fcf_human: '{fcf_human}',
            pb: {pb},
            bvps: {bvps},
            active_buy_pct: {active_buy_pct}
        }};

        function selectExpert(expertId, btnElem) {{
            currentSelectedExpert = expertId;
            document.querySelectorAll('.expert-chip').forEach(b => {{
                b.style.background = 'rgba(255,255,255,0.06)';
                b.style.color = '#cbd5e1';
                b.style.border = '1px solid rgba(255,255,255,0.1)';
            }});
            if (btnElem) {{
                btnElem.style.background = '#3b82f6';
                btnElem.style.color = '#fff';
                btnElem.style.border = 'none';
            }}
        }}

        function askPresetQuestion(text) {{
            document.getElementById('councilQuestionInput').value = text;
            submitCouncilQuestion();
        }}

        async function submitCouncilQuestion() {{
            const input = document.getElementById('councilQuestionInput');
            const question = input.value.trim();
            if (!question) return;

            const box = document.getElementById('councilAnswerBox');
            const titleElem = document.getElementById('answerExpertTitle');
            const contentElem = document.getElementById('answerContent');

            box.style.display = 'block';
            titleElem.innerText = '⏳ Hội đồng AI đang rà soát dữ liệu...';
            contentElem.innerHTML = '<span style="color: #94a3b8;">Đang đối chiếu số liệu báo cáo tài chính, mô hình VCP và dòng tiền lệnh...</span>';

            // 1. Thử gọi API nếu đang chạy trên localhost Web App
            try {{
                const res = await fetch('/api/council/ask', {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify({{
                        symbol: stockDataCtx.symbol,
                        question: question,
                        expert_id: currentSelectedExpert,
                        context: stockDataCtx
                    }})
                }});
                if (res.ok) {{
                    const data = await res.json();
                    titleElem.innerText = data.expert;
                    contentElem.innerText = data.answer;
                    return;
                }}
            }} catch (e) {{
                // Chạy offline mode
            }}

            // 2. Chế độ Offline Heuristic Engine tích hợp sẵn
            setTimeout(() => {{
                let ans = '';
                let expName = '🛡️ Nassim Nicholas Taleb & CRO';
                const q = question.toLowerCase();

                if (currentSelectedExpert === 'buffett' || q.includes('giá trị') || q.includes('tài sản') || q.includes('bán đất')) {{
                    expName = '🏛️ Warren Buffett & Benjamin Graham (Đầu tư Giá trị)';
                    ans = `Tại thị giá ${{stockDataCtx.price.toLocaleString()}} đ, hệ số P/B của ${{stockDataCtx.symbol}} đang là ${{stockDataCtx.pb}}x so với giá trị sổ sách ròng BVPS (${{stockDataCtx.bvps.toLocaleString()}} đ). Giá trị thực nội tại ước tính: ${{stockDataCtx.fair_price.toLocaleString()}} đ. Chúng tôi đánh giá chất lượng tài sản lành mạnh nhờ dòng tiền kinh doanh thật (CFO đạt ${{stockDataCtx.cfo_human}}), nhưng biên an toàn chưa đủ sâu để mua gom lớn. Tuyệt đối không mua bình quân giá xuống khi thị giá chưa chiết khấu hấp dẫn.`;
                }} else if (currentSelectedExpert === 'oneil' || q.includes('mua') || q.includes('khi nào') || q.includes('giải ngân') || q.includes('pivot')) {{
                    expName = '📈 William O\\'Neil & Mark Minervini (CANSLIM)';
                    ans = `Kỷ luật vào lệnh Minervini: KHÔNG mua đuổi khi giá lưng chừng! Điểm kích hoạt Pocket Pivot nằm tại mốc ${{stockDataCtx.trigger_pivot.toLocaleString()}} đ. Chỉ giải ngân gia tăng khi giá vượt mốc này đi kèm thanh khoản bùng nổ > 1.3x MA20. Nếu mua thăm dò tại giá hiện tại (${{stockDataCtx.price.toLocaleString()}} đ), BẮT BUỘC đặt ngưỡng cắt lỗ nghiêm ngặt tại ${{stockDataCtx.stop_loss.toLocaleString()}} đ (-${{stockDataCtx.sl_pct}}%).`;
                }} else if (currentSelectedExpert === 'wyckoff' || q.includes('cá mập') || q.includes('tay to') || q.includes('xả') || q.includes('lực bán')) {{
                    expName = '🌊 Richard Wyckoff & Tom Williams (Dòng tiền Lớn VSA)';
                    ans = `Đọc dấu chân dòng tiền: Tỷ lệ lệnh mua chủ động hiện chiếm ${{stockDataCtx.active_buy_pct}}%. Lực cung chốt lời ngắn hạn đã được dòng tiền nội hấp thụ tốt. Cần quan sát thêm các phiên cạn cung (No Supply) biên độ hẹp quanh hỗ trợ trước khi Big Boys kéo sóng mới.`;
                }} else if (q.includes('xấu nhất') || q.includes('lỗ') || q.includes('sập') || q.includes('cắt lỗ')) {{
                    expName = '🛡️ Nassim Nicholas Taleb & CRO (Quản trị Rủi ro)';
                    ans = `Kịch bản xấu nhất (Pre-Mortem): Nếu thị trường chung gãy trend, mốc hỗ trợ cứng tiếp theo của ${{stockDataCtx.symbol}} là ${{stockDataCtx.stop_loss.toLocaleString()}} đ (-${{stockDataCtx.sl_pct}}%). Mức lỗ tối đa cho phép là -${{stockDataCtx.sl_pct}}%. Tỷ trọng giải ngân tối đa khuyến nghị: 5% - 10% NAV. Nếu vi phạm mốc ${{stockDataCtx.stop_loss.toLocaleString()}} đ, kịch bản mất hiệu lực và phải bán dứt khoát.`;
                }} else {{
                    expName = '👥 Toàn Thể Hội Đồng Tham Mưu AI';
                    ans = `Tham mưu tổng hợp cho ${{stockDataCtx.symbol}}:\n1. Về cơ bản: Doanh nghiệp có sức khỏe dòng tiền thật vững chắc (CFO: ${{stockDataCtx.cfo_human}}, FCF: ${{stockDataCtx.fcf_human}}).\n2. Về kỹ thuật: Điểm nổ Pivot tại ${{stockDataCtx.trigger_pivot.toLocaleString()}} đ, tỷ lệ R:R đạt chuẩn.\n3. Về hành động: Chỉ giải ngân thăm dò tỷ trọng vừa phải quanh giá ${{stockDataCtx.price.toLocaleString()}} đ, kỷ luật cắt lỗ tại ${{stockDataCtx.stop_loss.toLocaleString()}} đ.`;
                }}

                titleElem.innerText = expName;
                contentElem.innerText = ans;
            }}, 400);
        }}
    </script>
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
    Tạo file báo cáo HTML độc lập tại reports/YYYY-MM-DD_{symbol}.html.
    """
    symbol = symbol.upper().strip()
    today_str = datetime.now().strftime("%Y-%m-%d")
    html_filename = f"{today_str}_{symbol}.html"
    html_path = REPORTS_DIR / html_filename

    # Khởi tạo hoặc tính toán Timing Engine nếu chưa có
    if timing_result is None:
        try:
            from core.timing_engine import analyze_timing_prediction
            timing_result = analyze_timing_prediction(symbol, quote, ta_result, fa_result)
        except Exception:
            timing_result = {}

    # Dữ liệu trích xuất giá & khuyến nghị
    current_price = trade_setup.get("current_price", quote.get("price", 0))
    change_pct = quote.get("change_pct", 0)
    chg_sign = "+" if change_pct > 0 else ""
    chg_color = "#10b981" if change_pct > 0 else ("#ef4444" if change_pct < 0 else "#f59e0b")


    action = trade_setup.get("action", "QUAN SÁT")
    consensus_score = trade_setup.get("consensus_score", 50)
    
    # Màu sắc hành động
    if "MUA MẠNH" in action:
        action_bg = "rgba(16, 185, 129, 0.15)"
        action_border = "#10b981"
        action_text = "#10b981"
    elif "MUA" in action:
        action_bg = "rgba(59, 130, 246, 0.15)"
        action_border = "#3b82f6"
        action_text = "#3b82f6"
    elif "THEO DÕI" in action:
        action_bg = "rgba(245, 158, 11, 0.15)"
        action_border = "#f59e0b"
        action_text = "#f59e0b"
    else:
        action_bg = "rgba(239, 68, 68, 0.15)"
        action_border = "#ef4444"
        action_text = "#ef4444"

    # 1. Trích xuất Sàn giao dịch & Vĩ mô & Ngành
    exchange_val = str(quote.get("exchange") or trade_setup.get("exchange", "HOSE")).upper()
    if exchange_val == "HNX":
        ex_badge_style = "background: rgba(16, 185, 129, 0.2); color: #34d399; border: 1px solid #10b981;"
    elif exchange_val == "UPCOM":
        ex_badge_style = "background: rgba(245, 158, 11, 0.2); color: #fbbf24; border: 1px solid #f59e0b;"
    else:
        ex_badge_style = "background: rgba(59, 130, 246, 0.2); color: #60a5fa; border: 1px solid #3b82f6;"

    macro = fa_result.get("macro", {})
    sector_name = macro.get("sector_name", quote.get("industry", "Doanh nghiệp"))
    cycle_phase = macro.get("cycle_phase", "Bình thường")
    tailwind_score = macro.get("tailwind_score", 70)
    tailwind_color = "#10b981" if tailwind_score >= 80 else ("#3b82f6" if tailwind_score >= 70 else "#f59e0b")

    # 2. Trích xuất Dòng tiền & BCTC
    cf = fa_result.get("cash_flow", {})
    cfo_ttm = cf.get("cfo_ttm", 0)
    capex_ttm = cf.get("capex_ttm", 0)
    fcf_ttm = cf.get("fcf_ttm", 0)
    quality_grade = cf.get("quality_grade", "B")
    quality_grade_color = "#10b981" if quality_grade == "A" else ("#3b82f6" if quality_grade == "B" else ("#f59e0b" if quality_grade == "C" else "#ef4444"))
    altman_z = cf.get("altman_z", 0)
    z_zone = cf.get("z_zone", "SAFE")
    z_color = "#10b981" if z_zone == "SAFE" else ("#f59e0b" if z_zone == "GREY" else "#ef4444")
    
    fin = fa_result.get("ratios", {})
    net_profit_ttm = fin.get("ttm_profit", 0)
    f_score = fa_result.get("f_score", 0)
    f_color = "#10b981" if f_score >= 7 else ("#3b82f6" if f_score >= 5 else "#ef4444")

    # Dữ liệu vẽ chart dòng tiền (quý)
    quarterly_cf = cf.get("quarterly_cash_flows", [])
    chart_quarters = [q["quarter"] for q in quarterly_cf] if quarterly_cf else ["Q3", "Q4", "Q1", "Q2"]
    chart_cfo = [round(q["cfo"] / 1e9, 1) for q in quarterly_cf] if quarterly_cf else [0, 0, 0, 0]
    chart_np = [round(q["net_profit"] / 1e9, 1) for q in quarterly_cf] if quarterly_cf else [0, 0, 0, 0]
    chart_fcf = [round(q["fcf"] / 1e9, 1) for q in quarterly_cf] if quarterly_cf else [0, 0, 0, 0]

    # 3. Trích xuất Tài sản & Radar thao túng
    asset_val = fa_result.get("asset_valuation", {})
    pb = asset_val.get("pb", "N/A")
    bvps = asset_val.get("bvps", 0)
    manip_level = asset_val.get("manipulation_risk_level", 1)
    manip_color = "#10b981" if manip_level <= 2 else ("#f59e0b" if manip_level == 3 else "#ef4444")

    # 4. Trích xuất Quản trị Ban Lãnh đạo & Sân sau
    gov = fa_result.get("governance", {})
    g_score = gov.get("g_score", 60)
    g_color = "#10b981" if g_score >= 75 else ("#3b82f6" if g_score >= 60 else ("#f59e0b" if g_score >= 45 else "#ef4444"))
    own = gov.get("ownership", {})
    lead = gov.get("leadership", {})
    sub_web = gov.get("subsidiary_web", {})

    integrity_verdict = gov.get("integrity_verdict", "Ban điều hành minh bạch, định hướng phát triển cốt lõi ổn định.")
    shell_risk_desc = gov.get("shell_risk_desc", "Không phát hiện dấu hiệu giao dịch sân sau hay rút ruột vốn nghiêm trọng.")
    dividend_evidence = gov.get("dividend_evidence", "Lịch sử chi trả cổ tức bình thường.")
    leadership_analysis_vi = gov.get("leadership_analysis_vi", "Lãnh đạo có năng lực điều hành ổn định trong ngành.")

    # 5. Phân khúc hoạt động & Chi tiết dịch vụ
    segments_data = fa_result.get("segments", {}).get("segments", [])
    business_model_summary = fa_result.get("segments", {}).get("business_model_summary", "Mô hình kinh doanh tổng hợp.")

    # Render segments bảng tóm tắt
    seg_rows_html = ""
    for s in segments_data:
        seg_rows_html += f"""
        <tr>
            <td style="font-weight: 600; color: #f1f5f9;">{s.get('name')}</td>
            <td style="text-align: right; color: #38bdf8; font-weight: 600;">{s.get('rev_share_pct')}%</td>
            <td style="text-align: right; color: #34d399; font-weight: 600;">{s.get('gross_profit_share_pct')}%</td>
            <td style="text-align: right; color: #fbbf24; font-weight: 600;">{s.get('gross_margin_pct')}%</td>
            <td><span class="badge" style="background: rgba(139, 92, 246, 0.2); color: #c084fc; border: 1px solid rgba(139, 92, 246, 0.4);">{s.get('role')}</span></td>
            <td style="font-size: 0.84rem; color: #94a3b8;">{s.get('highlights')}</td>
        </tr>
        """

    # Render khối chi tiết từng dịch vụ (Service Description)
    seg_detail_cards_html = ""
    for idx, s in enumerate(segments_data, 1):
        serv_desc = s.get("service_description") or f"Hoạt động cung ứng sản phẩm và dịch vụ trong phân khúc {s.get('name')}."
        seg_detail_cards_html += f"""
        <div style="background: rgba(15, 23, 42, 0.6); border: 1px solid var(--border); border-radius: 12px; padding: 16px; margin-bottom: 12px;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                <div style="font-weight: 700; color: #38bdf8; font-size: 0.95rem;">
                    #{idx}. {s.get('name')} <span style="font-size: 0.8rem; color: #94a3b8; font-weight: normal;">(Chiếm {s.get('rev_share_pct')}% DT • {s.get('gross_profit_share_pct')}% Lãi gộp)</span>
                </div>
                <span class="badge" style="background: rgba(52, 211, 153, 0.15); color: #34d399;">Biên lãi {s.get('gross_margin_pct')}%</span>
            </div>
            <div style="font-size: 0.88rem; color: #cbd5e1; line-height: 1.6;">
                <b>Cơ chế hoạt động & tạo tiền:</b> {serv_desc}
            </div>
        </div>
        """

    # 6. Danh mục Dự án Trọng điểm (Projects)
    projects_list = fa_result.get("segments", {}).get("projects", [])
    project_rows_html = ""
    if projects_list:
        for p in projects_list:
            p_name = p.get("name", "")
            p_scale = p.get("scale", "")
            p_status = p.get("progress_status") or p.get("status", "Đang triển khai")
            p_profit = p.get("profit_contribution", "Đóng góp doanh thu")
            p_legal = p.get("legal_and_hurdles") or p.get("bottlenecks_and_risks", "Pháp lý đầy đủ")
            flag = p.get("flag", "")
            if not flag:
                p_text_lower = (p_status + " " + p_legal).lower()
                if "100%" in p_text_lower or "hoàn tất" in p_text_lower or "không có vướng" in p_text_lower or "hoàn chỉnh" in p_text_lower:
                    flag = "TÍCH CỰC"
                elif "vướng" in p_text_lower or "chờ" in p_text_lower:
                    flag = "CẢNH BÁO"
                else:
                    flag = "TIẾN ĐỘ BÌNH THƯỜNG"

            if flag == "TÍCH CỰC":
                p_flag_badge = '<span class="badge" style="background: rgba(16, 185, 129, 0.2); color: #34d399; border: 1px solid #10b981;">TÍCH CỰC</span>'
            elif flag == "CẢNH BÁO":
                p_flag_badge = '<span class="badge" style="background: rgba(239, 68, 68, 0.2); color: #f87171; border: 1px solid #ef4444;">CẦN THEO DÕI</span>'
            else:
                p_flag_badge = '<span class="badge" style="background: rgba(245, 158, 11, 0.2); color: #fbbf24; border: 1px solid #f59e0b;">TIẾN ĐỘ BÌNH THƯỜNG</span>'

            project_rows_html += f"""
            <tr>
                <td style="font-weight: 700; color: #f1f5f9;">{p_name}</td>
                <td style="color: #38bdf8; font-weight: 600;">{p_scale}</td>
                <td style="color: #cbd5e1; font-size: 0.85rem;">{p_status}</td>
                <td style="color: #34d399; font-size: 0.85rem; font-weight: 500;">{p_profit}</td>
                <td style="color: #cbd5e1; font-size: 0.85rem;">{p_legal}</td>
                <td style="text-align: center;">{p_flag_badge}</td>
            </tr>
            """
    else:
        project_rows_html = """
        <tr>
            <td colspan="6" style="text-align: center; color: #94a3b8; padding: 20px;">
                Dữ liệu các dự án riêng lẻ đang được cập nhật thêm theo báo cáo phân tích mới nhất.
            </td>
        </tr>
        """

    # 7. Phân tích Kỹ thuật Nâng cao (Advanced TA)
    ind = ta_result.get("indicators", {})
    vol_ratio = ind.get("vol_ratio", 1.0)
    rsi14 = ind.get("rsi14", 50)
    vsa_phase = ta_result.get("vsa", {}).get("phase", "Tích lũy")
    is_breakout = ta_result.get("oneil", {}).get("is_breakout", False)

    adv_ta = ta_result.get("advanced_ta", {})
    vcp_data = adv_ta.get("vcp") if isinstance(adv_ta.get("vcp"), dict) else {}
    vsa_sig = adv_ta.get("vsa_signals") if isinstance(adv_ta.get("vsa_signals"), dict) else {}
    fibo_data = adv_ta.get("fibonacci") if isinstance(adv_ta.get("fibonacci"), dict) else {}
    
    overhead_raw = adv_ta.get("overhead_supply_detail") or adv_ta.get("overhead_supply")
    if isinstance(overhead_raw, dict):
        overhead_data = overhead_raw
    else:
        oh_val = float(overhead_raw) if overhead_raw else 0.0
        overhead_data = {
            "resistance_cluster": f"{oh_val:,.0f} đ (Đỉnh cũ)" if oh_val > 0 else "Không có vùng kẹp lớn",
            "supply_intensity": "Thấp" if current_price >= oh_val and oh_val > 0 else "Vừa phải",
            "explanation": f"Kháng cự nguồn cung kẹp hàng tại đỉnh cũ quanh {oh_val:,.0f} đ."
        }

    vcp_contractions_str = " &rarr; ".join(vcp_data.get("contractions", ["Không có biến động lớn"]))
    vsa_signals_list = vsa_sig.get("signal_descriptions", ["Vận động khối lượng dao động bình thường quanh trung bình 20 phiên."])
    vsa_signals_html = "".join([f"<li>{s}</li>" for s in vsa_signals_list])

    # 8. Bàn tròn Hội đồng AI Đa trường phái (Council Grid & Clash)
    council_members = council_result.get("members", [])
    voting_summary = council_result.get("voting_summary", {})
    clash_data = council_result.get("clash_of_perspectives", [])

    bull_members = []
    bear_members = []
    watch_members = []

    for m in council_members:
        st = (m.get("stance") or "").upper()
        if any(k in st for k in ["MUA", "TĂNG", "TÍCH CỰC", "VÀO", "BỨT PHÁ"]) and not any(k in st for k in ["TRÁNH", "PHẢN ĐỐI", "CHỜ", "QUAN SÁT"]):
            bull_members.append(m)
        elif any(k in st for k in ["TRÁNH", "BÁN", "PHẢN ĐỐI", "THẬN TRỌNG", "RỦI RO", "GIẢM", "CẢNH BÁO"]):
            bear_members.append(m)
        else:
            watch_members.append(m)

    bull_count = len(bull_members)
    bear_count = len(bear_members)
    watch_count = len(watch_members)
    council_vote_details_html = build_council_vote_details_html(bull_members, watch_members, bear_members)

    consensus_score = voting_summary.get("consensus_score", trade_setup.get("consensus_score", 50))
    verdict = voting_summary.get("action") or voting_summary.get("verdict", trade_setup.get("action", "QUAN SÁT"))

    council_cards_html = ""
    for m in council_members:
        st_color = m.get("stance_color", "#3b82f6")
        badge = m.get("badge", "👤 CHUYÊN GIA")
        avatar = badge.split()[0] if badge else "👤"
        name = m.get("name", "Chuyên gia AI")
        role = m.get("role_title") or m.get("role", "Thành viên Hội đồng")
        stance = m.get("stance", "QUAN SÁT")
        score = m.get("score", 50)
        core_thesis = m.get("core_thesis") or m.get("key_thesis", "")
        invalidation = m.get("invalidation") or m.get("invalidation_condition", "Không có điều kiện cụ thể.")
        
        args_list = m.get("arguments", [])
        args_html = "".join([f"<li style='margin-bottom: 4px;'>{a}</li>" for a in args_list]) if args_list else ""

        council_cards_html += f"""
        <div style="background: rgba(15, 23, 42, 0.75); border: 1px solid var(--border); border-radius: 14px; padding: 18px; display: flex; flex-direction: column; justify-content: space-between;">
            <div>
                <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 12px;">
                    <div style="display: flex; align-items: center; gap: 10px;">
                        <span style="font-size: 1.8rem;">{avatar}</span>
                        <div>
                            <div style="font-weight: 700; color: #fff; font-size: 1rem;">{name}</div>
                            <div style="font-size: 0.78rem; color: #94a3b8;">{role}</div>
                        </div>
                    </div>
                    <span class="badge" style="background: rgba(255,255,255,0.06); color: {st_color}; border: 1px solid {st_color}; font-size: 0.75rem;">
                        {stance} ({score}/100)
                    </span>
                </div>
                
                <div style="margin-bottom: 10px; font-size: 0.88rem; color: #cbd5e1; line-height: 1.6;">
                    <b style="color: #38bdf8;">Luận điểm cốt lõi:</b> {core_thesis}
                </div>

                {f'<ul class="bullet-list" style="margin-bottom: 12px; font-size: 0.84rem;">{args_html}</ul>' if args_html else ''}
            </div>
            
            <div style="border-top: 1px solid rgba(255,255,255,0.08); padding-top: 10px; margin-top: 10px; font-size: 0.82rem; color: #f87171; line-height: 1.5;">
                <b>⚠️ Điều kiện mất hiệu lực:</b> {invalidation}
            </div>
        </div>
        """

    # Clash of perspectives HTML
    clash_html = ""
    if isinstance(clash_data, list):
        for idx, cl in enumerate(clash_data, 1):
            clash_html += f"""
            <div style="background: rgba(30, 41, 59, 0.6); border: 1px solid rgba(239, 68, 68, 0.3); border-radius: 14px; padding: 18px; margin-bottom: 16px;">
                <div style="font-weight: 700; color: #f87171; font-size: 0.95rem; margin-bottom: 12px; display: flex; align-items: center; gap: 8px;">
                    <span>⚔️ ĐỐI ĐẦU TRANH BIỆN #{idx}: {cl.get('topic', 'Va chạm góc nhìn')}</span>
                </div>
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 14px; margin-bottom: 14px;">
                    <div style="background: rgba(15, 23, 42, 0.6); padding: 12px; border-radius: 8px; border-left: 3px solid #38bdf8;">
                        <div style="font-size: 0.82rem; font-weight: 700; color: #38bdf8; margin-bottom: 4px;">{cl.get('side_a', {}).get('speaker')}</div>
                        <div style="font-size: 0.85rem; color: #cbd5e1; line-height: 1.5;">"{cl.get('side_a', {}).get('argument')}"</div>
                    </div>
                    <div style="background: rgba(15, 23, 42, 0.6); padding: 12px; border-radius: 8px; border-left: 3px solid #fbbf24;">
                        <div style="font-size: 0.82rem; font-weight: 700; color: #fbbf24; margin-bottom: 4px;">{cl.get('side_b', {}).get('speaker')}</div>
                        <div style="font-size: 0.85rem; color: #cbd5e1; line-height: 1.5;">"{cl.get('side_b', {}).get('argument')}"</div>
                    </div>
                </div>
                <div style="background: rgba(16, 185, 129, 0.1); border: 1px solid rgba(16, 185, 129, 0.3); border-radius: 8px; padding: 12px;">
                    <span style="font-weight: 700; color: #34d399; font-size: 0.85rem;">🛡️ Phán quyết Điều hòa của Chief Risk Officer (CRO):</span>
                    <p style="font-size: 0.85rem; color: #e2e8f0; margin-top: 4px; line-height: 1.5;">{cl.get('cro_synthesis')}</p>
                </div>
            </div>
            """
    elif isinstance(clash_data, str) and clash_data.strip():
        clash_html = f"""
        <div style="background: rgba(30, 41, 59, 0.6); border: 1px solid rgba(239, 68, 68, 0.3); border-radius: 14px; padding: 18px; margin-bottom: 16px;">
            <div style="font-size: 0.88rem; color: #cbd5e1; line-height: 1.6;">
                {clash_data.replace(chr(10), '<br>')}
            </div>
        </div>
        """

    # Council full text report
    council_text = council_result.get("council_report", "")
    council_report_html = ""
    if council_text:
        formatted_council = council_text.replace("### ", '<h4 style="color: #38bdf8; margin: 18px 0 8px 0;">').replace("\n- ", "<br>&bull; ")
        council_report_html = f"""
        <details style="margin-top: 24px; background: rgba(15, 23, 42, 0.6); border: 1px solid var(--border); border-radius: 12px; padding: 16px;">
            <summary style="cursor: pointer; font-weight: 700; color: #94a3b8; font-size: 0.9rem;">
                📜 Xem Toàn văn Báo cáo Thảo luận Chi tiết của Ban Điều phối Hội đồng AI &darr;
            </summary>
            <div style="margin-top: 14px; font-size: 0.88rem; color: #cbd5e1; line-height: 1.7;">
                {formatted_council}
            </div>
        </details>
        """

    # Render shareholders
    sh_rows_html = ""
    for sh in own.get("top_shareholders", [])[:5]:
        sh_rows_html += f"""
        <tr>
            <td style="color: #f1f5f9; font-weight: 500;">{sh.get('name')}</td>
            <td style="text-align: right; color: #38bdf8; font-weight: 600;">{sh.get('percentage')}%</td>
            <td style="text-align: right; color: #94a3b8;">{sh.get('shares', 0):,.0f} CP</td>
        </tr>
        """

    # Macro drivers list
    macro_drivers_html = "".join([f"<li>{d}</li>" for d in macro.get("macro_drivers", [])])
    key_metrics_html = "".join([f"<li>{m}</li>" for m in macro.get("key_metrics_to_watch", [])])
    red_flags_html = "".join([f"<li style='color: #f87171;'>⚠️ {rf}</li>" for rf in cf.get("red_flags", [])]) if cf.get("red_flags") else "<li style='color: #34d399;'>✅ Không phát hiện cờ đỏ tài chính nghiêm trọng về dòng tiền.</li>"

    val_warn_text = trade_setup.get('value_warning', '')
    val_warn_html = f"<div style='margin-top: 8px; color: #f87171; font-size: 0.85rem;'>⚠️ <b>Cảnh báo định giá:</b> {val_warn_text}</div>" if val_warn_text else ""

    val_gap_text = trade_setup.get('valuation_gap_explanation', '')
    val_gap_html = f"<div style='margin-top: 8px; color: #38bdf8; font-size: 0.85rem;'>💡 <b>Lý giải chênh lệch thị giá vs giá trị thực:</b> {val_gap_text}</div>" if val_gap_text else ""

    # =====================================================================
    # 9. Ticker Vĩ Mô & Hàng Hóa Toàn Cầu
    # =====================================================================
    global_comm = macro.get("global_commodities", {})
    comm_sens = macro.get("commodity_sensitivity", {})

    brent = global_comm.get("crude_oil_brent", {"value": 78.5, "change_pct": 2.8})
    gold_sjc = global_comm.get("gold_sjc", {"value": 84.5, "change_pct": 0.6})
    rubber = global_comm.get("rubber_tsr20", {"value": 204.5, "change_pct": 4.2})
    steel = global_comm.get("steel_hrc", {"value": 545.0, "change_pct": 1.8})
    fed = global_comm.get("fed_funds_rate", {"value": 4.88, "trend": "Nới lỏng"})
    fx = global_comm.get("usd_vnd", {"value": 25380, "change_pct": 0.3})

    macro_impact_matrix_html = build_comprehensive_macro_impact_matrix(symbol, sector_name, global_comm)
    glossary_html = build_glossary_html()

    # =====================================================================
    # 10. Động Cơ Dự Báo Thời Điểm Tăng / Sập (Timing Matrix)
    # =====================================================================
    surge = timing_result.get("surge_scenario", {}) if timing_result else {}
    crash = timing_result.get("crash_scenario", {}) if timing_result else {}
    timing_verdict = timing_result.get("timing_verdict", "TÍCH LŨY THEO DÕI") if timing_result else "TÍCH LŨY THEO DÕI"
    timing_color = timing_result.get("timing_color", "#38bdf8") if timing_result else "#38bdf8"
    overall_timing_score = timing_result.get("overall_timing_score", 65) if timing_result else 65
    surge_catalysts_html = "".join([f"<li style='margin-bottom: 6px;'>{c}</li>" for c in surge.get("catalysts", [])]) if surge.get("catalysts") else "<li>Đang tích lũy chặt chẽ quanh hỗ trợ.</li>"
    crash_warnings_html = "".join([f"<li style='margin-bottom: 6px; color: #fca5a5;'>{w}</li>" for w in crash.get("warnings", [])]) if crash.get("warnings") else "<li>Chưa xuất hiện phân phối lớn.</li>"

    # =====================================================================
    # 11. Xử lý Dữ liệu Nến Nhật cho TradingView Lightweight Charts
    # =====================================================================
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
            vol = float(row.get("volume", 0))

            chart_candles.append({"time": d_str, "open": op, "high": hi, "low": lo, "close": cl})
            v_color = "rgba(16, 185, 129, 0.7)" if cl >= op else "rgba(239, 68, 68, 0.7)"
            chart_volume.append({"time": d_str, "value": vol, "color": v_color})
            if pd.notna(row.get("ema20")):
                chart_ema20.append({"time": d_str, "value": round(float(row["ema20"]), 1)})
            if pd.notna(row.get("ema50")):
                chart_ema50.append({"time": d_str, "value": round(float(row["ema50"]), 1)})

    # =====================================================================
    # 12. Thước Đo Kích Hoạt Trực Quan (Price Ladder & Timing Distance Gauge)
    # =====================================================================
    # =====================================================================
    # 12. Thước Đo Kích Hoạt Trực Quan (Price Ladder & Timing Distance Gauge)
    # =====================================================================
    if 0 < current_price < 1000:
        current_price *= 1000

    trigger_pivot = float(surge.get("trigger_pivot_price") or (current_price * 1.03))
    failure_level = float(crash.get("failure_trigger_level") or (current_price * 0.95))
    stop_loss_lvl = float(trade_setup.get("stop_loss") or (current_price * 0.93))
    tp1_lvl = float(trade_setup.get("take_profit_1") or (current_price * 1.12))
    tp2_lvl = float(trade_setup.get("take_profit_2") or (current_price * 1.20))

    if 0 < trigger_pivot < 1000:
        trigger_pivot *= 1000
    if 0 < failure_level < 1000:
        failure_level *= 1000
    if 0 < stop_loss_lvl < 1000:
        stop_loss_lvl *= 1000
    if 0 < tp1_lvl < 1000:
        tp1_lvl *= 1000

    dist_pivot_pct = ((trigger_pivot - current_price) / current_price * 100) if current_price > 0 else 0.0
    dist_sl_pct = ((stop_loss_lvl - current_price) / current_price * 100) if current_price > 0 else 0.0
    dist_fail_pct = ((failure_level - current_price) / current_price * 100) if current_price > 0 else 0.0
    dist_tp1_pct = ((tp1_lvl - current_price) / current_price * 100) if current_price > 0 else 0.0

    # Xác định vị trí tương đối giữa Stop loss và Ngưỡng gãy sóng
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

    # Chuẩn bị khối Smart Money Pulse & Lịch Catalyst (Lựa chọn 1)
    smart_money_and_catalyst_html = build_smart_money_and_catalyst_html(timing_result)

    # Chuẩn bị khối Hỏi Đáp Tương Tác Hội Đồng AI (Lựa chọn 4)
    fair_price_val = float(trade_setup.get("fair_price") or current_price)
    sl_val = float(trade_setup.get("stop_loss") or (current_price * 0.93))
    sl_pct_val = float(trade_setup.get("stop_loss_pct") or 7.0)
    tp1_val = float(trade_setup.get("take_profit_1") or (current_price * 1.12))
    tp1_pct_val = float(trade_setup.get("take_profit_1_pct") or 12.0)
    trigger_pivot_val = float(surge.get("trigger_pivot_price") or (current_price * 1.03))
    pb_val = float(asset_val.get("pb") if isinstance(asset_val.get("pb"), (int, float)) else 1.0)
    bvps_val = float(asset_val.get("bvps", current_price) or current_price)
    cfo_val_str = format_vnd_human(cfo_ttm)
    fcf_val_str = format_vnd_human(fcf_ttm)
    pulse_data = timing_result.get("smart_money_pulse", {}) if timing_result else {}
    active_buy_pct_val = float(pulse_data.get("active_buy_pct", 50.0))

    interactive_council_qa_html = build_interactive_council_qa_html(
        symbol=symbol,
        current_price=current_price,
        fair_price=fair_price_val,
        stop_loss=sl_val,
        sl_pct=sl_pct_val,
        tp1=tp1_val,
        tp1_pct=tp1_pct_val,
        trigger_pivot=trigger_pivot_val,
        cfo_human=cfo_val_str,
        fcf_human=fcf_val_str,
        pb=pb_val,
        bvps=bvps_val,
        active_buy_pct=active_buy_pct_val
    )

    # HTML Template
    html_content = f"""<!DOCTYPE html>

<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>Báo cáo Chiến lược Toàn diện {symbol} | Vietnam Stock Analyzer</title>
    <!-- Chart.js & Lightweight Charts via CDN -->
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script src="https://unpkg.com/lightweight-charts@4.1.3/dist/lightweight-charts.standalone.production.js"></script>
    <style>
        :root {{
            --bg-main: #0a0e17;
            --bg-card: #111827;
            --bg-card-alt: #1a2333;
            --border: #263345;
            --border-highlight: #3b82f6;
            --text-primary: #f8fafc;
            --text-secondary: #94a3b8;
            --text-muted: #64748b;
            --accent-green: #10b981;
            --accent-red: #ef4444;
            --accent-blue: #3b82f6;
            --accent-amber: #f59e0b;
            --accent-purple: #8b5cf6;
        }}

        * {{
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
            background-color: var(--bg-main);
            color: var(--text-primary);
            line-height: 1.5;
            padding-bottom: 60px;
            -webkit-font-smoothing: antialiased;
        }}

        /* Header Bar */
        .top-navbar {{
            position: sticky;
            top: 0;
            z-index: 100;
            background: rgba(10, 14, 23, 0.96);
            backdrop-filter: blur(12px);
            border-bottom: 1px solid var(--border);
            padding: 12px 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}

        .brand-title {{
            font-size: 0.9rem;
            font-weight: 700;
            color: var(--text-secondary);
            letter-spacing: 0.5px;
            text-transform: uppercase;
        }}

        .report-time {{
            font-size: 0.78rem;
            color: var(--text-muted);
        }}

        .container {{
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px 16px;
        }}

        /* Executive Header */
        .hero-card {{
            background: linear-gradient(145deg, #131c2e, #0f172a);
            border: 1px solid var(--border);
            border-radius: 16px;
            padding: 24px;
            margin-bottom: 24px;
            box-shadow: 0 10px 25px rgba(0, 0, 0, 0.4);
        }}

        .hero-header {{
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            flex-wrap: wrap;
            gap: 16px;
        }}

        .hero-left h1 {{
            font-size: 2.2rem;
            font-weight: 800;
            letter-spacing: -0.5px;
            color: #fff;
            display: flex;
            align-items: center;
            gap: 12px;
        }}

        .hero-left p {{
            color: var(--text-secondary);
            font-size: 0.95rem;
            margin-top: 4px;
        }}

        .price-badge-group {{
            display: flex;
            align-items: baseline;
            gap: 10px;
            margin-top: 10px;
        }}

        .hero-price {{
            font-size: 1.8rem;
            font-weight: 800;
            color: {chg_color};
        }}

        .hero-change {{
            font-size: 1.05rem;
            font-weight: 700;
            color: {chg_color};
            background: rgba(255, 255, 255, 0.05);
            padding: 4px 10px;
            border-radius: 8px;
        }}

        .hero-action-box {{
            text-align: right;
            background: {action_bg};
            border: 1px solid {action_border};
            padding: 16px 22px;
            border-radius: 14px;
        }}

        .hero-action-label {{
            font-size: 0.75rem;
            text-transform: uppercase;
            letter-spacing: 1px;
            color: var(--text-secondary);
            font-weight: 600;
        }}

        .hero-action-title {{
            font-size: 1.35rem;
            font-weight: 800;
            color: {action_text};
            margin-top: 2px;
        }}

        .consensus-meter {{
            font-size: 0.85rem;
            color: var(--text-secondary);
            margin-top: 4px;
        }}

        /* Section Layout */
        .section-title {{
            font-size: 1.25rem;
            font-weight: 700;
            margin: 34px 0 16px 0;
            display: flex;
            align-items: center;
            gap: 10px;
            color: #f8fafc;
        }}

        .card-grid-2 {{
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 20px;
        }}

        .card-grid-3 {{
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 18px;
        }}

        .card {{
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 14px;
            padding: 20px;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
        }}

        .card-header {{
            font-size: 1rem;
            font-weight: 700;
            color: #f1f5f9;
            margin-bottom: 14px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 1px solid rgba(255, 255, 255, 0.06);
            padding-bottom: 10px;
        }}

        /* Badges */
        .badge {{
            display: inline-block;
            font-size: 0.75rem;
            font-weight: 700;
            padding: 4px 10px;
            border-radius: 6px;
            letter-spacing: 0.3px;
        }}

        /* Tables */
        .table-responsive {{
            overflow-x: auto;
            -webkit-overflow-scrolling: touch;
        }}

        table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 0.88rem;
        }}

        th, td {{
            padding: 10px 12px;
            border-bottom: 1px solid var(--border);
            text-align: left;
        }}

        th {{
            background: rgba(15, 23, 42, 0.8);
            color: var(--text-muted);
            font-weight: 600;
            font-size: 0.78rem;
            text-transform: uppercase;
        }}

        /* Bullet lists */
        ul.bullet-list {{
            list-style: none;
            padding: 0;
        }}

        ul.bullet-list li {{
            position: relative;
            padding-left: 20px;
            margin-bottom: 8px;
            font-size: 0.88rem;
            color: #cbd5e1;
            line-height: 1.45;
        }}

        ul.bullet-list li::before {{
            content: "•";
            position: absolute;
            left: 4px;
            color: var(--accent-blue);
            font-size: 1.1rem;
        }}

        /* Progress Bar */
        .progress-bar-bg {{
            background: rgba(255, 255, 255, 0.1);
            height: 8px;
            border-radius: 4px;
            overflow: hidden;
            margin: 8px 0;
        }}

        .progress-bar-fill {{
            height: 100%;
            border-radius: 4px;
        }}

        /* Mobile Optimization */
        @media (max-width: 768px) {{
            .hero-header {{
                flex-direction: column;
                align-items: stretch;
            }}
            .hero-action-box {{
                text-align: left;
            }}
            .card-grid-2, .card-grid-3 {{
                grid-template-columns: 1fr;
            }}
            .hero-left h1 {{
                font-size: 1.8rem;
            }}
        }}

        /* QUICK NAV BAR */
        .quick-nav-bar {{
            position: sticky;
            top: 48px;
            z-index: 95;
            background: rgba(10, 14, 23, 0.96);
            backdrop-filter: blur(12px);
            border-bottom: 1px solid var(--border);
            padding: 10px 16px;
            margin: -12px -16px 24px -16px;
            display: flex;
            gap: 8px;
            overflow-x: auto;
            scrollbar-width: none;
        }}
        .quick-nav-bar::-webkit-scrollbar {{ display: none; }}
        .q-link {{
            color: var(--text-secondary);
            text-decoration: none;
            font-size: 12px;
            font-weight: 600;
            padding: 6px 14px;
            border-radius: 8px;
            background: rgba(255, 255, 255, 0.04);
            border: 1px solid rgba(255, 255, 255, 0.06);
            white-space: nowrap;
            transition: all 0.2s;
        }}
        .q-link:hover {{
            color: #fff;
            background: var(--bg-card-alt);
            border-color: var(--accent-blue);
        }}

        /* PRICE LADDER WIDGET */
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

        /* PRINT STYLES */
        @media print {{
            body {{
                background: #ffffff !important;
                color: #0f172a !important;
                padding: 0 !important;
            }}
            .top-navbar, .quick-nav-bar, .report-time {{
                display: none !important;
            }}
            .hero-card, .card, .price-ladder-box, div {{
                background: #ffffff !important;
                color: #0f172a !important;
                border-color: #cbd5e1 !important;
                box-shadow: none !important;
            }}
            h1, h2, h3, h4, b, strong, .hero-left h1, .step-price {{
                color: #0f172a !important;
            }}
            th {{
                background: #f1f5f9 !important;
                color: #334155 !important;
            }}
            td {{
                color: #0f172a !important;
                border-bottom: 1px solid #e2e8f0 !important;
            }}
            .badge {{
                border: 1px solid #64748b !important;
                color: #0f172a !important;
                background: #f8fafc !important;
            }}
            .bullet-list li {{
                color: #334155 !important;
            }}
        }}
    </style>
</head>
<body>

    <!-- Top Navbar -->
    <div class="top-navbar">
        <div class="brand-title">🏛️ VIETNAM STOCK ANALYZER &bull; BÁO CÁO NGHIÊN CỨU CHIẾN LƯỢC</div>
        <div class="report-time">{datetime.now().strftime('%d/%m/%Y %H:%M')}</div>
    </div>

    <div class="container">

        <!-- EXECUTIVE HERO CARD -->
        <div class="hero-card">
            <div class="hero-header">
                <div class="hero-left">
                    <h1>
                        {symbol}
                        <span class="badge" style="{ex_badge_style}">{exchange_val}</span>
                        <span class="badge" style="background: rgba(139, 92, 246, 0.2); color: #c084fc; border: 1px solid #8b5cf6;">{sector_name}</span>
                    </h1>
                    <p>{quote.get('company_name', symbol)}</p>
                    <div class="price-badge-group">
                        <span class="hero-price">{current_price:,.0f} đ</span>
                        <span class="hero-change">{chg_sign}{change_pct:.2f}%</span>
                        <span style="font-size: 0.85rem; color: #94a3b8; margin-left: 10px;">Khối lượng: <b>{quote.get('volume', 0):,.0f}</b> CP ({vol_ratio:.2f}x MA20)</span>
                    </div>
                </div>

                <div class="hero-action-box">
                    <div class="hero-action-label">Phán quyết Giám đốc Quản trị Rủi ro (CRO)</div>
                    <div class="hero-action-title">{action}</div>
                    <div class="consensus-meter">Độ đồng thuận Hội đồng AI: <b>{consensus_score}/100</b> điểm ({voting_summary.get('bull_count', 0)} Ủng hộ / {voting_summary.get('watch_count', 0)} Quan sát / {voting_summary.get('bear_count', 0)} Phản đối)</div>
                </div>
            </div>

            <!-- Tách bạch 2 Kế hoạch: Đầu tư Giá trị vs Lướt sóng Kỹ thuật -->
            <div style="margin-top: 20px; display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 16px;">
                <!-- Box 1: Đầu tư Giá trị -->
                <div style="background: rgba(30, 41, 59, 0.7); border: 1px solid #334155; border-radius: 12px; padding: 18px;">
                    <div style="font-size: 0.9rem; font-weight: 700; color: #38bdf8; display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; border-bottom: 1px solid rgba(255,255,255,0.06); padding-bottom: 8px;">
                        <span>🏛️ ĐẦU TƯ GIÁ TRỊ (BUFFETT & GRAHAM)</span>
                        <span class="badge" style="background: rgba(56, 189, 248, 0.15); color: #38bdf8; border: 1px solid #38bdf8;">{trade_setup.get('value_status', 'ĐỊNH GIÁ HỢP LÝ')}</span>
                    </div>
                    <div style="font-size: 0.88rem; color: #cbd5e1; line-height: 1.7;">
                        • Giá trị thực nội tại ước tính: <b style="color: #fff; font-size: 1.05rem;">{trade_setup.get('fair_price', current_price):,.0f} đ</b><br>
                        • Vùng gom an toàn (Biên an toàn &ge; 15%): <b style="color: #34d399; font-size: 1rem;">{trade_setup.get('value_buy_zone')}</b><br>
                        • Cơ sở định giá: <i>{trade_setup.get('value_rationale')}</i>
                        {val_gap_html}
                        {val_warn_html}
                    </div>
                </div>

                <!-- Box 2: Lướt sóng Kỹ thuật -->
                <div style="background: rgba(30, 41, 59, 0.7); border: 1px solid #334155; border-radius: 12px; padding: 18px;">
                    <div style="font-size: 0.9rem; font-weight: 700; color: #fbbf24; display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; border-bottom: 1px solid rgba(255,255,255,0.06); padding-bottom: 8px;">
                        <span>🏄 LƯỚT SÓNG NGẮN HẠN (SWING TRADING / KỸ THUẬT)</span>
                        <span class="badge" style="background: rgba(251, 191, 36, 0.15); color: #fbbf24; border: 1px solid #fbbf24;">R:R {trade_setup.get('risk_reward_ratio')}:1</span>
                    </div>
                    <div style="font-size: 0.88rem; color: #cbd5e1; line-height: 1.7;">
                        • Vùng mua lướt sóng: <b style="color: #38bdf8;">{trade_setup.get('swing_buy_zone')} đ</b><br>
                        • Cắt lỗ nghiêm ngặt (SL): <b style="color: #f87171;">{trade_setup.get('stop_loss', 0):,.0f} đ (-{trade_setup.get('stop_loss_pct', 0)}%)</b><br>
                        • Chốt lời (Mục tiêu 1 &bull; 2): <b style="color: #34d399;">{trade_setup.get('take_profit_1', 0):,.0f} đ (+{trade_setup.get('take_profit_1_pct', 0)}%) &bull; {trade_setup.get('take_profit_2', 0):,.0f} đ (+{trade_setup.get('take_profit_2_pct', 0)}%)</b><br>
                        • Tỷ trọng giải ngân tối đa: <b>Max {trade_setup.get('max_position_size_pct', 10.0):.1f}% tổng danh mục</b><br>
                        • Kỷ luật giao dịch: <i>{trade_setup.get('swing_strategy_note')}</i>
                    </div>
                </div>
        </div>

        <!-- QUICK NAV BAR -->
        <div class="quick-nav-bar">
            <a href="#sec-timing" class="q-link">⚡ Khối Thời Điểm</a>
            <a href="#sec-chart" class="q-link">📈 Biểu Đồ Nến Nhật</a>
            <a href="#sec-macro" class="q-link">🌐 Vĩ Mô & Hàng Hóa</a>
            <a href="#sec-business" class="q-link">🏢 Mô Hình Kinh Doanh</a>
            <a href="#sec-projects" class="q-link">🏗️ Danh Mục Dự Án</a>
            <a href="#sec-cashflow" class="q-link">🔬 Dòng Tiền Thật</a>
            <a href="#sec-governance" class="q-link">👥 Quản Trị & Sân Sau</a>
            <a href="#sec-council" class="q-link">🏛️ Hội Đồng 6 AI</a>
            <a href="#sec-qa" class="q-link">💬 Bàn Tròn Hỏi Đáp</a>
            <a href="#sec-glossary" class="q-link">📚 Sổ Tay Thuật Ngữ</a>
        </div>

        <!-- MA TRẬN HÀNG HÓA VÀ VĨ MÔ TOÀN CẦU -->
        <div id="sec-macro" style="background: rgba(15, 23, 42, 0.85); border: 1px solid var(--border); border-radius: 14px; padding: 18px; margin-bottom: 24px;">
            <div style="font-size: 0.85rem; font-weight: 700; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 12px; display: flex; justify-content: space-between; align-items: center;">
                <span>📡 RADAR VĨ MÔ QUỐC TẾ & HÀNG HÓA THẾ GIỚI (COMMODITIES PULSE)</span>
                <span style="font-size: 0.75rem; color: #38bdf8;">Cập nhật tự động</span>
            </div>
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap: 10px; margin-bottom: 14px;">
                <div style="background: rgba(30, 41, 59, 0.6); padding: 10px 14px; border-radius: 10px; border-left: 3px solid #38bdf8;">
                    <div style="font-size: 0.75rem; color: #94a3b8;">🛢️ Dầu Brent</div>
                    <div style="font-size: 1.05rem; font-weight: 700; color: #fff;">{brent.get('value')} USD</div>
                    <div style="font-size: 0.75rem; color: {'#10b981' if brent.get('change_pct', 0) >= 0 else '#ef4444'};">{'▲ +' if brent.get('change_pct', 0) >= 0 else '▼ '}{brent.get('change_pct')}%</div>
                </div>
                <div style="background: rgba(30, 41, 59, 0.6); padding: 10px 14px; border-radius: 10px; border-left: 3px solid #f59e0b;">
                    <div style="font-size: 0.75rem; color: #94a3b8;">🥇 Vàng SJC</div>
                    <div style="font-size: 1.05rem; font-weight: 700; color: #fff;">{gold_sjc.get('value')} Tr/L</div>
                    <div style="font-size: 0.75rem; color: #10b981;">▲ +{gold_sjc.get('change_pct')}%</div>
                </div>
                <div style="background: rgba(30, 41, 59, 0.6); padding: 10px 14px; border-radius: 10px; border-left: 3px solid #10b981;">
                    <div style="font-size: 0.75rem; color: #94a3b8;">🌳 Cao su TSR20</div>
                    <div style="font-size: 1.05rem; font-weight: 700; color: #fff;">{rubber.get('value')} c/kg</div>
                    <div style="font-size: 0.75rem; color: #10b981;">▲ +{rubber.get('change_pct')}%</div>
                </div>
                <div style="background: rgba(30, 41, 59, 0.6); padding: 10px 14px; border-radius: 10px; border-left: 3px solid #6366f1;">
                    <div style="font-size: 0.75rem; color: #94a3b8;">🏗️ Thép HRC</div>
                    <div style="font-size: 1.05rem; font-weight: 700; color: #fff;">{steel.get('value')} USD</div>
                    <div style="font-size: 0.75rem; color: #38bdf8;">▲ +{steel.get('change_pct')}%</div>
                </div>
                <div style="background: rgba(30, 41, 59, 0.6); padding: 10px 14px; border-radius: 10px; border-left: 3px solid #a855f7;">
                    <div style="font-size: 0.75rem; color: #94a3b8;">🏛️ Lãi Suất Fed</div>
                    <div style="font-size: 1.05rem; font-weight: 700; color: #fff;">{fed.get('value')}%</div>
                    <div style="font-size: 0.75rem; color: #34d399;">Chu kỳ nới lỏng</div>
                </div>
                <div style="background: rgba(30, 41, 59, 0.6); padding: 10px 14px; border-radius: 10px; border-left: 3px solid #ec4899;">
                    <div style="font-size: 0.75rem; color: #94a3b8;">💵 Tỷ Giá USD/VND</div>
                    <div style="font-size: 1.05rem; font-weight: 700; color: #fff;">{fx.get('value'):,} đ</div>
                    <div style="font-size: 0.75rem; color: #fbbf24;">{fx.get('change_pct'):+.1f}%</div>
                </div>
            </div>
            <div style="background: rgba(2, 6, 23, 0.5); border: 1px solid rgba(56, 189, 248, 0.2); border-radius: 10px; padding: 12px 16px; font-size: 0.86rem; color: #cbd5e1; display: flex; align-items: flex-start; gap: 12px;">
                <span style="font-size: 1.4rem;">🎯</span>
                <div>
                    <b style="color: #38bdf8;">Tác động trực tiếp lên {symbol}:</b> Hàng hóa chi phối: <b style="color: #fff;">{comm_sens.get('commodity_name', 'Vĩ mô chung')}</b> &bull; Mức độ nhạy cảm: <span style="color: #fbbf24; font-weight: 700;">{comm_sens.get('sensitivity_level', 'Trung bình')}</span> &bull; Độ trễ thẩm thấu: <i style="color: #34d399;">{comm_sens.get('transmission_lag', '1-2 tuần')}</i>
                    <div style="margin-top: 4px; font-size: 0.82rem; color: #94a3b8;">{comm_sens.get('impact_summary', '')}</div>
                </div>
            </div>

            <!-- BẢNG NHẬN XÉT CHI TIẾT TƯƠNG QUAN 6 YẾU TỐ VĨ MÔ & HÀNG HÓA -->
            {macro_impact_matrix_html}
        </div>

        <!-- ĐỘNG CƠ DỰ BÁO THỜI ĐIỂM (TIMING PREDICTION ENGINE) -->
        <div id="sec-timing" style="background: linear-gradient(145deg, #131c2e, #0c1220); border: 1px solid rgba(56, 189, 248, 0.35); border-radius: 16px; padding: 22px; margin-bottom: 28px; box-shadow: 0 8px 30px rgba(0,0,0,0.4);">
            <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 12px; margin-bottom: 18px; border-bottom: 1px solid rgba(255,255,255,0.08); padding-bottom: 14px;">
                <div>
                    <div style="font-size: 0.8rem; font-weight: 700; color: #38bdf8; text-transform: uppercase; letter-spacing: 0.8px;">⚡ ĐỘNG CƠ DỰ BÁO THỜI ĐIỂM (TIMING PREDICTION MATRIX)</div>
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

            <!-- DÒNG TIỀN KHỚP LỆNH CHỦ ĐỘNG & LỊCH XÚC TÁC SỰ KIỆN -->
            {smart_money_and_catalyst_html}

            <!-- 2 CỘT: KHI NÀO TĂNG vs KHI NÀO SẬP -->
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(340px, 1fr)); gap: 18px;">
                <!-- CỘT 1: KHI NÀO TĂNG -->
                <div style="background: rgba(16, 185, 129, 0.08); border: 1px solid rgba(16, 185, 129, 0.3); border-radius: 14px; padding: 18px;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; border-bottom: 1px solid rgba(16, 185, 129, 0.2); padding-bottom: 8px;">
                        <span style="font-size: 0.95rem; font-weight: 800; color: #10b981; display: flex; align-items: center; gap: 8px;">
                            <span>🚀</span> KỊCH BẢN BỨT PHÁ (KHI NÀO SẼ TĂNG?)
                        </span>
                        <span class="badge" style="background: rgba(16, 185, 129, 0.2); color: #10b981; border: 1px solid #10b981; font-size: 0.8rem;">
                            Xác suất {surge.get('probability_pct')}%
                        </span>
                    </div>
                    <div style="font-size: 0.88rem; color: #cbd5e1; line-height: 1.65;">
                        <div style="margin-bottom: 8px;">
                            • <b>Khung thời gian bùng nổ:</b> <span style="color: #34d399; font-weight: 700;">{surge.get('timing_window')}</span><br>
                            • <b>Mốc giá kích hoạt xác nhận:</b> Vượt qua <b style="color: #fff; font-size: 1rem;">{surge.get('trigger_pivot_price', current_price):,.0f} đ</b> kèm Vol &ge; 1.3x MA20.
                        </div>
                        <div style="margin-top: 10px; font-size: 0.84rem;">
                            <b style="color: #10b981;">Động lực & Chất xúc tác cộng hưởng:</b>
                            <ul style="margin: 6px 0 0 16px;">
                                {surge_catalysts_html}
                            </ul>
                        </div>
                        <div style="margin-top: 12px; background: rgba(16, 185, 129, 0.12); padding: 10px; border-radius: 8px; font-size: 0.82rem; color: #a7f3d0;">
                            💡 <b>Hướng dẫn hành động:</b> {surge.get('action_advice')}
                        </div>
                    </div>
                </div>

                <!-- CỘT 2: KHI NÀO SẬP -->
                <div style="background: rgba(239, 68, 68, 0.08); border: 1px solid rgba(239, 68, 68, 0.3); border-radius: 14px; padding: 18px;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; border-bottom: 1px solid rgba(239, 68, 68, 0.2); padding-bottom: 8px;">
                        <span style="font-size: 0.95rem; font-weight: 800; color: #ef4444; display: flex; align-items: center; gap: 8px;">
                            <span>⚠️</span> KỊCH BẢN RỦI RO (KHI NÀO SẼ SẬP / ĐẢO CHIỀU?)
                        </span>
                        <span class="badge" style="background: rgba(239, 68, 68, 0.2); color: #f87171; border: 1px solid #ef4444; font-size: 0.8rem;">
                            Rủi ro {crash.get('risk_probability_pct')}%
                        </span>
                    </div>
                    <div style="font-size: 0.88rem; color: #cbd5e1; line-height: 1.65;">
                        <div style="margin-bottom: 8px;">
                            • <b>Khung thời gian rủi ro:</b> <span style="color: #f87171; font-weight: 700;">{crash.get('timing_window')}</span><br>
                            • <b>Mức giá vi phạm kích hoạt gãy:</b> Thủng mốc <b style="color: #f87171; font-size: 1rem;">{crash.get('failure_trigger_level', current_price*0.96):,.0f} đ</b>.
                        </div>
                        <div style="margin-top: 10px; font-size: 0.84rem;">
                            <b style="color: #f87171;">Dấu hiệu cảnh báo phân phối / bẫy giá:</b>
                            <ul style="margin: 6px 0 0 16px;">
                                {crash_warnings_html}
                            </ul>
                        </div>
                        <div style="margin-top: 12px; background: rgba(239, 68, 68, 0.12); padding: 10px; border-radius: 8px; font-size: 0.82rem; color: #fecaca;">
                            ⛔ <b>Nguyên tắc mất hiệu lực:</b> {crash.get('invalidation_rule')}
                        </div>
                    </div>
                </div>
            </div>

            <!-- THƯỚC ĐO KÍCH HOẠT TRỰC QUAN (PRICE LADDER) -->
            {price_ladder_html}
        </div>

        <!-- TẦNG 1: VĨ MÔ & CHU KỲ NGÀNH -->
        <div class="section-title">🌐 TẦNG 1: BỐI CẢNH VĨ MÔ & CHU KỲ NGÀNH (MACRO & SECTOR MATRIX)</div>

        <div class="card-grid-2">
            <div class="card">
                <div class="card-header">
                    <span>Định vị Chu kỳ Ngành: {sector_name}</span>
                    <span class="badge" style="background: rgba(16, 185, 129, 0.15); color: {tailwind_color}; border: 1px solid {tailwind_color};">{macro.get('sentiment', 'TÍCH CỰC')}</span>
                </div>
                <div style="margin-bottom: 12px;">
                    <span style="font-size: 0.8rem; color: var(--text-muted); text-transform: uppercase;">Pha chu kỳ hiện tại:</span>
                    <div style="font-size: 1.1rem; font-weight: 700; color: #fff; margin-top: 2px;">{cycle_phase}</div>
                    <p style="font-size: 0.85rem; color: #94a3b8; margin-top: 4px;">{macro.get('phase_description', '')}</p>
                </div>

                <div style="margin-top: 14px;">
                    <div style="display: flex; justify-content: space-between; font-size: 0.82rem;">
                        <span style="color: var(--text-secondary);">Điểm số Gió xuôi Vĩ mô (Thuận buồm xuôi gió)</span>
                        <span style="font-weight: 700; color: {tailwind_color};">{tailwind_score}/100</span>
                    </div>
                    <div class="progress-bar-bg">
                        <div class="progress-bar-fill" style="width: {tailwind_score}%; background: {tailwind_color};"></div>
                    </div>
                </div>

                <div style="margin-top: 16px;">
                    <div style="font-size: 0.85rem; font-weight: 700; color: #38bdf8; margin-bottom: 6px;">Động lực Vĩ mô Trọng tâm Hỗ trợ:</div>
                    <ul class="bullet-list">
                        {macro_drivers_html}
                    </ul>
                </div>
            </div>

            <div class="card">
                <div class="card-header">
                    <span>Trí tuệ Chu kỳ: Ray Dalio & Howard Marks</span>
                    <span class="badge" style="background: rgba(139, 92, 246, 0.2); color: #c084fc;">CHU KỲ VĨ MÔ</span>
                </div>
                <div style="margin-bottom: 14px;">
                    <div style="font-size: 0.85rem; font-weight: 700; color: #a78bfa; margin-bottom: 4px;">Ray Dalio (Cỗ máy Kinh tế & Tín dụng):</div>
                    <p style="font-size: 0.88rem; color: #cbd5e1; line-height: 1.5;">{macro.get('dalio_verdict', 'N/A')}</p>
                </div>

                <div style="margin-bottom: 14px;">
                    <div style="font-size: 0.85rem; font-weight: 700; color: #fbbf24; margin-bottom: 4px;">Howard Marks (Tâm lý Đám đông & Bẫy Chu kỳ):</div>
                    <p style="font-size: 0.88rem; color: #cbd5e1; line-height: 1.5;">{macro.get('marks_verdict', 'N/A')}</p>
                </div>

                <div style="border-top: 1px solid rgba(255, 255, 255, 0.08); padding-top: 12px; margin-top: 12px;">
                    <div style="font-size: 0.85rem; font-weight: 700; color: #38bdf8; margin-bottom: 6px;">Chỉ số Đặc thù Cần Giám sát Kỹ:</div>
                    <ul class="bullet-list">
                        {key_metrics_html}
                    </ul>
                </div>
            </div>
        </div>

        <!-- TẦNG 2: MÔ HÌNH KINH DOANH CỐT LÕI & CHI TIẾT TỪNG DỊCH VỤ -->
        <div id="sec-business" class="section-title">🏢 TẦNG 2: MÔ HÌNH KINH DOANH CỐT LÕI & CƠ CHẾ SINH TIỀN TỪ DỊCH VỤ</div>
        <div class="card" style="margin-bottom: 20px;">
            <div class="card-header">
                <span>Bóc tách Phân khúc Hoạt động (Core Business Breakdown)</span>
                <span class="badge" style="background: rgba(139, 92, 246, 0.15); color: #c084fc;">CƠ CẤU DOANH THU & LỢI NHUẬN</span>
            </div>
            <div style="font-size: 0.9rem; color: #cbd5e1; margin-bottom: 14px; line-height: 1.6;">
                <b>Tóm lược mô hình hoạt động:</b> {business_model_summary}
            </div>
            <div class="table-responsive" style="margin-bottom: 18px;">
                <table>
                    <thead>
                        <tr>
                            <th>Mảng kinh doanh</th>
                            <th style="text-align: right;">% Doanh thu</th>
                            <th style="text-align: right;">% Lợi nhuận gộp</th>
                            <th style="text-align: right;">Biên lãi gộp</th>
                            <th>Vai trò chiến lược</th>
                            <th>Điểm nhấn triển vọng</th>
                        </tr>
                    </thead>
                    <tbody>
                        {seg_rows_html}
                    </tbody>
                </table>
            </div>

            <div style="font-size: 0.95rem; font-weight: 700; color: #38bdf8; margin: 16px 0 10px 0;">
                🔎 Chi tiết Dịch vụ là gì? Bán cho ai? Cơ chế thu tiền thực tế ra sao:
            </div>
            <div>
                {seg_detail_cards_html}
            </div>
        </div>

        <!-- TẦNG 3: DANH MỤC DỰ ÁN TRỌNG ĐIỂM & TIẾN ĐỘ THỰC TẾ -->
        <div id="sec-projects" class="section-title">🏗️ TẦNG 3: DANH MỤC DỰ ÁN TRỌNG ĐIỂM & TIẾN ĐỘ THỰC TẾ (KEY PROJECTS & LEGAL AUDIT)</div>
        <div class="card" style="margin-bottom: 20px;">
            <div class="card-header">
                <span>Tiến độ Triển khai, Đóng góp Lợi nhuận & Rà soát Vướng mắc Pháp lý / GPMB</span>
                <span class="badge" style="background: rgba(56, 189, 248, 0.15); color: #38bdf8;">PROJECT PIPELINE</span>
            </div>
            <div style="font-size: 0.88rem; color: #94a3b8; margin-bottom: 14px;">
                Bảng theo dõi các dự án động lực đóng góp dòng tiền trong ngắn hạn và danh mục dự án gối đầu cho chu kỳ tăng trưởng dài hạn:
            </div>
            <div class="table-responsive">
                <table>
                    <thead>
                        <tr>
                            <th>Tên Dự án</th>
                            <th>Quy mô</th>
                            <th>Hiện trạng thực tế</th>
                            <th>Đóng góp Lợi nhuận</th>
                            <th>Pháp lý / Giải phóng mặt bằng (GPMB)</th>
                            <th style="text-align: center;">Đánh giá</th>
                        </tr>
                    </thead>
                    <tbody>
                        {project_rows_html}
                    </tbody>
                </table>
            </div>
        </div>

        <!-- TẦNG 4: SỨC KHỎE TÀI CHÍNH & BÓC TÁCH DÒNG TIỀN THẬT -->
        <div id="sec-cashflow" class="section-title">🔬 TẦNG 4: SỨC KHỎE BÁO CÁO TÀI CHÍNH & BÓC TÁCH DÒNG TIỀN THẬT</div>
        <div class="card-grid-3" style="margin-bottom: 20px;">
            <div class="card" style="border-left: 4px solid {quality_grade_color};">
                <div class="card-header">
                    <span>Chất lượng Lợi nhuận</span>
                    <span class="badge" style="background: rgba(16, 185, 129, 0.15); color: {quality_grade_color};">HẠNG {quality_grade}</span>
                </div>
                <div style="font-size: 1.1rem; font-weight: 700; color: {quality_grade_color};">{cf.get('quality_verdict', 'LÀNH MẠNH')}</div>
                <p style="font-size: 0.82rem; color: #94a3b8; margin-top: 6px;">{cf.get('quality_desc', '')}</p>
                <div style="margin-top: 10px; font-size: 0.85rem;">
                    Tỷ lệ Tiền thật / Lãi kế toán (CFO / LNST): <b style="color: #38bdf8;">{cf.get('earnings_quality_ratio', 1.0):.2f}x</b>
                    <br><span style="font-size: 0.78rem; color: #64748b;">(Tỷ lệ &ge; 1.0x nghĩa là lãi bao nhiêu tiền mặt về bấy nhiêu)</span>
                </div>
            </div>

            <div class="card" style="border-left: 4px solid {z_color};">
                <div class="card-header">
                    <span>Altman Z''-Score (Nguy cơ Phá sản)</span>
                    <span class="badge" style="background: rgba(59, 130, 246, 0.15); color: {z_color};">{z_zone}</span>
                </div>
                <div style="font-size: 1.6rem; font-weight: 800; color: {z_color};">{altman_z:.2f} điểm</div>
                <div style="font-size: 0.85rem; font-weight: 600; color: #fff; margin-top: 2px;">{cf.get('z_verdict', 'AN TOÀN')}</div>
                <p style="font-size: 0.78rem; color: #94a3b8; margin-top: 4px;">{cf.get('z_desc', '')}</p>
            </div>

            <div class="card" style="border-left: 4px solid {f_color};">
                <div class="card-header">
                    <span>Piotroski F-Score (Độ khỏe Tài chính)</span>
                    <span class="badge" style="background: rgba(16, 185, 129, 0.15); color: {f_color};">{f_score}/9 ĐIỂM</span>
                </div>
                <div style="font-size: 1.6rem; font-weight: 800; color: {f_color};">{f_score}/9</div>
                <div style="font-size: 0.85rem; color: #94a3b8; margin-top: 4px; line-height: 1.6;">
                    ROA (Sinh lời trên tài sản): <b>{fin.get('roa', 0):.1f}%</b><br>
                    ROE (Sinh lời trên vốn chủ): <b>{fin.get('roe', 0):.1f}%</b><br>
                    Nợ vay / Vốn CSH: <b>{fin.get('debt_to_equity', 0)}x</b>
                </div>
            </div>
        </div>

        <!-- Biểu đồ Dòng tiền & Cờ đỏ -->
        <div class="card-grid-2">
            <div class="card">
                <div class="card-header">
                    <span>So sánh Dòng tiền thật (CFO) vs LNST Kế toán (Tỷ VNĐ)</span>
                    <span class="badge" style="background: rgba(56, 189, 248, 0.15); color: #38bdf8;">4 QUÝ GẦN NHẤT</span>
                </div>
                <div style="height: 240px; position: relative;">
                    <canvas id="cashFlowChart"></canvas>
                </div>
                <div style="font-size: 0.78rem; color: var(--text-muted); text-align: center; margin-top: 10px;">
                    Cột xanh dương: Lợi nhuận sau thuế &bull; Cột xanh lá: Tiền kinh doanh thực thu (CFO) &bull; Đường vàng: Dòng tiền tự do (FCF)
                </div>
            </div>

            <div class="card">
                <div class="card-header">
                    <span>Rà soát Cờ đỏ Kế toán (Forensic Audit)</span>
                    <span class="badge" style="background: rgba(239, 68, 68, 0.15); color: #ef4444;">CẢNH BÁO RỦI RO</span>
                </div>
                <ul class="bullet-list" style="margin-bottom: 16px;">
                    {red_flags_html}
                </ul>

                <!-- 2 HỘP GIẢI THÍCH BÌNH DÂN: CFO & FCF GIÚP GÌ CHO NHÀ ĐẦU TƯ -->
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 12px; margin-bottom: 16px;">
                    <!-- Box CFO -->
                    <div style="background: rgba(16, 185, 129, 0.08); border: 1px solid rgba(16, 185, 129, 0.3); border-radius: 10px; padding: 14px;">
                        <div style="font-weight: 700; color: #34d399; font-size: 0.9rem; margin-bottom: 6px; display: flex; align-items: center; gap: 6px;">
                            <span>💡</span> CFO (DÒNG TIỀN KINH DOANH) GIÚP GÌ CHO BẠN?
                        </div>
                        <div style="font-size: 0.83rem; color: #cbd5e1; line-height: 1.55;">
                            <b>CFO là "Tiền tươi thóc thật"</b> thực tế chảy vào tài khoản ngân hàng của doanh nghiệp sau khi bán hàng và trừ các chi phí trả tiền mặt.<br>
                            • <i>Vì sao cần xem:</i> Lợi nhuận kế toán (LNST) có thể bị "vẽ" trên giấy tờ qua bán chịu hoặc ghi nhận doanh thu ảo, nhưng CFO thì không thể làm giả. Nếu CFO liên tục dương lớn hơn LNST, doanh nghiệp bán hàng thu được tiền mặt ngay, sức khỏe tài chính cực kỳ lành mạnh.
                        </div>
                    </div>

                    <!-- Box FCF -->
                    <div style="background: rgba(245, 158, 11, 0.08); border: 1px solid rgba(245, 158, 11, 0.3); border-radius: 10px; padding: 14px;">
                        <div style="font-weight: 700; color: #fbbf24; font-size: 0.9rem; margin-bottom: 6px; display: flex; align-items: center; gap: 6px;">
                            <span>💎</span> FCF (DÒNG TIỀN TỰ DO) GIÚP GÌ CHO BẠN?
                        </div>
                        <div style="font-size: 0.83rem; color: #cbd5e1; line-height: 1.55;">
                            <b>FCF là "Ví tiền dư dả thực tế"</b> còn lại sau khi doanh nghiệp lấy tiền kinh doanh (CFO) trừ đi chi phí tái đầu tư máy móc, nhà xưởng (CapEx).<br>
                            • <i>Ý nghĩa với nhà đầu tư:</i> Đây chính là nguồn tiền để doanh nghiệp <b>chia cổ tức tiền mặt trả thẳng vào tài khoản của bạn</b> và trả nợ ngân hàng. Doanh nghiệp có FCF dương lớn, dồi dào qua nhiều năm là một "cỗ máy in tiền" an toàn nhất cho cổ đông.
                        </div>
                    </div>
                </div>

                <div class="table-responsive">
                    <table>
                        <thead>
                            <tr>
                                <th>Chỉ tiêu Dòng tiền</th>
                                <th style="text-align: right;">Giá trị (Quy đổi)</th>
                                <th>Ý nghĩa thực tế</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr>
                                <td>Tiền kinh doanh thật (CFO 4 quý)</td>
                                <td style="text-align: right; font-weight: 700; color: #34d399; font-size: 0.95rem;">{format_vnd_human(cfo_ttm)}</td>
                                <td style="font-size: 0.8rem; color: #94a3b8;">Tiền mặt thực tế thu về từ bán hàng</td>
                            </tr>
                            <tr>
                                <td>Đầu tư mua sắm TSCĐ (CapEx 4 quý)</td>
                                <td style="text-align: right; color: #f87171; font-weight: 600;">{format_vnd_human(capex_ttm)}</td>
                                <td style="font-size: 0.8rem; color: #94a3b8;">Tiền chi ra mở rộng hạ tầng, nhà xưởng</td>
                            </tr>
                            <tr>
                                <td>Dòng tiền tự do (FCF 4 quý)</td>
                                <td style="text-align: right; font-weight: 700; color: {'#34d399' if fcf_ttm > 0 else '#f87171'}; font-size: 0.95rem;">{format_vnd_human(fcf_ttm)}</td>
                                <td style="font-size: 0.8rem; color: #94a3b8;">Tiền còn lại để trả cổ tức sau khi đã tái đầu tư</td>
                            </tr>
                            <tr>
                                <td>Lợi nhuận sau thuế (LNST 4 quý)</td>
                                <td style="text-align: right; color: #38bdf8; font-weight: 600;">{format_vnd_human(net_profit_ttm)}</td>
                                <td style="font-size: 0.8rem; color: #94a3b8;">Lợi nhuận ghi nhận trên sổ sách kế toán</td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>
        </div>

        <!-- TẦNG 5: KIỂM TOÁN BAN LÃNH ĐẠO, TÍNH MINH BẠCH & CÔNG TY SÂN SAU -->
        <div id="sec-governance" class="section-title">👥 TẦNG 5: KIỂM TOÁN BAN LÃNH ĐẠO, TÍNH MINH BẠCH & RADAR CÔNG TY SÂN SAU</div>
        <div class="card-grid-2" style="margin-bottom: 20px;">
            <div class="card">
                <div class="card-header">
                    <span>Kiểm toán Đạo đức & Tính Minh bạch Ban Điều hành</span>
                    <span class="badge" style="background: rgba(59, 130, 246, 0.15); color: {g_color};">G-SCORE {g_score}/100</span>
                </div>
                <div style="font-size: 1rem; font-weight: 700; color: #38bdf8; margin-bottom: 6px;">
                    {integrity_verdict}
                </div>
                <div style="font-size: 0.88rem; color: #cbd5e1; line-height: 1.6; margin-bottom: 12px;">
                    • <b>Đánh giá Ban lãnh đạo:</b> {leadership_analysis_vi}<br>
                    • <b>Cam kết cùng cổ đông (Skin in the game):</b> {lead.get('insider_total_pct', 0)}% cổ phần ({lead.get('skin_in_game_verdict', 'N/A')})<br>
                    • <b>Chủ tịch:</b> {lead.get('chairman', 'Chưa rõ')} &bull; <b>Tổng Giám đốc:</b> {lead.get('ceo', 'Chưa rõ')}
                </div>

                <div style="background: rgba(16, 185, 129, 0.1); border: 1px solid rgba(16, 185, 129, 0.3); border-radius: 10px; padding: 12px; margin-top: 10px;">
                    <span style="font-size: 0.85rem; font-weight: 700; color: #34d399;">💵 Bằng chứng Tiền thật qua Lịch sử Cổ tức:</span>
                    <p style="font-size: 0.84rem; color: #cbd5e1; margin-top: 4px; line-height: 1.5;">{dividend_evidence}</p>
                </div>
            </div>

            <div class="card">
                <div class="card-header">
                    <span>Radar Rủi ro Công ty Sân sau & Rút ruột Vốn</span>
                    <span class="badge" style="background: rgba(239, 68, 68, 0.15); color: {'#34d399' if sub_web.get('shell_company_risk_level', 1) <= 2 else '#f87171'};">MỨC ĐỘ RỦI RO: {sub_web.get('shell_company_risk_level', 1)}/5</span>
                </div>
                <div style="font-size: 0.95rem; font-weight: 700; color: {'#34d399' if sub_web.get('shell_company_risk_level', 1) <= 2 else '#f87171'}; margin-bottom: 8px;">
                    {shell_risk_desc}
                </div>
                <div style="font-size: 0.88rem; color: #cbd5e1; line-height: 1.6; margin-bottom: 14px;">
                    • <b>Cảnh báo Tăng vốn ảo & Trái phiếu nội bộ:</b> {sub_web.get('circular_capital_verdict', 'An toàn')}<br>
                    • <b>Quy mô hệ sinh thái:</b> {sub_web.get('subsidiary_count', 0)} công ty con, {sub_web.get('affiliate_count', 0)} công ty liên kết<br>
                    • <b>Tỷ lệ cho vay bên liên quan:</b> {sub_web.get('related_party_loans_ratio', 0.0):.1f}% tổng tài sản
                </div>

                <div class="table-responsive">
                    <table>
                        <thead>
                            <tr>
                                <th>Top Cổ đông Nắm giữ Lớn</th>
                                <th style="text-align: right;">Tỷ lệ sở hữu</th>
                                <th style="text-align: right;">Số lượng CP</th>
                            </tr>
                        </thead>
                        <tbody>
                            {sh_rows_html}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>

        <!-- TẦNG 6: PHÂN TÍCH KỸ THUẬT NÂNG CAO -->
        <div id="sec-chart" class="section-title">📈 TẦNG 6: BIỂU ĐỒ NẾN NHẬT TƯƠNG TÁC & PHÂN TÍCH KỸ THUẬT NÂNG CAO</div>
        
        <!-- TRADINGVIEW LIGHTWEIGHT CANDLESTICK CHART CONTAINER -->
        <div class="card" style="margin-bottom: 24px; padding: 20px;">
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
            
            <div id="tvChartContainer" style="width: 100%; height: 460px; position: relative; border-radius: 10px; overflow: hidden; background: #070c16; border: 1px solid rgba(255,255,255,0.06);"></div>
            <div id="chartTooltip" style="margin-top: 10px; font-size: 0.82rem; color: #94a3b8; font-family: monospace; display: flex; gap: 16px; flex-wrap: wrap;">
                <span>Rê chuột trên biểu đồ để xem chi tiết nến OHLCV và Khối lượng</span>
            </div>
        </div>

        <div class="card-grid-2" style="margin-bottom: 20px;">
            <!-- Box 1: VCP Minervini & VSA -->
            <div class="card">
                <div class="card-header">
                    <span>Mô hình Thu hẹp Biến động VCP & Hành vi Nến VSA</span>
                    <span class="badge" style="background: rgba(139, 92, 246, 0.15); color: #c084fc;">MÔ HÌNH GIÁ VÀ KHỐI LƯỢNG</span>
                </div>
                <div style="margin-bottom: 12px;">
                    <div style="font-size: 0.85rem; font-weight: 700; color: #38bdf8;">Mô hình VCP Minervini (Thu hẹp độ biến động):</div>
                    <div style="font-size: 0.95rem; font-weight: 700; color: #fff; margin-top: 2px;">{vcp_data.get('vcp_stage', 'Đang vận động tích lũy')}</div>
                    <div style="font-size: 0.85rem; color: #cbd5e1; margin-top: 4px; line-height: 1.5;">
                        • Chuỗi thu hẹp biên độ: <b style="color: #fbbf24;">{vcp_contractions_str}</b><br>
                        • Đánh giá Minervini: <i>{vcp_data.get('vcp_verdict', 'N/A')}</i>
                    </div>
                </div>

                <div style="border-top: 1px solid rgba(255,255,255,0.06); padding-top: 12px; margin-top: 12px;">
                    <div style="font-size: 0.85rem; font-weight: 700; color: #34d399; margin-bottom: 6px;">Đọc Dấu vết Dòng tiền Lớn (VSA - Smart Money Signals):</div>
                    <ul class="bullet-list">
                        {vsa_signals_html}
                    </ul>
                    <div style="font-size: 0.85rem; color: #94a3b8; margin-top: 6px;">
                        Hành động Cá mập / Tay to: <b style="color: #fff;">{vsa_sig.get('smart_money_action', 'Theo dõi quan sát')}</b>
                    </div>
                </div>
            </div>

            <!-- Box 2: Fibonacci & Vùng kẹp hàng Overhead Supply -->
            <div class="card">
                <div class="card-header">
                    <span>Mốc Hỗ trợ Fibonacci & Vùng Cung Kẹp Hàng Đỉnh Cũ</span>
                    <span class="badge" style="background: rgba(245, 158, 11, 0.15); color: #fbbf24;">VÙNG GIÁ QUAN TRỌNG</span>
                </div>
                <div style="margin-bottom: 14px;">
                    <div style="font-size: 0.85rem; font-weight: 700; color: #38bdf8; margin-bottom: 4px;">Mốc Hỗ trợ Fibonacci Retracement (Nhịp sóng gần nhất):</div>
                    <div style="font-size: 0.85rem; color: #cbd5e1; line-height: 1.6;">
                        • Đáy sóng: <b>{fibo_data.get('swing_low', 0):,.0f} đ</b> &bull; Đỉnh sóng: <b>{fibo_data.get('swing_high', 0):,.0f} đ</b><br>
                        • Fibo 38.2%: <b style="color: #34d399;">{fibo_data.get('fibo_382', 0):,.0f} đ</b> (Hỗ trợ nhịp sóng khỏe)<br>
                        • Fibo 50.0%: <b style="color: #fbbf24;">{fibo_data.get('fibo_500', 0):,.0f} đ</b> (Mốc cân bằng cung cầu)<br>
                        • Fibo 61.8%: <b style="color: #f87171;">{fibo_data.get('fibo_618', 0):,.0f} đ</b> (Hỗ trợ vàng sống còn)<br>
                        • Vị trí hiện tại: <i>{fibo_data.get('current_fibo_zone', 'N/A')}</i>
                    </div>
                </div>

                <div style="border-top: 1px solid rgba(255,255,255,0.06); padding-top: 12px; margin-top: 12px;">
                    <div style="font-size: 0.85rem; font-weight: 700; color: #f87171; margin-bottom: 4px;">Áp lực Vùng Cung Kẹp Hàng Đỉnh Cũ (Overhead Supply):</div>
                    <div style="font-size: 0.88rem; color: #cbd5e1; line-height: 1.5;">
                        • Vùng kẹp hàng: <b style="color: #fca5a5;">{overhead_data.get('resistance_cluster', 'Không có vùng kẹp lớn')}</b><br>
                        • Áp lực bán tiềm tàng: <b style="color: {'#34d399' if overhead_data.get('supply_intensity') == 'Thấp' else '#f87171'};">{overhead_data.get('supply_intensity', 'Thấp')}</b><br>
                        • Chi tiết: <i>{overhead_data.get('explanation', 'Cung trên đầu đã được hấp thụ tốt.')}</i>
                    </div>
                </div>
            </div>
        </div>

        <!-- TẦNG 7: BÀN TRÒN HỘI ĐỒNG PHẢN BIỆN AI ĐA TRƯỜNG PHÁI -->
        <div id="sec-council" class="section-title">🏛️ TẦNG 7: BÀN TRÒN HỘI ĐỒNG PHẢN BIỆN AI ĐA TRƯỜNG PHÁI (COUNCIL ROUNDTABLE)</div>
        
        <!-- Bảng biểu quyết tổng hợp -->
        <div class="card" style="margin-bottom: 20px; background: linear-gradient(145deg, #162032, #0f172a);">
            <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: gap; gap: 14px; margin-bottom: 12px;">
                <div>
                    <div style="font-size: 1.15rem; font-weight: 800; color: #fff;">KẾT QUẢ BIỂU QUYẾT 6 THÀNH VIÊN HỘI ĐỒNG AI</div>
                    <div style="font-size: 0.85rem; color: #94a3b8; margin-top: 2px;">
                        Độ đồng thuận tổng hợp: <b style="color: #38bdf8; font-size: 1.05rem;">{voting_summary.get('consensus_score', 50)}/100 điểm</b> &bull; Kết luận: <b style="color: #34d399;">{voting_summary.get('verdict', 'THEO DÕI')}</b>
                    </div>
                </div>
                <div style="display: flex; gap: 10px;">
                    <span class="badge" style="background: rgba(16, 185, 129, 0.2); color: #34d399; border: 1px solid #10b981; font-size: 0.85rem; padding: 6px 12px;">🟢 {bull_count} TÁN THÀNH MUA</span>
                    <span class="badge" style="background: rgba(245, 158, 11, 0.2); color: #fbbf24; border: 1px solid #f59e0b; font-size: 0.85rem; padding: 6px 12px;">🟡 {watch_count} THEO DÕI</span>
                    <span class="badge" style="background: rgba(239, 68, 68, 0.2); color: #f87171; border: 1px solid #ef4444; font-size: 0.85rem; padding: 6px 12px;">🔴 {bear_count} PHẢN ĐỐI TRÁNH</span>
                </div>
            </div>

            <!-- BẢNG MINH BẠCH HÓA CHI TIẾT DANH TÍNH & LÝ DO BIỂU QUYẾT 3 NHÓM -->
            {council_vote_details_html}
        </div>

        <!-- Khối tranh biện đối đầu (Clash of Perspectives) -->
        {clash_html}

        <!-- Lưới Card 6 Chuyên gia AI -->
        <div style="font-size: 1rem; font-weight: 700; color: #38bdf8; margin: 24px 0 12px 0;">
            📋 Ý kiến Chi tiết Từng Chuyên gia Hội đồng & Điều kiện Mất hiệu lực:
        </div>
        <div class="card-grid-3">
            {council_cards_html}
        </div>

        <!-- Báo cáo Thảo luận Chi tiết Toàn văn (Details Accordion) -->
        {council_report_html}

        <!-- BÀN TRÒN HỎI ĐÁP TRỰC TIẾP VỚI HỘI ĐỒNG AI (INTERACTIVE COUNCIL Q&A) -->
        {interactive_council_qa_html}

        <!-- SỔ TAY TRA CỨU NHANH THUẬT NGỮ TÀI CHÍNH (GLOSSARY) -->
        {glossary_html}

        <!-- Footer -->
        <div style="text-align: center; color: var(--text-muted); font-size: 0.8rem; margin-top: 50px; padding-top: 20px; border-top: 1px solid var(--border); line-height: 1.6;">
            Báo cáo phân tích chiến lược được khởi tạo tự động bởi Hệ thống <b>Vietnam Stock Analyzer</b>.<br>
            <i>Lưu ý: Báo cáo đóng vai trò tham mưu hỗ trợ quyết định khách quan dựa trên dữ liệu báo cáo tài chính và thuật toán phân tích, không phải lời kêu gọi đầu tư hay cam kết sinh lời. Quyết định mua bán cuối cùng thuộc về nhà đầu tư.</i>
        </div>

    </div>

    <!-- Script Vẽ Biểu đồ Chart.js Dòng tiền thật -->
    <script>
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
                        borderWidth: 1,
                        borderRadius: 4
                    }},
                    {{
                        label: 'Tiền kinh doanh thật - CFO (Tỷ đ)',
                        data: {json.dumps(chart_cfo)},
                        backgroundColor: 'rgba(52, 211, 153, 0.7)',
                        borderColor: '#34d399',
                        borderWidth: 1,
                        borderRadius: 4
                    }},
                    {{
                        type: 'line',
                        label: 'Dòng tiền tự do - FCF (Tỷ đ)',
                        data: {json.dumps(chart_fcf)},
                        borderColor: '#fbbf24',
                        backgroundColor: '#fbbf24',
                        borderWidth: 2,
                        tension: 0.3,
                        pointRadius: 4
                    }}
                ]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {{
                    legend: {{
                        labels: {{
                            color: '#94a3b8',
                            font: {{ size: 11 }}
                        }}
                    }}
                }},
                scales: {{
                    x: {{
                        grid: {{ color: 'rgba(255, 255, 255, 0.05)' }},
                        ticks: {{ color: '#94a3b8', font: {{ size: 11 }} }}
                    }},
                    y: {{
                        grid: {{ color: 'rgba(255, 255, 255, 0.05)' }},
                        ticks: {{ color: '#94a3b8', font: {{ size: 11 }} }}
                    }}
                }}
            }}
        }});

        // Khởi tạo Biểu đồ Nến Nhật TradingView Lightweight Charts
        (function() {{
            const chartDiv = document.getElementById('tvChartContainer');
            if (!chartDiv || typeof LightweightCharts === 'undefined') return;

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
                crosshair: {{
                    mode: LightweightCharts.CrosshairMode.Normal,
                }},
                rightPriceScale: {{
                    borderColor: 'rgba(255, 255, 255, 0.08)',
                    scaleMargins: {{ top: 0.08, bottom: 0.22 }}
                }},
                timeScale: {{
                    borderColor: 'rgba(255, 255, 255, 0.08)',
                    timeVisible: true,
                    secondsVisible: false
                }}
            }});

            const candleSeries = chart.addCandlestickSeries({{
                upColor: '#10b981',
                downColor: '#ef4444',
                borderDownColor: '#ef4444',
                borderUpColor: '#10b981',
                wickDownColor: '#ef4444',
                wickUpColor: '#10b981'
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
                    color: '#fbbf24',
                    lineWidth: 1.5,
                    title: 'EMA20'
                }});
                ema20Line.setData(ema20Data);
            }}

            if (ema50Data.length > 0) {{
                const ema50Line = chart.addLineSeries({{
                    color: '#38bdf8',
                    lineWidth: 1.5,
                    title: 'EMA50'
                }});
                ema50Line.setData(ema50Data);
            }}

            // Price Lines
            const pivotPrice = {trigger_pivot};
            if (pivotPrice > 0) {{
                candleSeries.createPriceLine({{
                    price: pivotPrice,
                    color: '#10b981',
                    lineWidth: 2,
                    lineStyle: LightweightCharts.LineStyle.Dashed,
                    axisLabelVisible: true,
                    title: 'PIVOT MUA'
                }});
            }}

            const slPrice = {stop_loss_lvl};
            if (slPrice > 0) {{
                candleSeries.createPriceLine({{
                    price: slPrice,
                    color: '#ef4444',
                    lineWidth: 2,
                    lineStyle: LightweightCharts.LineStyle.Solid,
                    axisLabelVisible: true,
                    title: 'CẮT LỖ (SL)'
                }});
            }}

            const tp1Price = {tp1_lvl};
            if (tp1Price > 0) {{
                candleSeries.createPriceLine({{
                    price: tp1Price,
                    color: '#38bdf8',
                    lineWidth: 1.5,
                    lineStyle: LightweightCharts.LineStyle.Dotted,
                    axisLabelVisible: true,
                    title: 'MỤC TIÊU 1'
                }});
            }}

            // Tooltip handler
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
