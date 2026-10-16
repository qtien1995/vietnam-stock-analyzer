"""
Module Động Cơ Phân Tích Thời Điểm Kỹ Thuật (Technical Timing & Setup Engine)
Kết hợp hai lăng kính:
1. Dòng tiền & Hành vi Nến Wyckoff VSA (Cạn cung, Spring, Nổ Vol, Upthrust).
2. Lịch Xúc tác Sự kiện Trọng yếu & Độ nhạy Vĩ mô.

Nguyên tắc trung thực:
- Điểm số kỹ thuật (0 - 100) phản ánh mức độ hội tụ của các tín hiệu nến và thanh khoản.
- Không trình bày điểm heuristic như xác suất thống kê được kiểm định.
- Không đưa ra khung thời gian cam kết T+1..T+3 cố định nếu không có căn cứ thực nghiệm.
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
            "trading_hint": f"Còn {days_to_bctc} ngày: Dòng tiền thông minh thường đón đầu giải ngân trước 1-2 tuần. Doanh nghiệp có CFO và LNST tăng trưởng vượt trội sẽ hút dòng tiền gom."
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
            "event_name": f"Kỳ Cơ Cấu Danh Mục Các Quỹ ETF (Q{target_m//3})",
            "date_str": etf_third_friday.strftime("%d/%m/%Y"),
            "days_left": days_to_etf,
            "impact_level": "TRUNG BÌNH - CAO (Thanh khoản khớp lệnh đột biến phiên ATC)",
            "trading_hint": f"Còn {days_to_etf} ngày: Các quỹ ngoại tái cân bằng danh mục; cơ hội theo dõi cổ phiếu được mua ròng tăng tỷ trọng."
        })

    return catalysts


def analyze_timing_prediction(
    symbol: str,
    quote: Dict[str, Any],
    ta_result: Dict[str, Any],
    fa_result: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Phân tích hội tụ thời điểm kỹ thuật & Dòng tiền cho 1 mã cổ phiếu:
    1. Ước tính áp lực cung cầu trong phiên (Price-Volume Proxy).
    2. Hành vi Nến Wyckoff VSA & Thu hẹp độ biến động VCP.
    3. Giao dịch khối ngoại ròng.
    4. Lịch xúc tác sự kiện.
    """
    sym = symbol.upper().strip()
    price = float(quote.get("price") or 0.0)
    if 0 < price < 1000:
        price *= 1000

    change_pct = float(quote.get("change_pct") or 0.0)
    volume = float(quote.get("volume") or 0.0)
    
    # 1. Trích xuất thông số kỹ thuật (TA)
    indicators = ta_result.get("indicators", {})
    rsi = float(indicators.get("rsi14") or ta_result.get("rsi") or 50.0)
    vol_ratio = float(indicators.get("vol_ratio") or ta_result.get("vol_ratio") or 1.0)
    trend_state = ta_result.get("trend_state", "Sideway")
    support = float(indicators.get("sup_20d") or ta_result.get("support") or (price * 0.95))
    resistance = float(indicators.get("res_20d") or ta_result.get("resistance") or (price * 1.05))
    if 0 < support < 1000:
        support *= 1000
    if 0 < resistance < 1000:
        resistance *= 1000
    vsa_phase = ta_result.get("vsa", {}).get("phase", "Tích lũy")
    vsa_signal = ta_result.get("advanced_ta", {}).get("vsa_signal", "Thanh khoản ổn định")

    # 2. Ước tính áp lực Cung Cầu trong phiên (Price-Volume Proxy)
    foreign_net_vol = float(quote.get("foreign_net_vol") or 0.0)
    foreign_ratio = abs(foreign_net_vol) / max(1.0, volume) if volume > 0 else 0.0

    if change_pct > 2.0:
        active_buy_pct = min(82.0, 56.0 + change_pct * 3.0)
    elif change_pct > 0:
        active_buy_pct = min(65.0, 50.0 + change_pct * 3.5)
    elif change_pct < -2.0:
        active_buy_pct = max(22.0, 44.0 + change_pct * 3.0)
    else:
        active_buy_pct = max(35.0, 50.0 + change_pct * 3.5)
    
    if foreign_net_vol > 200_000:
        active_buy_pct = min(88.0, active_buy_pct + 6.0)
    elif foreign_net_vol < -500_000:
        active_buy_pct = max(20.0, active_buy_pct - 8.0)

    active_sell_pct = 100.0 - active_buy_pct

    if active_buy_pct >= 60.0:
        order_pressure_verdict = "LỰC CẦU CHIẾM ƯU THẾ (Bên mua chủ động ăn giá dư bán)"
        order_pressure_color = "#10b981"
    elif active_buy_pct <= 42.0:
        order_pressure_verdict = "ÁP LỰC BÁN CHIẾM ƯU THẾ (Bên bán chủ động hạ giá)"
        order_pressure_color = "#ef4444"
    else:
        order_pressure_verdict = "CÂN BẰNG CUNG CẦU (Giằng co tích lũy)"
        order_pressure_color = "#38bdf8"

    # Trạng thái Gom / Bán ròng Khối ngoại
    if foreign_net_vol > 300_000:
        foreign_verdict = f"Khối ngoại mua ròng (+{foreign_net_vol:,.0f} CP) chiếm {foreign_ratio*100:.1f}% thanh khoản"
        foreign_badge = "KHỐI NGOẠI MUA RÒNG 🟢"
    elif foreign_net_vol < -500_000:
        foreign_verdict = f"Khối ngoại bán ròng ({foreign_net_vol:,.0f} CP), cần theo dõi lực hấp thụ của dòng tiền nội"
        foreign_badge = "KHỐI NGOẠI BÁN RÒNG 🔴"
    else:
        foreign_verdict = "Giao dịch khối ngoại cân bằng, dòng tiền trong nước chi phối"
        foreign_badge = "TRUNG LẬP 🟡"

    catalyst_events = get_upcoming_catalysts(sym)

    # 4. Trích xuất thông số Vĩ mô & Hàng hóa
    macro_data = fa_result.get("macro", {})
    comm_sens = macro_data.get("commodity_sensitivity", {})
    sector_name = macro_data.get("sector_name", "Chung")
    tailwind_score = float(macro_data.get("tailwind_score", 70))
    comm_trend = comm_sens.get("trend_direction", "ỔN ĐỊNH")
    comm_name = comm_sens.get("commodity_name", "Vĩ mô chung")

    # 5. Điểm số Điều kiện Kỹ thuật Tăng (Setup Quality Score: 0 - 100)
    surge_points = 0
    surge_catalysts = []

    if "No Supply" in vsa_signal or vol_ratio < 0.75:
        surge_points += 25
        surge_catalysts.append(f"VSA Cạn Cung: Khối lượng chỉ đạt {vol_ratio:.2f}x MA20 vol, áp lực bán cạn kiệt.")
    elif "Spring" in vsa_signal or "Shakeout" in vsa_signal:
        surge_points += 25
        surge_catalysts.append("VSA Rũ Bỏ: Xuất hiện nến rút chân quanh vùng hỗ trợ kỹ thuật.")
    elif vol_ratio >= 1.3 and change_pct > 1.5:
        surge_points += 30
        surge_catalysts.append(f"Volume Tăng Đột Biến ({vol_ratio:.2f}x MA20): Dòng tiền chủ động gia tăng.")
    else:
        surge_points += 10
        surge_catalysts.append("Nền giá đang tích lũy chặt chẽ quanh các đường hỗ trợ.")

    if active_buy_pct >= 60:
        surge_points += 15
        surge_catalysts.append(f"Lực Cầu Chủ Động Tích Cực ({active_buy_pct:.1f}%).")

    if "Tăng" in trend_state or "Uptrend" in trend_state:
        surge_points += 20
        surge_catalysts.append("Xu hướng tăng trung hạn: Giá nằm trên EMA20 và EMA50 dốc lên.")
    elif "Sideway" in trend_state or "tích lũy" in trend_state.lower():
        surge_points += 12
        surge_catalysts.append("Đang nén biên độ tích lũy, chuẩn bị cho nhịp bứt phá mới.")

    if 50 <= rsi <= 65:
        surge_points += 15
        surge_catalysts.append(f"RSI({rsi:.1f}) ở Vùng Lành Mạnh: Xung lực tăng giá duy trì tốt, chưa quá mua.")
    elif 40 <= rsi < 50:
        surge_points += 10
        surge_catalysts.append(f"RSI({rsi:.1f}) chạm vùng hỗ trợ bật lên.")

    if "TĂNG" in comm_trend:
        surge_points += 15
        surge_catalysts.append(f"Hưởng lợi chu kỳ hàng hóa: {comm_name} có xu thế {comm_trend}.")
    elif tailwind_score >= 80:
        surge_points += 10
        surge_catalysts.append(f"Gió xuôi vĩ mô tích cực cho ngành {sector_name} ({tailwind_score:.0f} điểm).")

    trigger_pivot = round(max(resistance, price * 1.02) / 100) * 100
    if trigger_pivot <= 0 and price > 0:
        trigger_pivot = round(price * 1.03 / 50) * 50
    setup_quality_score = min(88, max(30, surge_points))

    # Diễn giải trạng thái kỹ thuật (thay vì hứa hẹn T+1..T+3 cố định)
    if vol_ratio >= 1.3 and active_buy_pct >= 65:
        surge_status_desc = "Đang xuất hiện xung lực dòng tiền nổ Volume bứt phá"
    elif "No Supply" in vsa_signal or vol_ratio < 0.75:
        surge_status_desc = "Pha cạn cung kiệt quệ, chờ phiên kích hoạt dòng tiền mồi (Pocket Pivot)"
    else:
        surge_status_desc = "Đang vận động tích lũy trong nền giá, kiên nhẫn chờ điểm vượt cản"

    # 6. Rủi ro Đảo chiều / Gãy Hỗ trợ
    crash_points = 0
    crash_warnings = []

    if rsi >= 75:
        crash_points += 30
        crash_warnings.append(f"Quá mua RSI({rsi:.1f}): Cổ phiếu tăng nóng, rủi ro điều chỉnh kỹ thuật ngắn hạn.")
    elif rsi >= 68 and change_pct < 0:
        crash_points += 20
        crash_warnings.append("Áp lực chốt lời ngắn hạn xuất hiện tại vùng kháng cự.")

    if active_sell_pct >= 62.0:
        crash_points += 25
        crash_warnings.append(f"Lực bán chủ động tăng cao ({active_sell_pct:.1f}%).")

    if "Upthrust" in vsa_signal:
        crash_points += 35
        crash_warnings.append("VSA Upthrust: Râu nến trên dài kèm khối lượng lớn báo hiệu áp lực bán chốt lời mạnh.")
    elif vol_ratio >= 1.8 and abs(change_pct) < 0.6:
        crash_points += 30
        crash_warnings.append(f"Khối lượng đột biến ({vol_ratio:.2f}x MA20) nhưng giá không tăng (Chững lại tại kháng cự).")

    if foreign_net_vol < -500_000:
        crash_points += 20
        crash_warnings.append(f"Khối ngoại bán ròng mạnh ({foreign_net_vol:,.0f} CP).")

    failure_level = round(min(support, price * 0.965) / 100) * 100
    if failure_level <= 0 and price > 0:
        failure_level = round(price * 0.95 / 50) * 50
    risk_points = min(85, max(15, crash_points))

    if crash_points >= 40:
        crash_status_desc = "Cảnh báo rủi ro rung lắc hoặc điều chỉnh ngắn hạn cao"
    elif crash_points >= 25:
        crash_status_desc = "Rủi ro rung lắc kiểm định lại hỗ trợ nếu không bứt phá thành công"
    else:
        crash_status_desc = "Rủi ro điều chỉnh sâu ở mức thấp, vùng hỗ trợ đang bảo vệ giá tốt"

    # 7. Tổng hợp Phán Quyết
    if setup_quality_score >= 70 and risk_points < 35:
        timing_verdict = "ĐIỀU KIỆN KỸ THUẬT TÍCH CỰC - CHỜ ĐIỂM XÁC NHẬN BỨT PHÁ"
        timing_badge = "BULLISH_SURGE"
        timing_color = "#10b981"
    elif risk_points >= 50:
        timing_verdict = "CẢNH BÁO RỦI RO ĐIỀU CHỈNH - HẠN CHẾ MUA ĐUỔI"
        timing_badge = "BEARISH_DUMP"
        timing_color = "#ef4444"
    elif setup_quality_score >= 50:
        timing_verdict = "TÍCH LŨY THEO DÕI - CHỜ DÒNG TIỀN VƯỢT PIVOT"
        timing_badge = "ACCUMULATING"
        timing_color = "#38bdf8"
    else:
        timing_verdict = "GIAO DỊCH THẬN TRỌNG - QUAN SÁT VÙNG HỖ TRỢ"
        timing_badge = "NEUTRAL_WATCH"
        timing_color = "#f59e0b"

    return {
        "symbol": sym,
        "timing_verdict": timing_verdict,
        "timing_badge": timing_badge,
        "timing_color": timing_color,
        "overall_timing_score": int(setup_quality_score),
        "setup_quality_score": int(setup_quality_score),
        "pivot_price": trigger_pivot,
        "breakdown_price": failure_level,
        "active_buy_pct": round(active_buy_pct, 1),
        "active_sell_pct": round(active_sell_pct, 1),
        "up_probability_pct": int(setup_quality_score),
        "down_probability_pct": int(risk_points),
        
        "smart_money_pulse": {
            "active_buy_pct": round(active_buy_pct, 1),
            "active_sell_pct": round(active_sell_pct, 1),
            "order_pressure_verdict": order_pressure_verdict,
            "order_pressure_color": order_pressure_color,
            "foreign_net_vol": foreign_net_vol,
            "foreign_verdict": foreign_verdict,
            "foreign_badge": foreign_badge,
            "estimation_proxy_note": "Tỷ lệ mua/bán ước tính từ diễn biến giá và khối lượng (Price-Volume Proxy), không phải dữ liệu sổ lệnh tick-by-tick."
        },

        "catalyst_calendar": catalyst_events,

        "surge_scenario": {
            "setup_quality_score": setup_quality_score,
            "probability_pct": setup_quality_score,  # Giữ alias cho backward-compatibility
            "timing_window": surge_status_desc,
            "trigger_pivot_price": trigger_pivot,
            "catalysts": surge_catalysts,
            "action_advice": f"Theo dõi mốc Pivot {trigger_pivot:,.0f} đ. Khi giá vượt qua mốc này kèm khối lượng xác nhận > 1.3x MA20, xem xét gia tăng vị thế."
        },
        
        "crash_scenario": {
            "risk_score": risk_points,
            "risk_probability_pct": risk_points,  # Giữ alias cho backward-compatibility
            "timing_window": crash_status_desc,
            "failure_trigger_level": failure_level,
            "warnings": crash_warnings if crash_warnings else ["Chưa phát hiện tín hiệu phân phối lớn hay phân kỳ âm."],
            "invalidation_rule": f"Nếu giá đóng cửa xuyên thủng mốc {failure_level:,.0f} đ, thiết lập tăng giá sẽ mất hiệu lực, cần tuân thủ kỷ luật cắt lỗ."
        },

        "methodology_disclaimer": "Điểm số và phân tích dựa trên mô hình Heuristic VSA & Xu hướng kỹ thuật, không phải dự báo tương lai chắc chắn hay xác suất thống kê cam kết."
    }
