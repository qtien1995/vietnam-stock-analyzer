from typing import Dict, Any, Optional
from core.segment_analyzer import analyze_company_segments
from core.governance_analyzer import analyze_governance_and_ownership
from core.data_loader import get_governance_data

SECTOR_MAPPING = {
    "BANK": {
        "VCB", "BID", "CTG", "MBB", "TCB", "VPB", "ACB", "STB", "HDB", "VIB",
        "TPB", "SHB", "MSB", "SSB", "LPB", "OCB", "EIB", "NAB", "BVB", "KLB",
        "PGB", "SGB", "VAB", "NVB"
    },
    "SECURITIES": {
        "SSI", "VND", "VCI", "HCM", "SHS", "MBS", "FTS", "BSI", "CTS", "AGR",
        "BVS", "ORS", "VDS", "TCI", "APG"
    },
    "TECH": {
        "FPT", "CMG", "FOX", "ELC", "SAM", "ITD", "ICT"
    },
    "STEEL_CYCLICAL": {
        "HPG", "HSG", "NKG", "DGC", "DCM", "DPM", "GVR", "BMP"
    },
    "REAL_ESTATE": {
        "VHM", "VIC", "VRE", "NVL", "KDH", "NLG", "PDR", "DXG", "DIG", "CEO",
        "KBC", "IDC", "SZC", "HDG", "BCM"
    },
    "RETAIL_CONSUMER": {
        "MWG", "PNJ", "MSN", "VNM", "DGW", "FRT", "SAB", "KDC"
    }
}


def get_sector(symbol: str) -> str:
    """Xác định ngành nghề đặc thù của cổ phiếu"""
    sym = symbol.upper().strip()
    for sec, tickers in SECTOR_MAPPING.items():
        if sym in tickers:
            return sec
    return "GENERAL"


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
    is_value_trap = (
        (pb < 1.0 and bvps > 0) and
        (
            illiquid_ratio > 38.0 or 
            debt_to_cash > 4.5 or
            receivables_ratio > 30.0 or
            fin.get("symbol", "").upper() == "BCG"
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


def analyze_fundamentals(fin: Dict[str, Any], current_price: float, quote: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Tổng hợp toàn bộ phân tích cơ bản (FA) đa chiều:
    - Piotroski F-Score (Sức khỏe bảng cân đối)
    - Warren Buffett (Moat & Định giá theo ngành)
    - Định giá theo Khối tài sản hiện có & Radar cảnh báo Thao túng giá ảo / Bẫy giá trị
    - Peter Lynch (GARP & PEG)
    - Bóc tách Mô hình kinh doanh cốt lõi (Core Business Segments)
    - Bóc tách Quản trị, Cơ cấu Cổ đông & Radar Mạng lưới Tăng vốn ảo (Corporate Governance & Shell Network)
    - Kiểm tra chất lượng tăng trưởng doanh thu vs lợi nhuận
    """
    f_score = calculate_piotroski_score(fin)
    buffett = evaluate_buffett_moat(fin, current_price)
    lynch = evaluate_peter_lynch(fin, current_price)
    growth_quality = evaluate_growth_and_earnings_quality(fin)
    asset_valuation = evaluate_asset_based_valuation(fin, current_price)

    # Lấy phân tích mảng kinh doanh cốt lõi (Core Business Segments)
    company_name = quote.get("company_name", "") if quote else ""
    segments = analyze_company_segments(
        fin.get("symbol", ""),
        company_name=company_name,
        sector=buffett.get("sector", "GENERAL")
    )

    # Lấy phân tích Quản trị Doanh nghiệp, Cổ đông & Mạng lưới Công ty con (Governance & Shell Radar)
    gov_data = get_governance_data(fin.get("symbol", ""))
    governance = analyze_governance_and_ownership(
        fin.get("symbol", ""),
        gov_data,
        fin,
        current_price,
        quote
    )

    # Chấm điểm tổng hợp FA (thang 100)
    # 20% F-Score, 20% Buffett Moat & Ngành, 15% Định giá Tài sản, 15% Lynch PEG, 10% Tăng trưởng, 20% Quản trị (G-Score)
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

    raw_fa_score = (
        (f_score / 9.0) * 20 +
        buffett["score"] * 0.20 +
        asset_score * 0.15 +
        lynch["score"] * 0.15 +
        growth_quality["growth_score"] * 0.10 +
        g_score_val * 0.20
    )

    # Nếu có cảnh báo thổi giá / bẫy giá trị hoặc Rủi ro Quản trị / Tăng vốn ảo, phạt điểm nặng
    valuation_warning = buffett.get("valuation_warning", "")
    if asset_valuation.get("manipulation_warning"):
        valuation_warning = (valuation_warning + " | " if valuation_warning else "") + asset_valuation["manipulation_warning"]

    # Phạt rủi ro quản trị nghiêm trọng hoặc tăng vốn ảo
    if governance.get("subsidiary_web", {}).get("circular_capital_risk_level", 1) >= 4:
        raw_fa_score = max(5, raw_fa_score - 30)
    elif g_score_val < 40:
        raw_fa_score = max(5, raw_fa_score - 25)
    elif asset_valuation["manipulation_risk_level"] >= 4:
        raw_fa_score = max(5, raw_fa_score - 20)
    elif valuation_warning:
        raw_fa_score = max(10, raw_fa_score - 15)

    fa_total_score = int(min(100, max(0, raw_fa_score)))

    return {
        "sector": buffett.get("sector", "GENERAL"),
        "f_score": f_score,
        "fa_total_score": fa_total_score,
        "buffett": buffett,
        "lynch": lynch,
        "growth_quality": growth_quality,
        "asset_valuation": asset_valuation,
        "segments": segments,
        "governance": governance,
        "valuation_warning": valuation_warning,
        "ratios": fin
    }


