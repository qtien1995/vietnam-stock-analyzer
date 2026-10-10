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

    # 2. Điểm số Đồng thuận (Consensus Score theo trọng số Hybrid trong config)
    # Nếu đang trong downtrend hoặc khối ngoại bán ròng mạnh, phạt điểm để tránh bắt dao rơi
    ta_penalty = 0
    if in_downtrend:
        ta_penalty += 10
    if heavy_foreign_sell:
        ta_penalty += 5

    effective_ta_score = max(5, ta_score - ta_penalty)
    consensus_score = int(fa_score * WEIGHT_FA + effective_ta_score * WEIGHT_TA)

    # 3. TÍNH TOÁN CẮT LỖ (STOP LOSS) THỰC TẾ CHO TTCK VIỆT NAM
    # Cắt lỗ KHÔNG ĐƯỢC đặt tại đỉnh hỗ trợ sup_20d vì sẽ bị quét bóng nến.
    # Phải đặt DƯỚI hỗ trợ với biên đệm 1.5 - 2.5%, hoặc 2.0x ATR.
    sl_by_support = (sup_20d * 0.98) if sup_20d > 0 else (current_price * 0.95)
    sl_by_atr = (current_price - 2.0 * atr) if atr > 0 else (current_price * 0.95)
    sl_candidate = min(sl_by_support, sl_by_atr)

    # Ràng buộc an toàn trên TTCK Việt Nam:
    # - Mức cắt lỗ ngắn hạn tối thiểu là MIN_STOP_LOSS_PCT (3.8%)
    # - Mức cắt lỗ ngắn hạn tối đa là MAX_STOP_LOSS_PCT (7.0%)
    max_sl_price = current_price * (1.0 - MIN_STOP_LOSS_PCT)
    min_sl_price = current_price * (1.0 - MAX_STOP_LOSS_PCT)

    sl_short = round(min(max(sl_candidate, min_sl_price), max_sl_price), 0)
    sl_pct = round(((current_price - sl_short) / current_price) * 100, 2)

    # === 3.1 BÓC TÁCH ĐỊNH GIÁ GIÁ TRỊ THỰC & VÙNG GOM TÍCH SẢN (BUFFETT & GRAHAM) ===
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
            fair_price = round(bvps * 1.3, 0)
        else:
            fair_price = current_price

    # Tỷ lệ chênh lệch so với giá trị thực
    premium_discount_pct = round(((current_price - fair_price) / fair_price) * 100, 1) if fair_price > 0 else 0.0
    
    # Xác định trạng thái định giá
    if premium_discount_pct > 15.0:
        value_status = "ĐẮT ĐỎ (VƯỢT GIÁ TRỊ THỰC)"
        value_warning = f"Thị giá ({current_price:,.0f} đ) đang cao hơn +{premium_discount_pct:.1f}% so với giá trị thực ước tính ({fair_price:,.0f} đ)."
    elif premium_discount_pct < -15.0:
        value_status = "RẺ / CÓ BIÊN AN TOÀN CAO"
        value_warning = ""
    else:
        value_status = "ĐỊNH GIÁ HỢP LÝ (FAIR VALUE)"
        value_warning = ""

    # Vùng mua giá trị an toàn: Luôn yêu cầu Biên an toàn (Margin of Safety) >= 15% - 25% dưới Fair Price
    value_buy_max = round(fair_price * 0.85, 0)  # Chiết khấu 15%
    value_buy_min = round(fair_price * 0.75, 0)  # Chiết khấu 25%
    value_buy_zone = f"≤ {value_buy_max:,.0f} VND (Vùng gom an toàn: {value_buy_min:,.0f} - {value_buy_max:,.0f} VND)"

    # Lý do định giá giá trị
    value_reasons = []
    if pe:
        value_reasons.append(f"P/E {pe:.1f}x")
    if pb and bvps > 0:
        value_reasons.append(f"P/B {pb:.2f}x (BVPS {bvps:,.0f} đ)")
    if cf_data.get("quality_grade"):
        value_reasons.append(f"Dòng tiền CFO Hạng {cf_data.get('quality_grade')}")
    if buffett.get("reasons"):
        value_reasons.append(buffett.get("reasons")[0])
    
    value_rationale = "; ".join(value_reasons)

    # Giải thích nguyên nhân chênh lệch giữa Thị giá vs Giá trị thực
    if premium_discount_pct > 15.0:
        valuation_gap_explanation = (
            f"Thị trường đang 'trả giá trước cho kỳ vọng tương lai' (Growth Premium): "
            f"Kỳ vọng bùng nổ từ mảng chiến lược hoặc dòng vốn đầu cơ đẩy P/B lên {pb if pb else 'cao'}x. "
            f"Trong khi định giá thận trọng ({fair_price:,.0f} đ) dựa trên BCTC hiện hữu để bảo vệ vốn."
        )
    elif premium_discount_pct < -15.0:
        valuation_gap_explanation = (
            f"Thị trường đang chiết khấu sâu do tâm lý thận trọng ngắn hạn. "
            f"Tạo biên an toàn {abs(premium_discount_pct):.1f}% so với giá trị thực ({fair_price:,.0f} đ) cho nhà đầu tư tích sản."
        )
    else:
        valuation_gap_explanation = "Thị giá phản ánh sát với giá trị tài sản và dòng tiền hiện hữu của doanh nghiệp."

    # === 3.2 MỤC TIÊU CHỐT LỜI (TAKE PROFIT) & LƯỚT SÓNG KỸ THUẬT ===
    # TP1 Ngắn hạn: Chuẩn hóa theo TARGET_PROFIT_1_PCT (+12%)
    tp_short = round(current_price * (1.0 + TARGET_PROFIT_1_PCT), 0)
    # TP2 Trung hạn: Chuẩn hóa theo TARGET_PROFIT_2_PCT (+20%)
    tp_mid = round(current_price * (1.0 + TARGET_PROFIT_2_PCT), 0)
    # TP3 Dài hạn: Theo Fair Value hoặc TARGET_PROFIT_3_PCT (+35%)
    tp_long = round(max(fair_price, current_price * (1.0 + TARGET_PROFIT_3_PCT)), 0)

    # Vùng mua lướt sóng tối ưu từ giá EMA20 đến giá hiện tại (+ tối đa 1.5%)
    buy_low = round(min(current_price * 0.98, ema20), 0)
    buy_high = round(current_price * 1.015, 0)
    buy_zone = f"{buy_low:,.0f} - {buy_high:,.0f}"

    # Lưu ý chiến lược khi lướt sóng
    if premium_discount_pct > 15.0:
        swing_strategy_note = f"⚠️ CẢNH BÁO: Thị giá ({current_price:,.0f} đ) đang cao hơn giá trị thực ({fair_price:,.0f} đ). Nếu lướt sóng theo đà dòng tiền, BẮT BUỘC tuân thủ kỷ luật cắt lỗ tại {sl_short:,.0f} đ (-{sl_pct}%), TUYỆT ĐỐI KHÔNG gồng lỗ thành đầu tư dài hạn!"
    elif premium_discount_pct < -15.0:
        swing_strategy_note = f"✅ An toàn kép: Vừa có hỗ trợ kỹ thuật nổ vol, vừa có biên an toàn cơ bản nâng đỡ (Rẻ hơn giá trị thực {abs(premium_discount_pct):.1f}%)."
    else:
        swing_strategy_note = "Cổ phiếu định giá hợp lý, giải ngân theo các nhịp tích lũy cạn cung quanh hỗ trợ."

    # Tỷ lệ R:R chuẩn xác
    risk_per_share = current_price - sl_short
    reward_per_share = tp_short - current_price
    risk_reward_ratio = round(reward_per_share / risk_per_share, 2) if risk_per_share > 0 else 2.0

    # 4. PHÁN QUYẾT HÀNH ĐỘNG (ACTION VERDICT)
    f_score = fa_analysis.get("f_score", 5)
    valuation_warning = fa_analysis.get("valuation_warning", "")

    if consensus_score >= 75 and f_score >= 6 and not in_downtrend and risk_reward_ratio >= (MIN_RISK_REWARD_RATIO - 0.3):
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
        "heavy_foreign_sell": heavy_foreign_sell,
        # Phân định Giá trị vs Lướt sóng
        "fair_price": fair_price,
        "value_status": value_status,
        "value_warning": value_warning,
        "value_buy_zone": value_buy_zone,
        "value_buy_max": value_buy_max,
        "value_buy_min": value_buy_min,
        "premium_discount_pct": premium_discount_pct,
        "value_rationale": value_rationale,
        "valuation_gap_explanation": valuation_gap_explanation,
        "swing_buy_zone": buy_zone,
        "swing_strategy_note": swing_strategy_note
    }
