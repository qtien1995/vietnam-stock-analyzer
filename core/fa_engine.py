from typing import Dict, Any, Optional
from config import FA_WEIGHTS, LEGAL_RISK_TICKERS
from core.segment_analyzer import analyze_company_segments
from core.governance_analyzer import analyze_governance_and_ownership
from core.data_loader import get_governance_data
from core.macro_engine import analyze_macro_and_sector_cycle, classify_sector


def get_sector(symbol: str, overview_data: Optional[Dict[str, Any]] = None) -> str:
    """Xác định ngành nghề đặc thù của cổ phiếu qua bộ lọc động toàn thị trường"""
    return classify_sector(symbol, overview_data)



def calculate_piotroski_score(fin: Dict[str, Any]) -> int:
    """
    Tính điểm Piotroski F-Score (0 - 9 điểm) đo lường sức khỏe tài chính.
    """
    score = 0
    ticker = fin.get("symbol", "").upper()
    sector = get_sector(ticker)

    # 1. Sinh lời: ROA dương
    roa = fin.get("roa") or 0.0
    if roa > 0:
        score += 1

    # 2. Sinh lời: ROE cao chứng tỏ hiệu quả vốn
    roe = fin.get("roe") or 0.0
    if roe > 10.0:
        score += 1

    # 3. Tăng trưởng lợi nhuận dương
    profit_growth = fin.get("profit_growth") or 0.0
    if profit_growth > 0:
        score += 1

    # 4. Tăng trưởng lợi nhuận vượt trội (> 15%)
    if profit_growth > 15.0:
        score += 1

    # 5. Đòn bẩy tài chính: Tỷ lệ Nợ / Vốn CSH an toàn (< 1.5)
    if sector == "BANK":
        score += 2 # Ngân hàng huy động tiền gửi là mô hình kinh doanh, tính đạt chuẩn
    else:
        debt_eq = fin.get("debt_to_equity") or 1.0
        if debt_eq < 0.9:
            score += 2
        elif debt_eq < 1.6:
            score += 1

    # 6. Biên lợi nhuận gộp lành mạnh (> 15%)
    gross_margin = fin.get("gross_margin") or 15.0
    if gross_margin > 15.0 or sector in ["BANK", "SECURITIES"]:
        score += 1

    # 7. Biên lợi nhuận ròng lành mạnh (> 8%)
    net_margin = fin.get("net_margin") or 8.0
    if net_margin > 8.0:
        score += 1

    # 8. Tăng trưởng doanh thu dương
    rev_growth = fin.get("revenue_growth") or 0.0
    if rev_growth > 8.0:
        score += 1

    return min(9, max(0, score))


def evaluate_buffett_moat(fin: Dict[str, Any], current_price: float) -> Dict[str, Any]:
    """
    Đánh giá doanh nghiệp theo phong cách Warren Buffett & Định giá theo từng ngành:
    - Ngân hàng / Chứng khoán: Trọng tâm P/B và ROE.
    - Công nghệ: P/E cao hơn chuẩn nhưng cảnh báo Multiple Contraction nếu > 24x.
    - Thép / Chu kỳ: Cảnh báo bẫy giá trị đỉnh lợi nhuận.
    - Sản xuất / Bán lẻ: P/E tham chiếu 14-16x.
    """
    ticker = fin.get("symbol", "").upper()
    sector = get_sector(ticker)
    roe = fin.get("roe") or 0.0
    debt_eq = fin.get("debt_to_equity") or 1.0
    
    eps_val = fin.get("eps")
    if eps_val and eps_val > 0:
        pe = round(current_price / eps_val, 2)
    elif fin.get("pe"):
        pe = fin.get("pe")
    else:
        pe = 15.0
        
    bvps_val = fin.get("bvps")
    if bvps_val and bvps_val > 0:
        pb = round(current_price / bvps_val, 2)
    elif fin.get("pb"):
        pb = fin.get("pb")
    else:
        pb = 1.5

    score = 0
    reasons = []
    valuation_warning = ""

    # 1. HIỆU QUẢ SINH LỜI (ROE BENCHMARK)
    if roe >= 18.0:
        score += 35
        reasons.append(f"ROE xuất sắc ({roe:.1f}%), thể hiện lợi thế cạnh tranh con hào kinh tế bền vững.")
    elif roe >= 14.0:
        score += 25
        reasons.append(f"ROE đạt chuẩn đầu tư ({roe:.1f}%).")
    else:
        score += 10
        reasons.append(f"ROE ({roe:.1f}%) chưa thực sự vượt trội theo tiêu chuẩn Buffett.")

    # 2. CẤU TRÚC VỐN & ĐÒN BẨY NỢ
    if sector == "BANK":
        score += 30
        reasons.append(f"Ngân hàng ({ticker}): Kinh doanh đòn bẩy tiền gửi đặc thù, miễn trừ tiêu chí Nợ/Vốn.")
    elif sector == "SECURITIES":
        score += 25
        reasons.append(f"Chứng khoán ({ticker}): Đòn bẩy nợ margin {debt_eq:.2f}x trong ngưỡng kiểm soát.")
    else:
        if debt_eq <= 0.8:
            score += 30
            reasons.append(f"Cấu trúc tài chính rất an toàn, nợ/vốn chỉ {debt_eq:.2f}x.")
        elif debt_eq <= 1.5:
            score += 20
            reasons.append(f"Nợ vay ở mức kiểm soát được ({debt_eq:.2f}x).")
        else:
            score += 5
            reasons.append(f"Đòn bẩy nợ cao ({debt_eq:.2f}x), rủi ro chi phí lãi vay khi thị trường biến động.")

    # 3. ĐỊNH GIÁ ĐẶC THÙ THEO NGÀNH (FAIR VALUE & MARGIN OF SAFETY)
    if sector == "BANK":
        # Ngân hàng: Dùng P/B chuẩn ngành (1.35x)
        fair_pb = 1.35
        fair_price = current_price * (fair_pb / pb) if pb > 0 else current_price
        if pb <= 1.2:
            score += 35
            reasons.append(f"Định giá ngân hàng hấp dẫn với P/B {pb:.2f}x (tham chiếu ngành {fair_pb}x).")
        elif pb <= 1.5:
            score += 25
            reasons.append(f"Định giá ngân hàng ở mức hợp lý với P/B {pb:.2f}x.")
        else:
            score += 10
            valuation_warning = f"P/B ({pb:.2f}x) cao hơn mặt bằng chung ngân hàng"
            reasons.append(f"P/B {pb:.2f}x tương đối cao so với trung bình ngành ngân hàng.")

    elif sector == "SECURITIES":
        # Chứng khoán: Dùng P/B tham chiếu ngành (1.50x)
        fair_pb = 1.50
        fair_price = current_price * (fair_pb / pb) if pb > 0 else current_price
        if pb <= 1.3:
            score += 35
            reasons.append(f"Định giá ngành chứng khoán rẻ với P/B {pb:.2f}x (P/E {pe:.1f}x).")
        elif pb <= 1.7:
            score += 25
            reasons.append(f"Định giá chứng khoán hợp lý với P/B {pb:.2f}x.")
        else:
            score += 10
            valuation_warning = f"P/B ({pb:.2f}x) đã phản ánh trọn vẹn sóng tăng"
            reasons.append(f"P/B {pb:.2f}x ở vùng cao của chu kỳ chứng khoán.")

    elif sector == "TECH":
        # Công nghệ (FPT, CMG): Cho phép P/E cao hơn (19.0x) vì tăng trưởng dài hạn
        fair_pe = 19.0
        fair_price = current_price * (fair_pe / pe) if pe > 0 else current_price
        if pe <= 15.0:
            score += 35
            reasons.append(f"Cổ phiếu công nghệ định giá rất hời với P/E {pe:.1f}x.")
        elif pe <= 22.0:
            score += 25
            reasons.append(f"Định giá công nghệ hợp lý với P/E {pe:.1f}x (tham chiếu 19x).")
        else:
            # Nguy cơ Multiple Contraction (như bài học FPT khi P/E > 25x)
            score += 5
            valuation_warning = f"Nguy cơ Multiple Contraction: P/E ({pe:.1f}x) đã ứng trước kỳ vọng tăng trưởng 2-3 năm tới"
            reasons.append(f"Cảnh báo: P/E {pe:.1f}x quá cao! Thị giá đã phản ánh trước kỳ vọng tăng trưởng dài hạn, rủi ro điều chỉnh de-rating lớn.")

    elif sector == "STEEL_CYCLICAL":
        # Thép / Hóa chất: P/E tham chiếu 8.5x
        fair_pe = 8.5
        fair_price = current_price * (fair_pe / pe) if pe > 0 else current_price
        if pe <= 7.0 and roe >= 15.0:
            score += 35
            reasons.append(f"Cổ phiếu chu kỳ định giá hấp dẫn với P/E {pe:.1f}x.")
        elif pe <= 11.0:
            score += 25
            reasons.append(f"Định giá chu kỳ hợp lý với P/E {pe:.1f}x.")
        else:
            score += 10
            reasons.append(f"P/E {pe:.1f}x phản ánh lợi nhuận đang ở vùng trũng chu kỳ hoặc thị giá cao.")

    else:
        # Ngành thông thường / Bán lẻ / Sản xuất
        fair_pe = 14.5
        fair_price = current_price * (fair_pe / pe) if pe > 0 else current_price
        if pe <= 11.0:
            score += 35
            reasons.append(f"Thị giá rất hấp dẫn với P/E {pe:.1f}x.")
        elif pe <= 16.0:
            score += 25
            reasons.append(f"Định giá hợp lý với P/E {pe:.1f}x.")
        else:
            score += 10
            valuation_warning = f"P/E ({pe:.1f}x) cao hơn trung bình thị trường"
            reasons.append(f"P/E {pe:.1f}x hơi cao, biên an toàn giá chưa đủ rộng.")

    margin_of_safety = round(((fair_price - current_price) / fair_price) * 100, 1) if fair_price > 0 else 0.0

    verdict = "MUA TÍCH SẢN" if score >= 75 else ("QUAN SÁT CHỜ CHIẾT KHẤU" if score >= 50 else "TRÁNH XA")

    return {
        "score": score,
        "sector": sector,
        "verdict": verdict,
        "fair_price": round(fair_price, 0),
        "margin_of_safety_pct": margin_of_safety,
        "valuation_warning": valuation_warning,
        "reasons": reasons
    }


def evaluate_growth_and_earnings_quality(fin: Dict[str, Any]) -> Dict[str, Any]:
    """
    Phân tích chất lượng tăng trưởng & Bóc tách Doanh thu vs Lợi nhuận:
    - Kiểm tra xem lợi nhuận đến từ hoạt động cốt lõi (Core Business) hay thu nhập tài chính/bất thường.
    """
    profit_growth = fin.get("profit_growth")
    revenue_growth = fin.get("revenue_growth")
    
    reasons = []
    quality = "Bình thường"
    growth_score = 50

    if profit_growth is not None and revenue_growth is not None:
        if profit_growth > 25.0 and revenue_growth < 5.0:
            quality = "Chất lượng lợi nhuận cần lưu ý (Lợi nhuận đi trước doanh thu)"
            reasons.append(f"Lợi nhuận tăng mạnh ({profit_growth:+.1f}%) nhưng doanh thu chỉ tăng {revenue_growth:+.1f}%, cần kiểm tra có phải từ thu nhập tài chính hoặc bán tài sản một lần.")
            growth_score = 60
        elif profit_growth > 15.0 and revenue_growth > 15.0:
            quality = "Tăng trưởng cốt lõi rất mạnh (Core Business Growth)"
            reasons.append(f"Cả Doanh thu ({revenue_growth:+.1f}%) và Lợi nhuận ({profit_growth:+.1f}%) cùng tăng trưởng 2 chữ số, hoạt động kinh doanh cốt lõi rất mở rộng.")
            growth_score = 90
        elif profit_growth <= 0 and revenue_growth <= 0:
            quality = "Kinh doanh đang suy giảm (Declining)"
            reasons.append(f"Cả Doanh thu ({revenue_growth:+.1f}%) và Lợi nhuận ({profit_growth:+.1f}%) đều sụt giảm trong kỳ báo cáo gần nhất.")
            growth_score = 25
        elif profit_growth > 0:
            quality = "Tăng trưởng ổn định"
            reasons.append(f"Lợi nhuận duy trì đà tăng trưởng dương ({profit_growth:+.1f}%).")
            growth_score = 70
        else:
            quality = "Lợi nhuận suy giảm"
            reasons.append(f"Lợi nhuận sụt giảm ({profit_growth:+.1f}%), cần theo dõi kỳ BCTC tiếp theo.")
            growth_score = 30
    else:
        reasons.append("Thiếu dữ liệu so sánh tăng trưởng doanh thu/lợi nhuận theo quý.")

    return {
        "quality": quality,
        "growth_score": growth_score,
        "reasons": reasons
    }


def evaluate_peter_lynch(fin: Dict[str, Any], current_price: float) -> Dict[str, Any]:
    """
    Đánh giá theo phong cách Peter Lynch (GARP - Growth at a Reasonable Price):
    - Hệ số PEG (P/E chia cho Tốc độ tăng trưởng)
    """
    eps_val = fin.get("eps")
    if eps_val and eps_val > 0:
        pe = round(current_price / eps_val, 2)
    elif fin.get("pe"):
        pe = fin.get("pe")
    else:
        pe = 15.0
        
    growth = fin.get("profit_growth") if fin.get("profit_growth") is not None else (fin.get("revenue_growth") or 15.0)
    
    # Tính PEG
    peg = round(pe / growth, 2) if growth > 0 else 99.9

    score = 0
    reasons = []

    if growth <= 0:
        score = 15
        category = "Cổ phiếu Lợi nhuận đi lùi (Declining)"
        reasons.append(f"Tăng trưởng âm hoặc bằng 0 ({growth:+.1f}%), loại khỏi tiêu chí mua tăng trưởng PEG.")
    elif peg <= 0.7:
        score = 90
        category = "Cổ phiếu Tăng trưởng giá rẻ (Fast Grower Undervalued)"
        reasons.append(f"Chỉ số PEG cực kỳ hấp dẫn ({peg} <= 0.7) với tốc độ tăng trưởng {growth:.1f}%.")
    elif peg <= 1.0:
        score = 75
        category = "Cổ phiếu Tăng trưởng giá hợp lý (GARP)"
        reasons.append(f"Chỉ số PEG đạt chuẩn xuất sắc ({peg} <= 1.0).")
    elif peg <= 1.5:
        score = 55
        category = "Cổ phiếu Tăng trưởng trung bình (Stalwart)"
        reasons.append(f"PEG ở mức chấp nhận được ({peg}).")
    else:
        score = 30
        category = "Cổ phiếu Định giá quá cao (Overvalued)"
        reasons.append(f"PEG cao ({peg}), giá cổ phiếu đang chạy nhanh hơn tốc độ tăng trưởng thực tế.")

    verdict = "MUA TĂNG TRƯỞNG" if score >= 70 else ("THEO DÕI" if score >= 50 else "ĐẮT QUÁ MỨC")

    return {
        "score": score,
        "peg": peg,
        "category": category,
        "verdict": verdict,
        "reasons": reasons
    }


def evaluate_asset_based_valuation(fin: Dict[str, Any], current_price: float) -> Dict[str, Any]:
    """
    Định giá cổ phiếu dựa trên Khối tài sản hiện có & Radar Phát hiện Thao túng / Thổi giá ảo:
    1. Định giá theo tài sản thực tế:
       - BVPS (Book Value Per Share): Vốn chủ sở hữu / Số CP lưu hành.
       - TBVPS (Tangible Book Value Per Share): Vốn chủ - Tài sản vô hình.
       - NCAVPS (Net-Net Graham): (Tài sản ngắn hạn - Nợ phải trả) / Số CP.
       - Net Cash/Share: (Tiền mặt & ĐTTC ngắn hạn - Nợ vay) / Số CP.
       - P/B thực tế = Thị giá / BVPS.
       - Mức chiết khấu / thặng dư so với tài sản ròng (% Discount/Premium).
    
    2. Radar Cảnh báo Thao túng / Thổi giá ảo (Manipulation & Speculation Radar):
       - MỨC 1: MÓN HỜI TÀI SẢN (ASSET DISCOUNT) - P/B < 1.0x, rủi ro thổi giá: RẤT THẤP.
       - MỨC 2: ĐỊNH GIÁ HỢP LÝ (FAIR VALUE) - P/B 1.0x - 2.2x kèm ROE >= 10%.
       - MỨC 3: ĐỊNH GIÁ CAO (VALUATION PREMIUM) - P/B 2.2x - 3.8x.
       - MỨC 4: BONG BÓNG ĐẦU CƠ (SPECULATIVE BUBBLE) - P/B > 3.8x nhưng ROE < 10% hoặc EPS âm.
       - MỨC 5: BÁO ĐỘNG ĐỎ - NGUY CƠ THAO TÚNG / THỔI GIÁ (HIGH MANIPULATION) - P/B > 5.0x - 10.0x kèm ROE < 5% hoặc lỗ triền miên.

    3. Kiểm định Chất lượng Tài sản (Asset Quality Audit):
       - Bộ đệm tiền mặt (Cash Buffer): Tiền mặt / Tổng tài sản.
       - Tỷ lệ tài sản đọng vốn (Illiquid Assets): (Phải thu + Tồn kho) / Tổng tài sản.
    """
    bvps = fin.get("bvps") or 0.0
    tbvps = fin.get("tbvps") or bvps
    ncavps = fin.get("ncavps") or 0.0
    shares = fin.get("issue_share") or 0.0
    cash = fin.get("cash") or 0.0
    total_debt = fin.get("total_debt") or 0.0
    total_assets = fin.get("total_assets") or 0.0
    receivables = fin.get("receivables") or 0.0
    inventories = fin.get("inventories") or 0.0
    roe = fin.get("roe") or 0.0

    pb = round(current_price / bvps, 2) if bvps > 0 else (fin.get("pb") or round(current_price / 10000.0, 2))
    net_cash_per_share = round((cash - total_debt) / shares, 0) if shares > 0 else 0.0
    asset_discount_pct = round(((bvps - current_price) / bvps) * 100, 1) if bvps > 0 else 0.0

    # Đánh giá chất lượng tài sản
    illiquid_ratio = round(((receivables + inventories) / total_assets) * 100, 1) if total_assets > 0 else 0.0
    cash_ratio = round((cash / total_assets) * 100, 1) if total_assets > 0 else 0.0

    asset_quality_verdict = "Lành mạnh"
    asset_quality_notes = []
    if cash_ratio >= 10.0:
        asset_quality_notes.append(f"Bộ đệm tiền mặt an toàn ({cash_ratio:.1f}% tổng tài sản, ~{cash:,.0f} VND).")
    elif cash_ratio < 3.0 and total_assets > 0:
        asset_quality_notes.append(f"Cảnh báo: Tỷ lệ tiền mặt rất mỏng ({cash_ratio:.1f}% tổng tài sản), rủi ro căng thẳng thanh khoản ngắn hạn.")
    else:
        asset_quality_notes.append(f"Dự trữ tiền mặt ở mức bình thường ({cash_ratio:.1f}% tổng tài sản).")

    if illiquid_ratio > 65.0:
        asset_quality_verdict = "Rủi ro đọng vốn cao (Tồn kho & Phải thu lớn)"
        asset_quality_notes.append(f"Cảnh báo tài sản: Phải thu và Tồn kho chiếm {illiquid_ratio:.1f}% tổng tài sản, rủi ro nợ xấu hoặc dòng tiền bị chôn chặt.")
    elif illiquid_ratio > 40.0:
        asset_quality_notes.append(f"Phải thu và Tồn kho chiếm {illiquid_ratio:.1f}% tổng tài sản (đặc thù nhóm xây lắp / hạ tầng / BĐS).")

    # Radar Thao túng & Thổi giá ảo
    manipulation_risk_level = 1
    manipulation_verdict = "AN TOÀN / MÓN HỜI TÀI SẢN"
    manipulation_warning = ""
    reasons = []

    real_asset_ratio = round(bvps / current_price, 2) if current_price > 0 else (round(1.0 / pb, 2) if pb > 0 else 1.0)
    debt_to_cash = round(total_debt / cash, 1) if cash > 0 else (99.0 if total_debt > 0 else 0.0)
    receivables_ratio = round((receivables / total_assets) * 100, 1) if total_assets > 0 else 0.0

    # Phân biệt MÓN HỜI TÀI SẢN THẬT vs BẪY GIÁ TRỊ (VALUE TRAP)
    # Nếu P/B < 1.0x nhưng tài sản đọng vốn lớn (illiquid > 38%), nợ vay ngập đầu hoặc tiền mặt mỏng
    sym_code = fin.get("symbol", "").upper().strip()
    is_value_trap = (
        (pb < 1.0 and bvps > 0) and
        (
            illiquid_ratio > 38.0 or 
            debt_to_cash > 4.5 or
            receivables_ratio > 30.0 or
            sym_code in LEGAL_RISK_TICKERS
        )
    )

    if is_value_trap:
        manipulation_risk_level = 4
        manipulation_verdict = "CẢNH BÁO BẪY GIÁ TRỊ & TÀI SẢN TRÊN GIẤY TỜ (VALUE TRAP)"
        manipulation_warning = f"P/B {pb:.2f}x rẻ ảo: Tài sản đọng vốn {illiquid_ratio:.1f}%, nợ vay gấp {debt_to_cash:.1f}x tiền mặt, nguy cơ bẫy giá trị!"
        reasons.append(f"⚠️ CẢNH BÁO BẪY GIÁ TRỊ: Thị giá ({current_price:,.0f} đ) thấp hơn sổ sách (BVPS {bvps:,.0f} đ, P/B {pb:.2f}x) nhưng tài sản ròng tiềm ẩn rủi ro lớn.")
        reasons.append(f"Chất lượng tài sản kém: Các khoản phải thu & Tồn kho chiếm {illiquid_ratio:.1f}% tổng tài sản, nợ vay ({total_debt:,.0f} đ) gấp {debt_to_cash:.1f}x tiền mặt.")
        reasons.append("Tài sản thực khó chuyển đổi thành tiền để bảo vệ cổ đông; nguy cơ trích lập dự phòng bào mòn vốn chủ sở hữu.")
    elif pb < 1.0 and bvps > 0:
        manipulation_risk_level = 1
        manipulation_verdict = "MÓN HỜI TÀI SẢN THỰC CHẤT (ASSET DISCOUNT)"
        reasons.append(f"Thị giá ({current_price:,.0f} đ) thấp hơn giá trị sổ sách tài sản ròng (BVPS: {bvps:,.0f} đ).")
        reasons.append(f"Chiết khấu {asset_discount_pct:.1f}% so với vốn chủ sở hữu. Mua 1 đồng cổ phiếu nhận về {real_asset_ratio} đồng tài sản thực.")
        reasons.append("Rủi ro bị thổi giá ảo: RẤT THẤP. Tài sản thực đóng vai trò 'đệm chống đỡ' bảo vệ giá vốn.")
    elif pb <= 2.2:
        manipulation_risk_level = 2
        manipulation_verdict = "ĐỊNH GIÁ HỢP LÝ (FAIR VALUE)"
        reasons.append(f"Hệ số P/B ở mức {pb:.2f}x, tương xứng với hiệu quả sinh lời trên tài sản (ROE {roe:.1f}%).")
        reasons.append("Thị giá phản ánh đúng quy mô tài sản và không có dấu hiệu bị bơm thổi bất thường.")
    elif pb <= 3.8:
        manipulation_risk_level = 3
        manipulation_verdict = "ĐỊNH GIÁ CAO (VALUATION PREMIUM)"
        if roe >= 18.0:
            reasons.append(f"P/B ở mức cao ({pb:.2f}x) nhưng được bảo chứng bởi ROE xuất sắc ({roe:.1f}%).")
        else:
            reasons.append(f"P/B {pb:.2f}x tương đối đắt so với khối tài sản hiện có, cần tăng trưởng đột biến để duy trì thị giá.")
    elif pb <= 6.0:
        manipulation_risk_level = 4
        manipulation_verdict = "CẢNH BÁO BONG BÓNG ĐẦU CƠ (SPECULATIVE BUBBLE)"
        manipulation_warning = f"Thị giá gấp {pb:.1f} lần tài sản thực trong khi ROE chỉ {roe:.1f}%"
        reasons.append(f"⚠️ CẢNH BÁO BONG BÓNG: Thị giá ({current_price:,.0f} đ) cao gấp {pb:.1f}x lần giá trị tài sản thực tế ({bvps:,.0f} đ).")
        reasons.append("Năng lực sinh lời không tương xứng với thị giá, cổ phiếu có tính chất đầu cơ theo dòng tiền nóng.")
    else:
        manipulation_risk_level = 5
        manipulation_verdict = "BÁO ĐỘNG ĐỎ - NGUY CƠ THAO TÚNG / THỔI GIÁ (HIGH MANIPULATION)"
        manipulation_warning = f"BÁO ĐỘNG ĐỎ: Thị giá bị thổi phồng gấp {pb:.1f}x lần tài sản thực!"
        reasons.append(f"🚨 BÁO ĐỘNG ĐỎ: P/B lên tới {pb:.1f}x! Thị giá hoàn toàn tách rời khỏi nền tảng tài sản thực tế.")
        reasons.append("Dấu hiệu điển hình của việc thao túng giá, đội lái bơm thổi tạo thanh khoản ảo.")
        reasons.append("Tuyệt đối không giải ngân theo đám đông, rủi ro sụp đổ giá và chia đôi tài khoản rất cao.")

    return {
        "bvps": bvps,
        "tbvps": tbvps,
        "ncavps": ncavps,
        "pb": pb,
        "net_cash_per_share": net_cash_per_share,
        "asset_discount_pct": asset_discount_pct,
        "manipulation_risk_level": manipulation_risk_level,
        "manipulation_verdict": manipulation_verdict,
        "manipulation_warning": manipulation_warning,
        "asset_quality_verdict": asset_quality_verdict,
        "asset_quality_notes": asset_quality_notes,
        "illiquid_ratio": illiquid_ratio,
        "cash_ratio": cash_ratio,
        "reasons": reasons
    }


def evaluate_cash_flow_and_forensic(fin: Dict[str, Any]) -> Dict[str, Any]:
    """
    Bóc tách Báo cáo Lưu chuyển Tiền tệ (Cash Flow Statement), 
    Chất lượng Lợi nhuận (Earnings Quality) và Mô hình Cảnh báo Kiệt quệ Tài chính Altman Z''-Score:
    1. Dòng tiền thuần từ HĐKD (CFO TTM) vs Lợi nhuận sau thuế (LNST TTM).
    2. Chi tiêu vốn (CapEx TTM) & Dòng tiền tự do (FCF TTM = CFO - CapEx).
    3. Tỷ lệ Chất lượng Lợi nhuận = CFO / LNST.
    4. Mô hình Altman Z''-Score cho thị trường mới nổi:
       Z'' = 6.56*X1 + 3.26*X2 + 6.72*X3 + 1.05*X4
    5. Rà soát Cờ đỏ kế toán (Forensic Accounting Red Flags).
    """
    cfo_ttm = fin.get("cfo_ttm") or 0.0
    capex_ttm = fin.get("capex_ttm") or 0.0
    fcf_ttm = fin.get("fcf_ttm") or (cfo_ttm - capex_ttm)
    cfi_ttm = fin.get("cfi_ttm") or 0.0
    cff_ttm = fin.get("cff_ttm") or 0.0
    ttm_profit = fin.get("ttm_profit") or 0.0
    total_assets = fin.get("total_assets") or 0.0
    total_debt = fin.get("total_debt") or 0.0
    owners_equity = fin.get("owners_equity") or 0.0
    retained_earnings = fin.get("retained_earnings") or 0.0
    working_capital = fin.get("working_capital") or (fin.get("current_assets", 0.0) - (fin.get("short_term_liabilities") or total_debt * 0.6))
    ebit_ttm = fin.get("ebit_ttm") or (ttm_profit * 1.25)
    quarterly_cf = fin.get("quarterly_cash_flows", [])

    red_flags = []
    
    # 1. Đánh giá chất lượng lợi nhuận (CFO vs Net Profit)
    earnings_quality_ratio = 1.0
    if ttm_profit > 0:
        earnings_quality_ratio = round(cfo_ttm / ttm_profit, 2)
        if earnings_quality_ratio >= 1.0:
            quality_grade = "A"
            quality_verdict = "XUẤT SẮC (DÒNG TIỀN THẬT DỒI DÀO)"
            quality_desc = f"CFO ({cfo_ttm:,.0f} đ) vượt trội so với LNST ({ttm_profit:,.0f} đ) - Tỷ lệ {earnings_quality_ratio:.2f}x. Tiền mặt thực thu lớn hơn lợi nhuận kế toán."
        elif earnings_quality_ratio >= 0.7:
            quality_grade = "B"
            quality_verdict = "LÀNH MẠNH (ĐẠT CHUẨN)"
            quality_desc = f"CFO ({cfo_ttm:,.0f} đ) tương đương LNST ({ttm_profit:,.0f} đ) - Tỷ lệ {earnings_quality_ratio:.2f}x. Vòng quay tiền mặt ổn định."
        elif earnings_quality_ratio >= 0.2:
            quality_grade = "C"
            quality_verdict = "TRUNG BÌNH - NGUY CƠ ĐỌNG VỐN"
            quality_desc = f"CFO ({cfo_ttm:,.0f} đ) thấp hơn nhiều so với LNST ({ttm_profit:,.0f} đ) - Tỷ lệ chỉ {earnings_quality_ratio:.2f}x. Lợi nhuận bị chiếm dụng vốn qua công nợ."
            red_flags.append(f"CFO thấp hơn nhiều so với LNST (Tỷ lệ {earnings_quality_ratio:.2f}x), tiền bị giam ở công nợ hoặc hàng tồn kho.")
        else:
            quality_grade = "D"
            quality_verdict = "BÁO ĐỘNG ĐỎ: LỢI NHUẬN TRÊN GIẤY!"
            quality_desc = f"CFO âm hoặc gần bằng 0 ({cfo_ttm:,.0f} đ) trong khi LNST dương ({ttm_profit:,.0f} đ). Doanh nghiệp báo lãi nhưng thực chất không thu được tiền mặt về!"
            red_flags.append("🚨 BÁO ĐỘNG ĐỎ DÒNG TIỀN: CFO âm nặng trong khi LNST dương. Nguy cơ lợi nhuận ảo trên sổ sách kế toán!")
    else:
        quality_grade = "D" if cfo_ttm < 0 else "C"
        quality_verdict = "DOANH NGHIỆP ĐANG LỖ HOẶC THÂM HỤT TIỀN"
        quality_desc = f"LNST âm ({ttm_profit:,.0f} đ), CFO ghi nhận {cfo_ttm:,.0f} đ."
        if cfo_ttm < 0:
            red_flags.append("Cả CFO và LNST đều âm, doanh nghiệp đang đốt tiền mặt trong hoạt động kinh doanh.")

    # Kiểm tra FCF
    if fcf_ttm > 0:
        fcf_verdict = f"Dương lớn ({fcf_ttm:,.0f} đ). Doanh nghiệp tự chủ tài chính hoàn toàn sau khi đầu tư mở rộng CapEx."
    else:
        fcf_verdict = f"Âm ({fcf_ttm:,.0f} đ). Nhu cầu vốn đầu tư CapEx ({capex_ttm:,.0f} đ) vượt quá dòng tiền kinh doanh tạo ra, cần vay nợ tài trợ."
        if capex_ttm > 0 and abs(fcf_ttm) > owners_equity * 0.3:
            red_flags.append("CapEx mở rộng vượt quá khả năng tạo tiền từ CFO, gia tăng áp lực nợ vay hoặc phát hành tăng vốn.")

    # 2. TÍNH TOÁN ALTMAN Z''-SCORE (EMERGING MARKETS)
    altman_z = 0.0
    z_zone = "SAFE"
    z_verdict = "AN TOÀN TÀI CHÍNH (SAFE ZONE)"
    if total_assets > 0:
        x1 = working_capital / total_assets
        x2 = retained_earnings / total_assets
        x3 = ebit_ttm / total_assets
        tot_liab = total_assets - owners_equity if total_assets > owners_equity else total_debt
        x4 = (owners_equity / tot_liab) if tot_liab > 0 else 3.0

        altman_z = round(6.56 * x1 + 3.26 * x2 + 6.72 * x3 + 1.05 * x4, 2)

        if altman_z >= 2.60:
            z_zone = "SAFE"
            z_verdict = "VÙNG AN TOÀN CAO (SAFE ZONE)"
            z_desc = f"Chỉ số Altman Z''-Score đạt {altman_z:.2f} (> 2.60). Xác suất phá sản / kiệt quệ tài chính trong 2 năm tới là cực thấp."
        elif altman_z >= 1.10:
            z_zone = "GREY"
            z_verdict = "VÙNG XÁM CẢNH BÁO (GREY ZONE)"
            z_desc = f"Chỉ số Altman Z''-Score đạt {altman_z:.2f} (trong ngưỡng 1.10 - 2.60). Sức khỏe tài chính trung bình, cần giám sát chặt chẽ áp lực trả nợ ngắn hạn."
        else:
            z_zone = "DISTRESS"
            z_verdict = "VÙNG NGUY HIỂM KIỆT QUỆ TÀI CHÍNH (DISTRESS ZONE)"
            z_desc = f"Chỉ số Altman Z''-Score rớt xuống {altman_z:.2f} (< 1.10). BÁO ĐỘNG ĐỎ: Doanh nghiệp có cấu trúc vốn rất yếu, nguy cơ mất khả năng thanh toán nợ vay cao!"
            red_flags.append(f"🚨 Altman Z''-Score ở mức báo động {altman_z:.2f} (< 1.10), cảnh báo rủi ro kiệt quệ tài chính nghiêm trọng.")
    else:
        z_desc = "Không đủ dữ liệu tài sản để tính Altman Z''-Score."

    return {
        "cfo_ttm": cfo_ttm,
        "capex_ttm": capex_ttm,
        "fcf_ttm": fcf_ttm,
        "cfi_ttm": cfi_ttm,
        "cff_ttm": cff_ttm,
        "earnings_quality_ratio": earnings_quality_ratio,
        "quality_grade": quality_grade,
        "quality_verdict": quality_verdict,
        "quality_desc": quality_desc,
        "fcf_verdict": fcf_verdict,
        "altman_z": altman_z,
        "z_zone": z_zone,
        "z_verdict": z_verdict,
        "z_desc": z_desc,
        "red_flags": red_flags,
        "quarterly_cash_flows": quarterly_cf,
        "ttm_profit": ttm_profit
    }


def analyze_fundamentals(fin: Dict[str, Any], current_price: float, quote: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Tổng hợp toàn bộ phân tích cơ bản (FA) đa chiều theo chu trình Top-Down:
    1. Vĩ mô & Ma trận Chu kỳ ngành (Macro & Sector Cycle)
    2. Bóc tách Báo cáo Lưu chuyển Tiền tệ & Dòng tiền Thật (Cash Flow Forensic)
    3. Mô hình Cảnh báo Kiệt quệ Tài chính Altman Z''-Score
    4. Piotroski F-Score (Sức khỏe bảng cân đối)
    5. Warren Buffett (Moat & Định giá theo ngành)
    6. Định giá theo Khối tài sản & Radar Thao túng giá ảo / Bẫy giá trị
    7. Peter Lynch (GARP & PEG)
    8. Bóc tách Mô hình kinh doanh cốt lõi (Core Business Segments)
    9. Bóc tách Quản trị, Cơ cấu Cổ đông & Radar Tăng vốn ảo (G-Score)
    """
    symbol = fin.get("symbol", "").upper().strip()
    f_score = calculate_piotroski_score(fin)
    buffett = evaluate_buffett_moat(fin, current_price)
    lynch = evaluate_peter_lynch(fin, current_price)
    growth_quality = evaluate_growth_and_earnings_quality(fin)
    asset_valuation = evaluate_asset_based_valuation(fin, current_price)
    cash_flow = evaluate_cash_flow_and_forensic(fin)

    # 1. Phân tích Vĩ mô & Chu kỳ Ngành (Macro & Sector Cycle)
    macro_analysis = analyze_macro_and_sector_cycle(symbol, fin.get("overview"))

    # 2. Phân tích Mảng kinh doanh cốt lõi (Segments)
    company_name = quote.get("company_name", "") if quote else ""
    segments = analyze_company_segments(
        symbol,
        company_name=company_name,
        sector=macro_analysis.get("sector_key", buffett.get("sector", "GENERAL"))
    )

    # 3. Phân tích Quản trị Doanh nghiệp & Cổ đông (Governance & Shell Radar)
    gov_data = get_governance_data(symbol)
    governance = analyze_governance_and_ownership(
        symbol,
        gov_data,
        fin,
        current_price,
        quote
    )

    # Chấm điểm tổng hợp FA (thang 100)
    asset_score = 50
    if asset_valuation["manipulation_risk_level"] == 1:
        asset_score = 90
    elif asset_valuation["manipulation_risk_level"] == 2:
        asset_score = 75
    elif asset_valuation["manipulation_risk_level"] == 3:
        asset_score = 50
    elif asset_valuation["manipulation_risk_level"] == 4:
        asset_score = 20
    else:
        asset_score = 10

    g_score_val = governance.get("g_score", 60)
    macro_tailwind = macro_analysis.get("tailwind_score", 70)

    # Cấu trúc trọng số FA hoàn thiện:
    # 15% Macro, 15% F-Score, 15% Buffett Moat, 15% Định giá Tài sản, 15% Dòng tiền CFO/Altman, 10% Lynch, 15% Quản trị G-Score
    cf_score = 85 if cash_flow["quality_grade"] == "A" else (70 if cash_flow["quality_grade"] == "B" else (40 if cash_flow["quality_grade"] == "C" else 15))
    if cash_flow["z_zone"] == "SAFE":
        cf_score = min(100, cf_score + 10)
    elif cash_flow["z_zone"] == "DISTRESS":
        cf_score = max(5, cf_score - 25)

    raw_fa_score = (
        macro_tailwind * FA_WEIGHTS.get("macro", 0.15) +
        (f_score / 9.0 * 100) * FA_WEIGHTS.get("f_score", 0.15) +
        buffett["score"] * FA_WEIGHTS.get("buffett", 0.15) +
        asset_score * FA_WEIGHTS.get("asset_valuation", 0.15) +
        cf_score * FA_WEIGHTS.get("cash_flow", 0.15) +
        lynch["score"] * FA_WEIGHTS.get("lynch", 0.10) +
        g_score_val * FA_WEIGHTS.get("governance", 0.15)
    )

    # Nếu có cảnh báo thổi giá / bẫy giá trị hoặc Rủi ro Quản trị / Dòng tiền ảo, phạt điểm nặng
    valuation_warning = buffett.get("valuation_warning", "")
    if asset_valuation.get("manipulation_warning"):
        valuation_warning = (valuation_warning + " | " if valuation_warning else "") + asset_valuation["manipulation_warning"]

    # Phạt rủi ro dòng tiền và kiệt quệ tài chính
    if cash_flow["quality_grade"] == "D":
        raw_fa_score = max(5, raw_fa_score - 25)
        valuation_warning = (valuation_warning + " | " if valuation_warning else "") + "Cảnh báo Lợi nhuận trên giấy (CFO âm)"
    if cash_flow["z_zone"] == "DISTRESS":
        raw_fa_score = max(5, raw_fa_score - 20)
        valuation_warning = (valuation_warning + " | " if valuation_warning else "") + "Cảnh báo Rủi ro Kiệt quệ Tài chính (Altman Z < 1.1)"

    # Phạt rủi ro quản trị nghiêm trọng hoặc tăng vốn ảo
    if governance.get("subsidiary_web", {}).get("circular_capital_risk_level", 1) >= 4:
        raw_fa_score = max(5, raw_fa_score - 30)
    elif g_score_val < 40:
        raw_fa_score = max(5, raw_fa_score - 25)
    elif asset_valuation["manipulation_risk_level"] >= 4:
        raw_fa_score = max(5, raw_fa_score - 20)
    elif valuation_warning:
        raw_fa_score = max(10, raw_fa_score - 10)

    fa_total_score = int(min(100, max(0, raw_fa_score)))

    return {
        "sector": macro_analysis.get("sector_key", buffett.get("sector", "GENERAL")),
        "sector_name": macro_analysis.get("sector_name", "Doanh nghiệp"),
        "f_score": f_score,
        "fa_total_score": fa_total_score,
        "macro": macro_analysis,
        "cash_flow": cash_flow,
        "buffett": buffett,
        "lynch": lynch,
        "growth_quality": growth_quality,
        "asset_valuation": asset_valuation,
        "segments": segments,
        "governance": governance,
        "valuation_warning": valuation_warning,
        "ratios": fin
    }


