"""
Module Động Cơ Dự Báo Thời Điểm Tăng / Sập (Timing Prediction Engine)
Kết hợp hai lăng kính thực chiến cốt lõi:
1. Dòng tiền Thông minh & Hành vi Nến Wyckoff VSA (Cạn cung, Spring, Nổ Vol, Upthrust, Phân kỳ âm).
2. Chất xúc tác Tin tức Vĩ mô & Hàng hóa (Catalyst Alignment & Macro Transmission Lag).

Trả về 2 Kịch bản phân nhánh độc lập:
- Kịch bản Bứt Phá ("Khi nào sẽ tăng?"): Mốc giá xác nhận, Xác suất %, Khung thời gian T+.
- Kịch bản Rủi Ro Sập ("Khi nào sẽ sập?"): Mức giá vi phạm kích hoạt gãy, Dấu hiệu phân phối, Xác suất %.
"""

from datetime import datetime
from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np


def get_upcoming_catalysts(symbol: str, current_dt: Optional[datetime] = None) -> List[Dict[str, Any]]:
    """
    Xác định Lịch Xúc Tác Sự Kiện Trọng Yếu (Catalyst Calendar) thực tế của TTCK Việt Nam:
    1. Kỳ Đáo Hạn Phái Sinh VN30 (Thứ 5 tuần thứ 3 hàng tháng)
    2. Hạn chót Công Bố Báo Cáo Tài Chính Quý (Q1, Q2, Q3, Q4)
    3. Kỳ Cơ Cấu Danh Mục Quỹ ETF Định Kỳ (Tháng 3, 6, 9, 12)
    4. Mùa Đại Hội Cổ Đông & Chốt Quyền Cổ Tức Tiền Mặt
    """
    now = current_dt or datetime.now()
    catalysts = []

    # 1. Đáo hạn Phái sinh VN30 (Thứ 5 tuần thứ 3 của tháng)
    first_day = datetime(now.year, now.month, 1)
    first_thurs = 1 + (3 - first_day.weekday()) % 7
    third_thurs = first_thurs + 14
    deriv_date = datetime(now.year, now.month, third_thurs)
    if deriv_date < now:
        n_month = now.month + 1 if now.month < 12 else 1
        n_year = now.year if now.month < 12 else now.year + 1
        f_day = datetime(n_year, n_month, 1)
        deriv_date = datetime(n_year, n_month, 1 + (3 - f_day.weekday()) % 7 + 14)
    days_to_deriv = (deriv_date.date() - now.date()).days
    catalysts.append({
        "event_name": "Đáo Hạn Phái Sinh Hợp Đồng Tương Lai VN30F",
        "date_str": deriv_date.strftime("%d/%m/%Y"),
        "days_left": days_to_deriv,
        "impact_level": "CAO (Gây rung lắc chỉ số & cổ phiếu vốn hóa lớn)",
        "trading_hint": f"Còn {days_to_deriv} ngày: Các đội tạo lập thường kéo/đạp trụ để chốt chỉ số phái sinh; hạn chế mua đuổi giá trần trước phiên đáo hạn 1-2 ngày."
    })

    # 2. Hạn chót công bố BCTC Quý
    if now.month in [1, 2, 3]:
        bctc_deadline = datetime(now.year, 4, 30)
        q_name = f"BCTC Quý 1/{now.year}"
    elif now.month in [4, 5, 6]:
        bctc_deadline = datetime(now.year, 7, 30)
        q_name = f"BCTC Quý 2 & Soát xét Bán niên/{now.year}"
    elif now.month in [7, 8, 9]:
        bctc_deadline = datetime(now.year, 10, 30)
        q_name = f"BCTC Quý 3/{now.year}"
    else:
        bctc_deadline = datetime(now.year + 1, 1, 30)
        q_name = f"BCTC Quý 4/{now.year}"
    days_to_bctc = (bctc_deadline.date() - now.date()).days
    if days_to_bctc >= 0:
        catalysts.append({
            "event_name": f"Hạn Chót Công Bố {q_name}",
            "date_str": bctc_deadline.strftime("%d/%m/%Y"),
            "days_left": days_to_bctc,
            "impact_level": "RẤT CAO (Phân hóa dòng tiền mạnh mẽ theo kết quả kinh doanh)",
            "trading_hint": f"Còn {days_to_bctc} ngày: Dòng tiền thông minh thường đón đầu giải ngân trước 1-2 tuần. Cổ phiếu có CFO và LNST tăng trưởng vượt trội sẽ hút dòng tiền gom mạnh."
        })

    # 3. Kỳ cơ cấu quỹ ETF (Tháng 3, 6, 9, 12 - Thứ 6 tuần thứ 3)
    etf_months = [3, 6, 9, 12]
    target_m = next((m for m in etf_months if m >= now.month), 3)
    target_y = now.year if target_m >= now.month else now.year + 1
    etf_first_day = datetime(target_y, target_m, 1)
    etf_third_friday = datetime(target_y, target_m, 1 + (4 - etf_first_day.weekday()) % 7 + 14)
    days_to_etf = (etf_third_friday.date() - now.date()).days
    if days_to_etf >= 0:
        catalysts.append({
            "event_name": f"Kỳ Cơ Cấu Danh Mục Các Quỹ ETF (VNM ETF, FTSE, Diamond - Q{ (target_m//3) })",
            "date_str": etf_third_friday.strftime("%d/%m/%Y"),
            "days_left": days_to_etf,
            "impact_level": "TRUNG BÌNH - CAO (Thanh khoản khớp lệnh đột biến phiên ATC)",
            "trading_hint": f"Còn {days_to_etf} ngày: Các quỹ ngoại tái cân bằng tỷ trọng danh mục; cơ hội săn cổ phiếu được mua ròng tăng tỷ trọng."
        })

    return catalysts


def analyze_timing_prediction(
    symbol: str,
    quote: Dict[str, Any],
    ta_result: Dict[str, Any],
    fa_result: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Dự báo chính xác thời điểm Tăng / Sập cho 1 mã cổ phiếu kết hợp:
    1. Dòng tiền Khớp lệnh Chủ động (Active Buy/Sell Pressure)
    2. Hành vi Nến Wyckoff VSA & Thu hẹp độ biến động VCP
    3. Chuỗi gom ròng Khối ngoại & Tự doanh
    4. Lịch Xúc tác Sự kiện Trọng yếu (Catalyst Calendar)
    """
    sym = symbol.upper().strip()
    price = float(quote.get("price") or 0.0)
    if 0 < price < 1000:
        price *= 1000

    change_pct = float(quote.get("change_pct") or 0.0)
    volume = float(quote.get("volume") or 0.0)
    
    # 1. Trích xuất thông số kỹ thuật (TA)
    rsi = float(ta_result.get("rsi") or 50.0)
    vol_ratio = float(ta_result.get("vol_ratio") or 1.0)
    trend_state = ta_result.get("trend_state", "Sideway")
    support = float(ta_result.get("support") or (price * 0.95))
    resistance = float(ta_result.get("resistance") or (price * 1.05))
    if 0 < support < 1000:
        support *= 1000
    if 0 < resistance < 1000:
        resistance *= 1000
    vsa_phase = ta_result.get("vsa_phase", "Tích lũy")
    vsa_signal = ta_result.get("vsa_signal", "Thị trường bình thường")

    # 2. Bóc tách Dòng tiền Khớp lệnh Chủ động & Khối Ngoại (Smart Money Pulse)
    # Tỷ lệ Mua chủ động ước tính từ diễn biến giá và khối ngoại
    foreign_net_vol = float(quote.get("foreign_net_vol") or 0.0)
    foreign_ratio = abs(foreign_net_vol) / max(1.0, volume) if volume > 0 else 0.0

    if change_pct > 2.0:
        active_buy_pct = min(85.0, 58.0 + change_pct * 3.5)
    elif change_pct > 0:
        active_buy_pct = min(68.0, 50.0 + change_pct * 4.0)
    elif change_pct < -2.0:
        active_buy_pct = max(20.0, 42.0 + change_pct * 3.5)
    else:
        active_buy_pct = max(35.0, 50.0 + change_pct * 4.0)
    
    # Điều chỉnh thêm bởi lực mua ròng khối ngoại
    if foreign_net_vol > 200_000:
        active_buy_pct = min(92.0, active_buy_pct + 8.0)
    elif foreign_net_vol < -500_000:
        active_buy_pct = max(18.0, active_buy_pct - 10.0)

    active_sell_pct = 100.0 - active_buy_pct

    if active_buy_pct >= 60.0:
        order_pressure_verdict = "PHE MUA ÁP ĐẢO (Lực cầu chủ động ăn thẳng giá Dư Bán)"
        order_pressure_color = "#10b981"
    elif active_buy_pct <= 42.0:
        order_pressure_verdict = "PHE BÁN CHIẾM ƯU THẾ (Áp lực chốt lời bán tháo vào giá Dư Mua)"
        order_pressure_color = "#ef4444"
    else:
        order_pressure_verdict = "CÂN BẰNG CUNG CẦU (Bên mua và bên bán đang giằng co tích lũy)"
        order_pressure_color = "#38bdf8"

    # Trạng thái Gom / Xả của Khối ngoại
    if foreign_net_vol > 300_000:
        foreign_verdict = f"Khối ngoại gom ròng mạnh (+{foreign_net_vol:,.0f} CP) chiếm {foreign_ratio*100:.1f}% thanh khoản"
        foreign_badge = "KHỐI NGOẠI GOM RÒNG 🟢"
    elif foreign_net_vol < -500_000:
        foreign_verdict = f"Khối ngoại xả ròng ({foreign_net_vol:,.0f} CP) cần theo dõi lực hấp thụ của dòng tiền nội"
        foreign_badge = "KHỐI NGOẠI BÁN RÒNG 🔴"
    else:
        foreign_verdict = "Giao dịch khối ngoại ở mức cân bằng, dòng tiền trong nước chi phối chính"
        foreign_badge = "TRUNG LẬP 🟡"

    # 3. Lịch Xúc Tác Sự Kiện Trọng Yếu
    catalyst_events = get_upcoming_catalysts(sym)

    # 4. Trích xuất thông số Vĩ mô & Hàng hóa (FA / Macro)
    macro_data = fa_result.get("macro", {})
    comm_sens = macro_data.get("commodity_sensitivity", {})
    sector_name = macro_data.get("sector_name", "Chung")
    tailwind_score = float(macro_data.get("tailwind_score", 70))
    comm_trend = comm_sens.get("trend_direction", "ỔN ĐỊNH")
    comm_name = comm_sens.get("commodity_name", "Vĩ mô chung")

    # =====================================================================
    # 5. MÔ HÌNH HÓA KỊCH BẢN TĂNG ("KHI NÀO SẼ TĂNG?")
    # =====================================================================
    surge_points = 0
    surge_catalysts = []

    # Tiêu chí 1: Hành vi VSA cạn cung hoặc Spring rũ bỏ
    if "No Supply" in vsa_signal or vol_ratio < 0.75:
        surge_points += 25
        surge_catalysts.append(f"VSA Cạn Cung (No Supply Bar): Khối lượng chỉ bằng {vol_ratio:.2f}x MA20 vol cho thấy lượng cung trôi nổi đã được Smart Money hấp thụ cạn kiệt.")
    elif "Stopping" in vsa_signal or "Spring" in vsa_signal or "Shakeout" in vsa_signal:
        surge_points += 25
        surge_catalysts.append("VSA Rũ Bỏ Thành Công: Xuất hiện nến rút chân gom hàng của tay to quanh vùng hỗ trợ.")
    elif vol_ratio >= 1.3 and change_pct > 1.5:
        surge_points += 30
        surge_catalysts.append(f"Volume Bùng Nổ ({vol_ratio:.2f}x MA20): Dòng tiền lớn nhập cuộc đẩy giá bứt phá.")
    else:
        surge_points += 10
        surge_catalysts.append("Nền giá đang tích lũy chặt chẽ quanh đường EMA hỗ trợ.")

    # Tiêu chí 2: Lệnh mua chủ động áp đảo
    if active_buy_pct >= 60:
        surge_points += 15
        surge_catalysts.append(f"Lực Mua Chủ Động Đột Biến ({active_buy_pct:.1f}%): Phe mua chủ động quét lệnh ăn lên quyết liệt.")

    # Tiêu chí 3: Vị thế xu hướng (Trend Template)
    if "Tăng mạnh" in trend_state or "Uptrend" in trend_state:
        surge_points += 20
        surge_catalysts.append("Trend Template Chuẩn: Giá nằm trên EMA20 và EMA50 dốc lên xác nhận sóng lớn.")
    elif "Sideway" in trend_state:
        surge_points += 12
        surge_catalysts.append("Đang nén biên độ (Mẫu hình VCP) chuẩn bị cho nhịp mở band tăng giá.")

    # Tiêu chí 4: Động lượng RSI lành mạnh
    if 50 <= rsi <= 65:
        surge_points += 15
        surge_catalysts.append(f"RSI({rsi:.1f}) ở Vùng Vàng: Xung lực tăng giá mạnh mẽ nhưng chưa bị quá mua.")
    elif 40 <= rsi < 50:
        surge_points += 10
        surge_catalysts.append(f"RSI({rsi:.1f}) chạm vùng hỗ trợ bật lên, dư địa tăng giá còn rất rộng.")

    # Tiêu chí 5: Hưởng lợi từ Hàng hóa & Vĩ mô thế giới
    if "TĂNG" in comm_trend:
        surge_points += 15
        surge_catalysts.append(f"Thiên Thời Hàng Hóa: {comm_name} đang trong xu thế {comm_trend}, tạo cú hích độ trễ 1-3 phiên cho nhóm {sector_name}.")
    elif tailwind_score >= 80:
        surge_points += 10
        surge_catalysts.append(f"Gió Xuôi Chiều Vĩ Mô: Ngành {sector_name} đạt {tailwind_score:.0f} điểm vĩ mô tích cực.")

    # Điểm xác nhận bứt phá (Trigger Pivot Price)
    trigger_pivot = round(max(resistance, price * 1.02) / 100) * 100
    if trigger_pivot <= 0 and price > 0:
        trigger_pivot = round(price * 1.03 / 50) * 50
    surge_prob = min(88, max(35, surge_points))

    # Khung thời gian tăng dự kiến
    if vol_ratio >= 1.3 or "No Supply" in vsa_signal or active_buy_pct >= 65:
        surge_timeframe = "1 - 3 phiên tới (Cận kề điểm nổ Pocket Pivot)"
    elif 50 <= rsi <= 65 and "TĂNG" in comm_trend:
        surge_timeframe = "3 - 5 phiên tới (Theo nhịp nén tích lũy T+)"
    else:
        surge_timeframe = "1 - 2 tuần tới (Chờ dòng tiền xác nhận vượt cản)"

    # =====================================================================
    # 6. MÔ HÌNH HÓA KỊCH BẢN SẬP / ĐẢO CHIỀU ("KHI NÀO SẼ SẬP?")
    # =====================================================================
    crash_points = 0
    crash_warnings = []

    # Cảnh báo 1: Quá mua & Phân kỳ âm
    if rsi >= 75:
        crash_points += 30
        crash_warnings.append(f"Báo Động Quá Mua RSI({rsi:.1f}): Cổ phiếu đã tăng nóng vào vùng rủi ro điều chỉnh mạnh.")
    elif rsi >= 68 and change_pct < 0:
        crash_points += 20
        crash_warnings.append("Áp lực chốt lời ngắn hạn xuất hiện tại vùng kháng cự.")

    # Cảnh báo 2: Lệnh bán chủ động xả mạnh
    if active_sell_pct >= 62.0:
        crash_points += 25
        crash_warnings.append(f"Lực Bán Chủ Động Đột Biến ({active_sell_pct:.1f}%): Phe bán đang xả thẳng lệnh MP vào giá dư mua.")

    # Cảnh báo 3: Nến Upthrust hoặc Nỗ lực không tương xứng
    if "Upthrust" in vsa_signal:
        crash_points += 35
        crash_warnings.append("VSA Upthrust Bar: Râu nến trên dài kèm khối lượng lớn báo hiệu tay to đang âm thầm xả hàng.")
    elif vol_ratio >= 1.8 and abs(change_pct) < 0.6:
        crash_points += 30
        crash_warnings.append(f"Hiện Tượng Phân Phối Giấu Vol: Khối lượng giao dịch đột biến ({vol_ratio:.2f}x MA20) nhưng giá không tăng được.")

    # Cảnh báo 4: Bẫy truyền thông 'Tin ra là bán'
    if "Đỉnh" in macro_data.get("cycle_phase", ""):
        crash_points += 20
        crash_warnings.append("Cảnh Báo Đỉnh Chu Kỳ: Lợi nhuận ngành đạt đỉnh cao nhất, nguy cơ 'Tin ra là bán'.")

    # Cảnh báo 5: Khối ngoại xả ròng
    if foreign_net_vol < -500_000:
        crash_points += 20
        crash_warnings.append(f"Khối Ngoại Xả Ròng Mạnh ({foreign_net_vol:,.0f} CP): Áp lực rút vốn của dòng tiền lớn ngoại khối.")

    # Mức giá vi phạm kích hoạt gãy (Failure Breakdown Level)
    failure_level = round(min(support, price * 0.965) / 100) * 100
    if failure_level <= 0 and price > 0:
        failure_level = round(price * 0.95 / 50) * 50
    crash_prob = min(85, max(15, crash_points))

    # Khung thời gian rủi ro sập
    if crash_points >= 40:
        crash_timeframe = "CẢNH BÁO CAO: Có thể điều chỉnh ngay trong 1 - 2 phiên tới!"
    elif crash_points >= 25:
        crash_timeframe = "Tiềm ẩn rủi ro rung lắc mạnh trong 3 - 5 phiên tới nếu không vượt cản"
    else:
        crash_timeframe = "Rủi ro sập thấp trong ngắn hạn, hỗ trợ cứng đang bảo vệ giá tốt"

    # =====================================================================
    # 7. TỔNG HỢP PHÁN QUYẾT THỜI ĐIỂM (TIMING VERDICT)
    # =====================================================================
    if surge_prob >= 70 and crash_prob < 35:
        timing_verdict = "ĐIỂM NỔ VOL TĂNG GIÁ CẬN KỀ (SẴN SÀNG BÙNG NỔ)"
        timing_badge = "BULLISH_SURGE"
        timing_color = "#10b981"
    elif crash_prob >= 50:
        timing_verdict = "CẢNH BÁO RỦI RO ĐẢO CHIỀU (TRÁNH MUA ĐUỔI - CHUẨN BỊ CHỐT LỜI)"
        timing_badge = "BEARISH_DUMP"
        timing_color = "#ef4444"
    elif surge_prob >= 55:
        timing_verdict = "TÍCH LŨY TÍCH CỰC - CHỜ ĐỢI TÍN HIỆU DÒNG TIỀN VƯỢT PIVOT"
        timing_badge = "ACCUMULATING"
        timing_color = "#38bdf8"
    else:
        timing_verdict = "GIAO DỊCH THẬN TRỌNG - QUAN SÁT VÙNG HỖ TRỢ CHƯA RÕ XU HƯỚNG"
        timing_badge = "NEUTRAL_WATCH"
        timing_color = "#f59e0b"

    return {
        "symbol": sym,
        "timing_verdict": timing_verdict,
        "timing_badge": timing_badge,
        "timing_color": timing_color,
        "overall_timing_score": int(surge_prob),
        
        # Nhịp đập Dòng tiền Lớn & Khớp lệnh
        "smart_money_pulse": {
            "active_buy_pct": round(active_buy_pct, 1),
            "active_sell_pct": round(active_sell_pct, 1),
            "order_pressure_verdict": order_pressure_verdict,
            "order_pressure_color": order_pressure_color,
            "foreign_net_vol": foreign_net_vol,
            "foreign_verdict": foreign_verdict,
            "foreign_badge": foreign_badge
        },

        # Lịch Xúc Tác Sự Kiện Trọng Yếu
        "catalyst_calendar": catalyst_events,

        # Chi tiết Kịch bản Tăng
        "surge_scenario": {
            "probability_pct": surge_prob,
            "timing_window": surge_timeframe,
            "trigger_pivot_price": trigger_pivot,
            "catalysts": surge_catalysts,
            "action_advice": f"Giải ngân 30-40% vị thế thăm dò quanh vùng giá hiện tại ({price:,.0f} đ). Khi giá vượt dứt khoát mốc {trigger_pivot:,.0f} đ kèm Vol lớn > 1.3x MA20, gia tăng tỷ trọng lên mức tối đa."
        },
        
        # Chi tiết Kịch bản Sập / Đảo chiều
        "crash_scenario": {
            "risk_probability_pct": crash_prob,
            "timing_window": crash_timeframe,
            "failure_trigger_level": failure_level,
            "warnings": crash_warnings if crash_warnings else ["Chưa phát hiện tín hiệu phân phối lớn hay phân kỳ âm nguy hiểm."],
            "invalidation_rule": f"Nếu giá xuyên thủng mốc hỗ trợ {failure_level:,.0f} đ kèm khối lượng gia tăng, toàn bộ kịch bản tăng giá sẽ BỊ MẤT HIỆU LỰC HOÀN TOÀN. Buộc phải cắt lỗ/bán hạ tỷ trọng ngay lập tức để bảo toàn vốn."
        }
    }
