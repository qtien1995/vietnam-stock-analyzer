from typing import Dict, Any
from config import (
    WEIGHT_FA,
    WEIGHT_TA,
    MIN_STOP_LOSS_PCT,
    MAX_STOP_LOSS_PCT,
    MIN_RISK_REWARD_RATIO,
    TARGET_PROFIT_1_PCT,
    TARGET_PROFIT_2_PCT,
    TARGET_PROFIT_3_PCT
)


def calculate_trade_setup(
    current_price: float,
    fa_analysis: Dict[str, Any],
    ta_analysis: Dict[str, Any],
    quote: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    Tính toán kế hoạch giao dịch chuẩn xác và kiểm định tính hợp lệ của thiết lập (Setup Validation Gate).
    
    Quy tắc an toàn bất di bất dịch:
    1. Nếu không có thiết lập hợp lệ (Downtrend sâu, kiệt quệ tài chính, thanh khoản chết, consensus < 45):
       -> Trả về has_valid_setup = False, setup_status = 'NO_VALID_SETUP', max_position = 0%.
       -> Tuyệt đối không tự động sinh ra vùng mua, điểm chốt lời hay R:R giả tạo để ép vào khuôn khổ.
    2. Cắt lỗ (Stop Loss) là ngưỡng kích hoạt kỷ luật bán, không phải cam kết mức lỗ tối đa trong điều kiện mở gap sàn.
    3. Quản trị tỷ trọng an toàn: Giới hạn rủi ro 1.5% NAV cho mỗi vị thế, trần tối đa 25% NAV.
    """
    if quote is None:
        quote = {}

    fa_score = fa_analysis.get("fa_total_score", 50)
    ta_score = ta_analysis.get("ta_total_score", 50)
    indicators = ta_analysis.get("indicators", {})
    foreign_net_vol = quote.get("foreign_net_vol", 0.0)

    # 1. Trích xuất mốc kỹ thuật & Trạng thái xu hướng
    ema20 = indicators.get("ema20", current_price * 0.97)
    ema50 = indicators.get("ema50", current_price * 0.92)
    sup_20d = indicators.get("sup_20d", current_price * 0.95)
    res_20d = indicators.get("res_20d", current_price * 1.05)
    atr = indicators.get("atr14", current_price * 0.03)

    in_downtrend = (current_price < ema20 and current_price < ema50)
    heavy_foreign_sell = (foreign_net_vol < -500_000)

    # 2. Điểm số Đồng thuận (Consensus Score)
    ta_penalty = 0
    if in_downtrend:
        ta_penalty += 12
    if heavy_foreign_sell:
        ta_penalty += 5

    effective_ta_score = max(5, ta_score - ta_penalty)
    consensus_score = int(fa_score * WEIGHT_FA + effective_ta_score * WEIGHT_TA)

    # 3. Trích xuất định giá cơ bản
    buffett = fa_analysis.get("buffett", {})
    asset_val = fa_analysis.get("asset_valuation", {})
    fin_ratios = fa_analysis.get("ratios", {})
    cf_data = fa_analysis.get("cash_flow", {})

    fair_price = float(buffett.get("fair_price") or 0.0)
    bvps = float(asset_val.get("bvps") or 0.0)
    pe = fin_ratios.get("pe")
    pb = asset_val.get("pb") or fin_ratios.get("pb")
    
    if fair_price <= 0:
        if bvps > 0:
            fair_price = round(bvps * 1.2, 0)
        else:
            fair_price = current_price

    premium_discount_pct = round(((current_price - fair_price) / fair_price) * 100, 1) if fair_price > 0 else 0.0

    if premium_discount_pct > 15.0:
        value_status = "ĐẮT ĐỎ (VƯỢT GIÁ TRỊ THỰC)"
        value_warning = f"Thị giá ({current_price:,.0f} đ) cao hơn +{premium_discount_pct:.1f}% so với giá trị thực ước tính ({fair_price:,.0f} đ)."
    elif premium_discount_pct < -15.0:
        value_status = "RẺ / CÓ BIÊN AN TOÀN CAO"
        value_warning = ""
    else:
        value_status = "ĐỊNH GIÁ HỢP LÝ (FAIR VALUE)"
        value_warning = ""

    # Vùng mua giá trị an toàn
    value_buy_max = round(fair_price * 0.85, 0)
    value_buy_min = round(fair_price * 0.75, 0)
    value_buy_zone = f"≤ {value_buy_max:,.0f} VND (Vùng gom an toàn: {value_buy_min:,.0f} - {value_buy_max:,.0f} VND)"

    # Xác định giới hạn biên độ theo sàn giao dịch
    exchange = str(quote.get("exchange", "HOSE")).upper()
    if "HNX" in exchange:
        exchange_max_sl_pct = 0.100
        exchange_min_sl_pct = 0.045
    elif "UPCOM" in exchange:
        exchange_max_sl_pct = 0.140
        exchange_min_sl_pct = 0.050
    else:
        exchange_max_sl_pct = MAX_STOP_LOSS_PCT  # 7.0%
        exchange_min_sl_pct = MIN_STOP_LOSS_PCT  # 3.8%

    # 4. KIỂM ĐỊNH TÍNH HỢP LỆ CỦA THIẾT LẬP (SETUP VALIDATION GATE)
    f_score = fa_analysis.get("f_score", 5)
    valuation_warning_fa = fa_analysis.get("valuation_warning", "")
    z_zone = cf_data.get("z_zone", "SAFE")
    cf_grade = cf_data.get("quality_grade", "B")

    # Điều kiện loại bỏ hoàn toàn (Disqualifiers)
    is_disqualified = (
        (consensus_score < 45) or
        (in_downtrend and current_price < ema50 * 0.95) or
        (z_zone == "DISTRESS" and cf_grade == "D") or
        (asset_val.get("manipulation_risk_level", 1) >= 5) or
        (fa_analysis.get("governance", {}).get("subsidiary_web", {}).get("circular_capital_risk_level", 1) >= 5)
    )

    invalidation_conditions = [
        f"Giá đóng cửa gãy thủng ngưỡng hỗ trợ cứng tại {sup_20d:,.0f} đ.",
        "Dòng tiền thuần hoạt động kinh doanh (CFO) âm kéo dài trong kỳ BCTC tiếp theo.",
        f"Thị trường chung (VN-Index) xác nhận gãy kênh xu hướng trung hạn hoặc xuất hiện phiên phân phối lớn."
    ]

    if is_disqualified:
        # TRẠNG THÁI: KHÔNG CÓ ĐIỂM MUA HỢP LỆ (NO_VALID_SETUP)
        action = "BÁN / TRÁNH XA (AVOID)" if consensus_score < 40 else "THEO DÕI (WATCHLIST)"
        color = "#ef4444" if action == "BÁN / TRÁNH XA (AVOID)" else "#f59e0b"
        
        if in_downtrend:
            action_summary = "Cổ phiếu nằm trong xu hướng giảm (Downtrend), dưới các đường trung bình động; không giải ngân bắt đáy."
        elif z_zone == "DISTRESS":
            action_summary = "Rủi ro kiệt quệ tài chính hoặc chất lượng dòng tiền yếu (CFO âm), tránh xa bảo vệ vốn."
        elif consensus_score < 45:
            action_summary = "Điểm số đồng thuận yếu (< 45/100), áp lực cung chiếm ưu thế, đứng ngoài quan sát."
        else:
            action_summary = "Chưa xuất hiện điểm mua đạt chuẩn tỷ lệ Lợi nhuận/Rủi ro."

        return {
            "has_valid_setup": False,
            "setup_status": "NO_VALID_SETUP",
            "exchange": exchange,
            "price_limit_pct": round(exchange_max_sl_pct * 100, 1),
            "action": action,
            "action_color": color,
            "action_summary": action_summary,
            "confidence": "CAO",
            "consensus_score": consensus_score,
            "current_price": current_price,
            "buy_zone": "CHƯA CÓ ĐIỂM MUA HỢP LỆ (ĐỨNG NGOÀI)",
            "stop_loss": 0.0,
            "stop_loss_pct": 0.0,
            "max_position_size_pct": 0.0,
            "take_profit_1": 0.0,
            "take_profit_1_pct": 0.0,
            "take_profit_2": 0.0,
            "take_profit_2_pct": 0.0,
            "take_profit_3": 0.0,
            "take_profit_3_pct": 0.0,
            "risk_reward_ratio": 0.0,
            "fa_score": fa_score,
            "ta_score": effective_ta_score,
            "in_downtrend": in_downtrend,
            "heavy_foreign_sell": heavy_foreign_sell,
            "fair_price": fair_price,
            "value_status": value_status,
            "value_warning": value_warning,
            "value_buy_zone": "KHÔNG ÁP DỤNG",
            "value_buy_max": value_buy_max,
            "value_buy_min": value_buy_min,
            "premium_discount_pct": premium_discount_pct,
            "value_rationale": "Không giải ngân khi cổ phiếu vi phạm bộ lọc rủi ro.",
            "valuation_gap_explanation": "Thị trường chiết khấu sâu do rủi ro nội tại hoặc xu hướng dòng tiền tiêu cực.",
            "swing_buy_zone": "KHÔNG ÁP DỤNG",
            "swing_strategy_note": "CẢNH BÁO BẢO VỆ VỐN: Không giải ngân khi chưa có tín hiệu tạo đáy và xác nhận cạn cung.",
            "invalidation_conditions": invalidation_conditions
        }

    # 5. KHI CÓ THIẾT LẬP HỢP LỆ (VALID_SETUP)
    # Tính cắt lỗ chuẩn xác đặt DƯỚI hỗ trợ kỹ thuật hoặc 2.0x ATR
    sl_by_support = (sup_20d * 0.98) if sup_20d > 0 else (current_price * 0.95)
    sl_by_atr = (current_price - 2.0 * atr) if atr > 0 else (current_price * 0.95)
    sl_candidate = min(sl_by_support, sl_by_atr)

    max_sl_price = current_price * (1.0 - exchange_min_sl_pct)
    min_sl_price = current_price * (1.0 - exchange_max_sl_pct)
    sl_short = round(min(max(sl_candidate, min_sl_price), max_sl_price), 0)
    sl_pct = round(((current_price - sl_short) / current_price) * 100, 2) if current_price > 0 else 7.0

    # Mục tiêu chốt lời (Take Profit) dựa trên kháng cự kỹ thuật và biên định giá
    # TP1: Vùng kháng cự gần nhất hoặc mục tiêu ngắn hạn
    target_1_est = max(res_20d, current_price * (1.0 + TARGET_PROFIT_1_PCT))
    tp_short = round(target_1_est, 0)
    tp1_pct = round(((tp_short - current_price) / current_price) * 100, 2) if current_price > 0 else 12.0

    # TP2: Mục tiêu trung hạn
    tp_mid = round(max(current_price * (1.0 + TARGET_PROFIT_2_PCT), fair_price * 0.95), 0)
    tp2_pct = round(((tp_mid - current_price) / current_price) * 100, 2) if current_price > 0 else 20.0

    # TP3: Dài hạn theo Fair Value hoặc sóng mở rộng
    tp_long = round(max(fair_price, current_price * (1.0 + TARGET_PROFIT_3_PCT)), 0)
    tp3_pct = round(((tp_long - current_price) / current_price) * 100, 2) if current_price > 0 else 35.0

    # Tỷ lệ R:R thực tế
    risk_per_share = max(1.0, current_price - sl_short)
    reward_per_share = max(1.0, tp_short - current_price)
    risk_reward_ratio = round(reward_per_share / risk_per_share, 2)

    # Phán quyết hành động
    if consensus_score >= 75 and f_score >= 6 and not in_downtrend and risk_reward_ratio >= 1.8:
        action = "MUA MẠNH (STRONG BUY)"
        color = "#10b981"
        action_summary = "Cổ phiếu hội tụ cơ bản tăng trưởng tốt và dòng tiền bứt phá trên các đường xu hướng."
        confidence = "CAO"
    elif consensus_score >= 60 and not in_downtrend:
        action = "MUA THĂM DÒ (TEST BUY)"
        color = "#38bdf8"
        action_summary = "Cổ phiếu có nền tảng cơ bản và kỹ thuật tốt, giải ngân thăm dò từng phần."
        confidence = "VỪA"
    else:
        action = "THEO DÕI (WATCHLIST)"
        color = "#f59e0b"
        action_summary = "Cổ phiếu đang tích lũy, kiên nhẫn chờ điểm xác nhận bứt phá hoặc BCTC quý tiếp theo."
        confidence = "VỪA"

    # Quản trị tỷ trọng vốn danh mục (% NAV)
    theoretical_pos = round((1.5 / sl_pct) * 100, 1) if sl_pct > 0 else 10.0

    if action == "MUA MẠNH (STRONG BUY)":
        max_position = min(theoretical_pos, 25.0)
    elif action == "MUA THĂM DÒ (TEST BUY)":
        max_position = min(theoretical_pos, 15.0)
    else:
        max_position = min(theoretical_pos, 5.0)

    # Vùng mua lướt sóng
    buy_low = round(min(current_price * 0.985, ema20), 0)
    buy_high = round(current_price * 1.015, 0)
    buy_zone = f"{buy_low:,.0f} - {buy_high:,.0f}"

    swing_strategy_note = (
        f"Tuân thủ nghiêm ngặt kỷ luật cắt lỗ tại {sl_short:,.0f} đ (-{sl_pct}%). "
        f"Lưu ý: Mức cắt lỗ là điều kiện kích hoạt lệnh kỷ luật, không phải bảo đảm tài chính trong kịch bản mở gap giảm sàn."
    )

    return {
        "has_valid_setup": True,
        "setup_status": "VALID_SETUP",
        "exchange": exchange,
        "price_limit_pct": round(exchange_max_sl_pct * 100, 1),
        "action": action,
        "action_color": color,
        "action_summary": action_summary,
        "confidence": confidence,
        "consensus_score": consensus_score,
        "current_price": current_price,
        "buy_zone": buy_zone,
        "stop_loss": sl_short,
        "stop_loss_pct": sl_pct,
        "max_position_size_pct": max_position,
        "take_profit_1": tp_short,
        "take_profit_1_pct": tp1_pct,
        "take_profit_2": tp_mid,
        "take_profit_2_pct": tp2_pct,
        "take_profit_3": tp_long,
        "take_profit_3_pct": tp3_pct,
        "risk_reward_ratio": risk_reward_ratio,
        "fa_score": fa_score,
        "ta_score": effective_ta_score,
        "in_downtrend": in_downtrend,
        "heavy_foreign_sell": heavy_foreign_sell,
        "fair_price": fair_price,
        "value_status": value_status,
        "value_warning": value_warning,
        "value_buy_zone": value_buy_zone,
        "value_buy_max": value_buy_max,
        "value_buy_min": value_buy_min,
        "premium_discount_pct": premium_discount_pct,
        "value_rationale": f"P/E {pe or 'N/A'}, P/B {pb or 'N/A'}, CFO Hạng {cf_data.get('quality_grade', 'B')}",
        "valuation_gap_explanation": "Thị giá phản ánh sát với giá trị tài sản và dòng tiền hiện hữu của doanh nghiệp.",
        "swing_buy_zone": buy_zone,
        "swing_strategy_note": swing_strategy_note,
        "invalidation_conditions": invalidation_conditions
    }
