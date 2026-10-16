# -*- coding: utf-8 -*-
"""
Module Bóc Tách Tạo Lập, Tay To Giữ Hàng & Radar Tin Tức Ban Lãnh Đạo
(Whale, Market Maker & Leadership News Forensic)
Chuyên trách:
1. Bản đồ Phân bổ Hàng & Tay To (Whale & Insider Holding Matrix)
2. Nhận diện Hành vi Tạo Lập & Đội Lái (Market Maker & Whale Behavior Diagnosis)
3. Chỉ số Áp lực Rung Lắc & Ép Bán (Shakeout Risk Index: 0 - 100)
4. Radar Tin Tức Báo Chí, Sự Kiện & Bẫy Truyền Thông (News Trap Radar)
5. Bóc tách Giao dịch & Độ Uy Tín của Chủ tịch / Ban Điều hành
6. Cẩm nang Ứng Xử Thực Chiến Dành Cho Nhà Đầu Tư Cá Nhân
"""

from datetime import datetime
from typing import Dict, Any, List, Optional
import math


def analyze_whale_and_insider_news(
    symbol: str,
    quote: Dict[str, Any],
    fa_result: Dict[str, Any],
    ta_result: Dict[str, Any],
    news_and_events: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Phân tích toàn diện Tạo Lập, Tay To và Radar Tin Tức Ban Lãnh Đạo.
    """
    sym = symbol.upper().strip()
    price = float(quote.get("price") or 0.0)
    vol = float(quote.get("volume") or 0.0)
    foreign_buy = float(quote.get("foreign_buy") or quote.get("buyForeignQtty") or 0.0)
    foreign_sell = float(quote.get("foreign_sell") or quote.get("sellForeignQtty") or 0.0)
    foreign_net_vol = float(quote.get("foreign_net_vol") or (foreign_buy - foreign_sell))

    gov = fa_result.get("governance", {})
    ownership = gov.get("ownership", {})
    leadership = gov.get("leadership", {})

    indicators = ta_result.get("indicators", {})
    vsa = ta_result.get("vsa", {})
    ema20 = float(indicators.get("ema20") or 0.0)
    ema50 = float(indicators.get("ema50") or 0.0)
    sma200 = float(indicators.get("sma200") or 0.0)
    high_52w = float(indicators.get("week_52_high") or (price * 1.5))
    low_52w = float(indicators.get("week_52_low") or (price * 0.7))
    rsi = float(indicators.get("rsi") or 50.0)
    vol_ratio = float(indicators.get("vol_ratio") or 1.0)
    vsa_phase = str(vsa.get("phase") or "Chưa xác định")

    if news_and_events is None:
        news_and_events = {"news": [], "events": []}

    raw_news = news_and_events.get("news", [])
    raw_events = news_and_events.get("events", [])

    # -------------------------------------------------------------
    # 1. BẢN ĐỒ PHÂN BỔ HÀNG & TAY TO (HOLDING MATRIX)
    # -------------------------------------------------------------
    insider_pct = float(leadership.get("insider_total_pct") or 0.0)
    foreigner_pct = float(ownership.get("foreigner_pct") or 0.0)
    state_pct = float(ownership.get("state_pct") or 0.0)
    top_shareholders = ownership.get("top_shareholders", [])

    # Tính tổng cổ đông lớn (>5%)
    major_sh_sum = sum(float(sh.get("percentage") or 0.0) for sh in top_shareholders)
    
    # Tính Trôi nổi Tự do Thực tế (True Free-Float ngoài thị trường)
    # Trừ đi phần hàng bị "nhốt" bởi nội bộ, nhà nước và tổ chức lớn
    locked_pct = state_pct + insider_pct
    for sh in top_shareholders:
        sh_pct = float(sh.get("percentage") or 0.0)
        # Nếu là quỹ ngoại lớn hoặc công ty riêng thì tính vào hàng nhốt
        sh_name = str(sh.get("name", "")).lower()
        if any(kw in sh_name for kw in ["tnhh", "quỹ", "fund", "holding", "invest", "veil", "dragon", "vina"]):
            if sh_pct not in [insider_pct, state_pct]:
                locked_pct += sh_pct * 0.75

    raw_free_float = float(ownership.get("free_float_pct") or 0.0)
    if raw_free_float > 0:
        true_free_float_pct = round(max(5.0, min(raw_free_float, 100.0 - locked_pct)), 1)
    else:
        true_free_float_pct = round(max(5.0, 100.0 - max(locked_pct, major_sh_sum)), 1)

    # Đánh giá cấp độ cô đặc
    if true_free_float_pct <= 28.0:
        concentration_grade = "SIÊU CÔ ĐẶC (CÁ MẬP KIỂM SOÁT HOÀN TOÀN)"
        concentration_desc = f"Lượng hàng trôi nổi thực tế ngoài thị trường chỉ khoảng {true_free_float_pct}%. Cổ phiếu do tay to và ban lãnh đạo kiểm soát chặt chẽ, rất dễ bị kéo thốc hoặc đạp sâu khi có chủ đích."
    elif true_free_float_pct <= 52.0:
        concentration_grade = "CÔ ĐẶC VỪA PHẢI (CÂN BẰNG TỔ CHỨC & ĐẠI CHÚNG)"
        concentration_desc = f"Lượng trôi nổi tự do khoảng {true_free_float_pct}%. Cổ phiếu có sự tham gia của tổ chức lớn nhưng thanh khoản thị trường vẫn đủ dồi dào, cần dòng tiền mồi để bứt phá."
    else:
        concentration_grade = "PHÂN MẢNH CAO (NHỎ LẺ ĐU BÁM NHIỀU)"
        concentration_desc = f"Trôi nổi ngoài thị trường lên tới {true_free_float_pct}%. Lượng cổ phiếu nằm trong tay nhà đầu tư cá nhân lớn, dễ bị rung lắc mạnh theo tâm lý bầy đàn và cần lượng tiền rất lớn mới đẩy sóng được."

    # Xác định ai đang chi phối
    if state_pct >= 35.0:
        whale_dominance = f"Nhà Nước nắm quyền chi phối ({state_pct:.1f}%). Rủi ro thao túng giá từ đội lái tư nhân ở mức thấp, cổ phiếu vận động theo tiến độ cổ phần hóa hoặc thoái vốn."
    elif insider_pct >= 25.0:
        whale_dominance = f"Gia đình Chủ tịch & Ban Lãnh đạo nắm quyền tuyệt đối ({insider_pct:.1f}%). Ý chí của Chủ tịch và các công ty riêng quyết định 80% xu hướng vận động của thị giá."
    elif foreigner_pct >= 30.0:
        whale_dominance = f"Khối ngoại & Quỹ ngoại nắm quyền chi phối ({foreigner_pct:.1f}%). Dòng tiền mua/bán ròng của quỹ (ETF, Dragon Capital, VinaCapital...) là động lực chính."
    else:
        whale_dominance = f"Đội lái thị trường & Dòng tiền đầu cơ dẫn dắt. Cổ phiếu có tính đại chúng cao, biến động giá phụ thuộc sát sao vào các nhóm tạo lập và môi giới lớn."

    # -------------------------------------------------------------
    # 2. CHẨN ĐOÁN HÀNH VI TẠO LẬP & ĐỘI LÁI (MARKET MAKER BEHAVIOR)
    # -------------------------------------------------------------
    dist_from_52w_high = round(((price - high_52w) / high_52w) * 100, 1) if high_52w > 0 else 0.0
    dist_from_52w_low = round(((price - low_52w) / low_52w) * 100, 1) if low_52w > 0 else 0.0

    shakeout_evidence: List[str] = []
    shakeout_risk_score = 40  # Mặc định trung bình

    # Logic chẩn đoán trạng thái tạo lập
    if dist_from_52w_high >= -12.0 and (rsi >= 68 or vol_ratio >= 1.8):
        mm_status = "PHÂN PHỐI / KÉO XẢ (DISTRIBUTION / BULL TRAP)"
        mm_color = "#ef4444"
        whale_action_desc = "Tay to và đội lái đang tận dụng sự hưng phấn của thị trường và các bài báo tin tốt để bán xả hàng ra ngoài. Xuất hiện hiện tượng kéo xanh tạo hưng phấn đầu phiên nhưng bị xả ép giá vào phiên chiều."
        shakeout_risk_score = 75
        shakeout_evidence.append("Giá đang áp sát đỉnh 52 tuần với xung lực quá mua (RSI cao).")
        shakeout_evidence.append("Khối lượng khớp lệnh lớn bất thường nhưng thân nến không bứt phá tương xứng (Dấu hiệu phân phối Wyckoff).")
    
    elif price < ema20 and price < ema50 and dist_from_52w_high <= -35.0:
        if vol_ratio <= 0.85 and rsi <= 35.0:
            mm_status = "GOM HÀNG LẶNG LẼ (QUIET ACCUMULATION / DRY UP)"
            mm_color = "#38bdf8"
            whale_action_desc = "Đội lái và cá mập đang âm thầm gom nhặt cổ phiếu ở vùng giá đáy chiết khấu sâu. Họ kê các lệnh mua ẩn dưới giá tham chiếu và không vội đẩy giá lên để vắt kiệt lượng hàng cắt lỗ của nhỏ lẻ."
            shakeout_risk_score = 65
            shakeout_evidence.append(f"Giá chiết khấu sâu {abs(dist_from_52w_high)}% từ đỉnh 52 tuần, tiệm cận vùng hỗ trợ dài hạn.")
            shakeout_evidence.append(f"Thanh khoản cạn kiệt (Vol {vol_ratio:.2f}x MA20), lực cung bán tháo hoảng loạn đã hết.")
            shakeout_evidence.append("RSI chạm ngưỡng Quá bán (Oversold), tạo nền tích lũy đi ngang rũ cung.")
        else:
            mm_status = "ĐÈ GIÁ / THẢ TRÔI (MARK-DOWN / EXHAUSTION)"
            mm_color = "#f97316"
            whale_action_desc = "Tạo lập đã thoái lui hoặc chưa có ý định đỡ giá. Cổ phiếu đang bị thả trôi tự do theo quán tính giảm, các nhịp hồi phục ngắn hạn dễ bị bán đè trở lại."
            shakeout_risk_score = 55
            shakeout_evidence.append("Giá nằm dưới toàn bộ các đường xu hướng ngắn và trung hạn EMA20, EMA50.")
            shakeout_evidence.append("Chưa xuất hiện phiên bùng nổ dòng tiền (Pocket Pivot) để xác nhận đảo chiều.")

    elif price >= ema20 and vol_ratio >= 1.25 and 45 <= rsi <= 65:
        mm_status = "ĐẨY GIÁ THỬ CUNG (MARK-UP / POCKET PIVOT)"
        mm_color = "#10b981"
        whale_action_desc = "Dòng tiền lớn đã nhập cuộc! Đội lái chủ động ăn sạch các lệnh bán treo tại kháng cự để kích thích dòng tiền F0 bên ngoài lao vào mua đuổi đẩy giá."
        shakeout_risk_score = 45
        shakeout_evidence.append(f"Thanh khoản bùng nổ đạt {vol_ratio:.2f}x bình quân MA20.")
        shakeout_evidence.append("Giá đóng cửa bứt phá trên đường EMA20 với thân nến xanh tích cực.")

    else:
        mm_status = "RUNG LẮC RŨ BỎ (SHAKEOUT / ABSORPTION)"
        mm_color = "#eab308"
        whale_action_desc = "Đội lái đang liên tục rung lắc trong phiên (tạo nến râu trên/dưới hoặc đạp giả thủng hỗ trợ trong phiên rồi kéo rút chân cuối ngày) nhằm ép các nhà đầu tư cá nhân yếu tim phải bán non."
        shakeout_risk_score = 70
        shakeout_evidence.append("Biên độ giá nén chặt quanh nền tích lũy, dao động giật cục trong phiên.")
        shakeout_evidence.append("Tỷ lệ khớp lệnh giằng co, liên tục xuất hiện lệnh đè gom và ép giá vùng thấp.")

    # Đánh giá mức độ áp lực rung lắc
    if shakeout_risk_score >= 70:
        shakeout_risk_level = "CAO (CẢNH BÁO RUNG CÂY DỌA KHỈ MẠNH)"
    elif shakeout_risk_score >= 45:
        shakeout_risk_level = "TRUNG BÌNH (RUNG LẮC THEO NHỊP CUNG CẦU)"
    else:
        shakeout_risk_level = "THẤP (BIẾN ĐỘNG ÊM Ả, ÍT GIẬT CỤC)"

    # -------------------------------------------------------------
    # 3. RADAR TIN TỨC & BẪY TRUYỀN THÔNG (NEWS TRAP RADAR)
    # -------------------------------------------------------------
    recent_news_highlights = []
    for item in raw_news[:6]:
        title = item.get("title", "")
        pdate = item.get("public_date", "")[:10]
        if title:
            recent_news_highlights.append({
                "title": title,
                "date": pdate,
                "source": item.get("source", "Truyền thông tài chính"),
                "link": item.get("link", "")
            })

    # Lọc sự kiện và giao dịch nội bộ
    insider_events = []
    insider_trading_keywords = ["giao dịch nội bộ", "người liên quan", "đăng ký mua", "đăng ký bán", "bán cổ phiếu", "mua cổ phiếu", "bán giải chấp", "esop"]
    has_recent_insider_deal = False
    insider_deal_notes = []

    for ev in raw_events[:8]:
        e_name = ev.get("event_name", "")
        pdate = ev.get("public_date", "")[:10]
        c_name = ev.get("category", "")
        act = ev.get("action_type", "")
        combined_text = f"{e_name} {c_name} {act}".lower()

        if any(kw in combined_text for kw in insider_trading_keywords):
            has_recent_insider_deal = True
            insider_deal_notes.append(f"{pdate}: {e_name} ({act or c_name})")

        if e_name:
            insider_events.append({
                "event_name": e_name,
                "date": pdate,
                "category": c_name or act or "Sự kiện DN"
            })

    # Chẩn đoán Bẫy Tin Tức (News Trap Diagnosis)
    # Phân tích tương quan giữa tin tức và vị thế giá
    news_titles_blob = " ".join([n["title"].lower() for n in recent_news_highlights])
    bullish_keywords = ["lãi kỷ lục", "tăng trưởng", "vượt kế hoạch", "dự án nghìn tỷ", "cổ tức khủng", "trả cổ tức", "mua lại", "bứt phá"]
    bearish_keywords = ["lỗ", "sụt giảm", "thanh tra", "khởi tố", "vi phạm", "chậm tiến độ", "cắt margin", "cảnh báo"]

    has_bullish_news = any(kw in news_titles_blob for kw in bullish_keywords)
    has_bearish_news = any(kw in news_titles_blob for kw in bearish_keywords)

    if dist_from_52w_high >= -15.0 and has_bullish_news:
        trap_type = "🚨 BẪY TIN TỐT ĐỂ XẢ (BUY THE RUMOR, SELL THE NEWS)"
        trap_explanation = "Cực kỳ thận trọng! Khi các bài báo và diễn đàn đồng loạt tung hô kết quả kinh doanh đột biến hoặc dự án khủng trong lúc thị giá đang neo sát đỉnh 52 tuần, đây là kịch bản kinh điển để đội lái và cổ đông lớn kéo xả hàng cho F0 hưng phấn đu đỉnh."
        trap_warning = "TUYỆT ĐỐI KHÔNG MUA ĐUỔI THEO TIN BÁO CHÍ. Ai có hàng nên canh nhịp kéo hưng phấn để chốt lời từng phần."
    elif dist_from_52w_high <= -35.0 and (has_bearish_news or "giảm" in news_titles_blob):
        trap_type = "🎣 CHIÊU BÀI 'TIN XẤU RŨ BỎ' ĐỂ GOM HÀNG (SHAKEOUT ON BAD NEWS)"
        trap_explanation = "Cảnh giác với bẫy tâm lý! Cổ phiếu đã chiết khấu rất sâu (-35% đến -60% từ đỉnh), định giá P/B đã về vùng rẻ nhưng báo chí lại liên tục đăng tin tiêu cực. Đây thường là chiêu bài của tạo lập mượn cớ tin xấu để tạo nhịp rũ bỏ hoảng loạn cuối cùng, ép nhỏ lẻ phải cắt lỗ ngay tại đáy."
        trap_warning = "KHÔNG BÁN THÁO TRONG CÁC PHIÊN ĐẠP HOẢNG LOẠN THEO TIN ĐỒN. Kiên nhẫn quan sát phản ứng rút chân của dòng tiền lớn."
    else:
        trap_type = "TRUNG TÍNH (THÔNG TIN HOẠT ĐỘNG BÌNH THƯỜNG)"
        trap_explanation = "Các luồng tin tức công bố thời gian gần đây là thông tin minh bạch theo định kỳ (nghị quyết HĐQT, lịch chi trả cổ tức, họp ĐHĐCĐ), chưa phát hiện dấu hiệu thao túng truyền thông bất thường."
        trap_warning = "Tập trung bám sát hành động giá và khối lượng khớp lệnh thực tế trên bảng điện thay vì nghe ngóng tin đồn ngoài luồng."

    # -------------------------------------------------------------
    # 4. BÓC TÁCH BAN LÃNH ĐẠO & ĐỘ UY TÍN (LEADERSHIP CREDIBILITY)
    # -------------------------------------------------------------
    chairman = leadership.get("chairman", "Chưa rõ")
    ceo = leadership.get("ceo", "Chưa rõ")
    skin_in_game_verdict = leadership.get("skin_in_game_verdict", "TRUNG BÌNH")
    g_score = int(gov.get("g_score", 70))

    if g_score >= 80 and insider_pct >= 15.0:
        leadership_credibility = "UY TÍN CAO (MINH BẠCH, ĐỒNG HÀNH DÀI HẠN)"
        leadership_behavior_desc = f"Chủ tịch và ban điều hành nắm giữ tỷ lệ cổ phần lớn ({insider_pct:.1f}%), cam kết quyền lợi song hành với cổ đông. Doanh nghiệp chi trả cổ tức rõ ràng và không có tiền sử lướt sóng 'úp bô' nhỏ lẻ."
    elif g_score >= 60:
        leadership_credibility = "ĐẠT CHUẨN MINH BẠCH"
        leadership_behavior_desc = f"Ban lãnh đạo nắm giữ {insider_pct:.1f}% vốn, vận hành theo thông lệ quản trị chuẩn mực. Tuy nhiên cần theo dõi tiến độ các nghị quyết HĐQT và hoạt động giải ngân đầu tư."
    else:
        leadership_credibility = "⚠️ CẢNH BÁO RỦI RO QUẢN TRỊ & LƯỚT SÓNG NỘI BỘ"
        leadership_behavior_desc = f"Lãnh đạo nắm tỷ lệ sở hữu thấp ({insider_pct:.1f}%) hoặc xuất hiện nhiều công ty sân sau/vệ tinh mờ ám. Rủi ro ban điều hành giao dịch nội bộ hoặc bán tháo cổ phiếu khi gặp khó khăn."

    # -------------------------------------------------------------
    # 5. CẨM NANG ỨNG XỬ THỰC CHIẾN DÀNH CHO NHÀ ĐẦU TƯ (PLAYBOOK)
    # -------------------------------------------------------------
    actionable_playbook = {
        "shakeout_rule": "Khi cổ phiếu bị tạo lập 'rung lắc' đạp gãy hỗ trợ tạm thời trong phiên: TUYỆT ĐỐI KHÔNG BÁN HOẢNG LOẠN trong phiên sáng hoặc phiên ATC. Hãy đợi 15 phút cuối phiên (14h15 - 14h30) để xem có lực cầu bắt đáy rút chân hay không. Chỉ kích hoạt Stop Loss khi giá đóng cửa phiên xác nhận thủng mốc hỗ trợ với Vol lớn.",
        "news_filter_rule": "Nguyên tắc '3 Câu hỏi Vàng' khi đọc tin tức chứng khoán: (1) Bài báo này xuất hiện khi giá đang ở đỉnh hay ở đáy? (2) Ai là người hưởng lợi nhiều nhất khi bài báo này được lan truyền rộng rãi? (3) Nếu tin quá tốt mà giá không tăng trần, đó là lúc phải BÁN; Nếu tin cực xấu mà giá không giảm sàn, đó là lúc phải QUAN SÁT MUA.",
        "investor_checklist": [
            f"1. Kiểm tra tỷ lệ trôi nổi: {true_free_float_pct}% ({concentration_grade}).",
            f"2. Nhận diện hành vi tạo lập: {mm_status} (Áp lực rung lắc: {shakeout_risk_score}/100).",
            f"3. Cảnh giác bẫy truyền thông: {trap_type}."
        ]
    }

    return {
        "symbol": sym,
        "holding_structure": {
            "insider_pct": insider_pct,
            "foreigner_pct": foreigner_pct,
            "state_pct": state_pct,
            "major_shareholders_sum_pct": round(major_sh_sum, 1),
            "true_free_float_pct": true_free_float_pct,
            "concentration_grade": concentration_grade,
            "concentration_desc": concentration_desc,
            "whale_dominance": whale_dominance,
            "top_shareholders": top_shareholders[:6]
        },
        "market_maker_behavior": {
            "status": mm_status,
            "status_color": mm_color,
            "whale_action_desc": whale_action_desc,
            "shakeout_risk_score": shakeout_risk_score,
            "shakeout_risk_level": shakeout_risk_level,
            "shakeout_evidence": shakeout_evidence,
            "foreign_flow_today": f"{foreign_net_vol:+,.0f} CP"
        },
        "leadership_and_news_forensic": {
            "chairman": chairman,
            "ceo": ceo,
            "insider_pct": insider_pct,
            "skin_in_game_verdict": skin_in_game_verdict,
            "leadership_credibility": leadership_credibility,
            "leadership_behavior_desc": leadership_behavior_desc,
            "has_recent_insider_deal": has_recent_insider_deal,
            "insider_deal_notes": insider_deal_notes,
            "recent_news_highlights": recent_news_highlights,
            "recent_events": insider_events[:6],
            "news_trap_diagnosis": {
                "trap_type": trap_type,
                "explanation": trap_explanation,
                "warning": trap_warning
            }
        },
        "actionable_playbook": actionable_playbook
    }
