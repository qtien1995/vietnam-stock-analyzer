from typing import Dict, Any

def calculate_trade_setup(
    current_price: float,
    fa_analysis: Dict[str, Any],
    ta_analysis: Dict[str, Any],
    quote: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    Tính toán kế hoạch giao dịch chuẩn xác đa khung thời gian:
    - Ngắn hạn (T+ / Swing)
    - Trung hạn (Trend Following)
    - Dài hạn (Value / Compounder)
    Đặc thù thị trường Việt Nam (HOSE/HNX):
    - Chống lỗi cắt lỗ phi thực tế (0.0% / 0.26%)
    - Giới hạn tỷ trọng danh mục an toàn (tối đa 25% NAV cho 1 cổ phiếu)
    - Nhận diện áp lực khối ngoại và xu hướng downtrend
    """
    if quote is None:
        quote = {}

    fa_score = fa_analysis.get("fa_total_score", 50)
    ta_score = ta_analysis.get("ta_total_score", 50)
    indicators = ta_analysis.get("indicators", {})
    foreign_net_vol = quote.get("foreign_net_vol", 0.0)

    # 1. Xác định các mốc kỹ thuật
    ema20 = indicators.get("ema20", current_price * 0.97)
    ema50 = indicators.get("ema50", current_price * 0.92)
    sup_20d = indicators.get("sup_20d", current_price * 0.95)
    atr = indicators.get("atr14", current_price * 0.03)

    # Kiểm tra trạng thái xu hướng giá
    in_downtrend = current_price < ema20 and current_price < ema50
    heavy_foreign_sell = foreign_net_vol < -500_000 # Khối ngoại bán ròng đột biến > 500k cp

    # 2. Điểm số Đồng thuận (Consensus Score - 45% FA, 55% TA theo chiến lược Hybrid)
    # Nếu đang trong downtrend hoặc khối ngoại bán ròng mạnh, phạt điểm để tránh bắt dao rơi
    ta_penalty = 0
    if in_downtrend:
        ta_penalty += 10
    if heavy_foreign_sell:
        ta_penalty += 5

    effective_ta_score = max(5, ta_score - ta_penalty)
    consensus_score = int(fa_score * 0.45 + effective_ta_score * 0.55)

    # 3. TÍNH TOÁN CẮT LỖ (STOP LOSS) THỰC TẾ CHO TTCK VIỆT NAM
    # Cắt lỗ KHÔNG ĐƯỢC đặt tại đỉnh hỗ trợ sup_20d vì sẽ bị quét bóng nến.
    # Phải đặt DƯỚI hỗ trợ với biên đệm 1.5 - 2.5%, hoặc 2.0x ATR.
    sl_by_support = (sup_20d * 0.98) if sup_20d > 0 else (current_price * 0.95)
    sl_by_atr = (current_price - 2.0 * atr) if atr > 0 else (current_price * 0.95)
    sl_candidate = min(sl_by_support, sl_by_atr)

    # Ràng buộc an toàn trên TTCK Việt Nam:
    # - Mức cắt lỗ ngắn hạn tối thiểu là 3.8% (tránh bị dính nhiễu ATO/ATC hoặc 1-2 bước giá)
    # - Mức cắt lỗ ngắn hạn tối đa là 7.0% (giới hạn an toàn chuẩn 1 phiên sàn HOSE)
    max_sl_price = current_price * 0.962  # Tối thiểu lỗ 3.8%
    min_sl_price = current_price * 0.930  # Tối đa lỗ 7.0%

    sl_short = round(min(max(sl_candidate, min_sl_price), max_sl_price), 0)
    sl_pct = round(((current_price - sl_short) / current_price) * 100, 2)

    # === MỤC TIÊU CHỐT LỜI (TAKE PROFIT) ===
    # TP1 Ngắn hạn: Tối thiểu +8% đến +10%
    tp_short = round(current_price * 1.09, 0)
    # TP2 Trung hạn: +20% đến +25%
    tp_mid = round(current_price * 1.22, 0)
    # TP3 Dài hạn: Theo Fair Value hoặc +35%
    fair_price = fa_analysis.get("buffett", {}).get("fair_price", current_price * 1.30)
    tp_long = round(max(fair_price, current_price * 1.35), 0)

    # Vùng mua tối ưu từ giá EMA20 đến giá hiện tại (+ tối đa 1.5%)
    buy_low = round(min(current_price * 0.98, ema20), 0)
    buy_high = round(current_price * 1.015, 0)
    buy_zone = f"{buy_low:,.0f} - {buy_high:,.0f}"

    # Tỷ lệ R:R chuẩn xác
    risk_per_share = current_price - sl_short
    reward_per_share = tp_short - current_price
    risk_reward_ratio = round(reward_per_share / risk_per_share, 2) if risk_per_share > 0 else 2.0

    # 4. PHÁN QUYẾT HÀNH ĐỘNG (ACTION VERDICT)
    f_score = fa_analysis.get("f_score", 5)
    valuation_warning = fa_analysis.get("valuation_warning", "")

    if consensus_score >= 75 and f_score >= 6 and not in_downtrend and risk_reward_ratio >= 1.8:
        action = "MUA MẠNH (STRONG BUY)"
        color = "green"
        action_summary = "Cổ phiếu hội tụ cơ bản tăng trưởng tốt và dòng tiền bứt phá trên các đường xu hướng."
    elif consensus_score >= 60 and not in_downtrend:
        action = "MUA THĂM DÒ (TEST BUY)"
        color = "cyan"
        action_summary = "Cổ phiếu có nền tảng cơ bản và kỹ thuật tốt, giải ngân thăm dò từng phần."
    elif consensus_score >= 45:
        action = "THEO DÕI (WATCHLIST)"
        color = "yellow"
        if in_downtrend:
            action_summary = "Cổ phiếu đang chịu áp lực điều chỉnh dưới MA ngắn hạn, kiên nhẫn chờ điểm cân bằng cạn cung."
        elif heavy_foreign_sell:
            action_summary = "Khối ngoại đang bán ròng mạnh, tạm thời theo dõi chờ áp lực cung hạ nhiệt."
        elif valuation_warning:
            action_summary = f"Cổ phiếu tích lũy nhưng {valuation_warning}, chờ chiết khấu thêm."
        else:
            action_summary = "Cổ phiếu đang trong biên độ tích lũy, chờ dòng tiền hoặc BCTC xác nhận."
    else:
        action = "BÁN / TRÁNH XA (AVOID)"
        color = "red"
        action_summary = "Áp lực điều chỉnh cao hoặc sức khỏe tài chính yếu, không giải ngân lúc này."

    # 5. QUẢN TRỊ TỶ TRỌNG VỐN AN TOÀN (% NAV)
    # Quy tắc quản trị rủi ro danh mục cá nhân (Max 25% NAV cho 1 cổ phiếu để tránh rủi ro tập trung):
    # Rủi ro chấp nhận tối đa 1.5% tổng NAV cho 1 vị thế
    theoretical_pos = round((1.5 / sl_pct) * 100, 1) if sl_pct > 0 else 10.0

    if action == "MUA MẠNH (STRONG BUY)":
        max_position = min(theoretical_pos, 25.0)
    elif action == "MUA THĂM DÒ (TEST BUY)":
        max_position = min(theoretical_pos, 15.0)
    elif action == "THEO DÕI (WATCHLIST)":
        max_position = min(theoretical_pos, 5.0) # Tối đa 5% lấy vị thế quan sát nếu muốn
    else:
        max_position = 0.0

    return {
        "action": action,
        "action_color": color,
        "action_summary": action_summary,
        "consensus_score": consensus_score,
        "current_price": current_price,
        "buy_zone": buy_zone,
        "stop_loss": sl_short,
        "stop_loss_pct": sl_pct,
        "max_position_size_pct": max_position,
        "take_profit_1": tp_short,
        "take_profit_1_pct": round(((tp_short - current_price) / current_price) * 100, 2),
        "take_profit_2": tp_mid,
        "take_profit_2_pct": round(((tp_mid - current_price) / current_price) * 100, 2),
        "take_profit_3": tp_long,
        "take_profit_3_pct": round(((tp_long - current_price) / current_price) * 100, 2),
        "risk_reward_ratio": risk_reward_ratio,
        "fa_score": fa_score,
        "ta_score": effective_ta_score,
        "in_downtrend": in_downtrend,
        "heavy_foreign_sell": heavy_foreign_sell
    }
